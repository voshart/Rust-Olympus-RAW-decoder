# Public specimen verification, 2026-10-08

The supplied leads were checked against the primary corpus records before media
was used. The [external manifest](../corpus/external-sources.json) records URLs,
byte counts, SHA-256 hashes and licence evidence for fourteen downloaded ORFs.
Media stays in the ignored `corpus/external/` directory.

## Source verification

- The five C-5050 files from [thorsted/digicam_corpus](https://github.com/thorsted/digicam_corpus)
  are covered by its [CC0 licence at the pinned commit](https://github.com/thorsted/digicam_corpus/blob/1bc58853d8de8b7f76ee80ef75dd8db8de9c4bd7/LICENSE).
  The commit is `1bc58853d8de8b7f76ee80ef75dd8db8de9c4bd7`. All downloads match
  both the pinned Git blob SHA-1 identities and recorded byte counts; SHA-256
  hashes are additionally recorded for experiments.
- PIXLS.US records **1993, 3041, 1787, 2978, 7262, 7796 and 6946** individually
  identify CC0 and publish SHA-256 hashes. All seven downloads match. The live
  [upstream data index](https://raw.pixls.us/json/getrepository.php?set=all) was
  checked directly; its snapshot SHA-256 is
  `8dc5f5c74e20cc3a38f4548d53bba4bb516835e2a859e80bf86e7ac6283b3aa3`.
- Two additional individually CC0 records cover the contributor's camera modes:
  **2856**, E-M5 II high resolution, and **3573**, E-M5 III high resolution.
  Their downloads also match the upstream hashes.
- The [rawmakase manifest](https://github.com/pch/rawmakase/blob/ad08443dd7a742ec658b667ef4e4dcb4e0eed830/tests/corpus/pixls.json)
  independently contains matching identities for the supplied seven PIXLS.US
  files. It was used as a cross-check, not as a grant of rights to photographs.
  No rawmakase decoder code or corpus script was opened.

There is a qualification to the other leads: [Reatom's fixture licence list](https://github.com/reatom/reatom/blob/v1001/examples/gallery/src/__fixtures__/LICENSES.md)
calls `RAW_OLYMPUS_C5050Z.ORF` CC0, but upstream PIXLS.US record **254**, with that
same source filename, is listed **CC-BY-NC-SA-4.0**, SHA-256
`f4b013e78204ebaadd740d93416080856b3c51ec154760e2e2de0e552873044a`.
That specimen was not downloaded or used. The five separately contributed
digicam_corpus photographs have distinct identities and are unaffected.
Likewise, a corpus README's general CC0 statement does not replace per-file checks.
The [HDR sample collection](https://github.com/aaron-rust/hdr-sample-images) describes
Nikon Z8 captures; it was not needed for this Olympus investigation.

## Held-out E-M5 II high-resolution packing

Record **2856** has input SHA-256
`5c42fa75d6b549514b722e2c50726c03e34fac4909ec3640e147ea7fa825fc8d`.
It has the same independently established layout as the creator-contributed
high-resolution file: 9280 x 6932 sensor, ten samples in sixteen bytes,
GRBG at the full sensor origin, and maker-note active crop (10,10), 9216 x 6912.

The existing LightCraft Rust reader matched **all 64,328,960** reference samples,
including borders, with **zero differences**. Both arrays, serialized row-major
little-endian u16, have SHA-256
`79aa165b0c74e88ff6c3e3e027e86aad30a6957d9b7d3d8990668aafbb393ef4`.
The [recorded result](results/public-packed12-reference.json) preserves the
reference's separate geometry fields. A subsequent Python reproduction checks
the same packing, padding and full-sensor hash.

This extends verified sample coverage to two original files in one camera mode.
It does not establish all Olympus modes, camera colour, lens corrections or
compressed coding. The Rust audit reported probe 4.17 ms / decode 40.13 ms on
this Windows machine with optimized development settings; this is not a slider
latency or Lightroom parity benchmark.

## C-5050 packed fields

All five digicam_corpus files declare **2576 x 1925**, `BitsPerSample=12`,
`Compression=1`, Exif **BGGR**, `IIRS` framing and `RowsPerStrip=16`.
They contain 122 strip records: 120 of 61,824 bytes, one of 11,592 bytes at
strip index 60, and one of 7,728 bytes at index 121. The total is exactly
7,438,200 bytes, or twelve bits per declared sample.

The short strips suggest two separately framed fields: 963 even rows followed
by 962 odd rows. The observed three-byte packing hypothesis is standard MSB:

```text
sample[0] = (a << 4) | (b >> 4)
sample[1] = ((b & 15) << 8) | c
```

The competing existing LE32/MSB hypothesis was measured before reference use.
On PB180002 the standard MSB horizontal same-parity mean difference was 24.541,
versus 1121.888 after reversing each four-byte word. Sequential storage rows had
vertical same-parity difference 30.339; mapping the first 963 rows to even output
rows and the remaining rows to odd output rows reduced it to 24.278. Continuity
alone was treated as a hypothesis, not proof.

A subsequent binary comparison found **zero mismatches across all 4,958,800
declared samples in each of the five files**. Sequential row mapping had about
4.93 million mismatches per file. Per-file hashes and counts are in the
[reference results](results/c5050-packing-reference.json). Reproduce the
measurements with [measure_field12.py](../tools/measure_field12.py).

The reference reports a 2576 x 1926 array, with a nonzero extra bottom row.
The compared scope is only the 1925 rows declared and covered by the strips.
The extra row is not specified or claimed verified. LightCraft currently rejects
this packed multi-field layout as unsupported; no C-5050 product change is
included here. A future implementation must handle all declared strip records
rather than clipping them to a conventional TIFF grid.

## Modern compressed candidates

All seven supplied modern PIXLS.US files and the added E-M5 III high-resolution
file still return explicit `Unsupported` from the current LightCraft reader.
Their stored bits per sample are below twelve, despite TIFF declaring sixteen
bits and no compression. TG-7 declares GRBG, while these other compressed
specimens declare RGGB. The initial container and perturbation observations
remain a **partial specification**; no decoder/predictor/reset rule is inferred
from this coverage or from the reference's error messages.
