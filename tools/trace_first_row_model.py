#!/usr/bin/env python3
"""Inspect a bounded window of an experimental first-row candidate without a reference."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

from inspect_orf import MAX_FILE, inspect
from measure_first_row_models import hypotheses, predict


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input',type=Path)
    parser.add_argument('--models',type=Path,required=True)
    parser.add_argument('--model-id',required=True)
    parser.add_argument('--start',type=int,required=True)
    parser.add_argument('--end',type=int,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    if args.output.exists() or not 0 <= args.start < args.end <= 8192 or args.end-args.start>64:
        raise ValueError('choose a new output and a window of at most 64 pixels')
    model = next(m for m in hypotheses(args.models) if m['id']==args.model_id)
    record = inspect(args.input)
    if len(record['strips'])!=1 or args.end>record['sensor'][0]:
        raise ValueError('window must be within the declared first row')
    with args.input.open('rb') as stream:
        data = stream.read(MAX_FILE+1)
    if len(data)>MAX_FILE or hashlib.sha256(data).hexdigest()!=record['sha256']:
        raise ValueError('original changed during tracing')
    strip = record['strips'][0]
    bits = ''.join(f'{b:08b}' for b in data[strip['offset']:strip['offset']+min(strip['size_bytes'],65536)])
    steps = []
    predict(bits,args.end,model,steps)
    report = dict(schema=1,input_sha256=record['sha256'],model=model,
                  predictor_method_sha256=hashlib.sha256(Path(__file__).with_name('measure_first_row_models.py').read_bytes()).hexdigest(),
                  interpretation='candidate-trace-only',tokens=steps[args.start:args.end])
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(report,stream,indent=2)
        stream.write('\n')
    for token in report['tokens']:
        print(token)
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError,ValueError,KeyError,TypeError,StopIteration) as error:
        print(f'candidate tracing failed: {error}',file=sys.stderr)
        sys.exit(1)
