# Rust Olympus RAW decoder

An openly licensed Olympus/OM System sample corpus, measured format specification,
and reproducible validation package for a safe pure-Rust ORF decoder.
**The measured compressed 12-bit profile now has a safe pure-Rust implementation
in LightCraft. It matches seventeen complete reference rasters: 434,555,200 samples,
including both 81 MP files and every stored sensor margin.** This repository keeps
the unchanged CC0 corpus, measurements, provenance and replay tools; product code
lives in the linked LightCraft branch. Generalized 14-bit decoding remains unverified.

**Upstream submission:** [LightCraft PR #360, ready for review](https://github.com/storytold/lightcraft/pull/360).
It awaits maintainer acceptance of the disclosed provenance and implementation scope.
The accepted CFA/probe work from #277 is retained, and the contribution now includes
13 pinned CC0 PIXLS.US files with complete sensor checksums and a required CI replay.
This repository is a reusable research and validation hub; it does
not currently publish a standalone Cargo crate or end-user RAW converter.

## Start here

| Goal | Entry point |
|---|---|
| Understand the supported compressed format | [Measured 12-bit specification](research/compressed-12bit-measured.md) and [pre-implementation review](research/compressed-12bit-review.md) |
| Read or integrate the Rust decoder | [Pinned codec source](https://github.com/voshart/lightcraft/blob/be241c9ac73beab2d82a3368c4248f956df71965/crates/raw/src/vendor/olympus12.rs), [ORF container integration](https://github.com/voshart/lightcraft/blob/be241c9ac73beab2d82a3368c4248f956df71965/crates/raw/src/vendor/orf.rs), and [implementation scope](research/rust-implementation.md) |
| Reproduce the 17 complete sensor comparisons | [Build and replay instructions](tools/README.md#reproduce-the-published-rust-validation) and [recorded results](research/results/rust-compressed-full-frame.json) |
| Reuse openly licensed photographs | [Download instructions below](#get-and-verify-the-photographs), [creator manifest](corpus/user-images.json), and [external manifest](corpus/external-sources.json) |
| Review origin and performance evidence | [Exposure/provenance history](research/orf12-provenance.md) and [release timings/method](research/rust-implementation.md#release-decoding-comparison) |

The decoder currently lives inside `lightcraft-raw` and uses that crate's error,
metadata and image types. The source links above are implementation references,
not drop-in standalone modules. A future standalone crate should have a stable
public API and reuse the same validation corpus. Keeping one product implementation
while upstream review is in progress avoids diverging copies.

The working path is independent measurements on original files, explicit
competing hypotheses, review of the resulting format description, and a safe
pure-Rust implementation. Vendor replies or a licence grant are not dependencies
of that plan. The [compressed research protocol](research/compressed-next-experiment.md)
preserves the earlier experiments; the implementation account above describes the
current result.

The creator-contributed corpus includes ten original ORFs and two companion JPEGs
from voshart's Olympus E-M5 II and E-M5 III, released by their creator under CC0.
The originals are unchanged and stored using Git LFS. Their filenames retain
camera/lens descriptions; SHA-256 hashes and byte counts identify every file.

## Get and verify the photographs

```sh
git lfs install
git clone https://github.com/voshart/Rust-Olympus-RAW-decoder.git
cd Rust-Olympus-RAW-decoder
git lfs pull
python tools/verify_corpus.py --require-media
```

Python 3.10+ is sufficient for verification and container inspection. Verification
also works on a clone containing only LFS pointers, but does not claim to have
verified downloaded media unless `--require-media` is supplied.

- [Creator-contributed photographs and hashes](corpus/user-images.json)
- [Photograph licence and contribution](corpus/voshart-olympus/README.md)
- [Verified external sample URLs, licences and hashes](corpus/external-sources.json)
- [Public sample findings and licence corrections](research/public-samples.md)

External samples are fetched on demand into an ignored directory. The external
manifest covers the twelve supplied corpus leads plus public E-M5 II and E-M5 III
high-resolution samples. Each PIXLS.US record was individually checked for CC0;
GitHub samples are pinned to a commit and were checked against their Git blob
identities. Third-party decoder source is not fetched.

```sh
python tools/fetch_corpus.py
python tools/inspect_orf.py corpus/voshart-olympus corpus/external --output .work/container-observations.json
```

## Current evidence

- Per-file Exif Bayer patterns are necessary: E-M5 II ordinary shots use RGGB,
  while the two examined E-M5 II high-resolution files use GRBG.
- The E-M5 II high-resolution packing has ten 12-bit samples in sixteen bytes.
  Independently unpacked pixels and the LightCraft Rust reader match a separately
  installed binary reference on all 64,328,960 sensor samples in each of two
  originals, including the public held-out sample.
- Five C-5050 samples use standard MSB 12-bit pairs in separate even/odd row
  fields. The candidate matches all declared pixels in all five files. The
  reference exposes an additional row not represented by the declared strips;
  that row is explicitly excluded from the claim.
- The measured modern compressed 12-bit profile now decodes in LightCraft. TIFF
  `Compression=1` and `BitsPerSample=16` do not prove that their sensor pixels
  are uncompressed. A shared strip prefix is an observation, not a codec rule.

Read the [partial format description](research/orf12-format.md),
[provenance and acceptance gates](research/orf12-provenance.md), and
[research tool instructions](tools/README.md). A sensor match does not establish
camera colour calibration, lens corrections or Lightroom rendering parity.

The [compressed-prefix findings](research/compressed-findings.md) now include
256 single-bit cases, 24 first-pixel flag/control cases, and an initial-codeword
hypothesis that matches the first two values on seven files across five camera
models, including two previously unmeasured cameras and two additional E-M5 III
originals. That initial stage did not specify later prediction, changing coding
parameters or full-frame decoding; the subsequent measurements are described below.

The independently measured [first-row hypothesis](research/compressed-first-row.md)
now covers changing widths, a two-parity bias state, the inclusive small-code
threshold and a discriminated escape grammar. It matches every first-row sample
on seven originals across five camera models (34,840 values), including
prospective PEN-F/TG-7 rows. Failed fits and refinements are preserved.

The [measured compressed 12-bit profile](research/compressed-12bit-measured.md)
extends the independently fitted state and prediction rules to seventeen full
rasters from nine models: **434,555,200 samples with zero differences and no
excluded margins**. Both 81 MP E-M5 III originals are included. Final-byte
influence and strict reader bounds are recorded. A separate specification/arithmetic
review preceded the Rust implementation. A follow-up raw-field inspection identifies
the examined profile on all seventeen originals, including OM SYSTEM notes the early
Python inspector missed. Field-role claims from the supplied prose are not adopted.
The [implementation and validation account](research/rust-implementation.md) records
the exact scope, rejection policy, safety tests, full-array replay and application checks.

The LightCraft contribution is published as [PR #360](https://github.com/storytold/lightcraft/pull/360),
with independent CFA/packed/header fixes, the measured specification and compressed
implementation retained as separate commits. Product code is pinned at
[b0654b3](https://github.com/voshart/lightcraft/commit/b0654b36ae5e4c84c874faded78d5c31164e6f81);
the submitted head [06221ee](https://github.com/voshart/lightcraft/commit/06221eec37c78f66e9d0c257f25053b52bc78050)
adds documentation cleanup and passed all seven `cargo xtask ci` gates, including
WASM. Native/headless application imports were inspected. Submission does not mean
an upstream release or maintainer approval of the provenance.

## Contributing

Useful follow-ups include additional licensed camera/mode samples, reproducible
unsupported-file reports, independent review of the measured specification, and
measured optimization experiments that preserve every sensor value. For a report,
include camera/mode, input SHA-256, tested commit, command and observed result;
share the original only when you have permission and an explicit suitable licence.
See [contributor instructions](AGENTS.md) before adding source or research.

Use [this repository's issues](https://github.com/voshart/Rust-Olympus-RAW-decoder/issues)
for corpus/research/replay questions and the linked LightCraft PR for product
integration review. Unknown compressed fingerprints, generalized 14-bit, camera
colour calibration and lens correction remain separate follow-up work.

## Licences and provenance

The contributed photographs are **CC0-1.0**, under
[their dataset licence](corpus/voshart-olympus/LICENSE-CC0.txt). Code and research
documentation are **MIT OR Apache-2.0**, except where a file explicitly says
otherwise. External photographs retain their individually recorded licences;
they are not relicensed by a software repository's licence.

No Adobe assets, camera coefficient tables or rejected PR #240 decoder/encoder
were used. Olympus compressed-decoder source pages were not opened. Later
source-derived prose and an incidental generic container-recognition code snippet
are disclosed in the provenance note; the frozen coding hypothesis predates
that exposure. The optional reference is a separately installed binary measuring
instrument and is not shipped here. AI authorship and the limits of assurances
about training data are disclosed in the provenance note.
See [NOTICE](NOTICE) and [contributor instructions](AGENTS.md).
