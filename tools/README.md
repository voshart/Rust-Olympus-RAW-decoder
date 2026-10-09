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

## Reproduce the published Rust validation

Prerequisites: Python 3.10+, Git LFS for the creator photographs, Rust/Cargo
1.90+ and a native linker. Start in this corpus checkout after the README's
clone/LFS instructions. Download and verify the external originals:

```sh
python tools/verify_corpus.py --require-media
python tools/fetch_corpus.py
```

Create a new sibling checkout for the pinned product code and build its audit
example. These commands use `lightcraft-orf` as an unused directory name:

```sh
git clone --branch orf/compressed-12bit https://github.com/voshart/lightcraft.git ../lightcraft-orf
git -C ../lightcraft-orf checkout --detach b0654b36ae5e4c84c874faded78d5c31164e6f81
cargo build --release --manifest-path ../lightcraft-orf/Cargo.toml -p lightcraft-raw --example orf_audit --target-dir ../lightcraft-orf/target
python tools/validate_rust.py --binary ../lightcraft-orf/target/release/examples/orf_audit --lightcraft ../lightcraft-orf --creators corpus/voshart-olympus --external corpus/external --sensor-dir .work/rust-replay-1 --output .work/rust-replay-1.json
```

On Windows use `orf_audit.exe` for the `--binary` path. Cargo may download Rust
dependencies during the build; corpus downloads also require network access.
Once built and downloaded, the comparison itself works offline and does not
require installing a reference decoder. It compares against recorded complete
reference hashes, rather than generating a new independent reference result.

Expected result: seventeen successful cases, 434,555,200 samples, zero differences
and no excluded sensor margins. See [the published report](../research/results/rust-compressed-full-frame.json).
The sensor dumps alone occupy about 0.87 GB, in addition to photographs and build
artifacts. Outputs are create-new; use a fresh sensor directory and report name
for every repeat. The audit also checks header/full metadata equality.

## Optional binary reference

LibRaw offers LGPL 2.1 OR CDDL 1.0; it is not covered by this repository's
MIT/Apache grants. Binary measurements do not certify independent authorship,
and the upstream review disputes the compressed decoder's provenance. See
[licensing scope and references](../research/licensing-and-references.md) before
reusing the evidence or describing the decoder as clean-room accepted.

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
The [product implementation account](../research/rust-implementation.md) records
the completed specification review, implementation and safety/CI checks. Upstream
maintainer review remains pending in [PR #360](https://github.com/storytold/lightcraft/pull/360).

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
under `research/methods`. Archived scripts expect their original `tools/` layout
for imports, sibling workers and repository paths. To replay one, restore its
exact bytes under a distinct filename in `tools/` of an isolated scratch checkout,
then run its original CLI with local corpus/runtime paths and fresh outputs.
All remain numerical research tools, not product dependencies.

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

## Raw profile observations and Rust replay

`observe_profile.py` records raw types/counts/values in the ImageProcessing
directory, including OM SYSTEM note framing. Its motivation came from supplied
source-derived prose; it does not assign semantic roles or implement 14-bit rules.
Use unchanged local ORFs and a fresh output filename.

```sh
python tools/observe_profile.py "corpus/voshart-olympus/P6190137_EM5MarkII_Lumix G 20mmF1.7 II.ORF" --output .work/profile-fields.json
```

`validate_rust.py` runs LightCraft's developer-only `orf_audit` executable on every
compressed original named in the pinned full-frame summary. It checks input hashes,
dimensions, depth, CFA, sample count and complete sensor output hashes. The Rust
example itself requires probe/full metadata equality. Generated sensor dumps need
fresh filenames and stay ignored. Build the example in the linked product checkout
first; the source hashes and numeric report make the exact tested code identifiable.

```sh
cargo build -p lightcraft-raw --example orf_audit
# Run from this corpus checkout, with your local product checkout and binary paths:
python tools/validate_rust.py --binary ../lightcraft/target/debug/examples/orf_audit --lightcraft ../lightcraft --creators corpus/voshart-olympus --external corpus/external --sensor-dir .work/rust-sensors --output .work/rust-comparison.json
```

No reference binary or network access is required for this recorded-hash replay.
The reference identities originate in the original complete-array comparisons,
not in a self-generated compressed encoder or an embedded-JPEG similarity test.
