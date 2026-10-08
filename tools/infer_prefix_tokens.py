#!/usr/bin/env python3
"""Infer a short measured token trace from bit mutations; not a sensor decoder.

Boundaries must be supported by observed sign/one/two-unit mutations. Widths
are fitted to those boundaries, not supplied by an assumed adaptive algorithm.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

from inspect_orf import MAX_FILE, inspect


def infer(path, reports, max_index=128):
    record = inspect(path)
    if len(record['strips']) != 1 or record['sensor'][0]*record['sensor'][1] > 32_000_000:
        raise ValueError('requires one strip and at most 32 million samples')
    observations = {}
    sources = []
    sensor_values = {}
    for report_path in reports:
        if report_path.stat().st_size > 4*1024*1024:
            raise ValueError('report exceeds observation budget')
        report_bytes = report_path.read_bytes()
        report = json.loads(report_bytes)
        if report['input_sha256'] != record['sha256']:
            raise ValueError('report belongs to a different original')
        sources.append(dict(file=report_path.name,sha256=hashlib.sha256(report_bytes).hexdigest()))
        for case in report['experiments']:
            x = case.get('first_changed_index_row_major')
            if x is None or not 0 <= x < min(record['sensor'][0],max_index):
                continue
            bit = case['strip_byte']*8+7-case['bit_lsb_index']
            delta = (case['first_changed_after']-case['first_changed_before']+32768)%65536-32768
            if bit in observations and observations[bit] != (x,delta):
                raise ValueError('conflicting repeated observations')
            observations[bit] = (x,delta)
            value = case['first_changed_before']
            if x in sensor_values and sensor_values[x] != value:
                raise ValueError('conflicting reference baseline values')
            sensor_values[x] = value
    starts = {}
    for bit,(x,delta) in sorted(observations.items()):
        second,third = observations.get(bit+1),observations.get(bit+2)
        if (abs(delta)%8 == 4 and second is not None and third is not None
                and second[0] == third[0] == x and abs(second[1]) == 2 and abs(third[1]) == 1):
            starts.setdefault(x,[]).append(dict(bit=bit,sign_delta=delta))
    with path.open('rb') as stream:
        data = stream.read(MAX_FILE+1)
    if len(data) > MAX_FILE or hashlib.sha256(data).hexdigest() != record['sha256']:
        raise ValueError('original changed during measurement')
    strip_at = record['strips'][0]['offset']
    source = data[strip_at:strip_at+min(record['strips'][0]['size_bytes'],4096)]
    bits = ''.join(f'{byte:08b}' for byte in source)
    tokens = []
    for x,candidates in sorted(starts.items()):
        next_candidates = starts.get(x+1,[])
        if len(candidates) != 1 or len(next_candidates) != 1:
            tokens.append(dict(x=x,boundary_candidates=candidates,status='missing or ambiguous next boundary'))
            continue
        start,end = candidates[0]['bit'],next_candidates[0]['bit']
        cursor = start+3
        if not 0 <= start < cursor < end <= len(bits):
            raise ValueError('invalid measured boundary')
        flags = int(bits[start:cursor],2)
        zeros = 0
        while zeros < 12 and cursor < end and bits[cursor] == '0':
            cursor += 1
            zeros += 1
        if zeros == 12:
            if cursor+12 > end:
                tokens.append(dict(x=x,start_bit=start,end_bit_exclusive=end,status='initial escape hypothesis conflicts with boundary'))
                continue
            quotient = int(bits[cursor:cursor+11],2)
            extra = int(bits[cursor+11])
            cursor += 12
        else:
            quotient = zeros
            extra = int(bits[cursor])
            cursor += 1
        width = end-cursor
        if not 0 <= width <= 16:
            tokens.append(dict(x=x,start_bit=start,end_bit_exclusive=end,status='unsupported inferred width',width=width))
            continue
        remainder = int(bits[cursor:end],2) if width else 0
        q = (quotient << width)+remainder
        mutation_q = (abs(candidates[0]['sign_delta'])-4)//8
        signed_high = ~q if flags&4 else q
        raw_code = 4*signed_high+(flags&3)
        predictors = {'zero':0}
        if x-1 in sensor_values:
            predictors['previous_sample'] = sensor_values[x-1]
        if x-2 in sensor_values:
            predictors['same_colour_left'] = sensor_values[x-2]
        if x-2 in sensor_values and x-4 in sensor_values:
            predictors['same_colour_linear'] = 2*sensor_values[x-2]-sensor_values[x-4]
        corrections = {name:sensor_values[x]-prediction-raw_code for name,prediction in predictors.items()}
        tokens.append(dict(x=x,start_bit=start,end_bit_exclusive=end,flags=flags,
                           zeros=zeros,quotient=quotient,extra_or_stop=extra,
                           remainder_width=width,remainder=remainder,unsigned_high=q,
                           sign_mutation_inferred_high=mutation_q,high_matches_mutation=q==mutation_q,
                           signed_high=signed_high,raw_signed_code=raw_code,sample=sensor_values[x],
                           predictor_corrections=corrections,status='measured trace'))
    return dict(schema=1,input_sha256=record['sha256'],source_reports=sources,
                method_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                interpretation='measured-first-row-token-boundaries-only',tokens=tokens)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input',type=Path)
    parser.add_argument('--reports',type=Path,nargs='+',required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--max-index',type=int,default=128)
    args = parser.parse_args()
    if args.output.exists() or not 1 <= len(args.reports) <= 8 or not 1 <= args.max_index <= 8192:
        raise ValueError('choose a new output path and one to eight reports')
    result = infer(args.input,args.reports,args.max_index)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(result,stream,indent=2)
        stream.write('\n')
    for token in result['tokens']:
        if token['status'] == 'measured trace':
            print(token['x'],token['remainder_width'],token['signed_high'],token['sample'],
                  token['predictor_corrections'].get('same_colour_left',token['predictor_corrections']['zero']),
                  token['high_matches_mutation'])
        else:
            print(token['x'],token['status'])
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError,ValueError,KeyError,TypeError) as error:
        print(f'token inference failed: {error}',file=sys.stderr)
        sys.exit(1)
