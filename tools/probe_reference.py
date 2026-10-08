#!/usr/bin/env python3
"""Isolated black-box strip-byte perturbations; observations, not a compressed format specification.

Each worker decodes the original and a one-byte mutation using a pinned binary
rawpy runtime. Only sample differences are reported. Decoder source and colour
calibration data are never inspected. Native failures/timeouts stay in a child.
"""

import argparse
import hashlib
import io
import json
import subprocess
import sys
from pathlib import Path

from inspect_orf import inspect


def worker(path, runtime, offset):
    record = inspect(path)
    strips = record["strips"]
    if len(strips) != 1 or not 0 <= offset < strips[0]["size_bytes"]:
        raise ValueError("experiment requires one strip and an in-range byte offset")
    sys.path.insert(0, str(runtime.resolve()))
    import numpy as np
    import rawpy

    data = path.read_bytes()
    with rawpy.imread(io.BytesIO(data)) as reference:
        original = reference.raw_image.copy()
    altered = bytearray(data)
    altered[strips[0]["offset"] + offset] ^= 1
    with rawpy.imread(io.BytesIO(altered)) as reference:
        changed = reference.raw_image
        if changed.shape != original.shape:
            raise ValueError("mutation changed the output geometry")
        mask = original != changed
        rows = np.flatnonzero(mask.any(axis=1))
        columns = np.flatnonzero(mask.any(axis=0))
        return {
            "strip_byte": offset, "xor": 1,
            "rawpy": rawpy.__version__, "libraw": list(rawpy.libraw_version),
            "baseline_sensor_sha256_le_u16": hashlib.sha256(original.astype("<u2", copy=False).tobytes()).hexdigest(),
            "changed_samples": int(np.count_nonzero(mask)),
            "bounding_box_xyxy_inclusive": [int(columns[0]), int(rows[0]), int(columns[-1]), int(rows[-1])] if rows.size else None,
        }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--reference-runtime", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--bytes", nargs="+", type=int, default=list(range(10)) + [16, 128, 4096])
    parser.add_argument("--worker", type=int)
    args = parser.parse_args()
    try:
        if args.worker is not None:
            print(json.dumps(worker(args.input, args.reference_runtime, args.worker)))
            return 0
        if args.output is None:
            raise ValueError("--output is required")
        if len(args.bytes) > 64:
            raise ValueError("at most 64 perturbations per run")
        record = inspect(args.input)
        result = {"schema": 1, "input_sha256": record["sha256"], "interpretation": "reference-behaviour-only", "experiments": []}
        for offset in args.bytes:
            command = [sys.executable, str(Path(__file__).resolve()), str(args.input), "--reference-runtime", str(args.reference_runtime), "--worker", str(offset)]
            try:
                run = subprocess.run(command, capture_output=True, text=True, timeout=20, check=False)
                if run.returncode == 0:
                    observation = json.loads(run.stdout)
                else:
                    observation = {"strip_byte": offset, "error": run.stderr.strip()[-800:], "returncode": run.returncode}
            except subprocess.TimeoutExpired:
                observation = {"strip_byte": offset, "error": "worker exceeded 20 seconds"}
            result["experiments"].append(observation)
            print(json.dumps(observation), flush=True)
        with args.output.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(result, stream, indent=2)
            stream.write("\n")
        return 0
    except Exception as error:
        # The optional native instrument has its own exception hierarchy. Fail the
        # experiment explicitly; do not classify its errors as camera-format rules.
        print(f"reference experiment failed: {type(error).__name__}: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
