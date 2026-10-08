#!/usr/bin/env python3
"""Prospectively compare fitted first-row hypotheses; not a complete ORF decoder."""
import argparse
import hashlib
import json
import struct
import subprocess
import sys
from collections import Counter
from pathlib import Path

from inspect_orf import MAX_FILE, inspect


def digest_row(values):
    return hashlib.sha256(struct.pack('<'+'H'*len(values),*values)).hexdigest()


def hypotheses(fit_path):
    if fit_path.stat().st_size > 1024*1024:
        raise ValueError('fit report exceeds budget')
    report = json.loads(fit_path.read_text())
    if 'models' in report:
        if not 1 <= len(report['models']) <= 1024:
            raise ValueError('one to 1024 models required')
        return report['models']
    biases = []
    for fit in next(s for s in report['bias_search'] if s['channels']==2)['fits']:
        for rounding in range(fit['rounding_offset_min'],fit['rounding_offset_max']+1):
            biases.append(dict(a=fit['a'],b=fit['b'],shift=fit['shift'],rounding=rounding))
    widths = next(s for s in report['width_search'] if s['channels']==2)['fits']
    models = [dict(id=f'B{i:02}-W{j:02}',bias=bias,width=width)
              for i,bias in enumerate(biases) for j,width in enumerate(widths)]
    if not 1 <= len(models) <= 1024:
        raise ValueError('one to 1024 fitted models required')
    return models


