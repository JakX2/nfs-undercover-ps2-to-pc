# Undercover PS2 → Carbon PC-shaped indexed geometry: bounded source-private gate

**Date:** 2026-11-04  
**Status:** Experimental offline geometry conversion, **NOT** engine-validated.  
**Code:** `undercover_pc_geometry_bridge.py` and `test_undercover_pc_geometry_bridge.py`.

## Why this matters

Previous research verified Undercover PS2 VIF candidate XYZ, UVs and ADC-filtered triangle faces and a standalone synthetic Carbon PC 36-byte vertex/index writer. The missing bridge was packaging actual PS2 face corners with their material texture-table indices into **complete, indexed Carbon-PC-shaped 0x80134000 geometry roots and eSolids**, rather than isolated platform subchunks. This module provides that bridge with strict native-readback checks.

The original Undercover **section 241 has four validated geometry packs with 135 eSolid occurrences but only 134 distinct model identities**. Section **3401** has four packs with 133 occurrences and 133 distinct identities. Selecting/deduplicating solely by model hash loses an original occurrence. The importer therefore selects **occurrence ordinals in geometry-pack/solid stream order**. Repeated identities across independently indexed packs are preserved as distinct source occurrences, while repeated identities *within* one pack fail validation.

## Byte pipeline

1. Open the owner's original unmodified Undercover PS2 `TRACKS.zip` read-only. Validate the `L2RB.BUN` section table, original `STREAML2RB.BUN` member CRC, bounded geometry roots, each eSolid's model index/header, PS2 platform mesh framing and local texture-hash table.
2. Select section **241** or **3401** and a **zero-based source eSolid occurrence ordinal**, not a model hash. Decode source VIF candidate XYZ, UV and ADC-derived triangles using the existing readers. Preserve per-triangle local source texture-table labels.
3. Group each source model's triangles by local texture-table index. Remap source vertex indices to each new local PC mesh, preserving exact triangle multiplicity, winding up to cyclic corner rotation, UV seams and local material labels. Duplicate source vertex occurrences when material boundaries require it.
4. Derive **candidate area-weighted normals** from nondegenerate triangles. Deterministically fall back to the first valid face normal for vertices whose weighted contributions cancel. Preserve degenerate geometric triangles when at least one normal-establishing face exists per material mesh; fail closed if an entire material mesh is degenerate. Source PS2 normals are **not** claimed to be recovered.
5. Pass grouped meshes through the existing `synthetic_pc_mesh_writer.make_pc_chunks()`: native-PC-shaped **36-byte** XYZ/normal/color/UV vertices, 16-bit triangle indices, 144-byte mesh records and material-name chunks.
6. Build a new `0x80134000` indexed geometry root containing `0x80134001` index header and `0x80134010` eSolid with original PS2 source header, original local texture-hash table, and new `0x80134100` PC platform children. The eSolid identity comes from the original source but **is not registered** with Carbon PC.
7. Validate with existing Carbon PC `parse_geometry_root`, `parse_solid`, `inspect_pc_solid` and `pc_geometry_attributes`; compare the decoded faces using an **exact float32 vertex XYZ + UV + local material label multiset**, preserving duplicate multiplicities and source orientation up to cyclic corner rotation. Return aggregate counts only.

The root/header layout passes the project's parsers but unknown serialized fields, source-header cross-platform interpretations and game-loader requirements remain unresolved. The new 0x80134001 header's 144-byte payload is a zeroed synthetic candidate. Copying original PS2 eSolid header bytes is **not** a verified Carbon PC ABI translation. Texture hashes in the material table are original donor identities, not evidence that a matching Carbon PC image resource is registered. The tool is intended for private structure experimentation and must **not** be placed inside a Carbon installation on the strength of parser acceptance alone.

## Actual private original archive audit

Both source sections were read from the owner's original archive and the new conversion logic was exercised for **every eSolid occurrence**, with source-private local mirrors of the established PS2 VIF and PC-shaped readback readers. The repository's actual native readers are also exercised by the **source-free** regression tests in GitHub CI; no original assets are available to that CI workflow. Counts are aggregate only.

| Source section | Original geometry packs | eSolid occurrences | Converted | Input vertex occurrences | Input faces | Generated PC meshes | Total candidate root bytes |
|---|---:|---:|---:|---:|---:|---:|---:|
| 241 | 4 | 135 | **135** | 54,737 | 38,205 | 158 | 2,297,264 |
| 3401 | 4 | 133 | **133** | 54,619 | 38,143 | 155 | 2,291,060 |
| **Total** | **8** | **268** | **268** | **109,356** | **76,348** | **313** | **4,588,324** |

Each candidate root was checked for face-corner XYZ/UV/material multiset equality after float32 packing. There were **6,346 degenerate geometric faces preserved** (3,174+3,172) and **80 vertices** used the deterministic candidate normal fallback (40+40). These are source geometry candidate statistics, not pixel counts or in-game triangles.

Separate private CLI controls succeeded on original source occurrence ordinals **0, 2 and 134** in section 241, and **0 and 132** in section 3401. Explicit opt-in created one **new private** source-derived `.bin` file with restrictive POSIX `0600` permissions inside a temporary directory, then it was deleted; the original archive SHA-256 was unchanged. **No original or generated game-asset bytes are in GitHub or the source-only ZIP.**

## Source-free test gates

- **60 new synthetic tests** cover round-tripping complete root→eSolid→native PC mesh, multiple materials, duplicate source texture hashes, UV seams, reversed winding, original face multiplicity, float32 precision, normal candidates, zero-area triangles, invalid indices/nonfinite values, output opt-in, malformed headers and a two-pack fixture in which the *same model identity occurs in both packs*.
- On a complete repository checkout, run `python -m unittest discover -s research/world_bridge -p 'test_*.py'` (source-only, no original game assets).
- The original archive audit must be run only by a user owning the source: `python research/world_bridge/undercover_pc_geometry_bridge.py --undercover-ps2-zip /private/UndercoverPS2/TRACKS.zip --section 241 --model-ordinal 0`. This command is **read-only** and prints aggregate metrics.
- To create a **new private parser candidate** only (not an installable patch), add `--write-private --private-output /private/work/PRIVATE_UC_PC_GEOMETRY.bin`. The output must not already exist, must not be inside a game `TRACKS` directory, and is excluded from source-control handoffs. An explicit write flag **and** output path are required.

## Limits and next genuine port gates

- No stock Carbon PC runtime, shader or scene loader was run. Parser-valid geometry **does not establish renderer-visible world geometry**.
- Not yet solved: native Carbon scene/stream registration, complete Carbon PC retail eSolid header semantics, multi-pack bundle insertion, texture identity/image registration, PS2 lighting/material modes, runtime draw calls, world visibility/occlusion, collision, traffic, navigation and gameplay.
- Normals and PS2 ADC triangle winding remain **candidate** interpretations. The close Carbon PS2 ↔ Carbon PC face matching from the project's previous work is calibration, not a guarantee for every Undercover source mesh.
- Original source asset pixels, hashes, vertices, exact model/texture inventories and all private PC-shaped outputs must remain private. Aggregate-only reports are okay; **never commit any converted game asset**.
- Next engineering step: preserve **all four** independent original geometry-pack partitions while preparing a private Carbon-style section/scene registry and resolving how their material table hashes refer to properly installed textures, before attempting an in-game geometry test.
