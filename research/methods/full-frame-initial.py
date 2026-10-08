#!/usr/bin/env python3
"""Full-raster measurement of frozen E01/V02; not a product decoder."""
import argparse
from array import array
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

from inspect_orf import MAX_FILE, inspect
from measure_row_models import write_new

MAX_SAMPLES = 96_000_000
MASKS = tuple((1 << n) - 1 for n in range(17))
# Hash of canonical JSON from the immutable pre-prose E01/V02 checkpoint.
FROZEN_MODEL_SHA256 = '0ce37940608bc56c3895c06d83cac051481066501bbec663be21ec4c24088a06'


class BoundedBits:
    """MSB-first measurements, preserving logical rather than refill positions."""

    def __init__(self, data, start_bit=56):
        if start_bit != 56 or len(data) < 7:
            raise ValueError('requires the independently observed seven-byte prefix')
        self.data = data
        self.byte = 7
        self.buffer = 0
        self.available = 0
        self.position = start_bit
        self.limit = len(data) * 8

    def fill(self, width):
        while self.available < width:
            end = min(self.byte + 8, len(self.data))
            chunk = self.data[self.byte:end]
            if not chunk:
                raise EOFError('missing required compressed bits')
            self.buffer = ((self.buffer & ((1 << self.available) - 1))
                           << (len(chunk) * 8)) | int.from_bytes(chunk, 'big')
            self.available += len(chunk) * 8
            self.byte = end

    def take(self, width):
        if not 0 <= width <= 16:
            raise ValueError('candidate coding width outside measured range')
        if self.position + width > self.limit:
            raise EOFError('missing required compressed bits')
        if self.available < width:
            self.fill(width)
        self.available -= width
        self.position += width
        return (self.buffer >> self.available) & MASKS[width]

    def zeros(self):
        width = min(12, self.limit - self.position)
        if width < 1:
            raise EOFError('missing required prefix bits')
        if self.available < width:
            self.fill(width)
        look = (self.buffer >> (self.available - width)) & MASKS[width]
        count = width - look.bit_length()
        if count == width and width < 12:
            raise EOFError('missing required prefix terminator')
        self.available -= count
        self.position += count
        return count


