# ORF research provenance and acceptance gates

Task: `LR-IMP-FORMATS` / M11.3. Started 2026-10-08. Baseline:
`629e39380e296f588c64cd9c0053a8edc3528f36` of storytold/lightcraft.

## Inputs and exposure disclosure

- Read: LightCraft's existing MIT/Apache code, the user-provided photographs,
  published metadata descriptions, PR #240's description and maintainer discussion.
  Later inputs include the individually verified CC0 corpus records and media
  listed in [external-sources.json](../corpus/external-sources.json), plus corpus
  licence/readme metadata. Olympus compressed-decoder source pages were not opened.
- After the initial compressed-prefix results at commit `6ac6d66`, LightCraft's
  documented clean-room NEF, PEF, Panasonic RW2, lossless-JPEG and unpacking
  implementations were read to assess reusable infrastructure. This exposure
  supplied no new Olympus coding rules. The same initial-pair hypothesis was
  subsequently tested prospectively on the two additional E-M5 III files.
- Not used as inputs: PR #240's `orfc.rs`, its compressed encoder, other ORF
  decoder source, camera coefficient tables, Adobe profiles or lens profiles.
- After the later-row hypothesis had been fitted and checked prospectively, the
  user requested a freeze. Ninety-six research files were copied and hashed before
  two user-supplied prose explanations were read. The first-row findings were
  already published at `15e7a61`; the later-row work was still locally uncommitted.
  [Checkpoint identities](results/pre-prose-checkpoint.json) preserve that state;
  they are not an external timestamp or certification of training-data provenance.
- The explanations were AI-generated/secondary prose, with claims attributed to
  existing RawSpeed and LibRaw implementations. The first was identified by the
  user as GPT-6 authored; separate authorship was not supplied for the follow-up.
  Their exact private copies have SHA-256
  `3cd72314488e765b0a142803e09cb0ed5e9a925b3684a241d97bfd26b0b81ba0` and
  `2880b5391ca849ca36582683e740cedbcf24728b881382bd71bea213a09cc44e`.
  Their reported decoder-source URLs were recorded as text, not opened. The
  supplied prose is not republished or used as independent verification.
- A prose documentation search during the first review incidentally returned a
  generic libopenraw container-recognition C++ snippet and API declarations. The
  source page was not opened, and no compressed Olympus rule was obtained from
  that snippet. LibRaw's February 2025 release-note prose and libopenraw's ORF
  format-note prose were read. No web visits were made after the user's subsequent
  instruction. Do not describe this history as zero code-snippet exposure.
- Work resumed from the unchanged E01/V02 model. The full-frame extension uses
  those pre-prose rules; new header/metadata-role interpretations from the supplied
  documents are external claims, not independently established 14-bit rules.
- The research tools and initial notes were authored with Codex. No assertion is made that an AI model's training contains
  no decoder knowledge. Instead, every new packing rule is tied to measurements
  collected before reference comparison. No compressed rule is supplied from
  remembered code or reconstructed from the rejected contribution.
- Metadata and simple packed-pair fixtures are independently generated with
  LightCraft's existing TIFF writer. They do not encode a compressed ORF stream.
- The creator explicitly released the ten initial originals under CC0 on
  2026-10-08 and authorized their publication here. Their starting hashes remain
  unchanged. This separate corpus repo stores them through Git LFS; no media,
  sensor arrays or instrument binaries are committed to LightCraft. The public
  E-M5 II held-out comparison now passes; it covers one additional specimen in
  the same camera mode, not all packed-camera variants.
- The creator explicitly added P5070002 and P2153108 to the CC0 contribution on
  the same date. The current corpus contains twelve unchanged originals: ten
  ORFs and two JPEGs. Both new input hashes were recorded before reference
  measurements, and copied media matches the source files exactly.

## Evidence trail

