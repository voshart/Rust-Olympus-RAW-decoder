# Compressed ORF bit perturbation experiment

Task M11.3, 2026-10-08. This protocol is recorded before collecting bit-level
mutation results. Vendor responses and a licence grant are not prerequisites for
the working research plan. Existing request drafts are optional historical work;
no requests have been sent.

## Question and competing hypotheses

For a short region at the start of the observed compressed strip, do successful
one-bit changes first affect sensor samples in high-bit-first, low-bit-first, or
neither order? We measure influence order; no entropy-code or predictor formula
is proposed from model memory.

- H1: a forward high-bit-first stream. Within a data byte, successful mutations
  may first affect earlier samples for higher bit positions.
- H2: a forward low-bit-first stream. The reverse influence ordering may hold.
- H3: the tested bits control framing, block metadata, or a non-local transform;
  neither simple ordering describes their first changed sensor samples.

Prefix-code coupling, ignored or masked samples, predictor state, and non-row-major
processing can confound this measurement. A monotonic first-change ordering is
supporting evidence, not proof of a complete bit-reader rule. Reference errors
are recorded as errors, never as valid-format requirements.

## Inputs and procedure

Initial specimen: creator-contributed E-M5 II P6190137, input SHA-256
`270052cf17913884cb0a1236c4e6a4851aa794f5fa854d821235fcfb3358fd34`.
Independent second specimen: PIXLS.US 1993, input SHA-256
`0b433019e5fa61548d7eb0eb7bb90894251542c056da72355202382696d0ceb8`.

1. Read originals without modifying them; record their hashes and geometry.
2. Mutate every single bit in strip bytes 7 through 14. This is 64 cases per
   original; previously only the low bit of a few bytes was tested.
3. Run each experiment in a child process with a 20-second timeout. Use only
   the pinned binary rawpy 0.27.1 / LibRaw 0.22.1 instrument and its sensor arrays.
4. Record mutation mask, changed sample count/bounds, first changed row-major
   index/value, and the length of the unchanged sample prefix. Preserve errors.
5. Compare strict within-byte first-change orderings among successful cases.
   Ties are non-discriminating. Cross-check any apparent ordering on the second
   specimen before promoting a local observation to a hypothesis.

Raw originals and full derived sensor arrays are never modified or published as
new fixtures by this experiment. Small observations refer to CC0 inputs; native
instrument binaries stay outside Git. No decoder source or camera tables are read.
The observations do not implement compressed decoding or close its acceptance gate.

## Registered follow-up: bytes 32 through 39

The initial E-M5 II measurement contains one pair with reverse first-change order
and two single-bit mutations with no sensor effect. Thus a naive monotonic mapping
of early file bits to successive pixels cannot be accepted. Before measuring the
next region, extend the same competing hypotheses to bytes 32 through 39 in both
specimens. This region is chosen to move past the first-sample encoding. It is
not asserted to be metadata-free. Use the same 64 cases and summary; preserve
contradictions and do not infer an entropy-code formula from the result.

## Registered follow-up: first-pixel flag combinations

The collected single-bit results at strip byte 7 have effects of one and two
units for bits 5 and 6. In both originals, these input bits equal the low two
bits of the first output value. Bit 7 produces a wrapped negative output. On
P6190137, negating 876 would give 64,660 as u16, but the observed value is 64,656.

Before combination tests, propose two competing transforms while keeping the
remaining input fixed. Let `q = floor(original_first_value / 4)` and let `f` be
the three high bits of byte 7 after mutation:

```text
H4: signed magnitude = (f & 4 ? -1 : 1) * (4*q + (f & 3))
H5: complemented high part = 4 * (f & 4 ? ~q : q) + (f & 3)
```

Compare both modulo 65,536, matching the instrument's u16 output. These are
predictions of a local observable transform, not decoding formulas for `q`.
The original first value is supplied by the reference; its high-part coding,
predictor, state and all later pixels remain unspecified.

Test XOR masks 0x00, 0x20, 0x40, 0x60, 0x80, 0xa0, 0xc0 and 0xe0 at byte 7
on both initial specimens. Independently test the same predictions on the
creator-contributed E-M5 III P5121636, input SHA-256
`1574efc88696ba6e9873b781f94dadb38ffe19667dc59fc8520331b3a7a72397`.
Keep errors and failed predictions. Require an original positive flag and
agreement between its low flag bits and first-value low bits; a failure rejects
this proposed scope. Successful mutations are not asserted to be valid camera
streams, particularly when reference samples exceed the declared ADC range.

