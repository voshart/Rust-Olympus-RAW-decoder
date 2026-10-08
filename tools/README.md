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
This repository specifies container metadata, observed packed layouts and the
[measured compressed 12-bit profile](../research/compressed-12bit-measured.md).
The product compressed Rust implementation still requires separate review and
implementation/safety gates.

For the preregistered bit-influence experiment, use the binary instrument above:

```sh
python tools/probe_bit_influence.py "corpus/voshart-olympus/P6190137_EM5MarkII_Lumix G 20mmF1.7 II.ORF" --reference-runtime .work/runtime --output .work/em5ii-bits.json
```

It tests 64 single-bit mutations, uses isolated workers with 20-second timeouts,
and compares the first changed sensor indices. `--bytes 32 33 34 35 36 37 38 39`
selects the registered later region. It bounds inputs to 32 million declared
samples and at most four workers. Tied influence indices, invisible mutations and
contradictions remain in the report; they do not become assumed format rules.

`probe_prefix_flags.py` tests all eight combinations of the first three proposed
flag bits against two preregistered numeric transforms. `measure_initial_tokens.py`
computes two candidate values from file bytes before requesting reference pixels:

```sh
python tools/measure_initial_tokens.py corpus/external/pixls-2978.ORF corpus/external/pixls-6946.ORF --reference-runtime .work/runtime --output .work/initial-pairs.json
```

Omit `--reference-runtime` for standard-library-only candidate measurements.
The reference check remains in a bounded child process. These are small numerical
hypothesis tools; they do not reconstruct a full sensor image, specify later
prediction/state or make unsupported variants decode in LightCraft. See
[findings and remaining questions](../research/compressed-findings.md).

New initial-pair reports also preserve reference sensor/visible geometry, the
full reference sensor hash, tested coordinates and signed candidate differences.
Reference margins and the maker-note active crop are recorded separately: the
initial pair is measured at the raw sensor origin, without applying a crop.

`infer_prefix_tokens.py` extracts mutation-supported boundaries and compares
several simple predictors. `fit_prefix_state.py` searches the explicitly recorded
small bias/width families on continuous measured prefixes. No missing token is
silently supplied. `measure_first_row_models.py` calculates all fitted candidate
rows before requesting reference rows and keeps failed models and exact mismatch
counts. `trace_first_row_model.py` reads a bounded window of a candidate trace
without a reference. The original methods used before refinements are archived
under `research/methods`; keep `tools` on `PYTHONPATH` when running an archived
method directly. All remain numerical research tools, not product dependencies.

## Full-raster measurements

`measure_full_frame.py` extends only the unchanged pre-prose E01/V02 model.
It uses a bounded byte reservoir, retains two previous rows, and writes candidate
arrays into `.work/`. Complete predictions and hashes are saved before invoking
the isolated native full-array comparator. It compares every declared sample,
including margins, and records row bit positions and unused tail bits.

```sh
python tools/measure_full_frame.py "corpus/voshart-olympus/P6190137_EM5MarkII_Lumix G 20mmF1.7 II.ORF" --models research/results/frozen-row-candidate.json --reference-runtime .work/runtime --sensor-dir .work/full-frames --predictions-output .work/full-predictions.json --output .work/full-comparisons.json
python tools/validate_full_frame_bounds.py --predictions .work/full-predictions.json --external-dir corpus/external --output .work/reader-bounds.json
```

At most eight inputs, 96 million samples per image, 512 million per batch and
16,384 columns are accepted. Mutation workers retain their 32-million-sample cap;
unchanged full-array controls have a 96-million cap. Every native worker has a
20-second timeout. These resource caps are research budgets, not format constants.

`validate_full_frame_bounds.py` uses independent procedural bit-string checks and
the recorded final token's fields. It tests missing required bytes without a
native dependency or compressed test encoder. The published full-raster summary
links all seventeen complete comparisons and the retained metadata-gate failures.
Missing depth observations on three controls are recorded, not supplied from a
camera-name lookup. This verifier's profile gate is not production identification.

Archived methods preserve the original failed/refined experiment implementations.
The pre-high-resolution row method was recovered exactly by reversing recorded
budget changes and verifying its original SHA-256; no coding rule was altered.
Historical local snapshot byte hashes may include Windows checkout line endings.
Model identity is also checked with a canonical JSON hash for portability.