| Id | Experiment | Result | Limit |
|---|---|---|---|
| C1 | `inspect_orf.py`, eight ORFs and two JPEGs, hashed before use | Models, lenses, dimensions, CFA and strip budgets recorded | Initial creator-contributed specimen coverage |
| C2 | Compare E-M5 II Exif CFA in ordinary/high-resolution modes | RGGB versus GRBG | No model-table inference |
| P1 | Divide high-resolution strip count by height and width | 14,848 bytes/row; ten samples/16 bytes | One initial original; later CC0 release |
| P2 | Count padding and compare low/high-nibble hypotheses in masked columns | 6,432,896 zero pads; sharply different border distributions | Statistics alone do not prove packing |
| P3 | Compare the Python hypothesis and final Rust reader to black-box sensor output | All three full-sensor hashes agree; 64,328,960 identical samples, including borders | Reference implementation may itself have bugs |
| P4 | Public held-out PIXLS.US 2856 | Python, final Rust reader and reference agree on all 64,328,960 sensor samples | Same camera mode; no general camera claim |
| L1 | Five C-5050 CC0 files, byte budgets and competing pair/row hypotheses | Field-mapped candidate matches all 4,958,800 declared samples per file | Extra reference row excluded; not yet implemented in LightCraft |
| S1 | Independently generated packed and Exif fixtures | Four Bayer layouts/two byte orders, boundary values, truncations and mutations | Round trips are supporting evidence, not independent correctness |
| S2 | Synthetic maker-note crop at u64::MAX | Old unchecked crop addition overflows; checked coordinates fall back to the sensor area | Non-conforming numeric tag type |
| X1 | Isolated compressed-strip byte perturbations | Reproducible reference failures/difference extents | Does not establish compressed coding rules |
| X2 | Prospectively apply the existing initial-pair hypothesis to two additional E-M5 III originals | All four candidate values match the binary reference; geometry, margins, differences and sensor hashes recorded | Only two coordinates per image tested; no full compressed decode |
| X3 | Additional 384 single-bit cases, measured token boundaries, explicit finite state fitting and prospective first-row comparisons | Candidate matches 34,840 first-row values on seven originals; escape/counter alternatives rejected by discriminating observations | Later-row prediction, resets and termination remain unspecified; see compressed-first-row.md |
| X4 | Registered row/reset/topology families, exploratory predictor trace and prospective threshold tests | Per-row all-state reset and threshold-32 conditional predictor; sixteen/eight-row matches on ten additional originals | Locally uncommitted pre-prose snapshot; failed controls/models retained |
| X5 | Unchanged E01/V02 applied to complete rasters before native full-array comparison | All 434,555,200 samples on seventeen files match, including two 81 MP originals and every stored margin | One binary reference family; finite camera/profile coverage |
| X6 | Twenty-four final-byte bit mutations; procedural reservoir oracle and final-token byte cuts | Fourteen unused-bit mutations have no sample effect; thirty required-byte cuts reject | No universal padding rule, 14-bit specification or completed product fuzzing suite |
| X7 | Follow-up raw-field inspection, motivated by user-supplied source-derived prose | Identical SHORT-valued fingerprint on all seventeen compressed originals; scalar coding fields zero on both packed controls; OM SYSTEM note framing recovered | Empirical fingerprint only; claimed field roles and generalized 14-bit rules are not adopted |
| X8 | Separate specification/arithmetic review, then independently written safe Rust reader and literal vectors | Seventeen complete product/reference sensor hashes agree; header/full information agrees; bounded allocations, strict EOF, range and mutation checks | Same author performs separate review; no third-party maintainer approval or assurance about AI training is claimed |

Published artifacts are in [research/results](results/): container observations,
user and public packed comparisons, C-5050 comparisons and the original
compressed-strip perturbations. Raw sensor dumps remain local. Input and output
hashes make accidental specimen changes detectable. Tools write observations
with create-new semantics and open photographs read-only.

## External measuring instrument

The separately installed binary Python package rawpy **0.27.1** uses LibRaw
**0.22.1**. NumPy **2.4.3** supports array comparisons. They are installed only
in the gitignored local research directory; none is a Cargo dependency, shipped
asset or runtime dependency. Their source was not opened. Only sensor arrays and
geometry were read; colour matrices and camera tables were not consulted.

Pinned Windows CPython 3.13 wheel hashes (SHA-256):

