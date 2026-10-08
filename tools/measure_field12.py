#!/usr/bin/env python3
"""Measure the observed C-5050 packed-pair/separate-field hypothesis; no decoder source."""
import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path

from inspect_orf import MAX_FILE, Tiff


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('--reference-runtime', type=Path, required=True)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if args.input.stat().st_size > MAX_FILE:
        raise ValueError('file exceeds observation budget')
    with args.input.open('rb') as stream:
        data = stream.read(MAX_FILE + 1)
    if len(data) > MAX_FILE or data[:4] != b'IIRS':
        raise ValueError('not the observed IIRS packed layout')
    tiff = Tiff(data)
    ifd = tiff.ifd(tiff.first)
    width, height = tiff.scalar(ifd,0x100), tiff.scalar(ifd,0x101)
    rps = tiff.scalar(ifd,0x116)
    if (not width or not height or width < 4 or height < 3 or width % 2 or width * height > 64_000_000
            or not rps or tiff.value(ifd,0x102) != [12] or tiff.scalar(ifd,0x103) != 1):
        raise ValueError('unverified packing or excessive geometry')
    offsets, counts = tiff.value(ifd,0x111), tiff.value(ifd,0x117)
    row_bytes = width // 2 * 3
    even_rows, odd_rows = (height + 1) // 2, height // 2
    expected = [min(rps, rows-y) * row_bytes
                for rows in (even_rows,odd_rows) for y in range(0,rows,rps)]
    if counts != expected or len(offsets) != len(counts):
        raise ValueError('strips do not match the proposed separate-field framing')
    source = b''.join(tiff.bytes(at,n) for at,n in zip(offsets,counts))
    sys.path.insert(0,str(args.reference_runtime.resolve()))
    import numpy as np
    # Standard MSB-first three-byte pairs are the proposed packing. Word reversal
    # and sequential rows are explicit alternatives, measured before reference use.
    def pairs_msb(src):
        pairs = np.frombuffer(src,dtype=np.uint8).reshape(-1,3).astype(np.uint16)
        samples = np.empty((len(pairs),2),dtype=np.uint16)
        samples[:,0] = (pairs[:,0] << 4) | (pairs[:,1] >> 4)
        samples[:,1] = ((pairs[:,1] & 15) << 8) | pairs[:,2]
        return samples.reshape(height,width)

    stored = pairs_msb(source)
    mapped = np.empty_like(stored)
    mapped[::2] = stored[:even_rows]
    mapped[1::2] = stored[even_rows:]
    def metrics(image):
        signed = image.astype(np.int32)
        return dict(horizontal_same_parity_mean_difference=float(np.mean(np.abs(signed[:,2:]-signed[:,:-2]))),
                    vertical_same_parity_mean_difference=float(np.mean(np.abs(signed[2:,:]-signed[:-2,:]))))
    hypotheses = dict(msb_sequential=metrics(stored),msb_separate_fields=metrics(mapped))
    if row_bytes % 4 == 0:
        words = np.frombuffer(source,dtype=np.uint8).reshape(height,-1,4)
        hypotheses['le32_msb_sequential'] = metrics(pairs_msb(words[:,:,::-1].copy().tobytes()))
    result = dict(input_sha256=hashlib.sha256(data).hexdigest(),declared_sensor=[width,height],
                  strip_lengths=counts,hypotheses=hypotheses,
                  candidate_sha256_le_u16=hashlib.sha256(mapped.astype('<u2').tobytes()).hexdigest())
    import rawpy
    with rawpy.imread(str(args.input)) as raw:
        reference = raw.raw_image
        if reference.shape[1] != width or not height <= reference.shape[0] <= height + 1:
            raise ValueError('reference geometry is outside the compared scope')
        declared = reference[:height,:]
        result['reference'] = dict(rawpy=rawpy.__version__,libraw=list(rawpy.libraw_version),numpy=np.__version__,
            full_reference_shape=list(reference.shape),compared_samples=int(mapped.size),
            sequential_mismatches=int(np.count_nonzero(stored!=declared)),
            separate_field_mismatches=int(np.count_nonzero(mapped!=declared)),
            sensor_sha256_le_u16=hashlib.sha256(declared.astype('<u2').tobytes()).hexdigest(),
            extra_reference_rows=int(reference.shape[0]-height),
            extra_reference_rows_nonzero_samples=int(np.count_nonzero(reference[height:,:])),
            scope='all declared rows; additional reference row excluded')
    text = json.dumps(result,indent=2) + '\n'
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        with args.output.open('x',encoding='utf-8') as stream:stream.write(text)
    else:
        print(text,end='')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError, TypeError, KeyError, ImportError, struct.error) as error:
        print(f'cannot measure packed fields: {error}',file=sys.stderr)
        sys.exit(1)
