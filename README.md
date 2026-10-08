# Rust Olympus RAW decoder

An openly licensed Olympus/OM System sample corpus and independently documented
ORF research, working toward a pure-Rust decoder suitable for permissive projects.
**This repository is currently a research and corpus project. Its measured 12-bit
research candidate matches seventeen complete compressed rasters; a product
Rust compressed decoder has not been implemented.**

The working path is independent measurements on original files, explicit
competing hypotheses, review of the resulting format description, and a safe
pure-Rust implementation. Vendor replies or a licence grant are not dependencies
of that plan. The next experiment is recorded in the
[compressed research protocol](research/compressed-next-experiment.md).

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
- Ordinary modern compressed files remain research inputs. TIFF
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
influence and strict reader bounds are recorded. This specification is ready
for separate review; generalized 14-bit parameters and a production-safe variant
identification policy still need evidence. Product Rust implementation and its
CI/safety gates are a subsequent stage.

The related LightCraft changes are on local branch `orf/independent-evidence`,
commits `6ccba8f` and `480985b`, based on upstream
`629e39380e296f588c64cd9c0053a8edc3528f36`. They are not yet an upstream PR.
That branch passed `cargo xtask ci`, including WASM, and the packed file was
visually checked through LightCraft's headless and desktop control interfaces.
This repository does not contain LightCraft's product implementation.

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
