#!/usr/bin/env python3
"""Record raw OlympusNew/OM SYSTEM fields; do not assign field roles or decode pixels.

This follow-up was motivated by user-supplied, source-derived prose. It measures
raw types/counts/values as a profile fingerprint; it does not adopt the prose's
generalized 14-bit coding interpretations. No decoder source is consulted.
"""

import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path

from inspect_orf import MAX_FILE, Tiff, exif_cfa


def observe(path):
    with path.open("rb") as stream:
        data = stream.read(MAX_FILE + 1)
    if len(data) > MAX_FILE:
        raise ValueError("input exceeds 512 MiB observation budget")
    tiff = Tiff(data)
    ifd = tiff.ifd(tiff.first)
    exif = tiff.ifd(tiff.scalar(ifd, 0x8769))
    note = exif.get(0x927C)
    if note is None:
        raise ValueError("no maker note")
    at = note[2]
    prefix = tiff.bytes(at, 16)
    if prefix.startswith(b"OLYMPUS\0"):
        order_at, ifd_at = 8, 12
    elif prefix.startswith(b"OM SYSTEM\0"):
        order_at, ifd_at = 12, 16
    else:
        raise ValueError("unexamined maker-note header")
    mark = tiff.bytes(at + order_at, 2)
    if mark not in (b"II", b"MM"):
        raise ValueError("unexamined maker-note byte order")
    order = "<" if mark == b"II" else ">"
    mn = tiff.ifd(at + ifd_at, base=at, order=order)
    ip_offset = tiff.scalar(mn, 0x2040)
    if ip_offset is None:
        raise ValueError("no ImageProcessing directory")
    ip = tiff.ifd(at + ip_offset, base=at, order=order)
    fields = {}
    for tag in [0x0611, *range(0x0640, 0x0654)]:
        entry = ip.get(tag)
        fields[f"{tag:04x}"] = None if entry is None else {
            "tiff_type": entry[0], "count": entry[1], "value": tiff.value(ip, tag)
        }
    return {
        "file": path.name, "input_sha256": hashlib.sha256(data).hexdigest(),
        "maker_prefix_hex": prefix.hex(), "maker_ifd_offset": ifd_at,
        "sensor": [tiff.scalar(ifd, 0x0100), tiff.scalar(ifd, 0x0101)],
        "bits_per_sample": tiff.value(ifd, 0x0102),
        "cfa": exif_cfa(tiff.value(exif, 0xA302), tiff.order),
        "fields": fields,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", type=Path, nargs="+")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    cases = []
    for path in args.inputs:
        try:
            cases.append(observe(path))
        except (OSError, ValueError, TypeError, struct.error) as error:
            print(f"{path.name}: {error}", file=sys.stderr)
            return 1
    result = {
        "schema": 1, "method": "tools/observe_profile.py",
        "method_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "motivation": "User-supplied source-derived prose; field roles are not adopted as coding rules.",
        "cases": cases,
    }
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    print(f"Recorded {len(cases)} unchanged originals.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
