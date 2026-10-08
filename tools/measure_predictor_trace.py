#!/usr/bin/env python3
"""Measure a short required-predictor trace from reference rows and experimental tokens."""
import argparse
import hashlib
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

from inspect_orf import MAX_FILE, inspect
from measure_row_models import predict_grid, write_new


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input',type=Path)
    parser.add_argument('--models',type=Path,required=True)
    parser.add_argument('--model-id',required=True)
    parser.add_argument('--reference-runtime',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    if args.output.exists() or args.models.stat().st_size>1024*1024:
        raise ValueError('choose a new output and a bounded model manifest')
    manifest = json.loads(args.models.read_text())
    config = next(m for m in manifest['models'] if m['id']==args.model_id)
    record = inspect(args.input)
    width,height = record['sensor']
    if len(record['strips'])!=1 or width>8192 or height<3 or width*height>32_000_000:
        raise ValueError('unsupported geometry')
    with args.input.open('rb') as stream:
        data = stream.read(MAX_FILE+1)
    if len(data)>MAX_FILE or hashlib.sha256(data).hexdigest()!=record['sha256']:
        raise ValueError('original changed during tracing')
    strip = record['strips'][0]
    bits = ''.join(f'{b:08b}' for b in data[strip['offset']:strip['offset']+min(strip['size_bytes'],262144)])
    steps = []
    predict_grid(bits,width,3,manifest['token_model'],config,steps)
    command = [sys.executable,str(Path(__file__).with_name('probe_bit_influence.py').resolve()),str(args.input),
        '--reference-runtime',str(args.reference_runtime),'--worker','7','0','--xor-mask','0',
        '--row-prefix-count',str(width),'--rows-prefix-count','3']
    run = subprocess.run(command,capture_output=True,text=True,timeout=20,check=True)
    reference = json.loads(run.stdout)
    rows = reference['prefix_rows_before']
    observations = []
    matches = Counter()
    for step in steps:
        x,y = step['x'],step['y']
        if y!=2 or not 2<=x<min(width,258):
            continue
        left,above,diagonal = rows[y][x-2],rows[y-2][x],rows[y-2][x-2]
        gradient = left+above-diagonal
        actual = rows[y][x]-step['raw_code']
        candidates = dict(left=left,above=above,gradient=gradient,
                          median=sorted([left,above,gradient])[1],average=(left+above)//2,
                          left_half_gradient=left+(above-diagonal)//2,
                          above_half_gradient=above+(left-diagonal)//2)
        equal = [name for name,value in candidates.items() if value==actual]
        matches.update(equal)
        observations.append(dict(x=x,y=y,left=left,above=above,diagonal=diagonal,
                                 required_predictor=actual,reference_sample=rows[y][x],
                                 raw_code=step['raw_code'],token=step,candidate_predictors=candidates,matches=equal))
    result = {key:reference[key] for key in ['rawpy','libraw','numpy','sensor_shape','reference_geometry','baseline_sensor_sha256_le_u16']}
    result.update(schema=1,input_sha256=record['sha256'],interpretation='exploratory-required-predictor-trace',
                  method_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  token_method_sha256=hashlib.sha256(Path(__file__).with_name('measure_row_models.py').read_bytes()).hexdigest(),
                  model=config,observations=observations,match_counts=dict(matches))
    write_new(args.output,result)
    print('candidate matches:',dict(matches))
    for row in observations:
        if 'median' not in row['matches']:
            print({key:row[key] for key in ['x','left','above','diagonal','required_predictor','matches']})
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError,ValueError,KeyError,TypeError,StopIteration,subprocess.SubprocessError) as error:
        print(f'predictor measurement failed: {error}',file=sys.stderr)
        sys.exit(1)
