# Contributor instructions

This is a clean-room ORF research/corpus project intended to support a permissive,
pure-Rust decoder. Product compressed 12-bit code lives in LightCraft; this repository
contains corpus, research and replay tools. Keep the README honest about scope and
verification; other coding profiles and generalized 14-bit are not established.

- Never read or copy GPL/LGPL/AGPL raw-decoder source or reconstruct it from memory.
  Do not read the rejected LightCraft PR #240 decoder or its compressed encoder.
- Do not include Adobe assets, profiles, camera matrices, lens tables or fonts.
- Tie every new non-obvious coding rule to specimen hashes, measured operations,
  competing hypotheses and discriminating observations. Preserve failed hypotheses.
  An AI model cannot certify that its training contains no decoder knowledge.
- Review the compressed format specification separately before writing its decoder.
  Metadata, prefix coincidences and reference errors do not establish coding rules.
- Optional black-box reference binaries live only in ignored .work/; no decoder
  source is inspected, copied or made a product dependency.
- Product code must be pure Rust, safe, bounded and return errors for hostile input.
  No production panic, unchecked input offsets, unbounded allocations or recursion.
- Keep contributed photographs unchanged. New media needs a creator's explicit
  open licence, an identity in a manifest and Git LFS. External media stays in the
  ignored corpus/external directory and must pass recorded SHA-256 checks.
- Photographs in corpus/voshart-olympus are CC0. Code/docs are MIT OR Apache-2.0.
  Preserve notices when importing permissively licensed source.
- Before committing research/tools, run `python tools/verify_corpus.py --require-media`
  and compile-check the Python tools. Do not claim a reference comparison without
  recording its geometry, margins, differences, versions and output hash.
- LightCraft has its own worktree, never-commit-media rule, CI and parity tracker.
  Keep product changes there; a corpus contribution does not land a product PR.

End commit messages with `Generated with Codex.` when applicable.
