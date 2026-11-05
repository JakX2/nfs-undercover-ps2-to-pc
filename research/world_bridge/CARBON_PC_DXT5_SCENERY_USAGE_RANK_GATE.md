# Carbon PC DXT5 existing-slot material and scenery prioritization

**2026-11-04. Read-only source research for draft PR #33.** This gate narrows the next private in-game smoke test to a Carbon PC texture whose original eSolid mesh triangles and scenery instances **actually refer to its existing resource identity**. It does not show runtime visibility, a camera position, stream registration, or in-game rendering. All original game assets, texture/model hashes, palette bytes, pixels and extracted streams remain private.

## Falsifiable question

Our earlier Undercover PS2 → Carbon DXT5 donor-stage experiment successfully substituted **Carbon PC section 142 DXT5 slot 0**, a 256×256 existing resource. But would a more strongly *referenced* Carbon DXT5 slot give the first Windows visual test a better chance of success?

The new read-only `carbon_pc_dxt5_material_target_rank.py` joins **four independently validated original record types** for each Carbon PC section:

1. Sorted native Carbon PC `0x33310002` texture identity index and `0x33310004` codec/dimensions/mipmap metadata. DXT5 ordinals count only codec `38`, in the same ascending identity order used by the existing donor-stage tool.
2. Indexed Carbon PC geometry pack (`0x80134000`) and each source eSolid's **occurrence-specific** `0x00134012` texture table. Existing validated 144-byte PC mesh records provide *per-material triangle counts*, not projected screen area.
3. Original scenery `0x80034100` root, its 72-byte info records and the 96-byte instance table's candidate info reference at `+0x54`. The first PC model hash at scenery-info `+0x18` supplies **primary-detail** model identity; all four candidate model slots can also be compared separately.
4. Optional Undercover PS2 `241` or `3401` texture-pack index supplies **exact dimension-compatible donor ordinals**. This preserves both existing PC resource identity and PC mip requirement. The stage tool generates missing PC mip levels; this still needs runtime testing.

Each scene instance is counted **once**, even when the same model hash repeats across its four LOD slots. Each eSolid mesh's triangles contribute by its actual texture-table index. The tool preserves repeated model occurrences instead of overwriting hash-keyed material variants. Texture-table references absent from a *local* texture pack are counted, but are **not declared missing game resources**. No original identity hash, filename or pixel data appears in output.

## Private original-source result

Original Carbon PC split `TRACKS` volumes were inspected privately; `L5RB.BUN` and its **82,837,504-byte** `STREAML5RB.BUN` had already been extracted with full ZIP CRC/size verification. The source table supplied exact section extents. The local independent geometry/material/instance join and the new ranking logic returned:

| Carbon PC RB section | Original PC eSolid models | Scenery instances | Native DXT5 slots | With source mesh and primary-detail scenery reference |
| --- | ---: | ---: | ---: | ---: |
| **141** | 29 | 29 | **6** | **6/6** |
| **142** | 103 | 103 | **28** | **28/28** |

These are *source model/instance candidate references*, not proof a texture is drawn in a particular race or camera view.

**Best higher-model-count test target:** Carbon PC **section 142, zero-based DXT5 slot 16**, **128×64**, **4 PC mip levels**, referenced by **12 distinct eSolid models** with **328 source triangles**, each with a primary-detail scenery instance in the inspected scene. Three Undercover PS2 section-241 donors and three section-3401 donors match 128×64 exactly. Undercover section-241 sorted-index ordinals: **12, 31, 36**; section 3401: **2, 32, 35**.

Additional controls: section 142 slot 3 (128×64) has **8 source models / 440 material triangles**; slot 19 (64×32) has **4 source models / 1,144 triangles**. The previously tested section 142 slot 0 (256×256) has **1 source model / 54 triangles**. Thus slot 16 raises the number of locally referenced primary-detail models from **1 to 12**, but *does not guarantee on-screen appearance*. One distinct solid-referenced texture identity in section 142 is absent from that section's local texture index; global/shared availability remains unknown.

### Source-backed high-contrast private dry run

Source **Undercover section 241, donor ordinal 31** (8-bit PS2 indexed, swizzle flag 1) was paired with **Carbon PC section 142, DXT5 slot 16**. Both are **128×64**. The existing source's full **4-level, 10,880-byte DXT5 span** was replaced entirely in memory; **10,458 bytes** changed, all *within the one image span*. Source metadata, resource identities, stream structure, and every other byte remained unchanged, and no files were written. The donor's base-level DXT5 encode→decode errors were **RGB MAE 1.00/255**, **alpha MAE 0.00/255** against the source-decoded Undercover RGBA buffer.

Original PC DXT5 vs donor decoded color differs by **RGB MAE approximately 139.56/255**. This makes a before/after visual test potentially more distinguishable, but the donor's currently reconstructed PS2 alpha averages about **62/255**; actual game blending could diminish or change that contrast. Current doubled-PS2-alpha decoding remains an explicit experiment, not verified material blending.

## Reproduction, source-only

New, source-free test module: **49/49 synthetic tests passed locally**. It rejects malformed textures/material tables, invalid mesh material indexes, impossible scenery links, duplicate-count inflation, missing local geometry and ambiguous candidate scenery roots. It exercises the scanner's orchestration with synthetic parser stand-ins; the existing repository validators independently exercise actual root, index, mesh and graph invariants. A real-source check is separate and never runs in public CI.

From the repository checkout, with the owner's privately extracted **original** Carbon PC files and source Undercover PS2 ZIP available:

```bash
cd research/world_bridge
python -m unittest -q test_carbon_pc_dxt5_material_target_rank
python carbon_pc_dxt5_material_target_rank.py \
  --carbon-bun /private/CarbonPC/L5RB.BUN \
  --carbon-stream /private/CarbonPC/STREAML5RB.BUN \
  --undercover-ps2-zip /private/UndercoverPS2/TRACKS.zip \
  --undercover-section 241 --top 8
```

The existing donor-stage CLI's default is read-only. The selected pair can be checked with:

```bash
python private_undercover_dxt5_stream_stage.py \
  --undercover-ps2-zip /private/UndercoverPS2/TRACKS.zip \
  --carbon-bun /private/CarbonPC/L5RB.BUN \
  --carbon-stream /private/CarbonPC/STREAML5RB.BUN \
  --undercover-section 241 --carbon-section 142 \
  --donor-ordinal 31 --pc-dxt5-slot 16
```

Do **not** commit or distribute the user's original archives, extracted BUNs, private modified streams, texture hashes, decoded images or installation paths. The code does not install, write, or launch game files. Existing stream staging and guarded Windows backup/restore are still opt-in, and a Windows Process Monitor capture plus actual before/after image comparison remain required to claim game-visible results.

**Next test:** use the guarded smoke-session tool on an owner's Windows Carbon installation, confirm the exact staged DXT5 image-span read and observe a visible before/after change, then byte-exact restore. Until then the result is **stronger static material/scenery target selection**, not an in-game texture success or a native Undercover world port.
