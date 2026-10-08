#!/usr/bin/env python3
"""Measure a preregistered two-value prefix hypothesis; not a complete ORF decoder."""
import argparse
import json
import subprocess
import sys
from pathlib import Path

from inspect_orf import inspect


def candidate(path):
    record = inspect(path)
    if len(record['strips']) != 1 or record['sensor'][0]*record['sensor'][1] > 32_000_000:
        raise ValueError('requires one strip and at most 32 million declared samples')
    source = bytes.fromhex(record['strips'][0]['prefix_32_hex'])
    if source[:7] != bytes((0,0,0,0,1,0,0)):
        raise ValueError('outside the observed prefix-hypothesis scope')
    bits = ''.join(f'{byte:08b}' for byte in source)
    cursor = 56

    def take(count):
        nonlocal cursor
        if cursor+count > len(bits):
            raise ValueError('hypothesis exhausted the observed prefix')
        first = cursor
        cursor += count
        return int(bits[first:cursor],2)

    fields = []
    for _ in range(2):
        first = cursor
        flags = take(3)
        zeros = 0
        while zeros < 12 and cursor < len(bits) and bits[cursor] == '0':
            zeros += 1
            cursor += 1
        quotient = take(11) if zeros == 12 else zeros
        extra_or_stop = take(1)
        remainder = take(4)
        high = 16*quotient+remainder
        value = (4*(~high if flags&4 else high)+(flags&3)) & 65535
        fields.append(dict(start_bit=first,end_bit_exclusive=cursor,flags=flags,zero_count=zeros,
                           quotient=quotient,terminator_or_extra_bit=extra_or_stop,remainder=remainder,
                           high_part=high,candidate_value=value))
    return dict(file=path.name,input_sha256=record['sha256'],fields=fields,
                interpretation='initial-two-values-only')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('inputs',type=Path,nargs='+')
    parser.add_argument('--reference-runtime',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    if args.output.exists() or not 1 <= len(args.inputs) <= 16:
        raise ValueError('choose a new output path and 1 to 16 inputs')
    # All predictions precede reference acquisition, including held-out inputs.
    results = [candidate(path) for path in args.inputs]
    for result in results:
        print('candidate before reference:',result['file'],[f['candidate_value'] for f in result['fields']],flush=True)
    failed = False
    if args.reference_runtime:
        worker = Path(__file__).resolve().with_name('probe_bit_influence.py')
        for path,result in zip(args.inputs,results):
            command = [sys.executable,str(worker),str(path),'--reference-runtime',str(args.reference_runtime),
                       '--worker','7','0','--xor-mask','0']
            try:
                run = subprocess.run(command,capture_output=True,text=True,timeout=20,check=False)
                if run.returncode:
                    result['reference_error'] = run.stderr.strip()[-800:]
                    failed = True
                    continue
                reference = json.loads(run.stdout)
                values = reference['first_row_before'][:2]
                matches = [f['candidate_value']==v for f,v in zip(result['fields'],values)]
                result.update(rawpy=reference['rawpy'],libraw=reference['libraw'],
                              reference_first_two_values=values,matches=matches)
                failed |= len(matches) != 2 or not all(matches)
                print('reference:',result['file'],values,matches,flush=True)
            except subprocess.TimeoutExpired:
                result['reference_error'] = 'worker exceeded 20 seconds'
                failed = True
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(dict(schema=1,protocol='research/compressed-next-experiment.md',
                       all_candidates_precede_reference=True,cases=results),stream,indent=2)
        stream.write('\n')
    return int(failed)


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f'initial-token experiment failed: {error}',file=sys.stderr)
        sys.exit(1)
