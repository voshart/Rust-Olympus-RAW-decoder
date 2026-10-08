#!/usr/bin/env python3
"""Fit the recorded median/average decision family to measured neighbour triples."""
import argparse
import hashlib
import json
import sys
from pathlib import Path


def metrics(left,above,diagonal):
    a,b = abs(left-diagonal),abs(above-diagonal)
    return dict(maximum=max(a,b),minimum=min(a,b),sum=a+b,
                separation=abs(left-above),curvature=abs(left+above-2*diagonal))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('trace',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    if args.output.exists() or args.trace.stat().st_size>1024*1024:
        raise ValueError('choose a new output and a bounded trace')
    raw = args.trace.read_bytes()
    trace = json.loads(raw)
    triples = trace['observations']
    if not 1<=len(triples)<=1024:
        raise ValueError('one to 1024 measured triples required')
    fits,counts = [],[]
    for inclusive in [False,True]:
        for metric in ['maximum','minimum','sum','separation','curvature']:
            exact = 0
            for threshold in range(129):
                valid = True
                for row in triples:
                    left,above,diagonal = row['left'],row['above'],row['diagonal']
                    product = (left-diagonal)*(above-diagonal)
                    between = product<=0 if inclusive else product<0
                    use_average = between and metrics(left,above,diagonal)[metric]<=threshold
                    candidate = (left+above)//2 if use_average else sorted([left,above,left+above-diagonal])[1]
                    if candidate!=row['required_predictor']:
                        valid = False
                        break
                if valid:
                    exact += 1
                    fits.append(dict(diagonal_between_inclusive=inclusive,metric=metric,threshold=threshold))
            counts.append(dict(inclusive=inclusive,metric=metric,exact_fits=exact,tested=129))
    result = dict(schema=1,protocol='research/compressed-next-experiment.md',
                  method_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  trace_sha256=hashlib.sha256(raw).hexdigest(),observations=len(triples),
                  family_counts=counts,fits=fits)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(result,stream,indent=2)
        stream.write('\n')
    print('exact fits:',fits)
    return 0


if __name__=='__main__':
    try:
        sys.exit(main())
    except (OSError,ValueError,KeyError,TypeError) as error:
        print(f'predictor fit failed: {error}',file=sys.stderr)
        sys.exit(1)
