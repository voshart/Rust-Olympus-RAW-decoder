# Draft requests for an ORF specification or permissive implementation grant

Optional historical drafts, retained for reference. No outreach has been sent.
The working research plan proceeds through independent file measurements and
does not depend on a vendor response or licence grant.
The user photographs are not attachments to either request.

## To the LibRaw maintainers

Subject: Scope of a permissive licence grant for Olympus compressed ORF decoding

We develop LightCraft and PhotoCraft, open-source photo applications in pure Rust
under MIT OR Apache-2.0. Our project policy currently prevents using or deriving
product code from copyleft raw decoders. Olympus compressed ORF is a significant
coverage gap.

Would the relevant rights holders consider licensing a precisely scoped Olympus
compressed-ORF decoding implementation under MIT or Apache-2.0 for a Rust port?
The grant would need to identify the exact version/routine, required helpers,
constants and all applicable contributions. We would first appreciate guidance
on that code's ownership and history, including whether any incorporated code
requires permission from another author.

We are not requesting a general commercial-use permission or a proprietary SDK.
We would retain the agreed attribution and keep the resulting implementation
independently maintained. If a grant is possible, please describe the scope and
terms for our maintainers to review before any implementation is selected.

## To OM System developer support

Subject: Publishable Olympus/OM System ORF compression specification

We develop LightCraft and PhotoCraft, open-source photo applications written in
pure Rust. We are seeking a publishable description of the Olympus/OM System
compressed ORF bitstream, initially the 12-bit variants. Container metadata and
ordinary packed samples are understood, but compressed sensor decoding remains
unsupported under our project's clean-room policy.

Could you provide a specification we may use and publish for an independent
implementation, or a reference implementation expressly licensed under MIT or
Apache-2.0? Helpful details would cover bit ordering, residual coding, prediction,
state/reset boundaries, termination and identification of 12-/14-bit and
high-resolution variants.

Our initial CC0 validation set includes E-M5 II and E-M5 III captures. We
would welcome guidance about later OM System variants. A proprietary SDK alone
would not fit our product's licensing and pure-Rust requirements.
