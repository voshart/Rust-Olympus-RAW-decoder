# Creator-contributed Olympus originals

Creator/contributor: **voshart**. Contributed and released under **CC0-1.0** on
2026-10-08, with the explicit instruction to add the photographs to this public
repository as CC0. The dedication applies to the eight ORFs and two JPEGs listed
in [user-images.json](../user-images.json).

See the [CC0 legal text](LICENSE-CC0.txt) and
[Creative Commons CC0 description](https://creativecommons.org/publicdomain/zero/1.0/).

Files are the unchanged camera originals, including their embedded camera
metadata, and are stored using Git LFS. Filenames describe the E-M5 II/E-M5 III
bodies and Olympus/Panasonic lenses used. File and sensor dimensions are distinct;
high-resolution modes must be examined per file.

```sh
git lfs pull
python tools/verify_corpus.py --require-media
```

SHA-256 hashes and byte counts identify the originals. Verify them before using
an experiment result. Refer to immutable repository commits when publishing a
reproduction. Derived sensor arrays and reference binaries are not committed.
