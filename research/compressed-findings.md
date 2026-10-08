# Independent compressed-prefix measurements

Task M11.3, 2026-10-08. The working plan uses independently recorded measurements,
reviewed format hypotheses and a future pure-Rust implementation. Vendor replies
and licence requests are optional historical work, not prerequisites. No outreach
has been sent and no third-party decoder source was opened.

These are **partial research results**, not an approved full compressed ORF
specification. Original file hashes, binary-instrument versions, mutations and
failed hypotheses are retained. The [protocol](compressed-next-experiment.md)
records each hypothesis before its prospective validation. AI training cannot be
certified free of decoder knowledge; the new rules here are tied to the measured
operations below and are not filled in from remembered algorithms.

## Single-bit influence

256 isolated one-bit cases cover two regions in an E-M5 II file and a public
E-M1 II file. Every case returned a reference array. Two E-M5 II cases produced
no sensor difference. For successful changed cases, compare the first changed
row-major sensor indices for higher/lower bit positions in each byte:

| Specimen / strip bytes | Higher-bit-first pairs | Reverse pairs | Ties | Invisible mutations |
|---|---:|---:|---:|---:|
| E-M5 II, 7-14 | 29 | 1 | 180 | 2 |
| E-M1 II, 7-14 | 80 | 0 | 144 | 0 |
| E-M5 II, 32-39 | 96 | 0 | 128 | 0 |
| E-M1 II, 32-39 | 108 | 0 | 116 | 0 |

The later region supports high-bit-first influence locally. A naive monotonic
mapping throughout the early region is rejected: in the E-M5 II, one lower bit
first affects a later sample than an even lower bit. The invisible bits at
byte 10 bit 5 and byte 14 bit 6 are retained as observations. Pair comparisons
are correlated and are not statistical confidence estimates.

Reports: [E-M5 II early](results/em5ii-bit-influence-7-14.json),
[E-M1 II early](results/em1ii-bit-influence-7-14.json),
[E-M5 II later](results/em5ii-bit-influence-32-39.json),
[E-M1 II later](results/em1ii-bit-influence-32-39.json).
Every experiment runs in a child with a 20-second timeout; native errors are
observations, not valid-format requirements.

## First-pixel flag combinations

The single-bit measurements give unit/two-unit effects for byte 7 bits 5/6.
The original bits equal the low two bits of the first sensor value. Bit 7
produces a wrapped negative value. Two hypotheses were registered before testing
all eight combinations of the three bits:

```text
q = floor(original first value / 4)     # supplied from reference in this experiment
f = three high bits of byte 7 after mutation

H4: (f & 4 ? -1 : 1) * (4*q + (f & 3))
H5: 4 * (f & 4 ? ~q : q) + (f & 3)
```

Compare modulo 65,536 to the instrument's u16 output. **H5 matches all 24 cases**
across E-M5 II, E-M1 II and the independently tested E-M5 III. H4 matches 15/24.
This establishes a candidate local transform while holding the other bits fixed;
it does not decode `q`. The changed streams are not asserted to be valid camera
outputs, especially when sensor values exceed the declared ADC range.

Reports: [E-M5 II](results/em5ii-prefix-flags.json),
[E-M1 II](results/em1ii-prefix-flags.json),
[E-M5 III](results/em5iii-prefix-flags.json).

## Initial codeword hypothesis

The next proposal was derived from measured weights, zero-run effects, the
invisible bits and observed first-token boundaries. It was registered before
comparison on two additional cameras. Starting at strip bit 56 (byte 7), propose:

1. Read three flag bits, high bit first.
2. Count up to twelve zeros. Below twelve, consume the one terminator and use
   the count as `u`. At twelve, read an eleven-bit `u`, then consume one extra
   bit. Its value is not asserted as a format requirement.
3. Read four bits `v`; propose `q = 16*u + v`.
4. Apply H5 to `q` and the flags. Propose the same initial remainder width for
   the first two codewords.

The tool computes candidates from file bytes before obtaining reference arrays.
Both initial values match on all five originals, including PEN-F and TG-7, whose
reference pixels had not been inspected before this validation:

| File / camera | Candidate first pair | Reference first pair | Tested scope |
|---|---|---|---|
| P6190137 / E-M5 II | 876, 1624 | 876, 1624 | Initial two values |
| P5121636 / E-M5 III | 656, 1521 | 656, 1521 | Initial two values |
| PIXLS.US 1993 / E-M1 II | 314, 328 | 314, 328 | Initial two values |
| PIXLS.US 2978 / PEN-F | 1163, 1566 | 1163, 1566 | Held-out initial pair |
| PIXLS.US 6946 / TG-7 | 738, 499 | 738, 499 | Held-out initial pair |

On P6190137 the predicted token boundaries are bits 87 and 118: the next codewords
start at byte 10 bit 0 and byte 14 bit 1. These agree with the first-influence
measurements. All field offsets and hashes are preserved in
[the original candidate report](results/initial-token-hypothesis.json) and
[the reproducible-tool report](results/initial-token-reproduction.json).

This is a **numerical hypothesis tool for two values**, not a full compressed
decoder. Ten matching initial values do not establish later coding, predictor
state, row resets, full-frame termination, all quotient boundaries or other
variants. The original one-off measurement is archived byte-for-byte in
[methods](methods/initial-token-measurement.py), matching the script hash in its
report. Use [measure_initial_tokens.py](../tools/measure_initial_tokens.py) for
portable reproduction and isolated reference workers.

## Next research gate

Measure how the remainder width changes after the initial pair and how signed
differences relate to neighbouring pixels. Preserve competing predictor/state
models and failed traces. Then establish row/field resets and termination,
compare every declared sensor sample on held-out images, and review the complete
specification before a product implementation. Later 14-bit/high-resolution
variants and camera colour remain separate coverage/quality work.

No additional photographs, purchases or vendor replies are required for the
next experiments. Full sensor arrays and native instrument binaries remain
unbundled. LightCraft's seven compressed creator-contributed files still use
embedded previews; its existing packed-reader fixes remain unchanged.
