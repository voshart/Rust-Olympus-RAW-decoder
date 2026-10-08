# Olympus ORF: independently observed container and packed 12-bit layout

This document covers container metadata and the independently established packed
layout, which is implemented in the related LightCraft branch. The separate
[measured compressed 12-bit profile](compressed-12bit-measured.md) now documents
entropy coding, prediction, state/reset and completion observations with full
sample comparisons. Compressed ORF remains unsupported in the product pending
separate specification review and implementation.
See [provenance and acceptance gates](orf12-provenance.md).

## Scope and evidence

The creator-contributed set has eight original ORFs from an Olympus E-M5 II and
E-M5 III, and two companion JPEGs. The creator has released the unchanged
originals as CC0 in [the Git LFS corpus](../corpus/user-images.json). Derived
sensor arrays and binary instruments remain unbundled. Repeatable tools are in
[tools](../tools/README.md); file hashes and observations are in
[versioned results](results/container-observations.json). The initial specimens
are summarized below; [public findings](public-samples.md) extend the evidence
with fourteen external originals.
This is verified sample coverage, not a guarantee for every camera or mode.

| Specimen group | Count | Full sensor | Maker-note active crop | Exif CFA | Stored bits per sensor sample |
|---|---:|---|---|---|---:|
| E-M5 II ordinary shots | 5 | 4640 × 3472 | (8, 8), 4608 × 3456 | RGGB | 6.041–7.272 |
| E-M5 III ordinary shot | 1 | 5240 × 3912 | (12, 12), 5184 × 3888 | RGGB | 8.155 |
| E-M5 III high-resolution shot | 1 | 10400 × 7792 | (8, 8), 10368 × 7776 | RGGB | 6.647 |
| E-M5 II high-resolution shot | 1 | 9280 × 6932 | (10, 10), 9216 × 6912 | GRBG | exactly 12.8 |

All eight files declare `BitsPerSample=16`, `Compression=1`, one strip covering
the full sensor, and Olympus ImageProcessing `ValidBits=[12, 0]`. Those standard
TIFF tags therefore do **not** distinguish packed samples from the vendor's
compressed samples. Seven shorter strips are compressed candidates; their
compressed coding rules have not been established. A camera-model lookup cannot
replace the per-file CFA tag: the E-M5 II's ordinary and high-resolution files
declare different layouts.

## Container and metadata

Observed files start with `IIRO` and use classic little-endian TIFF IFD framing.
The existing reader also supports the established `IIRS` and `MMOR` magics.
Exif tag `0xa302` is an UNDEFINED blob: two 16-bit repeat dimensions in the TIFF
byte order, followed by row-major one-byte colour values. For Bayer, require
exactly eight bytes, dimensions 2 × 2 and one of these four layouts:

| Bytes after dimensions | Layout |
|---|---|
| 0, 1, 1, 2 | RGGB |
| 2, 1, 1, 0 | BGGR |
| 1, 0, 2, 1 | GRBG |
| 1, 2, 0, 1 | GBRG |

The layout is anchored at the full sensor origin. Crop offsets are applied later
by the existing normalization path. Missing, malformed or non-Bayer Exif layouts
fall back to the existing data-based phase estimate; that estimate only identifies
the green diagonal and does not establish which remaining site is red or blue.
It compares same-parity block means to reduce sensitivity to point texture.

Olympus maker-note sub-IFDs supply the crop and black/WB tags through the existing
parser. New-style notes in these files start with `OLYMPUS\0II`, with offsets
relative to the maker note. Crop coordinates are checked before use. This work
does not introduce a colour matrix, a camera look or lens calibration.

Metadata sources: [CIPA Exif 2.32](https://www.cipa.jp/std/documents/e/DC-X008-Translation-2019-E.pdf),
[ExifTool EXIF tag names](https://exiftool.org/TagNames/EXIF.html) and
[Olympus tag names](https://exiftool.org/TagNames/Olympus.html).
Only format/tag descriptions were used, not decoder or metadata-library source.

## Established packed layout: E-M5 II high-resolution specimen

Rule P1: each row has `width / 10 × 16` bytes; width is divisible by ten.
The observed 9280 × 6932 specimen has 14,848 bytes per row and a 102,926,336-byte
strip. That is exactly ten samples per 16 bytes, without an extra strip header.

Rule P2: each group contains five three-byte pairs, followed by one zero byte.
All **6,432,896** observed padding bytes are zero. For a pair `(a, b, c)`:

```text
sample[0] = a | ((b & 0x0f) << 8)
sample[1] = (b >> 4) | (c << 4)
```

Rules P1/P2 were proposed from byte measurements before comparing reference
pixels. The opposite nibble layout was a competing hypothesis. On 1,792 samples
from the left eight columns, the selected layout had mean 350.713 and standard
deviation 32.339; the opposite layout had mean 903.503 and standard deviation
723.595. Border plausibility alone was not treated as proof.

Rule P3: concatenate groups left to right and rows top to bottom, preserving the
full sensor including borders. A subsequent black-box comparison against a
pinned binary instrument matched **all 64,328,960** samples, including borders,
with zero difference. Both independently unpacked and reference arrays have
SHA-256 `aea032c10a27ff82918a465b4cc0bdb701f65ce119a3d134ad8ebd60ff5d61d3`
when serialized as row-major little-endian u16.
The final Rust reader independently produced that same full-sensor hash.
A held-out CC0 E-M5 II file from PIXLS.US record 2856 also matches every declared
sample between the Python hypothesis, Rust reader and binary instrument; its
sensor hash is `79aa165b0c74e88ff6c3e3e027e86aad30a6957d9b7d3d8990668aafbb393ef4`.
See [the held-out evidence](public-samples.md#held-out-e-m5-ii-high-resolution-packing).

The product recognizes this packing ahead of the existing LE32/MSB-first packed
layout for a little-endian, single-full-height-strip, unsigned one-sample layout,
validates zero padding, and reads Exif CFA. Unverified variants stay unsupported. A tagged packed header probe
checks the strip but does not allocate/unpack sensor samples. Word16 files still
need samples to establish effective depth; packed files without a valid Exif CFA
still need samples for the fallback phase estimate. `probe_info` and successful
full decode must describe the same image.

## Initial compressed-stream observations

The paragraphs below preserve the initial, deliberately limited observations.
Subsequent rule derivations and seventeen complete raster comparisons are in
[the measured compressed profile](compressed-12bit-measured.md).

The seven compressed candidates share a seven-byte strip prefix; a prefix is an
observation, not a documented codec identifier. The isolated perturbation tool
changes one strip byte at a time and records reference success/failure and the
affected sensor bounds. An error from the reference is not a product-format rule.
On one E-M5 II ordinary specimen, XOR 1 at each of strip bytes 0–6 caused the
reference to reject the input. Bytes 7 and 8 changed roughly the entire sensor;
byte 9 changed 4,027,172 samples, byte 128 changed 2,849,404, and byte 4096 changed
16,800 within columns 4599–4639 and rows 0–1598. This only records the behaviour
of LibRaw 0.22.1 on those exact mutations; it does not define a valid header,
predictor, adaptive rule or reset interval.
Long-range changes can be caused by variable-length coding, predictor propagation,
adaptive state or several mechanisms together. These experiments do not select
one explanation, establish bit order, or justify a decoder implementation.

The subsequent experiments distinguish competing bit-order, code-length,
predictor and reset hypotheses. The resulting evidence account is ready for
separate review before a product decoder and its test vectors are written.
The rejected compressed encoder/decoder
from PR #240 is not an input to this document or implementation.
