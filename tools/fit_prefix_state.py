#!/usr/bin/env python3
"""Search recorded small state families against measured traces, not raw pixels."""
import argparse
import hashlib
import json
import sys
from pathlib import Path


def load_trace(path):
    if path.stat().st_size > 1024*1024:
        raise ValueError('trace exceeds budget')
    data = path.read_bytes()
    result = json.loads(data)
    tokens = []
    for token in result['tokens']:
        if token['x'] != len(tokens) or token['status'] != 'measured trace':
            break
        if not token['high_matches_mutation']:
            raise ValueError('high-part hypothesis conflicts with mutation')
        correction = token['predictor_corrections']['zero' if token['x'] < 2 else 'same_colour_left']
        if correction%4:
            raise ValueError('same-colour correction is not a multiple of four')
        tokens.append(dict(x=token['x'],q=token['unsigned_high'],k=token['remainder_width'],
                           signed_high=token['signed_high'],bias=correction//4))
    if not 4 <= len(tokens) <= 128:
        raise ValueError('requires a short continuous measured prefix')
    return dict(file=path.name,sha256=hashlib.sha256(data).hexdigest(),tokens=tokens)


def bias_fits(traces,channels):
    transitions = []
    for trace in traces:
        tokens = trace['tokens']
        for i,token in enumerate(tokens[:-channels]):
            transitions.append((token['signed_high']+token['bias'],token['bias'],tokens[i+channels]['bias']))
    fits = []
    for shift in range(1,9):
        denominator = 1 << shift
        for a in range(17):
            for b in range(17):
                low,high = 0,denominator-1
                for difference,bias,target in transitions:
                    subtotal = a*difference+b*bias
                    low = max(low,target*denominator-subtotal)
                    high = min(high,(target+1)*denominator-1-subtotal)
                    if low > high:
                        break
                if low <= high:
                    fits.append(dict(a=a,b=b,shift=shift,rounding_offset_min=low,rounding_offset_max=high))
    return dict(channels=channels,transitions=len(transitions),fits=fits)


def width_fits(traces,channels):
    fits = []
    tested = 0
    for decay_shift in [None]+list(range(1,13)):
        for threshold_log in range(9):
            for required_count in range(1,9):
                for stable_base in range(1,5):
                    for stable_shift in range(4):
                        tested += 1
                        valid = True
                        for trace in traces:
                            states = [[0,0] for _ in range(channels)]
                            for token in trace['tokens']:
                                state = states[token['x']%channels]
                                magnitude,count = state
                                warm = count < required_count
                                k = max(4 if warm else stable_base,magnitude.bit_length()-(2 if warm else stable_shift))
                                if k != token['k']:
                                    valid = False
                                    break
                                q = token['q']
                                state[0] = q+(magnitude >> decay_shift if decay_shift is not None else 0)
                                state[1] = count+1 if q < 1 << threshold_log else 0
                            if not valid:
                                break
                        if valid:
                            fits.append(dict(decay_shift=decay_shift,small_threshold_log2=threshold_log,
                                             required_small_count=required_count,stable_base=stable_base,
                                             stable_shift=stable_shift))
    return dict(channels=channels,tested_models=tested,fits=fits)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('traces',type=Path,nargs='+')
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    if args.output.exists() or not 1 <= len(args.traces) <= 8:
        raise ValueError('choose a new output and one to eight traces')
    traces = [load_trace(path) for path in args.traces]
    result = dict(schema=1,protocol='research/compressed-next-experiment.md',
                  method_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  training=[dict(file=t['file'],sha256=t['sha256'],continuous_tokens=len(t['tokens'])) for t in traces],
                  bias_search=[bias_fits(traces,n) for n in [1,2]],
                  width_search=[width_fits(traces,n) for n in [1,2]])
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(result,stream,indent=2)
        stream.write('\n')
    for family in ['bias_search','width_search']:
        for search in result[family]:
            print(family,search['channels'],'channels:',len(search['fits']),'fits')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError,ValueError,KeyError,TypeError) as error:
        print(f'prefix-state fit failed: {error}',file=sys.stderr)
        sys.exit(1)
