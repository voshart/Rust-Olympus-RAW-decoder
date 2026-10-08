# ORF research tools

These are developer tools, not product dependencies. Container inspection,
licence/hash manifests and downloads use Python's standard library. They read
media without modification. Outputs are create-new files; choose a new name to
repeat an experiment. Keep reference binaries, sensor arrays and private
experiments in the ignored `.work/` directory.

```sh
python tools/verify_corpus.py --require-media
python tools/fetch_corpus.py --id pixls-2856
python tools/inspect_orf.py corpus/voshart-olympus corpus/external --output .work/observations.json
```

`inspect_orf.py` bounds file sizes, IFD traversal and tag values. Its observation
manifest whitelists camera/lens, geometry, CFA, bit/strip budgets and hashes. It
excludes GPS, serials, embedded names and timestamps, but contains filenames and
raw strip prefixes. The published corpus contains the unchanged camera originals,
including their own metadata.

## Optional binary reference

Download binary wheels only into the ignored research area. Do not build or
inspect decoder source. The established measuring instrument is rawpy 0.27.1 /
LibRaw 0.22.1, with NumPy 2.4.3. Exact Windows/CPython 3.13 wheel hashes are in
[provenance](../research/orf12-provenance.md); other platforms need their own hashes.

```sh
python -m pip download --only-binary=:all: --dest .work/wheels rawpy==0.27.1 numpy==2.4.3
python -m pip install --no-index --find-links .work/wheels --only-binary=:all: --target .work/runtime rawpy==0.27.1 numpy==2.4.3
python tools/measure_packed12.py "corpus/voshart-olympus/PA280725_EM5MkII_Lumix G Fisheye 8mmF3.5.ORF" --reference-runtime .work/runtime --output .work/user-packing.json
python tools/measure_packed12.py corpus/external/pixls-2856.ORF --reference-runtime .work/runtime --output .work/public-packing.json
python tools/measure_field12.py corpus/external/c5050-PB180002.ORF --reference-runtime .work/runtime --output .work/c5050-packing.json
python tools/probe_reference.py "corpus/voshart-olympus/P6190137_EM5MarkII_Lumix G 20mmF1.7 II.ORF" --reference-runtime .work/runtime --output .work/perturbations.json
```

`measure_packed12.py` records padding and competing nibble hypotheses before its
optional reference check. `measure_field12.py` compares standard MSB/LE32 word
packing and sequential/separate-field row maps, disclosing the extra reference
row. `probe_reference.py` isolates each byte mutation in a child process with a
20-second timeout and at most 64 cases. Reference failures and changed bounds are
observations, not compressed coding rules. None reads camera calibration tables.

The related LightCraft checkout contains the actual Rust audit example:

```sh
cargo run -p lightcraft-raw --example orf_audit -- --sensor-dir plan/orf-research/rust-sensor /path/to/high-res.orf
```

It checks header/full metadata agreement and optionally writes full-sensor
little-endian u16 dumps. That Rust implementation is not duplicated here.
This repository currently specifies container metadata and observed packed
layouts; an independently established compressed specification is still needed.
