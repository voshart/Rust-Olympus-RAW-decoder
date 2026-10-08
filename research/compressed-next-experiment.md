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

## Registered follow-up: the first row boundary

After first-row evidence commit `15e7a61`, investigate P5070002's predicted row
end at bit 49412 (strip byte 6176, next bit index 3). Mutate all eight bits of
byte 6176 to test whether subsequent bits first affect row 1, a separate row
field, or padding. Preserve invisible cases and any non-causal influence.

For numerical two-row comparisons, keep the measured E01 first-row token rules.
Search row alignment to 1/8/16/32 bits; state reset choices none, every-row all,
every-row width-only, every-row bias-only, and corresponding two-row resets;
and border seeds zero, preceding-row same column, two-rows-above same column,
or preceding-row last same-parity pixel. Use same-colour left prediction for
columns after the first pair in these first two rows. Compute all candidates
before acquiring the reference row-1 values. A match of row 0 alone does not
support a row-boundary choice.

Later-row neighbour topology is a separate next experiment. Neither an apparent
byte alignment nor familiar predictor code from another format supplies an
Olympus rule without a discriminating observation.

### Registered third-row topology comparison

The row-boundary bit mutations split precisely at bit 49412: preceding bits
first affect row 0 column 5239, subsequent bits first affect row 1 column 0.
The two-row numerical comparison requires no alignment padding and a per-row
bias reset. It does not yet distinguish bias-only from all-state reset.

A control implementation bug initially made `previous_row_end` use zero on
row 1; its initial method/report are retained and the control is corrected.
The apparent duplicate matches are not evidence for that border-seed choice.

Before acquiring row-2 values, compare all/bias-only resets, zero/above-one/
above-two/previous-row-end border seeds, and these elementary neighbour
topologies at row distances one and two: left, above, left+above-diagonal,
median(left,above,left+above-diagonal), their average, left plus half the
above-diagonal difference, above plus half the left-diagonal difference, and
Paeth's nearest neighbour to the gradient (ties left, then above, then diagonal).
Half divisions use floor, an explicit hypothesis. First rows lacking an above
neighbour use left. Retain the measured token rules and one-bit row alignment.
Calculate and save all candidate three-row matrices before reference acquisition
on P5070002 and the original E-M5 II P6190137. These are new later-row checks;
the first rows and P5070002 row 1 were already inspected.

### Registered exploratory predictor trace

The third-row comparison yields no exact model. The nearest elementary model
uses all-state row resets, above-two border seeds and a median predictor at
two-row/two-column distance. It matches the first 26 third-row values before
a four-unit discrepancy; 863 values in that row differ. Keep that failed model.

Collect the first 256 third-row neighbour triples using actual reference samples
and the independently fitted token/bias fields. Infer the required predictor as
`reference_sample - raw_code`. Compare its equality to left, above, gradient,
median, average and the elementary half-gradient options; record unmatched
values. Examine ordering and signed neighbour differences to choose a bounded
candidate decision family. This is exploratory fitting on P5070002. Any refined
formula must be registered before prospective later-row tests on other originals.

### Recorded predictor decision family

All 256 reconstructed predictor values equal the elementary median or the
floor average of left/above. The nineteen values not equal to the median have
the diagonal strictly between left and above and small neighbour differences.
Search a decision family: default median; choose floor average when
`(left-diagonal)*(above-diagonal)` is negative (or non-positive as a control)
and one of the following metrics is at most an integer threshold in 0-128:
maximum absolute difference from the diagonal, minimum absolute difference,
sum of absolute differences, absolute left/above difference, or absolute
`left+above-2*diagonal`. Preserve every exact fit and failed family totals.
This family is selected after viewing the exploratory triples. Validate any
fitted choices on complete later rows of E-M5 II P6190137 and E-M1 II PIXLS.US
1993, saving candidate matrices before their new reference row acquisition.

The predictor-family fit retains exactly four choices: strict diagonal-between
condition, maximum difference metric, and inclusive thresholds 30/31/32/33.
Register these four complete four-row candidates with all-state row reset,
above-two border seeds, two-row distance and no alignment. Compare all four on
P5070002 as an extended refinement check, and prospectively on P6190137 and
PIXLS.US 1993. Each candidate is computed and saved before those reference
row-1/2/3 values are acquired for this experiment.

### Registered sixteen-row coverage check

Threshold 32 alone matches all four rows of P5070002 and P6190137; thresholds
30/31/33 have preserved failures. All four match the lower-contrast E-M1 II
rows, so that specimen does not discriminate the threshold. Freeze the 32-unit
strict-between rule and all-state row resets before extending the check.

