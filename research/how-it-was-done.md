# How this work was done

This repository preserves the investigation behind a Rust Olympus/OM System RAW
decoder: photographs, measurements, competing explanations, failed experiments,
a measured format specification, and validation results. The central method was
to use **LibRaw as a black-box numerical oracle**, through separately installed
rawpy binaries, and compare proposed decoding rules with its sensor output.
Adobe code, application assets, profiles and camera calibration tables are not
recorded inputs to this investigation. This is an account of the recorded work,
not a certification of an AI model's training data or of upstream acceptance.

## Photographs used

- **12 creator-contributed photographs:** ten ORFs and two JPEGs made by voshart,
  dedicated to CC0 and preserved unchanged using Git LFS. Their identities and
  terms are in [user-images.json](../corpus/user-images.json).
- **14 external ORFs:** five C-5050 photographs from a pinned CC0 digicam_corpus
  commit and nine individually checked CC0 PIXLS.US records. Sources, hashes and
  licence evidence are in [external-sources.json](../corpus/external-sources.json)
  and [public-samples.md](public-samples.md).
- **A rejected non-CC0 lead:** the Reatom fixture named `RAW_OLYMPUS_C5050Z.ORF`
  was labelled CC0 by that fixture list, but the corresponding PIXLS.US record
  254 was listed CC-BY-NC-SA-4.0. The research notes explicitly record that it
  was **not downloaded or used**. It is distinct from the five CC0 C-5050 files.

These are the documented Olympus research inputs. The external files are fetched
on demand into an ignored directory; listing a URL does not put the media in Git.
Not every photograph participates in every experiment. The complete compressed
decoder comparison covers seventeen files; packed-layout experiments have their
own specimen sets and comparison limits.

## Follow the investigation

1. **Inspect the originals.** Read TIFF/Exif container fields, dimensions, Bayer
   patterns, strip locations and byte budgets. Hash the original files and keep
   them unchanged. Start with [container observations](results/container-observations.json)
   and the [early format notes](orf12-format.md).
2. **Propose rules and test alternatives.** Try packing and row-layout hypotheses;
   mutate selected strip bits in temporary copies; measure which reference
   samples change. Preserve failures as well as successes. The
   [first-row account](compressed-first-row.md),
   [experiment protocol and later-row work](compressed-next-experiment.md),
   [historical methods](methods/) and [results](results/) show the progression.
3. **Fit and test the compressed model.** Investigate token boundaries, escapes,
   adaptive state, prediction, row resets and termination. Compare competing
   rules and apply the candidates to additional specimens. The
   [measured specification](compressed-12bit-measured.md) links the numerical
   evidence for the resulting E01/V02 profile.
4. **Freeze the evidence and record later exposure.** First-row work was committed
   before two supplied prose explanations were read. Later-row work was captured
   in a 96-file hash manifest. Those later AI-generated explanations attributed
   details to LibRaw/RawSpeed implementations. Decoder source pages were not
   opened, according to the record; source-derived prose exposure did occur.
   A generic libopenraw container snippet also appeared incidentally in a search,
   and a further performance explanation was read after implementation. The
   [full provenance history](orf12-provenance.md) preserves this sequence and
   its limits. A checkpoint hash is not an independent timestamp or proof of
   clean-room authorship.
5. **Review the specification, then implement Rust.** The same AI-assisted author
   performed the research, [specification/arithmetic review](compressed-12bit-review.md)
   and implementation. The reader uses bounded allocations, strict bit reads,
   checked arithmetic and explicit unsupported cases. The
   [implementation account](rust-implementation.md) links the product source
   and describes its tests.
6. **Compare complete sensor rasters.** Serialize uncorrected sensor samples as
   row-major little-endian u16 and compare complete hashes, geometry, Bayer
   patterns and margins with the recorded reference output. The
   [Rust report](results/rust-compressed-full-frame.json) records seventeen
   complete matches: 434,555,200 samples, zero differences, no excluded margins.
   That is finite specimen coverage, not proof of every Olympus profile or of
   rendered colour accuracy.

## What a reader can reproduce

The [tool instructions](../tools/README.md#reproduce-the-published-rust-validation)
explain how to fetch and verify the photographs, build the pinned LightCraft
audit example, and compare its output with published complete-sensor hashes.
This replay does not need LibRaw installed. Generating fresh oracle measurements
does require the separately installed binary reference; its versions and wheel
identities are recorded in [provenance](orf12-provenance.md#external-measuring-instrument).

The actual Rust decoder, audit example and product tests live in the linked
LightCraft fork, not in this repository. Full sensor arrays, private supplied
prose and reference-runtime binaries are not tracked here. Hashes and summaries
preserve their recorded identities; they do not substitute for the files
themselves. Preserve the linked LightCraft source as well as this repository
when archiving the work.

The upstream provenance objection is recorded in
[licensing-and-references.md](licensing-and-references.md). Numerical validation,
the licence offered for original material, and acceptance under LightCraft's
contribution policy are separate questions. This guide preserves the method
without claiming that those questions have been settled.
