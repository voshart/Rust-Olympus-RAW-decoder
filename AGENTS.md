# Contributor instructions

This is an ORF research/corpus project aiming to support an independently derived,
permissively licensed pure-Rust decoder. The compressed decoder's provenance is
disputed upstream; do not describe it as certified clean-room or accepted.
This repository contains the standalone Rust decoder, local TIFF support,
corpus, research and replay tools. Preserve the original LightCraft submission
and worktrees; the standalone crate does not require that checkout. Keep the README honest about scope and
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
- Photographs in corpus/voshart-olympus are CC0. Original code/authored docs are
  offered under MIT OR Apache-2.0; this does not relicense third-party material or
  settle provenance. See research/licensing-and-references.md. Preserve notices
  when importing permissively licensed source. Do not erase exposure history or
  present a new AI session or a restored checkpoint as proof of independence.
- Before committing research/tools, run `python tools/verify_corpus.py --require-media`
  and compile-check the Python tools. Do not claim a reference comparison without
  recording its geometry, margins, differences, versions and output hash.
- LightCraft has its own worktree, never-commit-media rule, CI and parity tracker.
  Keep LightCraft integration changes there; the standalone decoder lives here.
  Run cargo fmt --all --check, cargo clippy --workspace --all-targets -- -D warnings
  and cargo test --workspace before committing Rust changes. Run the explicit
  full-sensor corpus tests when changing decoding or container selection.

End commit messages with `Generated with Codex.` when applicable.