Compute and save sixteen-row predictions on P5121636, P2153108, PEN-F 2978 and
TG-7 6946 before acquiring those later reference rows. Separately check public
E-M10 III 1787, E-M1X 3041, OM-1 II 7262 and OM-3 7796 as additional camera
coverage, subject to the existing file/geometry budgets. Preserve failures;
camera identity alone cannot establish shared coding rules.

### Registered high-resolution coverage check

The frozen candidate matches all sixteen tested rows of the eight additional
ordinary specimens. Extend its first eight rows to the two E-M5 III
high-resolution originals P5131023 and PIXLS.US 3573. The native unchanged
control now has a declared-sample cap of 96 million, decodes only once and
hashes/comparisons by rows; mutation experiments retain their 32-million cap.
Prefix matrices remain capped at 131,072 values. No runtime/source code is
inspected, and reference pixels are acquired after both candidate matrices.

## Registered full-raster extension after the prose review

Work resumed on 2026-10-08 after an immutable 96-file pre-prose snapshot was
verified. Two user-supplied prose explanations and their reported source links
have been read as text. Several new claims explicitly derive from RawSpeed or
LibRaw implementations. Those source pages have not been opened. A prior prose
documentation search incidentally exposed a generic container-recognition code
excerpt; this is disclosed in the private review log. Make no further web visits.

The measured E01 token rules and V02 spatial/reset hypothesis are unchanged.
They were recorded before either prose explanation. Do not implement the new
metadata-role or eight-byte-header claims, or describe them as independent
findings. A failed full-raster check rejects the current hypothesis's extension.

1. Build a bounded standard-library streaming verifier of E01/V02, with a
   byte-backed bit reader rather than a string of all encoded bits. Retain the
   measured bit-56 start and preserve logical bit positions. Read only inside
   the declared strip and report an error when a required bit is unavailable.
2. First compare that verifier's early rows with the frozen row hashes and bit
   positions, without reacquiring a native reference. This validates the new
   measurement implementation against the previous experiment, not the format.
3. Compute and save complete candidate rasters before asking the pinned binary
   instrument for their full numerical comparisons. Include all stored columns,
   rows and margins. Use at most eight inputs per batch, 96 million samples per
   image, 512 million per batch and 16,384 samples per row; retain sensor dumps
   only in the ignored `.work/` directory. Keep failures in the reports.
4. Check all nine creator-contributed compressed originals, then the additional
   already-local 12-bit CC0 specimens from E-M1 II, PEN-F, TG-7, E-M10 III,
   E-M1X, OM-1 II, OM-3 and the second E-M5 III high-resolution original.
   Packed/multistrip specimens are outside this compressed experiment.
5. Record method/model/input hashes, instrument versions, full stored and visible
   geometry, exact sample difference counts, first mismatch, maximum difference,
   candidate/reference full-sensor hashes, every row's final bit position, output
   range and observed unused strip bits/bytes. Ending after the declared number
   of samples is the hypothesis being tested; this does not prove the absence
   of an unobserved terminal field or establish a universal padding rule.

No compressed test encoder or product Rust decoder is introduced by this stage.
Full-raster agreement remains finite specimen evidence rather than proof of all
12-bit cameras or the generalized 14-bit format. Specification review is separate
from eventual product implementation.

### Recorded metadata-gate correction

The initial full-raster tool required the inspector's `valid_bits=[12,0]`.
That observation is not exposed by the current inspector on TG-7 6946,
OM-1 II 7262 or OM-3 7796. These three inputs were excluded before prediction;
their failed report entries and the initial method are retained. Their sixteen
rows were already prospectively matched before prose exposure. Permit absent
valid-bits observations for this research extension, record their absence and
measure the entire resulting output range. Reject an exposed contradictory
depth. This is a metadata-coverage correction, not a new 14-bit coding rule or
a production format-identification policy. E01/V02 is unchanged.

### Registered final-byte and truncation checks

After complete candidates have been computed, use their recorded final token
positions to select the last consumed byte and any unused final-byte bits on
ordinary inputs P6190137, P5070002 and PIXLS.US 1993. The competing hypotheses
are: unused byte-tail bits do not affect reconstruction; or they provide a
terminal validation condition observed by the reference. Mutate every bit in
the selected final byte in isolated, unchanged-geometry, 20-second native
workers. Preserve errors, differences and invisible cases; do not assert that
mutated samples outside the ADC range are valid camera data.

Separately validate the research bit reader's strict bounds against a simple
bit-string oracle on procedural bytes. For final-token truncation, extract the
last token's start/end and test cuts before its required final byte. A cut must
fail on a required read; removing only unused trailing bytes/bits has a different
meaning. No missing bit is supplied as zero and no universal all-zero/all-one
padding acceptance rule is inferred from a finite corpus or native tolerance.
