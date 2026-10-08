#!/usr/bin/env python3
"""Check the research reader against independent bits and measured final tokens."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

from inspect_orf import MAX_FILE
from measure_full_frame import BoundedBits
from measure_row_models import write_new


def procedural_checks():
    prefix = bytes(7)
    data = prefix + bytes(range(256))
    oracle = ''.join(f'{byte:08b}' for byte in data)
    reader = BoundedBits(data)
    count = sequence = 0
    while reader.position < len(oracle):
        width = min(sequence % 17, len(oracle) - reader.position)
        position = reader.position
        expected = int(oracle[position:position + width], 2) if width else 0
        if reader.take(width) != expected or reader.position != position + width:
            raise ValueError('bit-string oracle disagrees with reservoir read')
        count += 1
        sequence += 1
    try:
        reader.take(1)
    except EOFError:
        pass
    else:
        raise ValueError('reader fabricated a bit after exhaustion')
    if reader.take(0) != 0:
        raise ValueError('empty field read changed at exhaustion')
    for number in range(65536):
        body = number.to_bytes(2, 'big')
        oracle = f'{number:016b}'[:12]
        expected = len(oracle) - len(oracle.lstrip('0'))
        reader = BoundedBits(prefix + body)
        if reader.zeros() != expected or reader.position != 56 + expected:
            raise ValueError('zero-prefix count disagrees with independent oracle')
        if expected < 12 and reader.take(1) != 1:
            raise ValueError('zero-prefix terminator differs')
    for number in range(256):
        reader = BoundedBits(prefix + bytes([number]))
        try:
            measured = reader.zeros()
        except EOFError:
            if number != 0:
                raise ValueError('reader rejected an available short terminator')
        else:
            expected = 8 - number.bit_length()
            if number == 0 or measured != expected or reader.take(1) != 1:
                raise ValueError('short prefix disagrees with independent oracle')
    return dict(variable_width_reads=count, exhaustive_two_byte_prefixes=65536,
                short_final_byte_prefixes=256, required_eof_rejected=True)


def replay_token(data, token):
    # Test instrumentation positions the reservoir at an independently recorded
    # token boundary; no discarded source bytes are supplied to required reads.
    reader = BoundedBits(data)
    start = token['start_bit']
    reader.byte = start // 8
    reader.position = reader.byte * 8
    reader.take(start % 8)
    flags = reader.take(3)
    run = reader.zeros()
    k = token['k']
    quotient = reader.take(15 - k) if run == 12 else run
    reader.take(1)
    q = (quotient << k) + reader.take(k)
    return flags, q, reader.position


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--predictions', type=Path, nargs='+', required=True)
    parser.add_argument('--external-dir', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists() or not 1 <= len(args.predictions) <= 8:
        raise ValueError('choose a new output and one to eight reports')
    repo = Path(__file__).resolve().parent.parent
    procedural = procedural_checks()
    cases = []
    for report_path in args.predictions:
        with report_path.open('rb') as stream:
            raw_report = stream.read(16 * 1024 * 1024 + 1)
        if len(raw_report) > 16 * 1024 * 1024:
            raise ValueError('prediction report exceeds budget')
        report = json.loads(raw_report)
        for case in report['cases']:
            candidate = case.get('candidate')
            if candidate is None:
                continue
            root = args.external_dir if case['file'].startswith('pixls-') else repo / 'corpus/voshart-olympus'
            path = (root / case['file']).resolve()
            if not path.is_relative_to(root.resolve()):
                raise ValueError('input identity escapes corpus directory')
            with path.open('rb') as stream:
                original = stream.read(MAX_FILE + 1)
            if len(original) > MAX_FILE or hashlib.sha256(original).hexdigest() != case['input_sha256']:
                raise ValueError('input changed after full prediction')
            strip = case['strips'][0]
            data = original[strip['offset']:strip['offset'] + strip['size_bytes']]
            token = candidate['last_16_tokens'][-1]
            expected = (token['flags'], token['q'], token['end_bit_exclusive'])
            if replay_token(data, token) != expected:
                raise ValueError('final-token replay differs from recorded fields')
            cuts = []
            for cut in range(token['start_bit'] // 8, (token['end_bit_exclusive'] + 7) // 8):
                try:
                    replay_token(data[:cut], token)
                except EOFError:
                    cuts.append(dict(strip_bytes_retained=cut, missing_required_bits_rejected=True))
                else:
                    raise ValueError('truncated final token was accepted')
            if not cuts:
                raise ValueError('no final-byte truncation exercised')
            cases.append(dict(file=case['file'], input_sha256=case['input_sha256'],
                final_token=token, intact_replay_agrees=True, truncations=cuts))
            print('strict final-token cuts:', case['file'], len(cuts), flush=True)
    reader_path = Path(__file__).with_name('measure_full_frame.py')
    write_new(args.output, dict(schema=1,
        method_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        reader_method_sha256=hashlib.sha256(reader_path.read_bytes()).hexdigest(),
        native_reference_acquired=False, procedural_checks=procedural, cases=cases))
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f'research reader bounds check failed: {error}', file=sys.stderr)
        sys.exit(1)
