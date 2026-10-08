#!/usr/bin/env python3
"""Read-only ORF container observations; no compressed-pixel decoder or third-party code.

Python 3.10+, standard library only. Output deliberately excludes GPS, serials,
capture timestamps, owner names, and camera JPEG pixels. Keep private manifests local.
"""

import argparse
import hashlib
import json
import math
import struct
import sys
from collections import Counter
from pathlib import Path

MAX_FILE = 512 * 1024 * 1024
TYPE_SIZE = {1: 1, 2: 1, 3: 2, 4: 4, 5: 8, 6: 1, 7: 1, 8: 2, 9: 4, 10: 8, 11: 4, 12: 8, 13: 4}


class Tiff:
    """Classic TIFF entry framing from the published TIFF/Exif structure."""

    def __init__(self, data, base=0):
        self.data = data
        self.base = base
        mark = self.bytes(base, 2)
        if mark not in (b"II", b"MM"):
            raise ValueError("missing TIFF byte order")
        self.order = "<" if mark == b"II" else ">"
        self.visited = set()
        self.first = self.uint(base + 4, "I") + base

    def bytes(self, offset, count):
        if offset < 0 or count < 0 or offset + count > len(self.data):
            raise ValueError(f"truncated range at {offset}, length {count}")
        return self.data[offset:offset + count]

    def uint(self, offset, fmt, order=None):
        return struct.unpack((order or self.order) + fmt, self.bytes(offset, struct.calcsize(fmt)))[0]

    def ifd(self, offset, base=None, order=None):
        base = self.base if base is None else base
        order = order or self.order
        key = (offset, base, order)
        if key in self.visited or len(self.visited) >= 32:
            raise ValueError("cyclic or excessive IFD traversal")
        self.visited.add(key)
        count = self.uint(offset, "H", order)
        if count > 4096:
            raise ValueError("excessive IFD entry count")
        self.bytes(offset + 2, count * 12 + 4)
        result = {}
        for index in range(count):
            entry = offset + 2 + index * 12
            tag, typ, num = struct.unpack(order + "HHI", self.bytes(entry, 8))
            if typ not in TYPE_SIZE:
                continue
            length = TYPE_SIZE[typ] * num
            at = entry + 8 if length <= 4 else base + self.uint(entry + 8, "I", order)
            # Record a location, not a copy of a potentially huge undefined blob.
            self.bytes(at, 0)
            result[tag] = (typ, num, at, length, order)
        return result

    def value(self, entries, tag):
        entry = entries.get(tag)
        if entry is None:
            return None
        typ, count, at, length, order = entry
        if length > 65536:
            raise ValueError(f"tag {tag:#x} exceeds observation budget")
        raw = self.bytes(at, length)
        if typ == 2:
            return raw.rstrip(b"\0").decode("ascii", errors="replace")
        if typ in (1, 7):
            return list(raw)
        formats = {3: "H", 4: "I", 8: "h", 9: "i", 11: "f", 12: "d", 13: "I"}
        if typ in formats:
            return list(struct.unpack(order + formats[typ] * count, raw))
        return None

    def scalar(self, entries, tag):
        value = self.value(entries, tag)
        return value[0] if isinstance(value, list) and value else None


def exif_cfa(raw, order):
    if raw is None or len(raw) != 8:
        return None
    width, height = struct.unpack(order + "HH", bytes(raw[:4]))
    values = raw[4:]
    if (width, height) != (2, 2) or sorted(values) != [0, 1, 1, 2]:
        return None
    # Only diagonal greens are Bayer layouts; adjacent greens are invalid here.
    if values[0] == values[3] == 1 or values[1] == values[2] == 1:
        return "".join("RGB"[v] for v in values)
    return None


def jpeg_size(data):
    at = 2
    while at + 4 <= len(data):
        if data[at] != 0xFF:
            return None
        marker = data[at + 1]
        at += 2
        if marker == 0xFF:
            at -= 1
            continue
        if marker in (0xD9, 0xDA):
            return None
        if marker in (0x01, 0xD8) or 0xD0 <= marker <= 0xD7:
            continue
        length = int.from_bytes(data[at:at + 2], "big")
        if length < 2 or at + length > len(data):
            return None
        if marker in (0xC0, 0xC1, 0xC2) and length >= 8:
            return [int.from_bytes(data[at + 5:at + 7], "big"), int.from_bytes(data[at + 3:at + 5], "big")]
        at += length
    return None


