# Measured compressed ORF first-row hypothesis

Task M11.3, 2026-10-08. This is a partial numerical description supported by
independent specimen measurements. It is not a full compressed-stream
specification or a product decoder. Later-row prediction, row/field resets,
termination and other camera modes were still open at this stage. The subsequent
[complete measured profile](compressed-12bit-measured.md) records the later-row
derivation and full-raster checks; this document retains the first-row evidence.

## Evidence and derivation

The [registered protocol](compressed-next-experiment.md) records competing
grammars and state families before prospective tests. An additional 384 isolated
single-bit cases extend the earlier 256 cases. Mutation-supported flag boundaries,
payload weights and signed-flag effects yield 18 and 26 continuous training
tokens. The [measured E-M5 II trace](results/em5ii-measured-prefix-tokens.json)
and [E-M1 II trace](results/em1ii-measured-prefix-tokens.json) preserve corrections
for zero, previous-sample, same-colour-left and linear predictors.

The bounded [state search](results/prefix-state-exploratory-fits.json) finds five
bias coefficient/range entries and thirty width-state fits for two parity
channels. Neither family fits a shared channel. These are fits in a recorded
family, not proof that every other possible model is impossible. The smallest
bias coefficients are 3 and 1 with divisor 32 and no rounding offset.

The first 450-model prospective comparison reproduces all 5,240 first-row values
in P2153108, but its nearly constant border does not discriminate those models.
Every model fails on P5070002; the best matches 246 values. A measured `q=16`
boundary then supports an inclusive small-code threshold, extending its match
to 744 values. The next failure is a two-bit-remainder escape: an eleven-bit
quotient is insufficient there. The affine `15-k` payload candidate matches
complete first rows, and a discriminating mutation rejects a competing changing
zero-threshold grammar that otherwise predicts the same originals.

Failed models and their first mismatches are retained in the
[initial comparison](results/first-row-prospective-comparisons.json) and
[threshold refinement](results/first-row-refinement-comparisons.json).

## Candidate rules for the first row

Observed inputs have one compressed strip with prefix bytes `00 00 00 00 01 00 00`.
Start at strip bit 56, reading each byte high bit first. This observation does
not assign meanings to the seven prefix bytes.

Keep independent states for even and odd columns. Each starts with magnitude
`A=0`, small-code count `N=0`, bias `B=0`, and previous pixel `P=0`.

For the next column of that parity:

1. Choose remainder width `k=max(4,bit_length(A)-2)` while `N<3`, otherwise
   `k=max(2,bit_length(A))`.
2. Read three flag bits `f`. Count zero bits up to twelve. Below twelve, consume
   the one terminator and use the zero count as quotient `u`. At twelve zeros,
   read `15-k` quotient bits and consume one extra bit. Then read `k` remainder
   bits `v`. Propose `q=(u<<k)+v`.
3. Let `h=~q` if flag bit 2 is set, otherwise `h=q`. Let `D=h+B` and compute
   `pixel=P+4*D+(f&3)`.
4. Update `B=floor((3*D+B)/32)`, `A=q`, and `N=N+1` when `q<=16`, otherwise
   `N=0`. Set `P=pixel` for the next column of this parity.

Signed floor division matters for negative corrections. Research comparisons
use modulo 65,536 to match the measuring instrument's u16 output. This does not
establish acceptance of malformed streams or above-range camera pixels.

## Discriminating observations

At P5070002 pixel 242, independent mutations recover `q=16`. The next even-column
token at pixel 246 has a three-bit remainder, not the four bits predicted by a
strictly-less-than-16 counter. The [boundary measurements](results/em5iii-fisheye-boundary-288-295.json)
and [measured tokens](results/fisheye-threshold-measured-tokens.json) retain it.
Missing preceding predictor values in that narrow trace are not supplied from
an assumption.

At pixel 744, the changing-payload and changing-zero-threshold hypotheses both
predict 543 and an escape ending at bit 6082. But changing bit 6066 (strip byte
758 bit 5) first affects pixel 746 under the fixed twelve-zero grammar, and
pixel 744 under the alternative. The instrument first changes pixel 746 from
395 to 54,003, exactly matching the fixed-threshold candidate's local prediction.
Changing bit 6079 (byte 759 bit 0) causes no sensor difference, consistent with
the extra bit being ignored there. See the complete
[64-case escape measurement](results/em5iii-fisheye-escape-756-763.json) and
[two discriminating cases](results/escape-discriminating-cases.json).
The high mutated value is reference behaviour outside the declared ADC range;
the changed file is not asserted to be a valid camera output.

## Complete first-row checks

The candidate matches all 34,840 declared first-row samples on seven originals
across five camera models, with no crop or margins excluded from those rows:

| Specimen | Camera | Compared samples | Differences |
|---|---|---:|---:|
| P6190137 | E-M5 II | 4,640 | 0 |
| P5121636 | E-M5 III | 5,240 | 0 |
| P5070002 | E-M5 III | 5,240 | 0 |
| P2153108 | E-M5 III | 5,240 | 0 |
| PIXLS.US 1993 | E-M1 II | 5,240 | 0 |
| PIXLS.US 2978 | PEN-F | 5,200 | 0 |
| PIXLS.US 6946 | TG-7 | 4,040 | 0 |

The PEN-F/TG-7 candidate rows were computed and saved before acquiring their
reference first rows; only their initial pairs had previously been inspected.
P5070002 was used for refinement, and the other extended comparisons are
supporting checks. Reports preserve every competing model, row hash, full
reference sensor hash, geometry, margins and instrument versions:
[escape predictions](results/first-row-escape-predictions.json),
[escape comparisons](results/first-row-escape-comparisons.json),
[extended predictions](results/first-row-extended-predictions.json), and
[extended comparisons](results/first-row-extended-comparisons.json).

The measuring instrument remains rawpy 0.27.1 / LibRaw 0.22.1 / NumPy 2.4.3,
installed as binaries only. Methods used before refinements are archived in
[methods](methods/), preserving their report hashes. Camera colour, lens
correction and full-frame decoding acceptance remain separate work.
