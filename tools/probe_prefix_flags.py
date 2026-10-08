#!/usr/bin/env python3
"""Test preregistered first-pixel flag predictions against an isolated binary reference."""
import argparse
import json
import subprocess
import sys
from pathlib import Path

from inspect_orf import inspect


def run(args, mask):
    script = Path(__file__).resolve().with_name('probe_bit_influence.py')
    command = [sys.executable,str(script),str(args.input),'--reference-runtime',str(args.reference_runtime),
               '--worker','7','0','--xor-mask',str(mask)]
    try:
        result = subprocess.run(command,capture_output=True,text=True,timeout=20,check=False)
        if result.returncode == 0:
            return json.loads(result.stdout)
        return dict(xor_mask=mask,error=result.stderr.strip()[-800:],returncode=result.returncode)
    except subprocess.TimeoutExpired:
        return dict(xor_mask=mask,error='worker exceeded 20 seconds')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input',type=Path)
    parser.add_argument('--reference-runtime',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError('choose a new output path')
    record = inspect(args.input)
    if len(record['strips']) != 1:
        raise ValueError('requires one observed compressed strip')
    prefix = bytes.fromhex(record['strips'][0]['prefix_32_hex'])
    if len(prefix) < 8:
        raise ValueError('strip is too short for the proposed byte-7 experiment')
    flags = prefix[7] >> 5
    zero = run(args,0)
    if 'error' in zero:
        raise ValueError('unmodified reference case failed')
    first = zero['first_row_before'][0]
    if flags & 4 or flags & 3 != first & 3:
        raise ValueError('original is outside the preregistered positive/low-bit scope')
    high = first // 4
    cases = [zero] + [run(args,mask) for mask in (32,64,96,128,160,192,224)]
    for case in cases:
        changed_flags = (prefix[7] ^ case['xor_mask']) >> 5
        magnitude = high*4+(changed_flags&3)
        h4 = (-magnitude if changed_flags&4 else magnitude) & 65535
        h5 = ((~high if changed_flags&4 else high)*4+(changed_flags&3)) & 65535
        case.update(changed_flags=changed_flags,predicted_signed_magnitude_u16=h4,
                    predicted_complemented_high_u16=h5)
        if 'error' not in case:
            actual = case['first_row_after'][0]
            case.update(actual_first_u16=actual,signed_magnitude_matches=actual==h4,
                        complemented_high_matches=actual==h5)
    result = dict(schema=1,input_sha256=record['sha256'],original_byte7=prefix[7],
                  original_first_u16=first,original_high_part=high,
                  interpretation='local-reference-transform-only',
                  protocol='research/compressed-next-experiment.md',experiments=cases,
                  successful=sum('error' not in c for c in cases),
                  signed_magnitude_matches=sum(c.get('signed_magnitude_matches',False) for c in cases),
                  complemented_high_matches=sum(c.get('complemented_high_matches',False) for c in cases))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(result,stream,indent=2);stream.write('\n')
    print(json.dumps({k:v for k,v in result.items() if k!='experiments'}),flush=True)
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f'prefix experiment failed: {error}',file=sys.stderr)
        sys.exit(1)
