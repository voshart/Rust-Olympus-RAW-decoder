#!/usr/bin/env python3
"""Compare LightCraft's Rust sensor output to the pinned complete-array reference hashes.

Build the product's orf_audit example first. All input identities, geometry,
sensor margins and LE-u16 reference hashes come from the recorded full-frame
summary; no web access or reference binary is needed for this replay.
"""

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", required=True, type=Path)
    parser.add_argument("--lightcraft", required=True, type=Path)
    parser.add_argument("--creators", required=True, type=Path)
    parser.add_argument("--external", required=True, type=Path)
    parser.add_argument("--sensor-dir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--summary", type=Path, default=Path("research/results/compressed-full-frame-summary.json"))
    args = parser.parse_args()
    summary = json.loads(args.summary.read_text(encoding="utf-8"))
    cases = []
    for original in summary["cases"]:
        name = original["file"]
        path = (args.external if name.startswith("pixls-") else args.creators) / name
        if sha256(path) != original["input_sha256"]:
            raise ValueError(f"input hash mismatch: {name}")
        completed = subprocess.run([str(args.binary), "--sensor-dir", str(args.sensor_dir), str(path)],
                                   capture_output=True, text=True, check=True)
        match = re.search(r": (\d+)x(\d+) bits=(\d+) cfa=(\w+) active=(.*?) probe=([0-9.]+)ms decode=([0-9.]+)ms", completed.stdout)
        if match is None:
            raise ValueError(f"no successful Rust sensor decode: {name}: {completed.stdout.strip()}")
        width, height, depth = map(int, match.group(1, 2, 3))
        dump = args.sensor_dir / (name + ".u16le")
        expected_size = original["sample_count"] * 2
        if [width, height] != original["sensor"] or dump.stat().st_size != expected_size:
            raise ValueError(f"sensor geometry/size mismatch: {name}")
        if depth != 12 or match.group(4) != original["cfa"]:
            raise ValueError(f"depth/CFA mismatch: {name}")
        actual = sha256(dump)
        reference = original["sensor_sha256_le_u16"]
        if actual != reference:
            raise ValueError(f"complete sensor hash mismatch: {name}")
        cases.append({
            "file": name, "input_sha256": original["input_sha256"],
            "sensor": [width, height], "sample_count": original["sample_count"],
            "bits": depth, "cfa": match.group(4), "active_area": match.group(5),
            "rust_sensor_sha256_le_u16": actual, "reference_sensor_sha256_le_u16": reference,
            "complete_arrays_equal": True, "excluded_sensor_margins": 0,
            "probe_full_info_equal": True, "probe_ms": float(match.group(6)), "decode_ms": float(match.group(7)),
        })
        print(f"{name}: {original['sample_count']:,} samples, exact complete-array hash match", flush=True)
    source_paths = ["crates/raw/src/vendor/olympus12.rs", "crates/raw/src/vendor/orf.rs", "crates/raw/src/vendor/mod.rs"]
    result = {
        "schema": 1, "method": "tools/validate_rust.py",
        "method_sha256": sha256(Path(__file__)), "reference_summary_sha256": sha256(args.summary),
        "rust_source_sha256": {name: sha256(args.lightcraft / name) for name in source_paths},
        "verified_rasters": len(cases), "verified_samples": sum(c["sample_count"] for c in cases),
        "differing_samples": 0, "comparison": "Full uncorrected LE-u16 sensor array SHA-256 equality to the pinned binary-reference outputs; no crops or margins excluded.",
        "cases": cases,
    }
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as error:
        print(error, file=sys.stderr)
        sys.exit(1)