def predict(bits,count,model,steps=None):
    cursor = 56
    states = [[0,0,0,0] for _ in range(2)]  # magnitude, count, bias, left
    values = []
    histogram = Counter()
    escape_count = 0

    def take(n):
        nonlocal cursor
        if not 0 <= n <= 16 or cursor+n > len(bits):
            raise ValueError('candidate exhausted bounded stream window')
        start = cursor
        cursor += n
        return int(bits[start:cursor],2) if n else 0

    for x in range(count):
        start_bit = cursor
        magnitude,small_count,bias,left = states[x%2]
        width_model = model['width']
        warm = small_count < width_model['required_small_count']
        k = max(4 if warm else width_model['stable_base'],
                magnitude.bit_length()-(2 if warm else width_model['stable_shift']))
        if not 0 <= k <= 16:
            raise ValueError('candidate width outside bounded scope')
        histogram[k] += 1
        flags = take(3)
        escape = model.get('escape',{})
        limit = 16-k if escape.get('zero_limit')=='16-minus-k' else 12
        if not 1 <= limit <= 16:
            raise ValueError('candidate escape threshold outside scope')
        zeros = 0
        while zeros < limit and cursor < len(bits) and bits[cursor]=='0':
            zeros += 1
            cursor += 1
        payload = 15-k if escape.get('payload_bits')=='15-minus-k' else 11
        quotient = take(payload) if zeros==limit else zeros
        take(1)
        escape_count += zeros==limit
        q = (quotient << k)+take(k)
        signed = ~q if flags&4 else q
        difference = signed+bias
        pixel = (left+4*difference+(flags&3)) & 65535
        values.append(pixel)
        bias_model = model['bias']
        next_bias = (bias_model['a']*difference+bias_model['b']*bias+bias_model['rounding']) >> bias_model['shift']
        decay = width_model['decay_shift']
        next_magnitude = q+(magnitude >> decay if decay is not None else 0)
        threshold = 1 << width_model['small_threshold_log2']
        small = q <= threshold if width_model.get('inclusive_small_threshold',False) else q < threshold
        next_count = small_count+1 if small else 0
        states[x%2] = [next_magnitude,next_count,next_bias,pixel]
        if steps is not None:
            steps.append(dict(x=x,start_bit=start_bit,end_bit_exclusive=cursor,k=k,
                              flags=flags,zeros=zeros,q=q,signed_high=signed,difference=difference,
                              sample=pixel,state_before=[magnitude,small_count,bias,left],
                              state_after=states[x%2].copy()))
    return values,dict(end_bit_exclusive=cursor,width_histogram=dict(histogram),escape_count=escape_count)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('inputs',type=Path,nargs='+')
    parser.add_argument('--fits',type=Path,required=True)
    parser.add_argument('--reference-runtime',type=Path,required=True)
    parser.add_argument('--predictions-output',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    if args.predictions_output.exists() or args.output.exists() or not 1 <= len(args.inputs) <= 4:
        raise ValueError('choose new outputs and one to four inputs')
    models = hypotheses(args.fits)
    predictions = []
    internal_rows = []
    for path in args.inputs:
        record = inspect(path)
        width,height = record['sensor']
        if len(record['strips'])!=1 or width>8192 or width*height>32_000_000:
            raise ValueError('requires one strip, width <=8192 and at most 32 million samples')
        with path.open('rb') as stream:
            data = stream.read(MAX_FILE+1)
        if len(data)>MAX_FILE or hashlib.sha256(data).hexdigest()!=record['sha256']:
            raise ValueError('original changed during prediction')
        strip = record['strips'][0]
        source = data[strip['offset']:strip['offset']+min(strip['size_bytes'],65536)]
        if source[:7] != bytes((0,0,0,0,1,0,0)):
            raise ValueError('outside observed prefix scope')
        bits = ''.join(f'{byte:08b}' for byte in source)
        cases,rows = [],{}
        for model in models:
            case = dict(model=model)
            try:
                values,trace = predict(bits,width,model)
                rows[model['id']] = values
                case.update(trace,row_sha256_le_u16=digest_row(values),first_values=values[:16],
                            above_declared_12bit_count=sum(v>4095 for v in values))
            except ValueError as error:
                case['candidate_error'] = str(error)
            cases.append(case)
        predictions.append(dict(file=path.name,input_sha256=record['sha256'],tested_row=0,
                                sample_count=width,models=cases))
        internal_rows.append(rows)
        print('predicted before reference:',path.name,len(rows),'bounded candidate rows',flush=True)
    method_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    for destination,value in [(args.predictions_output,dict(schema=1,protocol='research/compressed-next-experiment.md',
            method_sha256=method_hash,fit_report_sha256=hashlib.sha256(args.fits.read_bytes()).hexdigest(),
            all_predictions_precede_reference=True,reference_acquired=False,cases=predictions))]:
        destination.parent.mkdir(parents=True,exist_ok=True)
        with destination.open('x',encoding='utf-8',newline='\n') as stream:
            json.dump(value,stream,indent=2)
            stream.write('\n')
    results = []
    worker = Path(__file__).resolve().with_name('probe_bit_influence.py')
    for path,prediction,rows in zip(args.inputs,predictions,internal_rows):
        command = [sys.executable,str(worker),str(path),'--reference-runtime',str(args.reference_runtime),
                   '--worker','7','0','--xor-mask','0','--row-prefix-count',str(prediction['sample_count'])]
        run = subprocess.run(command,capture_output=True,text=True,timeout=20,check=True)
        reference = json.loads(run.stdout)
        actual = reference['first_row_before']
        if len(actual)!=prediction['sample_count']:
            raise ValueError('reference row geometry differs from declared width')
        comparisons = []
        for model in models:
            values = rows.get(model['id'])
            if values is None:
                comparisons.append(dict(model_id=model['id'],candidate_error=True))
                continue
            differences = [i for i,(v,a) in enumerate(zip(values,actual)) if v!=a]
            first = differences[0] if differences else None
            comparisons.append(dict(model_id=model['id'],different_samples=len(differences),
                first_mismatch_xy=[first,0] if first is not None else None,
                first_candidate_value=values[first] if first is not None else None,
                first_reference_value=actual[first] if first is not None else None))
        result = {key:reference[key] for key in ['rawpy','libraw','numpy','sensor_shape','reference_geometry','baseline_sensor_sha256_le_u16']}
        result.update(file=path.name,input_sha256=prediction['input_sha256'],tested_row=0,sample_count=len(actual),
                      reference_row_sha256_le_u16=digest_row(actual),reference_first_values=actual[:16],comparisons=comparisons)
        results.append(result)
        print('reference:',path.name,sum(c.get('different_samples')==0 for c in comparisons),'exact first-row models',flush=True)
    with args.output.open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(dict(schema=1,protocol='research/compressed-next-experiment.md',method_sha256=method_hash,
                       predictions_file=args.predictions_output.name,all_predictions_precede_reference=True,cases=results),stream,indent=2)
        stream.write('\n')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError,ValueError,KeyError,TypeError,subprocess.SubprocessError) as error:
        print(f'first-row hypothesis experiment failed: {error}',file=sys.stderr)
        sys.exit(1)
