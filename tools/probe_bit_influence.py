#!/usr/bin/env python3
"""Isolated single-bit reference measurements, not an ORF decoder or specification."""
import argparse
import hashlib
import io
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from inspect_orf import MAX_FILE, inspect


def worker(path, runtime, byte, bit, xor_mask=None, row_prefix_count=16):
    record = inspect(path)
    strips = record['strips']
    if (len(strips) != 1 or not 0 <= byte < strips[0]['size_bytes']
            or not 0 <= bit < 8 or not 1 <= row_prefix_count <= 8192
            or record['sensor'][0]*record['sensor'][1] > 32_000_000):
        raise ValueError('requires one strip, an in-range bit, and at most 32 million samples')
    sys.path.insert(0,str(runtime.resolve()))
    import numpy as np
    import rawpy
    with path.open('rb') as stream:
        data = stream.read(MAX_FILE+1)
    if len(data) > MAX_FILE:
        raise ValueError('file grew beyond observation budget')
    with rawpy.imread(io.BytesIO(data)) as reference:
        original = reference.raw_image.copy()
        sizes = reference.sizes
        geometry = dict(sensor_wh=[sizes.raw_width,sizes.raw_height],
                        visible_origin_xy=[sizes.left_margin,sizes.top_margin],
                        visible_wh=[sizes.width,sizes.height])
    altered = bytearray(data)
    mutation = 1 << bit if xor_mask is None else xor_mask
    if not 0 <= mutation <= 255:
        raise ValueError('mutation must fit one byte')
    altered[strips[0]['offset']+byte] ^= mutation
    with rawpy.imread(io.BytesIO(altered)) as reference:
        changed = reference.raw_image
        if changed.shape != original.shape:
            raise ValueError('mutation changed reference geometry')
        mask = original != changed
        count = int(np.count_nonzero(mask))
        first = int(np.argmax(mask)) if count else None
        rows = np.flatnonzero(mask.any(axis=1))
        cols = np.flatnonzero(mask.any(axis=0))
        width = original.shape[1]
        return dict(strip_byte=byte,bit_lsb_index=bit if xor_mask is None else None,xor_mask=mutation,
            rawpy=rawpy.__version__,libraw=list(rawpy.libraw_version),numpy=np.__version__,
            baseline_sensor_sha256_le_u16=hashlib.sha256(original.astype('<u2',copy=False).tobytes()).hexdigest(),
            sensor_shape=list(original.shape),reference_geometry=geometry,changed_samples=count,
            first_changed_index_row_major=first,
            first_changed_xy=[first%width,first//width] if first is not None else None,
            first_changed_before=int(original.flat[first]) if first is not None else None,
            first_changed_after=int(changed.flat[first]) if first is not None else None,
            bounds_xyxy_inclusive=[int(cols[0]),int(rows[0]),int(cols[-1]),int(rows[-1])] if count else None,
            first_row_before=original[0,:row_prefix_count].tolist(),first_row_after=changed[0,:row_prefix_count].tolist())


def run_case(args, byte, bit):
    command = [sys.executable,str(Path(__file__).resolve()),str(args.input),
               '--reference-runtime',str(args.reference_runtime),'--worker',str(byte),str(bit)]
    try:
        run = subprocess.run(command,capture_output=True,text=True,timeout=20,check=False)
        if run.returncode == 0:
            return json.loads(run.stdout)
        return dict(strip_byte=byte,bit_lsb_index=bit,error=run.stderr.strip()[-800:],returncode=run.returncode)
    except subprocess.TimeoutExpired:
        return dict(strip_byte=byte,bit_lsb_index=bit,error='worker exceeded 20 seconds')


def summarize(cases):
    by_byte = {}
    for case in cases:
        by_byte.setdefault(case['strip_byte'],[]).append(case)
    summary = dict(successful=sum('error' not in c for c in cases),errors=sum('error' in c for c in cases),
                   strict_high_bit_first_pairs=0,strict_low_bit_first_pairs=0,tied_pairs=0,bytes=[])
    for byte, group in sorted(by_byte.items()):
        success = [c for c in group if c.get('first_changed_index_row_major') is not None]
        # Pairs are ordered by descending bit position: higher bits consumed first
        # would tend to affect earlier samples. Ties cannot discriminate.
        success.sort(key=lambda c:-c['bit_lsb_index'])
        for i, earlier in enumerate(success):
            for later in success[i+1:]:
                a,b = earlier['first_changed_index_row_major'],later['first_changed_index_row_major']
                key = 'strict_high_bit_first_pairs' if a < b else 'strict_low_bit_first_pairs' if a > b else 'tied_pairs'
                summary[key] += 1
        summary['bytes'].append(dict(strip_byte=byte,
            first_changed_indices_bits_7_to_0=[next((c.get('first_changed_index_row_major') for c in group if c['bit_lsb_index']==bit),None) for bit in range(7,-1,-1)]))
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input',type=Path)
    parser.add_argument('--reference-runtime',type=Path,required=True)
    parser.add_argument('--output',type=Path)
    parser.add_argument('--bytes',type=int,nargs='+',default=list(range(7,15)))
    parser.add_argument('--jobs',type=int,default=2)
    parser.add_argument('--worker',type=int,nargs=2,metavar=('BYTE','BIT'))
    parser.add_argument('--xor-mask',type=int,help=argparse.SUPPRESS)
    parser.add_argument('--row-prefix-count',type=int,default=16,help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.worker is not None:
        print(json.dumps(worker(args.input,args.reference_runtime,*args.worker,args.xor_mask,args.row_prefix_count)))
        return 0
    if args.output is None or args.output.exists():
        raise ValueError('choose a new --output path')
    if len(args.bytes) > 8 or not 1 <= args.jobs <= 4:
        raise ValueError('at most 64 cases, with 1 to 4 isolated workers')
    record = inspect(args.input)
    cases = [(byte,bit) for byte in args.bytes for bit in range(8)]
    observations = []
    with ThreadPoolExecutor(max_workers=args.jobs) as executor:
        for observation in executor.map(lambda case:run_case(args,*case),cases):
            observations.append(observation)
            if len(observations)%8 == 0:
                print(f'{len(observations)}/{len(cases)} isolated bit experiments recorded',flush=True)
    result = dict(schema=1,input_sha256=record['sha256'],interpretation='reference-behaviour-only',
                  protocol='research/compressed-next-experiment.md',experiments=observations,summary=summarize(observations))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(result,stream,indent=2);stream.write('\n')
    print(json.dumps(result['summary']),flush=True)
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as error:
        # Native instrument exceptions belong to the experiment, not product code.
        print(f'bit influence experiment failed: {type(error).__name__}: {error}',file=sys.stderr)
        sys.exit(1)
