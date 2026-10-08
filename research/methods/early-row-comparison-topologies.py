#!/usr/bin/env python3
"""Compare bounded early-row prediction/reset hypotheses; not a full RAW decoder."""
import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

from inspect_orf import MAX_FILE, inspect
from measure_first_row_models import digest_row


def prediction(grid,row,x,config):
    if x<2:
        border = config['border']
        if border=='previous_row_end':
            return grid[row-1][-2+x] if row else 0
        distance = 1 if border=='above_one' else 2
        if border=='zero' or row<distance:
            return 0
        return grid[row-distance][x]
    left = grid[row][x-2]
    distance = config.get('row_distance',2)
    mode = config.get('predictor','left')
    if row<distance or mode=='left':
        return left
    above,diagonal = grid[row-distance][x],grid[row-distance][x-2]
    gradient = left+above-diagonal
    if mode=='above': return above
    if mode=='gradient': return gradient
    if mode=='median': return sorted([left,above,gradient])[1]
    if mode=='average': return (left+above)//2
    if mode=='left_half_gradient': return left+(above-diagonal)//2
    if mode=='above_half_gradient': return above+(left-diagonal)//2
    if mode=='paeth': return min([left,above,diagonal],key=lambda v:abs(v-gradient))
    raise ValueError('unknown predictor hypothesis')


def predict_grid(bits,width,rows,model,config):
    cursor = 56
    states = [[0,0,0] for _ in range(2)]
    grid = []
    row_ends = []

    def take(n):
        nonlocal cursor
        if not 0<=n<=16 or cursor+n>len(bits):
            raise ValueError('candidate exhausted bounded stream window')
        at = cursor
        cursor += n
        return int(bits[at:cursor],2) if n else 0

    for row in range(rows):
        if row:
            alignment = config['alignment_bits']
            cursor = (cursor+alignment-1)//alignment*alignment
            reset = config['reset']
            if reset.startswith('row_') or reset.startswith('pair_') and row%2==0:
                for state in states:
                    if reset.endswith(('all','width')):
                        state[0:2] = [0,0]
                    if reset.endswith(('all','bias')):
                        state[2] = 0
        grid.append([])
        for x in range(width):
            magnitude,count,bias = states[x%2]
            warm = count<3
            k = max(4 if warm else 2,magnitude.bit_length()-(2 if warm else 0))
            flags = take(3)
            zeros = 0
            while zeros<12 and cursor<len(bits) and bits[cursor]=='0':
                zeros += 1
                cursor += 1
            quotient = take(15-k) if zeros==12 else zeros
            take(1)
            q = (quotient<<k)+take(k)
            signed = ~q if flags&4 else q
            difference = signed+bias
            pixel = (prediction(grid,row,x,config)+4*difference+(flags&3))&65535
            grid[row].append(pixel)
            states[x%2] = [q,count+1 if q<=16 else 0,(3*difference+bias)>>5]
        row_ends.append(cursor)
    return grid,row_ends


