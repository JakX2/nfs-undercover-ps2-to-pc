# V10: first original Undercover scenery model selection for a Carbon PC candidate

**Date:** 2026-11-05. **Status:** original-source static selection and clean-checkout source-only tests; **not an installed or game-rendered model**.

## Result

A bounded independent source-only audit of the owner's CRC-verified, two-member Undercover PS2 `TRACKS.zip` (`TRACKS/L2RB.BUN` and `TRACKS/STREAML2RB.BUN`) found the first reproducible **material-image-complete source scenery model candidates**.

| Original source control | Section 241 | Section 3401 |
| --- | ---: | ---: |
| Geometry pack sizes (source order) | 114 / 16 / 3 / 2 | 113 / 16 / 2 / 2 |
| Indexed source eSolid occurrences | 135 | 133 |
| Source scenery-info rows | 130 | 130 |
| Model occurrences referenced by primary scenery-info identities | 131 | 129 |
| Source models excluded for missing full-table image identities | 21 | 21 |
| Repeated model occurrences in more than one pack in that section, excluded | 2 | 0 |
| Source models outside the 4–2,048-face window, after closure checks | 2 | 2 |
| **Eligible candidates** | **106** | **106** |
| Validated local source image identities | 46 | 46 |

**Minimum-size test:** Section **241**, zero-based geometry pack **0**, zero-based model ordinal **6**: **8 triangles**, **one local material-table identity**, image-backed in the original source, **one** primary scenery-info reference. Section 3401 also has the same source model identity at pack 0/model ordinal 6.

**Slightly larger test:** With a 128–1,024-triangle window, section **241**, pack **0**, model ordinal **42**: **144 triangles**, one original image-backed texture identity and one primary scenery-info reference. In section 3401 the corresponding selection is pack 0/model ordinal 41. These are positional ordinal selectors; no original model hashes, names or source geometry bytes are published.

The original source ZIP was unchanged, and both entries passed ZIP CRC verification. The owner's repacked two-member test ZIP had SHA-256 `5ea66feecdfdcf63e24b9dd8244eeccd9a393a8d06eb50b3984c520116abfcde`. The prior standalone V9 source-auditor's 35 tests also passed in the local runtime.

## Implementation

Source-only V10 gate: [`undercover_pc_first_model_gate.py`](https://github.com/JakX2/nfs-undercover-ps2-to-pc/blob/research/ps2-map-swap-as-pc-port-oracle/research/world_bridge/undercover_pc_first_model_gate.py). Tests: [`test_undercover_pc_first_model_gate.py`](https://github.com/JakX2/nfs-undercover-ps2-to-pc/blob/research/ps2-map-swap-as-pc-port-oracle/research/world_bridge/test_undercover_pc_first_model_gate.py). Technical report: [V10 gate](https://github.com/JakX2/nfs-undercover-ps2-to-pc/blob/research/ps2-map-swap-as-pc-port-oracle/research/world_bridge/UNDERCOVER_PC_FIRST_MODEL_V10_GATE.md).

The V10 gate validates strict original scenery/model identity, complete **local eSolid texture-table** image-index closure, actual PS2 strip/VIF material triangle counts, a PC parser-shaped eSolid and a matching private PC-shaped DXT5 texture root. Neither candidate buffer is written to disk. GitHub Actions clean checkout passed **1,560 / 1,560 synthetic tests**.

**Evidence boundary:** the independent original-file ordinal audit used the prior V9 strict source-index/strip parser and a bounded original scenery-info record interpretation. The new V10 **end-to-end original-file PC geometry and DXT5 conversion** has **not** been run against the owner source in this milestone. The original-source ordinal counts are not a claim of a successful retail Carbon resource registration.

## Current blockers and next experiment

The generated geometry still includes unverified PC descriptor and material headers. The candidate texture pack has unverified retail PC registration/sampler ABI. Native Carbon scenery-info placement, post-scene control references, streaming lifetime, collision and visibility are also unresolved. A visually recognizable building is **not** established by an 8- or 144-triangle count alone.

**Next:** run the full V10 read-only owner-source conversion (try section 241 with `--min-triangles 128 --max-triangles 1024` for the second candidate), then use the original Carbon loader as an explicit *separate*, reversible private experiment. Keep the eight original source packs intact and do not install parser-shaped asset candidates as game patches.
