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
