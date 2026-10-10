# How this work was done

The central method was **LibRaw as a black-box numerical oracle**, through
separately installed rawpy binaries: propose decoding rules, measure their
predictions, and compare them with uncorrected sensor output. No Adobe code,
assets or profiles are recorded as inputs.

This page is a reading route through the evidence; the linked documents retain
the detailed experiments and disclosures.

## Inputs

The documented corpus comprises [12 photographs made by voshart](../corpus/user-images.json)
(ten ORFs and two JPEGs, dedicated to CC0) and
[14 external CC0 ORFs](../corpus/external-sources.json)
(five digicam_corpus and nine individually checked PIXLS.US files).

One candidate, `RAW_OLYMPUS_C5050Z.ORF` / PIXLS.US record 254, was labelled CC0
by a fixture list but CC-BY-NC-SA-4.0 by its source record. It was **not downloaded
or used**. See [the source checks](public-samples.md).

## From observations to implementation

| Step | What happened | Evidence |
|---|---|---|
| Inspect | Hash originals; examine container fields, Bayer patterns, strips and byte budgets. | [Early format notes](orf12-format.md) |
| Experiment | Try competing packing/token rules; perturb strip bits in temporary copies and observe reference sample changes. | [First-row investigation](compressed-first-row.md) |
| Extend | Test prediction, adaptive state, row resets and termination on additional specimens; retain failed hypotheses. | [Experiment history](compressed-next-experiment.md), [measured specification](compressed-12bit-measured.md) |
| Implement | Review the specification and arithmetic, then write a bounded Rust reader and tests. | [Review](compressed-12bit-review.md), [implementation and source links](rust-implementation.md) |
| Validate | Compare complete little-endian u16 sensor hashes, geometry, CFA and margins. Seventeen compressed rasters matched: 434,555,200 samples, zero differences, no excluded margins. | [Recorded Rust results](results/rust-compressed-full-frame.json) |

## Exposure and reproduction

Research, specification review and implementation were performed by the same
AI-assisted author. First-row work was committed and later-row work frozen
before two supplied AI-generated explanations about LibRaw/RawSpeed were read.
Later source-derived prose and an incidental generic libopenraw container snippet
are disclosed in the [provenance timeline](orf12-provenance.md). Decoder source
pages were not opened according to that record. This does not certify an AI
model's training data or resolve [the upstream provenance objection](licensing-and-references.md).

[Standalone replay instructions](standalone-rust.md#build-and-reproduce) build the
Rust decoder stored here and compare output with published hashes, without
LightCraft or LibRaw installed. Fresh oracle measurements need the separately
installed reference runtime. Full sensor dumps, private prose inputs and runtime
binaries are not tracked here. The original LightCraft integration is also
preserved in [the source snapshot](source-snapshot/manifest.json).