def inspect(path):
    size = path.stat().st_size
    if size > MAX_FILE:
        raise ValueError("file exceeds 512 MiB observation budget")
    with path.open("rb") as stream:
        data = stream.read(MAX_FILE + 1)
    if len(data) > MAX_FILE:
        raise ValueError("file grew beyond observation budget")
    record = {"file": path.name, "size_bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
    if data.startswith(b"\xff\xd8"):
        record.update(kind="jpeg", dimensions=jpeg_size(data))
        return record
    if data[:4] not in (b"IIRO", b"IIRS", b"MMOR"):
        raise ValueError("not an ORF or JPEG observation input")
    tiff = Tiff(data)
    ifd = tiff.ifd(tiff.first)
    exif_at = tiff.scalar(ifd, 0x8769)
    exif = tiff.ifd(exif_at) if exif_at is not None else {}
    cfa = tiff.value(exif, 0xA302)
    record.update(
        kind="orf", magic=data[:4].decode("ascii"), byte_order=tiff.order,
        make=tiff.value(ifd, 0x010F), model=tiff.value(ifd, 0x0110),
        sensor=[tiff.scalar(ifd, 0x0100), tiff.scalar(ifd, 0x0101)],
        bits_per_sample=tiff.value(ifd, 0x0102), compression=tiff.scalar(ifd, 0x0103),
        rows_per_strip=tiff.scalar(ifd, 0x0116), cfa_bytes=cfa, cfa=exif_cfa(cfa, tiff.order),
        lens_model=tiff.value(exif, 0xA434),
    )
    if any(not isinstance(v, int) or v <= 0 for v in record["sensor"]) or math.prod(record["sensor"]) > (1 << 30):
        raise ValueError("invalid or excessive sensor dimensions")
    note = exif.get(0x927C)
    if note:
        at = note[2]
        if data[at:at + 10] == b"OLYMPUS\0II":
            mn = tiff.ifd(at + 12, base=at, order="<")
            ip_offset = tiff.scalar(mn, 0x2040)
            if ip_offset is not None:
                ip = tiff.ifd(at + ip_offset, base=at, order="<")
                record["image_processing"] = {
                    name: tiff.value(ip, tag) for name, tag in (
                        ("valid_bits", 0x0611), ("black_levels", 0x0600),
                        ("crop_left", 0x0612), ("crop_top", 0x0613),
                        ("crop_width", 0x0614), ("crop_height", 0x0615),
                    )
                }
    offsets = tiff.value(ifd, 0x0111) or []
    counts = tiff.value(ifd, 0x0117) or []
    if len(offsets) != len(counts) or len(offsets) > 4096:
        raise ValueError("missing or excessive strip offsets/counts")
    strips = []
    for offset, count in zip(offsets, counts):
        src = tiff.bytes(offset, count)
        window = src[:min(len(src), 1024 * 1024)]
        frequencies = Counter(window)
        entropy = -sum((n / len(window)) * math.log2(n / len(window)) for n in frequencies.values()) if window else 0.0
        strips.append({
            "offset": offset, "size_bytes": count, "sha256": hashlib.sha256(src).hexdigest(),
            "prefix_32_hex": src[:32].hex(), "first_mib_byte_entropy": round(entropy, 6),
        })
    record["strips"] = strips
    record["stored_bits_per_sensor_sample"] = round(sum(counts) * 8 / math.prod(record["sensor"]), 6)
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", nargs="+", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    paths = []
    for path in args.inputs:
        if path.is_dir():
            paths.extend(p for p in path.iterdir() if p.suffix.lower() in (".orf", ".jpg", ".jpeg"))
        else:
            paths.append(path)
    records = []
    failed = False
    for path in sorted(paths, key=lambda p: str(p).lower()):
        try:
            records.append(inspect(path))
        except (OSError, ValueError, TypeError, struct.error) as error:
            records.append({"file": path.name, "error": str(error)})
            failed = True
    result = {"schema": 1, "tool": "container-observations-only", "files": records}
    text = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    try:
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            # No accidental overwrite of an original or an earlier observation.
            with args.output.open("x", encoding="utf-8", newline="\n") as stream:
                stream.write(text)
        else:
            print(text, end="")
    except OSError as error:
        print(f"cannot write observations: {error}", file=sys.stderr)
        return 1
    return int(failed)


if __name__ == "__main__":
    sys.exit(main())