def write_new(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(value,stream,indent=2)
        stream.write('\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('inputs',type=Path,nargs='+')
    parser.add_argument('--models',type=Path,required=True)
    parser.add_argument('--rows',type=int,required=True)
    parser.add_argument('--reference-runtime',type=Path,required=True)
    parser.add_argument('--predictions-output',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    if args.output.exists() or args.predictions_output.exists() or not 1<=len(args.inputs)<=4 or not 2<=args.rows<=16:
        raise ValueError('choose new outputs, one to four files, and two to sixteen rows')
    if args.models.stat().st_size>1024*1024:
        raise ValueError('model manifest exceeds budget')
    manifest = json.loads(args.models.read_text())
    configs = manifest['models']
    if not 1<=len(configs)<=256:
        raise ValueError('one to 256 models required')
    records = [inspect(path) for path in args.inputs]
    total = sum(record['sensor'][0]*args.rows for record in records)*len(configs)
    if total>4_000_000:
        raise ValueError('candidate matrix exceeds four-million-value budget')
    candidates = []
    internal = []
    for path,record in zip(args.inputs,records):
        width,height = record['sensor']
        if len(record['strips'])!=1 or width>8192 or height<args.rows or width*height>32_000_000:
            raise ValueError('unsupported declared geometry')
        with path.open('rb') as stream:
            data = stream.read(MAX_FILE+1)
        if len(data)>MAX_FILE or hashlib.sha256(data).hexdigest()!=record['sha256']:
            raise ValueError('original changed during experiment')
        strip = record['strips'][0]
        bits = ''.join(f'{b:08b}' for b in data[strip['offset']:strip['offset']+min(strip['size_bytes'],262144)])
        cases,values = [],{}
        for config in configs:
            case = dict(model_id=config['id'])
            try:
                grid,ends = predict_grid(bits,width,args.rows,manifest['token_model'],config)
                values[config['id']] = grid
                case.update(row_sha256_le_u16=[digest_row(row) for row in grid],row_end_bits=ends,
                            first_values_per_row=[row[:16] for row in grid],
                            above_declared_12bit_count=sum(v>4095 for row in grid for v in row))
            except ValueError as error:
                case['candidate_error'] = str(error)
            cases.append(case)
        candidates.append(dict(file=path.name,input_sha256=record['sha256'],sensor=record['sensor'],
                               tested_rows=args.rows,sample_count=width*args.rows,comparisons=cases))
        internal.append(values)
        print('predicted before reference:',path.name,len(values),'candidate matrices',flush=True)
    method_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    write_new(args.predictions_output,dict(schema=1,method_sha256=method_hash,
        protocol='research/compressed-next-experiment.md',model_manifest=manifest,
        all_predictions_precede_reference=True,reference_acquired=False,cases=candidates))
    results = []
    worker = Path(__file__).with_name('probe_bit_influence.py').resolve()
    for path,record,values in zip(args.inputs,records,internal):
        width = record['sensor'][0]
        command = [sys.executable,str(worker),str(path),'--reference-runtime',str(args.reference_runtime),
                   '--worker','7','0','--xor-mask','0','--row-prefix-count',str(width),'--rows-prefix-count',str(args.rows)]
        try:
            run = subprocess.run(command,capture_output=True,text=True,timeout=20,check=True)
            reference = json.loads(run.stdout)
            actual = reference['prefix_rows_before']
            if len(actual)!=args.rows or any(len(row)!=width for row in actual):
                raise ValueError('reference prefix geometry differs')
        except (ValueError,KeyError,subprocess.SubprocessError) as error:
            results.append(dict(file=path.name,reference_error=str(error)[-800:]))
            continue
        comparisons = []
        for config in configs:
            grid = values.get(config['id'])
            if grid is None:
                comparisons.append(dict(model_id=config['id'],candidate_error=True))
                continue
            differences = [(x,y) for y,row in enumerate(grid) for x,(v,a) in enumerate(zip(row,actual[y])) if v!=a]
            first = differences[0] if differences else None
            comparisons.append(dict(model_id=config['id'],different_samples=len(differences),
                first_mismatch_xy=list(first) if first is not None else None,
                first_candidate_value=grid[first[1]][first[0]] if first is not None else None,
                first_reference_value=actual[first[1]][first[0]] if first is not None else None))
        result = {key:reference[key] for key in ['rawpy','libraw','numpy','sensor_shape','reference_geometry','baseline_sensor_sha256_le_u16']}
        result.update(file=path.name,input_sha256=record['sha256'],tested_rows=args.rows,sample_count=width*args.rows,
                      reference_row_sha256_le_u16=[digest_row(row) for row in actual],
                      reference_first_values_per_row=[row[:16] for row in actual],comparisons=comparisons)
        results.append(result)
        print('reference:',path.name,sum(c.get('different_samples')==0 for c in comparisons),'exact row models',flush=True)
    write_new(args.output,dict(schema=1,method_sha256=method_hash,protocol='research/compressed-next-experiment.md',
                              predictions_file=args.predictions_output.name,all_predictions_precede_reference=True,cases=results))
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError,ValueError,KeyError,TypeError,subprocess.SubprocessError) as error:
        print(f'early-row hypothesis experiment failed: {error}',file=sys.stderr)
        sys.exit(1)
