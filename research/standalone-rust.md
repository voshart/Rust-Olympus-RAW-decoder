# Standalone Rust decoder

This repository now builds `olympus-raw` without a LightCraft checkout, branch,
application, system library or reference runtime. All implementation source and
the TIFF support are here. Cargo fetches ordinary Rust dependencies; `Cargo.lock`
records the tested resolution. The supported Rust version is 1.90 or newer.

## Use from another Rust application

Clone this repository and add a path dependency:

```toml
[dependencies]
olympus-raw = { path = "../Rust-Olympus-RAW-decoder" }
```

```rust
fn sensor(bytes: &[u8]) -> olympus_raw::Result<olympus_raw::SensorImage> {
    olympus_raw::decode_orf(bytes)
}
```

`SensorImage` contains uncorrected row-major u16 samples, stored width/height,
the Bayer layout at the full sensor origin, sensor-relative active crop, Exif
orientation, and available camera black-level/white-balance metadata. Pixels
retain margins and are not rotated. Black levels are the original maker-note
values; the caller must interpret/remap them when cropping. White-balance ratios
are not a camera colour matrix. This crate performs no demosaicing, camera colour
calibration, rendering, library management or photo editing.

The file API accepts the measured compressed E01/V02 12-bit profile and the
measured E-M5 II padded high-resolution layout. It requires a little-endian,
single full-height strip and valid per-file Exif Bayer metadata. Unknown coding
fingerprints, generalized 14-bit, other packed/word layouts and missing Bayer
metadata return errors. This intentionally has narrower container coverage than
LightCraft's complete RAW crate. No speculative decoder fallback is used.

`compressed::decode(strip, width, height)` is also available for applications
that already parse ORF containers. It checks prefix, dimensions, stream and sample
bounds, **but does not inspect the container or its coding fingerprint**. The
caller must check the measured profile and layout before selecting this codec;
see the [specification](compressed-12bit-measured.md) and `src/lib.rs` adapter.

## Build and reproduce

From the repository root:

```sh
cargo test --workspace
cargo clippy --workspace --all-targets -- -D warnings
cargo run --release --example decode -- input.orf output.u16le
```

The example creates a new output file and prints sensor metadata. The output is
an uncorrected little-endian u16 raster, not a displayable JPEG or TIFF.

For the complete recorded sensor comparisons, first obtain creator media through
Git LFS and fetch the individually licensed external originals:

```sh
git lfs pull
python tools/verify_corpus.py --require-media
python tools/fetch_corpus.py
cargo test --release --test corpus -- --ignored --nocapture
```

These explicitly requested tests fail if a required original is absent or its
hash differs. They compare all seventeen compressed rasters with the historical
oracle hashes, plus both E-M5 II padded high-resolution rasters. They also check
dimensions, Bayer layouts and recorded active crops. They do not generate new
independent oracle results. Ordinary synthetic tests require no media or runtime.
The [extraction replay record](results/standalone-rust-replay.json) identifies the
validated source and records 19 complete matches / 563,213,120 samples.

## Source preservation and changes

The extraction starts at LightCraft contribution commit
`b350683bd9a8194ed626c38bb1dfda3b9d3a4ef6`. The original compressed reader and
ORF integration are preserved verbatim in [source-snapshot/](source-snapshot/),
with their input SHA-256 identities in [the manifest](source-snapshot/manifest.json).
These are historical sources for inspection, not build inputs requiring LightCraft.

The compressed algorithm and its existing tests are retained in
`src/compressed.rs`; changes are module visibility, local TIFF/error imports,
documentation paths and formatting. The padded-pair unpacker is retained in
`src/packed.rs`. `src/lib.rs` supplies a small standalone container adapter and
public sensor/error types in place of LightCraft's application types. New
container tests and full-sensor replays verify this boundary.

`vendor/olympus-tiff` preserves the MIT/Apache LightCraft TIFF reader, writer,
maker-note support and tests locally. Its package name/manifest, test imports and
formatting were adapted; notices and licence texts are retained. It is pure Rust
and depends on serde and thiserror, not LightCraft. See [NOTICE](../NOTICE).

This extraction preserves the existing [provenance disclosures](orf12-provenance.md)
and [licensing scope](licensing-and-references.md). It is not a new clean-room
claim, an upstream acceptance claim, or a fresh performance benchmark. The
existing LightCraft submission and all local worktrees remain intact.
