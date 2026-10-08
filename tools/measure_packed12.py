#!/usr/bin/env python3
"""Measure a 10-sample/16-byte packing hypothesis independently of a decoder.

The hypothesis was formed from strip size, zero padding, and masked-column
statistics before consulting reference pixels. --reference-runtime optionally
loads a separately installed rawpy binary for a black-box comparison. It never
reads decoder source, camera matrices, or camera calibration tables.
"""

import argparse
import hashlib
import json
import statistics
import sys
from pathlib import Path

from inspect_orf import inspect


def measure(path, runtime):
    record = inspect(path)
    w, h = record["sensor"]
    strips = record["strips"]
    if w % 10 or len(strips) != 1 or strips[0]["size_bytes"] != w * h // 10 * 16:
        raise ValueError("input does not meet the 10-sample/16-byte hypothesis")
    data = path.read_bytes()
    strip = strips[0]
    src = memoryview(data)[strip["offset"]:strip["offset"] + strip["size_bytes"]]
    padding_count = len(src) // 16
    nonzero_padding = sum(v != 0 for v in src[15::16])

    def sample(x, y, low_nibble):
        at = (y * w // 10 + x // 10) * 16 + (x % 10 // 2) * 3
        a, b, c = src[at:at + 3]
        if low_nibble:
            return (a | ((b & 15) << 8)) if x % 2 == 0 else ((b >> 4) | (c << 4))
        return ((a << 4) | (b >> 4)) if x % 2 == 0 else (((b & 15) << 8) | c)

    result = {
        "input_sha256": record["sha256"], "sensor": [w, h],
        "padding_count": padding_count, "nonzero_padding": nonzero_padding,
        "masked_column_candidates": {},
    }
    for name, low in (("low_nibble", True), ("high_nibble", False)):
        values = [sample(x, y, low) for y in range(0, h, 31) for x in range(8)]
        result["masked_column_candidates"][name] = {
            "count": len(values), "mean": statistics.mean(values), "stdev": statistics.pstdev(values),
            "min": min(values), "max": max(values),
        }
    if runtime:
        sys.path.insert(0, str(runtime.resolve()))
        import numpy as np
        import rawpy

        result["reference"] = {"rawpy": rawpy.__version__, "numpy": np.__version__, "libraw": list(rawpy.libraw_version)}
        with rawpy.imread(str(path)) as reference:
            pixels = reference.raw_image
            if pixels.shape != (h, w):
                raise ValueError(f"reference sensor shape {pixels.shape} differs from {(h, w)}")
            result["reference"]["sensor_sha256_le_u16"] = hashlib.sha256(pixels.astype("<u2", copy=False).tobytes()).hexdigest()
            result["reference"]["geometry"] = reference.sizes._asdict()
            mismatches = 0
            maximum_difference = 0
            candidate_hash = hashlib.sha256()
            for y in range(h):
                groups = np.frombuffer(src[y * w // 10 * 16:(y + 1) * w // 10 * 16], dtype=np.uint8).reshape(-1, 16)
                triplets = groups[:, :15].reshape(-1, 3).astype(np.uint16)
                row = np.empty(w, dtype=np.uint16)
                row[0::2] = triplets[:, 0] | ((triplets[:, 1] & 15) << 8)
                row[1::2] = (triplets[:, 1] >> 4) | (triplets[:, 2] << 4)
                difference = np.abs(row.astype(np.int32) - pixels[y].astype(np.int32))
                mismatches += int(np.count_nonzero(difference))
                maximum_difference = max(maximum_difference, int(difference.max()))
                candidate_hash.update(row.astype("<u2", copy=False).tobytes())
            result["reference"].update(
                compared_samples=w * h, mismatches=mismatches, maximum_difference=maximum_difference,
                candidate_sha256_le_u16=candidate_hash.hexdigest(),
            )
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--reference-runtime", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = measure(args.input, args.reference_runtime)
        with args.output.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(result, stream, indent=2)
            stream.write("\n")
        print(json.dumps(result, indent=2))
        return int(bool(result.get("reference", {}).get("mismatches", 0)))
    except (OSError, ValueError, KeyError, TypeError, ImportError) as error:
        print(f"measurement failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
