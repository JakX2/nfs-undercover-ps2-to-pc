# V20: Carbon PC texture-first source-section prefix correction

**Date:** 2026-11-12  
**Branch:** `research/ps2-map-swap-as-pc-port-oracle` (draft PR #33).  
**Status:** Source-only, synthetic tests. No proprietary game asset or runnable port distributed.

## Source-backed correction to V19

The previous V19 experiment built a `.pcchunk` in this order:

    GEOMETRY (0x80134000) -> TEXTURE (0xB3300000)

That is **not the order** in owner-original Carbon PC RB sections 141/142 that our already-existing `carbon_pc_native_postscene_layout_gate.py` parses from the private source. Those original sections begin:

    TEXTURE (0xB3300000)
    -> GEOMETRY (0x80134000), on a 16-byte boundary
    -> SCENERY (0x80034100), on a 16-byte boundary
    -> POST-SCENE CONTROL (0x372xx sequences)

The original source controls also contain a possible intervening zero chunk before the scenery root in one section. The ordering is evidence from selected native **streaming sections**, not a claim that every third-party external `.BUN` loader expects precisely this sequence.

V20 corrects `carbon_pc_first_model_stream_assembly.py` so a one-model private `.pcchunk` now contains:

    TEXTURE (PC-shaped DXT5)
    -> GEOMETRY (PC-shaped indexed eSolid)

The builder verifies that the complete texture root length places the geometry at a **16-byte aligned offset**. If not, it fails closed instead of inventing an unverified padding chunk. The combined file is independently reparsed by the previous V16 bounded native PC chunk scanner, and full-table texture/material identity closure remains mandatory.

The owner-private, exclusive `--write-private` exporter now **requires texture-first order** and rejects obsolete geometry-first V19 `.pcchunk` files. Previously created V19 experimental files should be regenerated from owner-original game assets using the current code. They were never known to be Carbon-loader-ready.

## Explicit missing dependencies, not invented replacements

V20's redacted first-model assembly report now provides:

- `native_carbon_section_texture_before_geometry: true`
- `native_carbon_geometry_start_aligned_16: true`
- `missing_carbon_scenery_root: true`
- `missing_carbon_postscene_control: true`
- `complete_native_carbon_stream_section: false`

The **0x80034100 scene instance/detail tables** and **0x372xx Carbon control records** have been studied in other repository probes, but source-backed relocation and candidate generation have **not** been implemented. It would be incorrect to create fabricated matching records just to satisfy a parser. Likewise, a structurally plausible streaming section is not automatically accepted by the separate XNFSModFiles external loader.

## Validation

The V20 implementation and regression tests cover texture-before-geometry ordering, 16-byte geometry start alignment, continued PC geometry/DXT5 parsing, original material-table closure, default denial of unsafe direct game installation, private file regeneration, rejection of geometry-first V19 export data, and malformed resource tags.

On commit `86b0cfeff88f`, [GitHub Actions run 43250274520](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/43250274520) passed **1,797 synthetic source-only tests**. No Carbon executable or original game files were used in CI.

Two earlier V20 CI runs failed during the transition: one from tests expecting the old geometry-first layout, and one from a negative test that changed opaque padding instead of a validated resource tag. Both were corrected and the final code run passed.

## Remaining decisive engineering work

1. Reconstruct one **source-backed Carbon PC scenery root** pointing to the candidate eSolid and a real tested placement, without guessing layout fields.
2. Determine whether Carbon's **post-scene 0x372xx control data** can be generated or safely reused with matching verified references. This is a distinct dependency for original PC stream sections.
3. Independently prove a **known-good original Carbon external bundle** loads and registers through the actual selected loader on an owner's Windows installation.
4. Only then attempt a converted Undercover candidate, capture controlled runtime read/registration/visual evidence and begin scene/collision work.

**No Undercover asset is yet confirmed rendered by Carbon PC, and no playable Undercover-on-Carbon conversion exists.** The separate Wii C++ physics research branch PR #35 is unchanged.
