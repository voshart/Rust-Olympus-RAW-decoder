#!/usr/bin/env python3
"""Verify creator-contributed originals or their exact Git LFS pointer identities."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAX_FILE = 512 * 1024 * 1024


def digest_file(path):
    size = 0
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        while block := stream.read(1024 * 1024):
            size += len(block)
            if size > MAX_FILE:
                raise ValueError('file exceeds verification budget')
            digest.update(block)
    return size, digest.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--require-media', action='store_true')
    args = parser.parse_args()
    failed = False
    media = pointers = 0
    manifest = json.loads((ROOT/'corpus/user-images.json').read_text(encoding='utf-8'))
    for entry in manifest['files']:
        name = entry['path']
        try:
            path = (ROOT/name).resolve()
            licence = (ROOT/entry['license_path']).resolve()
            if not path.is_relative_to(ROOT) or not licence.is_relative_to(ROOT):
                raise ValueError('manifest path escapes the repository')
            if entry['license'] != 'CC0-1.0' or not licence.is_file():
                raise ValueError('missing creator-contributed CC0 licence')
            size = path.stat().st_size
            if size > MAX_FILE or not 0 < entry['size_bytes'] <= MAX_FILE:
                raise ValueError('file exceeds verification budget')
            if size <= 1024:
                pointer = path.read_bytes()
                expected = (f"version https://git-lfs.github.com/spec/v1\n"
                            f"oid sha256:{entry['sha256']}\nsize {entry['size_bytes']}\n").encode('ascii')
                if pointer != expected:
                    raise ValueError('invalid or mismatched LFS pointer')
                if args.require_media:
                    raise ValueError('media not fetched; run git lfs pull')
                pointers += 1
                print(f'pointer identity verified: {name}')
            else:
                actual_size, actual_hash = digest_file(path)
                if actual_size != entry['size_bytes'] or actual_hash != entry['sha256']:
                    raise ValueError('byte count or SHA-256 mismatch')
                media += 1
                print(f'media verified: {name}')
        except (OSError, ValueError, KeyError, UnicodeError) as error:
            print(f'{name}: {error}', file=sys.stderr)
            failed = True
    print(f'{media} photographs verified; {pointers} pointer identities verified.')
    return int(failed)


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError, KeyError) as error:
        print(f'cannot verify corpus: {error}', file=sys.stderr)
        sys.exit(1)