## Registered follow-up: initial high-part codeword hypothesis

The single-bit measurements also show a sequence of first-output increments of
64 when successive early zero bits are changed to one, four low payload bits
with weights 32, 16, 8 and 4, and an entirely invisible bit at byte 10 bit 5.
The measured first-token boundary is byte 10 bit 0. Together with the already
tested three flag bits, these support the following *initial-token hypothesis*:

- Read bits high to low starting at byte 7. Read three flag bits.
- Count up to twelve zeros. Below twelve, consume a one terminator and use the
  zero count as `u`. At twelve zeros, read an eleven-bit `u` and consume one
  additional bit. The latter bit is not asserted to require a particular value.
- Read four bits `v`; propose `q = 16*u + v`.
- Apply H5 above to `q` and the flags, rather than supplying `q` from the reference.
- Propose the same initial four-bit remainder width for the first two codewords.
  Prediction and changing remainder widths after them remain unspecified.

This is a numerical research hypothesis, not an approved compressed specification
or product decoder. Alternative escape widths ten/twelve and an omitted extra
bit predict different boundaries; preserve the candidate's exact field positions
and any mismatch. Test the first two values on the three already measured files,
then on previously unmeasured PIXLS.US 2978 (PEN-F) and 6946 (TG-7). Compute and
record candidate values before obtaining those files' reference arrays. Do not
extend this initial rule to later pixels merely because the first two match.

## Registered follow-up: changing codeword widths and first-row prediction

Recorded after commit `44893b4`, before collecting the following measurements.
Use the two original training specimens, P6190137 and PIXLS.US 1993, and retain
P5070002/P2153108 as prospective validation inputs for values beyond the initial
pair. Their first pair has already been checked; their later sensor values have
not been inspected for this experiment.

1. Extend the one-bit influence measurements to strip bytes 15-22 and 23-30 on
   both training originals, using the same isolated, capped instrument. Combine
   these with the previously recorded regions. Infer potential flag boundaries
   from one/two-unit effects and the first affected pixel, preserving invisible
   bits and ambiguous boundaries.
2. Compare a constant four-bit remainder after the initial pair with changing
   widths in 0-16. Test each proposed width against observed token boundaries
   and payload-bit weights before fitting any state formula. The initial
   zero-run/escape description remains a hypothesis; a later boundary conflict
   must reject its extension rather than be hidden by selecting a predictor.
3. For supported token boundaries, compare raw signed codeword values with
   reference samples using zero, previous sample, same-colour left neighbour
   (two positions earlier), and a constant-step extrapolation from same-colour
   neighbours. Record any unexplained correction instead of assuming it is a
   known codec's adaptive state.
4. If a changing-width or correction model can be fitted on the training
   observations, register its exact competing formulas before comparing later
   values on the two new E-M5 III files. Compute predictions before acquiring
   those reference values. Keep failures and the distinction between a local
   first-row model and a complete sensor-stream specification.

No later-state formula is supplied from remembered decoder code. Empirical
searches must record their candidate family and objective. Camera colour and
lens corrections are outside this bitstream experiment.

### Recorded exploratory fitting family

The new training traces expose remainder widths and signed high parts using
mutation-supported boundaries. The same-colour-left correction is divisible by
four on the continuous measured prefixes. Let `B` be that correction divided
by four and `D = signed_high + B`. Search these bounded families, recording all
fits rather than choosing a remembered formula:

- Bias update: `B_next = floor((a*D + b*B + c) / 2^s)`, with `a,b` in 0-16,
  `s` in 1-8, and `c` in 0 through `2^s-1`. Initial bias is zero. The objective
  is exact agreement with all observed next-parity corrections.
- Width state: initial magnitude `A=0`, small-code count `N=0`; after a token,
  update `A=q` or `A=q+floor(A/2^d)` for `d` in 1-12, where `q` is its measured
  unsigned high part. Increment `N` when `q < 2^t`, otherwise reset it, with
  `t` in 0-8. Before a token, choose `k=max(base, bit_length(A)-shift)`.
  While `N < r`, use base 4 and shift 2 (constrained by the initial and large
  second-parity-token observations). Otherwise search base 1-4 and shift 0-3.
  Search `r` in 1-8. Objective: exact agreement with every measured width.
