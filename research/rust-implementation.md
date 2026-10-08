# Reviewed compressed 12-bit Rust implementation

2026-10-08, LightCraft M11.3. The user authorized implementation after the measured
specification package. The specification and arithmetic were reviewed in a separate
document before writing new product compressed code. [The separate review](compressed-12bit-review.md)
records the exact arithmetic, profile and safety policy. The researcher, reviewer and
implementer are the same AI-assisted author; this is disclosed rather than described
as independent third-party approval. No web visits were made during this stage.
Neither rejected `orfc.rs` nor upstream compressed-decoder source was read.

The product source is in voshart's LightCraft fork, commit [b0654b3](https://github.com/voshart/lightcraft/commit/b0654b36ae5e4c84c874faded78d5c31164e6f81):

- [crates/raw/src/vendor/olympus12.rs](https://github.com/voshart/lightcraft/blob/b0654b36ae5e4c84c874faded78d5c31164e6f81/crates/raw/src/vendor/olympus12.rs): strict reader, fixed E01/V02 state/predictor
  and sensor reconstruction, independent literal fixtures and hostile-input checks.
- [crates/raw/src/vendor/orf.rs](https://github.com/voshart/lightcraft/blob/b0654b36ae5e4c84c874faded78d5c31164e6f81/crates/raw/src/vendor/orf.rs): empirical profile/layout gate, metadata and
  sample-free tagged header probing; existing packed/word routes are retained.
- [docs/raw/orf12-review.md](https://github.com/voshart/lightcraft/blob/b0654b36ae5e4c84c874faded78d5c31164e6f81/docs/raw/orf12-review.md): pre-implementation specification/arithmetic review.

The source-only branches retain separate independent-fix, specification and product
commits. No photographs, native measuring binaries, coefficient tables or compressed
test encoder from the rejected contribution are product dependencies. This is a
verified contribution, not an upstream release or proof of every Olympus variant.

## Profile identification and safety

The follow-up [raw-field observations](results/observed-profile-fields.json) were
motivated by user-supplied source-derived prose. They record types/counts/values,
without importing those explanations' field-role claims or 14-bit rules. The
observed SHORT-valued vector is identical across all seventeen compressed originals:
`0611=[12,0]`, scalar `0640..0649=[0,5,0,2,5,4,3,2,3,4]`, absent `064a..064f`,
and scalar `0650..0653=[7,15,12,5]`. The two packed controls have zero scalar fields.
The extended container inspector reads both OlympusNew and OM SYSTEM framing;
original missing-metadata reports are preserved, not rewritten as successes.

That exact fingerprint selects the already measured fixed codec before the old
strip-density heuristic. It requires little-endian framing, one unsigned component,
declared 16-bit storage, one full-height explicitly bounded strip, Bayer metadata
and prefix `00 00 00 00 01 00 00`. Unknown nonzero/malformed coding fields remain
unsupported. Missing/zero coding fields retain existing packed/word selection.

Even dimensions, at most 16,384 columns, 20,000 rows and 96 million samples are
coverage/resource policy. Minimum input length is checked before fallible sensor
allocation. No required bit is zero-filled. Samples outside 0..4095 fail before
updating prediction state. The reviewed bias and sample bounds justify remainder
width at most nine and bounded signed arithmetic. The small-code counter saturates
at three, preserving every measured comparison. Signed bias division uses floor.

Decode exactly the declared sample count. Zero to seven unused final bits may have
either value; an entire unused byte remains outside verified scope. Header probes
check prefix/layout/minimum length without allocating or interpreting sensor data.
Syntactically valid corruption may change samples; this codec is not an integrity
checksum. Colour calibration and lens corrections are separate from decompression.

## Validation

[The Rust replay](results/rust-compressed-full-frame.json) identifies source hashes,
unchanged input hashes, complete LE-u16 reference hashes, dimensions, CFA, active
crop and probe/full equality. **17 rasters / 434,555,200 samples / zero differences /
zero excluded sensor margins**, including both 81,036,800-sample E-M5 III files.
It uses the recorded binary-reference outputs from the measured specification;
no new reference runtime or web access is needed to replay those comparisons.

Twenty-one focused ORF/core tests cover literal bias/predictor vectors, threshold
32, strict diagonal ordering, inclusive q=16, escapes, resets across non-byte-aligned
rows, EOF, arbitrary unused tail bits, altered profiles/depth, missing CFA, invalid
layouts, excessive dimensions, container mutations and arbitrary hostile payloads.
The reservoir is also checked against all 65,536 two-byte bit-string values.

LightCraft's `cargo xtask ci` passes all seven gates: format, clippy with warnings
denied, workspace tests, parity, layers, assets and WASM. A throwaway native session
imports the E-M5 II, E-M5 III fisheye and 81 MP originals as `kind=raw` with
`previewOnly=null`; desktop screenshots were inspected. An independent headless
snapshot of P2153108 was also inspected. No persistent personal library was used.

Timing is recorded per file, under concurrent local CI load, using optimized dev
builds. Those timings are not release benchmarks, slider latency measurements or
evidence of colour parity. Generalized 14-bit, other fingerprints and additional
camera models remain follow-up work.

## Release decoding comparison

A subsequent user question prompted a [release comparison](results/decoder-release-timings.json),
using the [archived Rust timing method](methods/decode-timing-2026-10-08.rs).
No product code changed. Input is loaded before measurement, followed by one
untimed warmup and five timed sensor decodes. Report the median wall time; exclude
file I/O, result cleanup, demosaicing, colour conversion and rendering. The standalone
harness uses Cargo's release opt-level 3, debug=0 and no LTO, with
`RAYON_NUM_THREADS=4`. Its path dependency is the pinned LightCraft raw crate.

| Specimen | Stored MP | Median sensor decode |
|---|---:|---:|
| Compressed ORF, E-M5 II | 16.11 | 176.8 ms |
| Compressed ORF, E-M5 III | 20.50 | 307.3 ms |
| Compressed ORF, E-M5 III high resolution | 81.04 | 826.6 ms |
| Packed ORF, E-M5 II high resolution | 64.33 | 48.7 ms |
| Lossless NEF, D5100 | 16.37 | 107.4 ms |
| CR2, Canon 6D | 20.65 | 220.2 ms |
| Compressed ARW, A7 III | 24.34 | 16.6 ms |
| PEF, Pentax K3 | 24.51 | 128.5 ms |
| DNG, Pixel 2 XL | 12.23 | 19.3 ms |

On these samples, compressed ORF throughput is comparable to CR2 and slower than
NEF/PEF. Packed ORF and ARW2 are much quicker. Codec structure, scene and sample
size differ; this is not a universal format ranking or a render/export benchmark.
The report records full input hashes, all five times and the compiled method hash.
