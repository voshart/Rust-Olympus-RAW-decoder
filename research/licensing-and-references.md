# Licensing scope and reference history

The repository offers original code and authored research documentation under
MIT OR Apache-2.0. That is a license grant for contributors' original material,
not a finding that every described coding rule or linked implementation has
independently established provenance. No third-party source or photograph is
relicensed merely by appearing in a reference or a repository manifest.

## What the licenses cover

| Material | Offered or upstream terms | Scope |
|---|---|---|
| Original repository tools and authored documents | MIT OR Apache-2.0 | The contributors' original material; preserve required notices. This is not clean-room certification. |
| Creator-contributed Olympus photographs | CC0-1.0 | The unchanged originals identified in the [creator manifest](../corpus/user-images.json) and [dataset dedication](../corpus/voshart-olympus/LICENSE-CC0.txt). |
| External photographs | Individually recorded licenses | See [external-sources.json](../corpus/external-sources.json); the software license does not replace those terms. |
| LibRaw, used through an optional separately installed binary instrument | LGPL 2.1 OR CDDL 1.0 | LibRaw's library licenses; the user may choose either. The library and reference arrays are not bundled. |
| RawSpeed, referenced by later source-derived prose | LGPL 2.1 | The upstream library's terms. It is not a repository dependency or bundled source. |
| Product Rust decoder | Offered in the linked LightCraft fork | Its implementation and provenance are under upstream review; this research repository does not publish a standalone Cargo decoder. |

## Official third-party license references

- [LibRaw's official licensing statement](https://www.libraw.org/about) offers
  GNU Lesser General Public License 2.1 OR Common Development and Distribution
  License 1.0. LibRaw is not GPL-only and is not MIT/Apache licensed.
- [RawSpeed's official repository](https://github.com/darktable-org/rawspeed)
  identifies GNU Lesser General Public License 2.1.
- [CDDL 1.0](https://opensource.org/license/CDDL-1.0), sections 3.1–3.2 and 3.6:
  covered source and modifications remain under CDDL, while a larger work may
  contain separately licensed code. The copyleft scope is file-based.
- [LGPL 2.1](https://opensource.org/license/lgpl-2-1), sections 0, 2 and 6:
  running the library is distinguished from incorporating or modifying covered
  code; output is covered only when its contents constitute a work based on the
  library. Library modifications and distribution/linking have their own terms.
  A straightforward translation of covered code into Rust does not remove those
  obligations.

Using LibRaw to compare sensor numbers does not, by itself, establish that the
Rust code is a derivative of LibRaw. Conversely, numerical agreement and a
MIT/Apache label do not establish independent authorship. The actual creation
process matters, and LightCraft may apply a stricter contribution policy.

The reference instrument was rawpy 0.27.1 with LibRaw 0.22.1 and NumPy 2.4.3.
Wrapper/support packages retain their own upstream terms; the LibRaw entry above
does not describe every package in the optional environment. The exact binary
versions and wheel hashes are in [the provenance record](orf12-provenance.md#external-measuring-instrument).
The optional environment is not needed for replay against published hashes.

## Measurements and source-derived explanations

The [provenance history](orf12-provenance.md) records the actual exposure:

- First-row findings were committed at `15e7a61` before the two supplied format
  explanations were read. Later-row work was frozen in a 96-file hash manifest.
  The [checkpoint record](results/pre-prose-checkpoint.json) is a recorded state,
  not an external timestamp or independent certification.
- Those pre-summary experiments already used a black-box LibRaw reference for
  measurements and comparisons. Restoring that checkpoint would retain oracle use.
- Later AI-generated explanations attributed implementation details to RawSpeed
  and LibRaw. Their private hashes and exposure sequence remain disclosed. The
  supplied text is not republished or treated as independent verification.
- Reported origins included the [RawSpeed Olympus decompressor source URL](https://github.com/darktable-org/rawspeed/blob/develop/src/librawspeed/decompressors/OlympusDecompressor.cpp),
  [dcraw's site](https://www.dechifro.org/dcraw/), the
  [LibRaw repository](https://github.com/LibRaw/LibRaw) and its
  [February 2025 release notes](https://www.libraw.org/news/libraw-202502-snapshot).
  The decoder source URLs were recorded as references and were not opened.
  A source URL is not an approved independent specification.
- Release-note and format-note prose were read, and a generic libopenraw
  container-recognition snippet appeared incidentally in a search. The record
  does not claim zero code-snippet exposure. A third implementation-specific
  performance explanation was read after implementation and is also disclosed.
- Research, specification review and implementation were performed by the same
  AI-assisted author. No assurance is made about the model's training data.

## Unresolved upstream decision

The [review on LightCraft PR #360](https://github.com/storytold/lightcraft/pull/360#issuecomment-6073438977)
objects to implementation similarity, source-derived prose exposure and LibRaw
oracle use. It leaves the final decision to the maintainer. The
[license and process clarification](https://github.com/storytold/lightcraft/pull/360#issuecomment-6073712543)
asks whether the pre-summary experiments can support a separately reviewed
specification and implementation, or whether black-box LibRaw-assisted inference
itself is outside the project's policy.

Until that is resolved, do not describe the compressed decoder as clean-room
certified, upstream accepted, or cleared solely because license files exist.
Its numerical validation remains recorded evidence; its provenance acceptance
is a separate unresolved question. The review welcomes the independent padded
packed-layout, corpus and CFA fixes as a separate contribution.
