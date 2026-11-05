# Carbon PC post-scene V6: section-299 eSolid header variant and RA counterprobe

**Original-source observation:** 2026-11-05. **Scope:** owner's original Carbon PC `L5RB.BUN`/`STREAML5RB.BUN` and `L5RA.BUN`/`STREAML5RA.BUN`, extracted or streamed from a CRC-checked four-volume `TRACKS` archive. All probing was read-only, offline. **No game loading, rendering or pointer relocation has been demonstrated.**

## Section 299 is a distinct, structurally valid geometry variant

The previous V5 strict eSolid reader excluded section 299 because it encountered a version word it did not recognize. A separate version-aware bounded reader confirmed:

| Section 299 | Read-only source result |
|---|---:|
| Native PC indexed solids | 77 |
| Indexed hashes matching embedded eSolid header hashes | 77/77 |
| Serialized eSolid version word `0x00000016` | 73 |
| Alternative word `0x00400016` | 4 |
| Scene-info model identities backed by local solid index | 77/77 |
| `0x37250` control groups | 6 |
| Groups with identical non-sentinel u32 words 17 and 19 (`+0x44`, `+0x4C`) matching scenery **and** indexed solids | **6/6** |

The unusual value has the `0x00400000` bit set relative to `0x16`. **Its meaning is unknown.** It may be a flag or format variant, not necessarily a different version or a runtime-compatible alternative.

Across the seven RB sections 141, 142, 242, 299, 341, 342 and 442, the bounded version-aware parser authenticated **441 indexed solids, 441 corresponding scenery-info records and 20/20 matching native post-scene control-group pairs**. The new six observations extend V5's 14/14 result, but both studies use the same RB source population, so they do **not** constitute independent holdout validation. The field pair remains a **candidate serialized model identity**, not a proven pointer or registry ABI.

## Independent original Carbon PC RA counterprobe

The `STREAML5RA.BUN` member was decoded sequentially with a bounded section buffer. Full-stream uncompressed size and ZIP CRC-32 checks passed. This did not require materializing the 1.24 GB stream.

| RA section census | Count |
|---|---:|
| Indexed `0x34110` section rows | 962 |
| Sections within 32 MiB inspection limit | 961 |
| Bounded sections starting with the PC texture-root tag | 569 |
| Bounded sections with other prefixes | 392 |
| Sections matching the **exact RB-style** texture → geometry → scenery → `0x372xx` suffix sequence | **0** |
| Section excluded because it exceeds the 32 MiB bound | 1 |

This is a *profile mismatch*, not evidence that RA has no post-scene controls, geometry or scenery. The RA stream may organize its resources differently. No model-hash identity test was possible using the RB-specific profile.

## Code, validation and boundaries

The standalone V6 version-aware RB parser and synthetic regression tests are available in the **V6 source-only research kit**. The combined V1–V6 suite passed **150/150 tests**, with 16 new adversarial V6 checks, and the packaged files were independently extracted, hashed and re-tested. The V6 parser reproduces the RB version census; the separate RA bounded scan is recorded as an aggregate experiment and is **not reproduced by the public V6 script**.

Original RB ZIP-member SHA-256 matches the V5 provenance fingerprints. No proprietary models, binaries, textures, archive payloads, per-resource model hashes or patched game files were committed. No original source was modified.

See [V5 source evidence](CARBON_PC_POSTSCENE_ORIGINAL_RB_V5.md) and [draft PR #33](https://github.com/JakX2/nfs-undercover-ps2-to-pc/pull/33).

**Next research:** characterize the four unusual section-299 solids and independently identify Carbon PC RA layout and native loader handling before any private reversible runtime installation.
