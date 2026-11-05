# V12 · Native Carbon PC/PS2 eSolid header delta and Undercover first-model correction

**2026-11-05.** Original-source, read-only paired-format research. **No executable, installation, game archive or proprietary asset is published or patched.** This is not native Carbon scene registration or game-rendering proof.

## Why this matters

V11 generated an original-Undercover-derived, indexed PC-shaped `0x80134000` geometry resource from PS2 VIF XYZ/UV/faces. The candidate still retained its original PS2 eSolid header at `0x00134011`; the unsupported original header fields were a direct obstacle to a trustworthy first-model runtime test.

V12 matches **original Carbon PC against Carbon PS2**, model for model, under the **same model identity**, and derives a conservative transformation from actual native PC records rather than guessing a new header template.

## Original source controls

The owner's original Carbon PC split `TRACKS` archive was CRC-verified and its `TRACKS/L5RB.BUN` (179,464 bytes) and `TRACKS/STREAML5RB.BUN` (82,837,504 bytes) were read in memory. The independently supplied original Carbon PS2 `TRACKS.zip` supplied its matching `L5RB.BUN`/stream sections. Identical indexed eSolid identity and full original material tables were required before accepting any paired header.

| Carbon world RB section | Same-identity PC/PS2 eSolids | Exact after clearing high 16 bits of source PS2 eSolid word `+0x14` | Other difference |
|:--|--:|--:|:--|
| **141** | 29 | 29 | none |
| **142** | 103 | 103 | none |
| **299** | 77 | 73 | four PC special-version flags |
| **Total** | **209** | **205** | **4** |

All 209 matched models have identical **normalized header lengths**, material-table counts and full material hash tables across both Carbon platform builds. After removal of the harmless optional leading `0x11` alignment filler, the only differing bytes anywhere in each complete header are contained in **two locations**:

- Serialized word `+0x14`, high 16 bits: **nonzero in the 209 original PS2 records; zero in all 209 original PC records**. Low 16 bits agree.
- Word `+0x0C`, PC special-version flag: **4 of 209 PC records use `0x00400016`** versus PS2 `0x00000016`. Those four have no additional differences beyond the count halfword and version flag.

In other words, preserving the PS2 header but clearing **only** that upper halfword yields **205 perfectly identical complete native PC headers** under same-hash Carbon controls. No template graft, invented name hash, coordinate rewrites or fake engine pointers are required for these ordinary controls.

The four special-version records remain **unresolved**. V12 deliberately **does not invent a rule** for selecting that version, nor does it automatically rewrite the rare original PS2 `0x00800016` variant found in the Undercover source. The meaning of the packed upper halfword remains unproven.

## Undercover original model application

The owner-original Undercover PS2 RB scenery in section **241**, geometry pack **0**, supplied two fully source-image-backed and scene-referenced models in model ordinals **6** and **42** (zero-based). The new source-backed header transform was applied to the PC-shaped candidate geometry **in memory only**, preserving the original source model identity and material table; then the indexed PC-style eSolid was parsed again with an independent readback of XYZ, UV and oriented, texture-labelled faces.

| Original Undercover model | Source faces | Source VIF strip count | Header bytes actually changed | PC-shaped eSolid root bytes | Source/PC geometry witness |
|:--|--:|--:|--:|--:|:--|
| ordinal **6** | 8 | 1 | **1** | 1,236 | Pass (8/8) |
| ordinal **42** | 144 | 11 | **2** | 11,920 | Pass (144/144) |

The two models are unchanged outside their native-profile-candidate eSolid header highword, and the transform preserves the prior geometry/UV/material face witness. This original run used the **independent local original-source VIF+PC-shaped geometry mirror**. The new V10 CLI's combined owner-original VIF+DXT5 run with the opt-in profile has **not yet** been performed.

## Reusable source-only implementation and tests

[Draft PR #33](https://github.com/JakX2/nfs-undercover-ps2-to-pc/pull/33) now contains:

- [`carbon_pc_esolid_header_delta_gate.py`](https://github.com/JakX2/nfs-undercover-ps2-to-pc/blob/research/ps2-map-swap-as-pc-port-oracle/research/world_bridge/carbon_pc_esolid_header_delta_gate.py), a fail-closed PS2 header normalizer that requires real source identity/count/face agreement, modifies only the two verified highword bytes, and classifies the four PC special-version exceptions without inventing them.
- An **opt-in** `pc_header_profile='carbon_native_control'` on `convert_decoded_ps2_model()`, preserving the legacy default `preserve_source`.
- An **opt-in** `--pc-header-profile carbon_native_control` on the V10 first-model CLI, enabling read-only original Undercover geometry and material-image candidate checks.
- [22 new synthetic tests](https://github.com/JakX2/nfs-undercover-ps2-to-pc/blob/research/ps2-map-swap-as-pc-port-oracle/research/world_bridge/test_carbon_pc_esolid_header_delta_gate.py).

The complete clean-checkout GitHub Actions source-only suite passed **1,626/1,626 tests** after these changes.

A separate offline **V12 source-only ZIP kit** contains a standalone original Carbon PC/PS2 file auditor with **41 additional synthetic-only tests**, supporting owner-extracted Carbon PC and PS2 RB files, or a Carbon PS2 `TRACKS.zip`. The private native Carbon and Undercover source archives, original models, texture pixels, hashes and converted mesh bytes are excluded.

## Next decisive loader gate

This is a significant reduction of **header ABI uncertainty**, not a finished model port. The current PC mesh/vertex writer still has synthetic/default material and platform-info bytes. The DXT5 texture candidate has unknown native registration/sampler fields. The world scene-info, post-scene controls, visibility, placement, collision and streaming lifetime are not registered in Carbon.

The next game-side experiment should verify an original known-good Carbon bundle can be loaded through a reversible external resource path, before attempting new Undercover geometry/texture identities. The user previously demonstrated Carbon can launch with a separately staged texture stream and then return to byte-verified original files; that test did **not** visually confirm the Undercover texture.

**No Undercover in-game scenery model, map sector, collision, traffic or playable PC world has been demonstrated.**