def trailer(data, end_bit):
    if not 0 <= end_bit <= len(data) * 8:
        raise ValueError('invalid candidate end position')
    partial_count = (8 - end_bit % 8) % 8
    partial = data[end_bit // 8] & MASKS[partial_count] if partial_count else 0
    tail = data[(end_bit + 7) // 8:]
    counts = Counter(tail)
    return dict(unused_bits=len(data) * 8 - end_bit,
                partial_byte_unused_bits=partial_count,
                partial_byte_low_value=partial,
                complete_unused_bytes=len(tail),
                complete_unused_zero_bytes=counts.get(0, 0),
                unused_nonzero_bit_count=partial.bit_count()
                + sum(byte.bit_count() * count for byte, count in counts.items()),
                first_32_complete_unused_bytes_hex=tail[:32].hex(),
                last_32_complete_unused_bytes_hex=tail[-32:].hex())


def candidate_rows(data, width, height, trace=None):
    """Exactly the frozen rules, retaining two previous rows and one current row."""
    if (not 1 <= width <= 16384 or not 1 <= height <= 20000
            or width * height > MAX_SAMPLES):
        raise ValueError('candidate raster exceeds research budgets')
    if data[:7] != b'\x00\x00\x00\x00\x01\x00\x00':
        raise ValueError('unobserved compressed prefix')
    bits = BoundedBits(data)
    take, zeros = bits.take, bits.zeros
    history = []
    for y in range(height):
        current = array('H')
        above = history[0] if y >= 2 else None
        magnitude, small, bias = [0, 0], [0, 0], [0, 0]
        outside_12 = outside_u16 = maximum_q = maximum_k = 0
        for x in range(width):
            parity = x & 1
            warm = small[parity] < 3
            k = max(4 if warm else 2,
                    magnitude[parity].bit_length() - (2 if warm else 0))
            start_bit = bits.position
            flags = take(3)
            run = zeros()
            quotient = take(15 - k) if run == 12 else run
            take(1)
            q = (quotient << k) + take(k)
            difference = (~q if flags & 4 else q) + bias[parity]
            if x < 2:
                predicted = above[x] if above is not None else 0
            else:
                left = current[x - 2]
                if above is None:
                    predicted = left
                else:
                    up, diagonal = above[x], above[x - 2]
                    a, b = left - diagonal, up - diagonal
                    if a * b < 0 and max(abs(a), abs(b)) <= 32:
                        predicted = (left + up) // 2
                    else:
                        gradient = left + up - diagonal
                        predicted = max(min(left, up), min(max(left, up), gradient))
            sample = predicted + 4 * difference + (flags & 3)
            outside_u16 += not 0 <= sample <= 65535
            value = sample & 65535
            outside_12 += value > 4095
            current.append(value)
            magnitude[parity] = q
            small[parity] = small[parity] + 1 if q <= 16 else 0
            bias[parity] = (3 * difference + bias[parity]) // 32
            maximum_q = max(maximum_q, q)
            maximum_k = max(maximum_k, k)
            if trace is not None and y == height - 1 and x >= width - 16:
                trace.append(dict(x=x, y=y, start_bit=start_bit,
                                  end_bit_exclusive=bits.position,
                                  k=k, flags=flags, q=q, sample=value))
        yield current, bits.position, dict(above_12bit_count=outside_12,
            outside_u16_before_wrap_count=outside_u16, maximum_q=maximum_q,
            maximum_k=maximum_k)
        history.append(current)
        if len(history) > 2:
            del history[0]


def row_bytes(row):
    if sys.byteorder == 'little':
        return row.tobytes()
    copy = array('H', row)
    copy.byteswap()
    return copy.tobytes()


def full_candidate(path, record, sensor_path):
    with path.open('rb') as stream:
        data = stream.read(MAX_FILE + 1)
    if len(data) > MAX_FILE or hashlib.sha256(data).hexdigest() != record['sha256']:
        raise ValueError('original changed during experiment')
    width, height = record['sensor']
    strips = record['strips']
    if (len(strips) != 1 or record['byte_order'] != '<'
            or record['compression'] != 1
            or record.get('image_processing', {}).get('valid_bits') != [12, 0]):
        raise ValueError('outside observed single-strip 12-bit profile')
    strip = strips[0]
    compressed = data[strip['offset']:strip['offset'] + strip['size_bytes']]
    if len(compressed) != strip['size_bytes']:
        raise ValueError('short declared strip')
    digest = hashlib.sha256()
    row_hashes, row_ends, edge_rows, trace = [], [], [], []
    counts = dict(above_12bit_count=0, outside_u16_before_wrap_count=0,
                  maximum_q=0, maximum_k=0)
    start = time.monotonic()
    with sensor_path.open('xb') as stream:
        for y, (row, end_bit, metrics) in enumerate(candidate_rows(compressed, width, height, trace)):
            block = row_bytes(row)
            stream.write(block)
            digest.update(block)
            row_hashes.append(hashlib.sha256(block).hexdigest())
            row_ends.append(end_bit)
            for key in ('above_12bit_count', 'outside_u16_before_wrap_count'):
                counts[key] += metrics[key]
            for key in ('maximum_q', 'maximum_k'):
                counts[key] = max(counts[key], metrics[key])
            if y < 2 or y >= height - 2:
                edge_rows.append(dict(y=y, first_16=list(row[:16]), last_16=list(row[-16:])))
            if (y + 1) % 512 == 0:
                print(f'candidate {path.name}: {y + 1}/{height} rows', flush=True)
    return dict(sensor_sha256_le_u16=digest.hexdigest(), sample_count=width * height,
                sensor_dump=sensor_path.name, row_sha256_le_u16=row_hashes,
                row_end_bits=row_ends, final_bit_exclusive=row_ends[-1],
                trailer=trailer(compressed, row_ends[-1]), edge_rows=edge_rows,
                last_16_tokens=trace, candidate_elapsed_seconds=round(time.monotonic() - start, 3),
                **counts)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('inputs', type=Path, nargs='+')
    parser.add_argument('--models', type=Path, required=True)
    parser.add_argument('--reference-runtime', type=Path, required=True)
    parser.add_argument('--sensor-dir', type=Path, required=True)
    parser.add_argument('--predictions-output', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    repo = Path(__file__).resolve().parent.parent
    if (not 1 <= len(args.inputs) <= 8 or args.output.exists()
            or args.predictions_output.exists()
            or not args.sensor_dir.resolve().is_relative_to(repo / '.work')):
        raise ValueError('use new outputs, one to eight inputs and an ignored .work sensor directory')
    with args.models.open('rb') as stream:
        model_bytes = stream.read(1024 * 1024 + 1)
    if len(model_bytes) > 1024 * 1024:
        raise ValueError('model manifest exceeds budget')
    model = json.loads(model_bytes)
    canonical_hash = hashlib.sha256(json.dumps(model, sort_keys=True, separators=(',', ':')).encode('utf-8')).hexdigest()
    if canonical_hash != FROZEN_MODEL_SHA256:
        raise ValueError('this experiment requires the unchanged pre-prose E01/V02 model')
    records = [inspect(path) for path in args.inputs]
    if sum(record['sensor'][0] * record['sensor'][1] for record in records) > 512_000_000:
        raise ValueError('batch exceeds 512 million declared samples')
    args.sensor_dir.mkdir(parents=True, exist_ok=True)
    candidates = []
    for path, record in zip(args.inputs, records):
        result = dict(file=path.name, input_sha256=record['sha256'],
            sensor=record['sensor'], cfa=record['cfa'],
            image_processing=record.get('image_processing'), strips=record['strips'])
        sensor = args.sensor_dir / (path.stem + '.u16le')
        try:
            result['candidate'] = full_candidate(path, record, sensor)
        except (OSError, ValueError, EOFError) as error:
            result['candidate_error'] = str(error)
        candidates.append(result)
        print('candidate saved before reference:', path.name,
              result.get('candidate_error', 'complete'), flush=True)
    worker = Path(__file__).with_name('probe_bit_influence.py').resolve()
    common = dict(schema=1, protocol='research/compressed-next-experiment.md',
        method_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        reference_worker_sha256=hashlib.sha256(worker.read_bytes()).hexdigest(),
        model_manifest_sha256=hashlib.sha256(model_bytes).hexdigest(), model_manifest=model,
        all_predictions_precede_reference=True)
    write_new(args.predictions_output, dict(**common, reference_acquired=False, cases=candidates))
    comparisons = []
    for path, record, candidate in zip(args.inputs, records, candidates):
        result = dict(file=path.name, input_sha256=record['sha256'], sensor=record['sensor'])
        if 'candidate_error' in candidate:
            result['candidate_error'] = candidate['candidate_error']
        else:
            command = [sys.executable, str(worker), str(path), '--reference-runtime',
                str(args.reference_runtime), '--worker', '7', '0', '--xor-mask', '0',
                '--candidate-sensor', str(args.sensor_dir / candidate['candidate']['sensor_dump'])]
            try:
                run = subprocess.run(command, capture_output=True, text=True, timeout=20, check=True)
                reference = json.loads(run.stdout)
                result.update(reference=reference,
                    hash_agrees=candidate['candidate']['sensor_sha256_le_u16'] == reference['baseline_sensor_sha256_le_u16'])
                if reference['full_sensor_comparison']['candidate_sha256_le_u16'] != candidate['candidate']['sensor_sha256_le_u16']:
                    raise ValueError('candidate changed before comparison')
                print('full reference:', path.name,
                      reference['full_sensor_comparison']['different_samples'], 'differences', flush=True)
            except (OSError, ValueError, KeyError, subprocess.SubprocessError) as error:
                result['reference_error'] = str(error)[-1000:]
        comparisons.append(result)
    write_new(args.output, dict(**common, predictions_file=args.predictions_output.name, cases=comparisons))
    return int(any('reference_error' in item or 'candidate_error' in item
                   or not item.get('hash_agrees', False)
                   or item.get('reference', {}).get('full_sensor_comparison', {}).get('different_samples') != 0
                   for item in comparisons))


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError, KeyError, TypeError, EOFError, subprocess.SubprocessError) as error:
        print(f'full-raster experiment failed: {error}', file=sys.stderr)
        sys.exit(1)
