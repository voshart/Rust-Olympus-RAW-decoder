#!/usr/bin/env python3
"""Fetch only hash-pinned, individually verified CC0 ORF media; no decoder sources."""
import argparse
import hashlib
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAX_FILE = 160 * 1024 * 1024
HOSTS = {'raw.githubusercontent.com', 'raw.pixls.us'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--id', action='append', help='select specimen IDs; default is all fourteen')
    args = parser.parse_args()
    entries = json.loads((ROOT/'corpus/external-sources.json').read_text(encoding='utf-8'))['files']
    wanted = set(args.id or (e['id'] for e in entries))
    if wanted - {e['id'] for e in entries}:
        raise ValueError('unknown specimen ID')
    dest = (ROOT/'corpus/external').resolve()
    if not dest.is_relative_to(ROOT):
        raise ValueError('download directory escapes repository')
    dest.mkdir(parents=True, exist_ok=True)
    for entry in entries:
        if entry['id'] not in wanted:
            continue
        url = urllib.parse.urlsplit(entry['url'])
        if entry['license'] != 'CC0-1.0' or url.scheme != 'https' or url.hostname not in HOSTS:
            raise ValueError('sample is not a verified CC0 media source')
        name = entry['filename']
        if name != Path(name).name or '/' in name or '\\' in name or Path(name).suffix.lower() != '.orf':
            raise ValueError('invalid media basename')
        size = entry['size_bytes']
        if not 0 < size <= MAX_FILE:
            raise ValueError('sample exceeds download budget')
        target = (dest/name).resolve()
        if target.parent != dest:
            raise ValueError('media path escapes download directory')
        if target.exists():
            if target.stat().st_size != size:
                raise ValueError(f'{name}: existing file has the wrong byte count')
            data = target.read_bytes()
        else:
            encoded = urllib.parse.quote(entry['url'], safe=':/?=&')
            with urllib.request.urlopen(encoded, timeout=30) as response:
                if urllib.parse.urlsplit(response.geturl()).hostname not in HOSTS:
                    raise ValueError('unexpected media redirect host')
                data = response.read(size + 1)
        if len(data) != size or hashlib.sha256(data).hexdigest() != entry['sha256']:
            raise ValueError(f'{name}: byte count or SHA-256 mismatch')
        if data[:4] not in (b'IIRO', b'IIRS', b'MMOR'):
            raise ValueError(f'{name}: not an ORF container')
        if not target.exists():
            with target.open('xb') as stream:
                stream.write(data)
        print(f"verified {entry['id']}: {size} bytes", flush=True)
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError, KeyError) as error:
        print(f'cannot fetch corpus: {error}', file=sys.stderr)
        sys.exit(1)
