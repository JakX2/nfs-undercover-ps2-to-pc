# Carbon PC original RB post-scene identity evidence (V5)

**Observed:** 2026-11-04. **Scope:** owner's original Carbon PC `L5RB.BUN` and `STREAML5RB.BUN`, extracted from a CRC-checked four-volume `TRACKS` ZIP. **Read-only offline analysis, not a playable port or runtime test.**

## Verified source controls

The `0x34110` section index contains **15** entries. In **seven** independently framed sections (141, 142, 242, 299, 341, 342, 442), an anchored texture → geometry → scenery chain is followed by a complete native PC post-scene suffix (`0x37220`, `0x37260`, `0x37250`, `0x37270`). Together, these contain **20** native control groups.

Six sections (141, 142, 242, 341, 342, 442) additionally pass strict original PC geometry index, embedded eSolid header-hash, and scenery-info/instance checks. They contain **14 control groups** and **364 scenery-info records**, with every scene identity backed by a corresponding local indexed solid. The six suffix byte sequences are distinct, and none of the six section-local model-hash sets overlap.

Section **299** has valid native suffix framing but uses an eSolid variant not covered by the current strict parser. Its six groups are excluded from the fully authenticated count rather than treated as validated model-reference controls.

## Candidate model-hash fields

Two little-endian u32 fields in each `0x37250` 120-byte payload consistently agree:

| Payload word | Byte offset | Original-source evidence |
|---|---:|---|
| 17 | `+0x44` | Matches a model hash in both local scenery and local indexed PC solids |
| 19 | `+0x4C` | Identical to word 17 and matches the same local model hash |

All **14/14** fully authenticated groups have this identical local-only pair. The existing V3 strict all-informative-word screen passes these two slots and no others. Its predeclared misaligned-byte and reversed-endian negative controls yielded **zero local-only model-hash matches**.

These are **candidate serialized model identities**, not confirmed pointer fields, an object registration ABI, or a relocation rule. The offsets were selected after exploratory analysis of the same RB section population, so this is cross-sectional confirmation, **not an independent holdout**. Actual game loading, textures, collision, streaming and Undercover geometry integration are still unverified.

## Source provenance and reproducibility

SHA-256 of the privately CRC-checked original ZIP members (fingerprints, **not** distributable game bytes):

- `L5RB.BUN`: `64b17e0af1ed559d6df4a067b826919ef7f9b1c940cea01af768b2057c5a4f3c`
- `STREAML5RB.BUN`: `b51449726b758f33de7ab2878decb53e82b56b71672070376f098a349fd5616f`

The source-only V1–V5 synthetic suite passes **134/134 tests**. Original RB findings were checked by an independent local bounded root/index/scenery parser used with the V4/V5 field controls. Reproduction with the complete GitHub PR parser dependency set remains a follow-up.

See [draft PR #33](https://github.com/JakX2/nfs-undercover-ps2-to-pc/pull/33) for the source-only world-bridge research. Do not commit or redistribute original game data, model/texture payloads, patched archives, or retail executables.

**Next:** independently validate the two fields against a separate Carbon stream or platform control; investigate section 299's different eSolid profile; only then study loader-side interpretation and reversible private experiments.