| Wheel | Hash |
|---|---|
| rawpy-0.27.1-cp313-cp313-win_amd64.whl | 1d2d32bfe7df6421f214f0502d34bd599ce53156401928c4f538336f2f8b3689 |
| numpy-2.4.3-cp313-cp313-win_amd64.whl | 0a60e17a14d640f49146cb38e3f105f571318db7826d9b6fef7e4dce758faecd |

Binary-distribution sources: [rawpy on PyPI](https://pypi.org/project/rawpy/0.27.1/),
[NumPy on PyPI](https://pypi.org/project/numpy/2.4.3/).
The optional instrument is not needed to build, test or run LightCraft.

## Post-implementation performance-prose exposure

On 2026-10-08, after product implementation, full-frame validation and release
benchmarks were published, the user supplied a third prose document titled
"How Olympus RAW decoders are optimized for speed". Its original attachment
SHA-256 is `7f4f1c46ef97f8264cb890bafc83b65a0dd575c1e7e08d8c370d125d2e159aad`.
It describes implementation-specific techniques attributed to RawSpeed and LibRaw,
as well as general optimization ideas. The attachment was read; its source links,
decoder code and other web pages were not opened. Those upstream implementation
and speedup claims were not independently verified. The prose is not republished.

The pre-exposure product source remains pinned at
[`b0654b3`](https://github.com/voshart/lightcraft/commit/b0654b36ae5e4c84c874faded78d5c31164e6f81);
documentation-only cleanup was already published at
[`06221ee`](https://github.com/voshart/lightcraft/commit/06221eec37c78f66e9d0c257f25053b52bc78050).
The research/benchmark repository was at `497365c6dcce0d167c31a8b8606802548da7d577`
before this disclosure. No product implementation or measured coding rule changed
in response to this document.

Inspection of our existing Rust source confirms it already uses an in-memory bit
reservoir, `leading_zeros()` for adaptive bit width, and direct reconstruction into
the sensor buffer without a full-frame residual buffer. Prefix decoding currently
uses repeated one-bit reads; this is a candidate for a separately measured future
experiment, not an established bottleneck or promised speedup. Potential follow-up
would compare our original implementation against an independently written change,
preserving strict EOF/tail handling, all seventeen full-sensor hashes and hostile-input
checks. Generalized 14-bit remains outside scope. Performance work is deferred from
the initial submission so the already verified implementation stays reviewable.

## Before a compressed decoder is acceptable

The working path is independent measurement. Vendor/specification requests are
optional historical drafts and do not hold up this work. Subsequent bit-level
protocols, failed hypotheses and initial-codeword comparisons are recorded in
[compressed findings](compressed-findings.md). The subsequent
[complete measured profile](compressed-12bit-measured.md) has full-raster
comparisons. It has since received the separate review and product checks recorded
below. Those measurements do not authorize skipping implementation/safety gates.

1. Independently derive the bitstream description. For each non-obvious rule,
   record specimen hash, operation, competing hypotheses and discriminating
   observations. Preserve failed hypotheses rather than retrofitting a story.
2. Review the specification separately from code. Disclose exposure to other
   implementations; a new AI session alone is not provenance evidence.
3. Implement only the approved specification, with independently supported test
   vectors. Keep unknown variants explicitly unsupported.
4. Compare every sensor sample on held-out files, stating the full dimensions,
   active crop, CFA origin and any unverified margins. Add bounded allocation,
   arithmetic, truncation and mutation coverage. Run the full project CI.
5. Keep camera colour and lens correction acceptance separate from unpacking.
   Accurate samples do not establish Lightroom rendering parity.

This work satisfies the observed padded packed-layout gate on two E-M5 II files
and numerical full-raster checks of the measured compressed 12-bit profile on
seventeen files. A separate specification/arithmetic review preceded product
implementation. The user explicitly authorized that stage; this is not a claim of
upstream maintainer approval or independent third-party certification. Product
safety tests and CI are recorded in [the implementation account](rust-implementation.md).
Generalized 14-bit coverage, other fingerprints and colour calibration remain.
A rights-holder grant is an alternative to
independent derivation only for exactly the implementation covered by that grant;
the maintainers must decide whether it fits the project policy.