- Evaluate separate even/odd-column states and, as a control, one shared state.
  Fit only continuous measured prefixes (before an unmeasured boundary); do not
  bridge a missing token with a silently invented state.

This is an exploratory family selected after seeing the training measurements.
Any exact fit must be registered before prospective validation, and a failed
held-out prediction rejects the proposed extension even when training matches.

### Registered prospective first-row model comparison

The exploratory fit found five bias coefficient/range entries (fifteen concrete
rounding-offset choices) and thirty width states for two channels. No one-channel
model fitted either family. The continuous training prefixes contain 18 and 26
tokens, with forty next-parity bias transitions. Test all 450 combinations on
the complete declared first row of P5070002 and P2153108; do not select a winner
from training alone.

For each candidate, start at strip bit 56 with zero per-parity magnitude, small
count, bias and left pixel. Choose the fitted width before each token. Retain
the initial zero-run/escape hypothesis (twelve zeros, eleven-bit quotient, one
extra bit); a later mismatch can reject that extension. Decode the flags and
high part using the measured complemented transform. Set `D=signed_high+B` and
`pixel=left+4*D+low_flags`, update the fitted bias with floor division, and update
magnitude/count from unsigned `q`. Each parity's previous pixel becomes `left`.
Compare pixel values modulo 65536 and preserve out-of-ADC-range predictions.

Calculate and save every candidate's row hash, first values, end bit and width
histogram before acquiring reference first-row arrays on either new specimen.
Then record exact difference counts, first mismatch, versions, geometry, margins
and full reference sensor/row hashes. Keep all failed candidates. This tests a
first-row numerical hypothesis and does not specify later-row prediction,
state resets, termination or high-resolution variants.

### Registered boundary-value refinement

The initial 450-model comparison matches the entire P2153108 first row for all
models, so that nearly constant border row does not discriminate their state.
The best P5070002 models match 246 values, then diverge. An exploratory trace of
the simplest fitted model locates unsigned `q=16` at pixel 242. Treating it as
small would permit the even-column count to reach three before pixel 246,
changing that token's proposed width from four to three. The latter predicts
383, matching the recorded first mismatch reference, rather than 431.

Before further comparison, register the inclusive condition `q <= 16` against
the original `q < 16`, with the fitted no-decay magnitude and bias
`floor((3*D+B)/32)`. Also retain fitted decay alternatives. Collect single-bit
mutations in P5070002 strip bytes 288-295 to check the affected token boundaries
and q values independently. If the refinement reproduces its whole first row,
compute complete first-row candidates on PEN-F (PIXLS.US 2978) and TG-7
(PIXLS.US 6946) before obtaining their reference rows. Those two initial pairs
were measured earlier; their remaining first-row values have not been inspected.
The P5070002 recheck is exploratory refinement, not held-out validation.

### Registered escape-width refinement

The inclusive threshold extends P5070002 agreement to 744 samples. The next
failure is an escape at a two-bit remainder: the initial fixed eleven-bit
quotient proposal predicts high part 15, but the reference value requires high
part 52 with the already fitted predictor. A thirteen-bit quotient followed by
the measured extra bit and two remainder bits gives 52 and ends at bit 6082.
Together with the initial four-bit remainder / eleven-bit quotient observation,
register `escape_payload_bits = 15-k` as an affine candidate.

Two distinct grammars fit that original bit sequence: a fixed twelve-zero
escape with `15-k` payload bits, or a `16-k` zero threshold with eleven payload
bits. Both have a 31-bit total escape word. Collect all single-bit cases in
P5070002 strip bytes 756-763. In particular, bit 6066 (byte 758 bit 5) is payload
in the first hypothesis and a zero-run bit in the second. Their first affected
pixel and value predictions differ. Preserve no-effect/wrapped cases.

Before new reference comparisons, test the original grammar and both refinements
using inclusive threshold, no-decay magnitude and the simplest fitted bias.
Rechecks on P5070002 are exploratory; prospective first-row checks on PEN-F and
TG-7 must save candidates before reference acquisition. No escape condition
is accepted from a baseline coincidence alone.
