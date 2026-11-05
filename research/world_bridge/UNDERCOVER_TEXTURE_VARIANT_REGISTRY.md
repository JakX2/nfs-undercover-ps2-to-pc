# Undercover PS2: source-section-aware texture variants

**2026-11-03. Read-only original-file research, no game assets distributed or modified.**

## Why an explicit texture selector is needed

The original Undercover PS2 secondary-area `TRACKS/L2RB.BUN` section table leads to two complete, structurally validated texture packs in `TRACKS/STREAML2RB.BUN` at section IDs **241** and **3401**.

The original image metadata parser (`texture_metadata_pixel_bridge.py`) finds **46 indexed textures in each**. Each same-name hash occurs in **both** sections. All 46 pairs have matching source names, PS2 palette codec, and candidate texture-mode flags. But **every pair has different image dimensions**.

| Verified aggregate | Result |
| --- | ---: |
| Source texture packs | **2** |
| Total indexed texture records | **92** |
| Distinct name hashes | **46** |
| Hashes with multiple section-specific variants | **46/46** |
| Pairs with equal dimensions | **0/46** |
| Section 241 at least as large in both dimensions | **46/46** |
| Section 241 strictly larger in one or both dimensions | **46/46** |
| Pairs with different mip counts | **1** |
| Pairs with mismatched names / codecs / mode flags | **0** |

All variants retain their own actual original image/palette offsets, byte sizes, dimensions and mip counts. Therefore a global hash → single image dictionary would discard valid source information. The smaller section-3401 version is not declared redundant: resolution differences may reflect intentional LOD, stream residency, performance, or other loader behavior not yet verified.

## The source-only registry

`texture_variant_registry.py` implements an in-memory registry keyed by **source section plus original name hash**. Calling `resolve(hash)` without a source-section hint raises an ambiguity error whenever the name hash has more than one source. Explicit `resolve(hash, section=241)` and `resolve(hash, section=3401)` preserve their different metadata and return defensive copies.

It also checks that reused name hashes have compatible names, source codec and candidate texture-mode values. A hash collision with different identity metadata causes a visible error instead of silently overwriting another record. The optional `coverage(...)` function counts model texture references present locally versus anywhere in the examined sections, **without printing original hashes**. Presence in an indexed source pack does not guarantee texture runtime availability.

## Reproduce

From repo root with the owner's original **Undercover PS2** TRACKS archive:

```sh
python research/world_bridge/texture_variant_registry.py \
  --undercover-ps2-zip /private/undercover_ps2/TRACKS.zip

python -m unittest discover -s research/world_bridge \
  -p 'test_texture_variant_registry.py' -v
```

The CLI reads only the bounded L2RB small bundle and L2RB stream, validates the donor `0x34110` section rows and full texture metadata/pixel spans, and prints aggregate JSON. It never writes source files, exports texture names/hash inventories, emits pixel data or chooses one variant on the user's behalf.

### Verification

- **15/15 new synthetic-only variant-registry tests** pass locally, including explicit ambiguous selection failure, changed image offsets, inherited mipmap variants, source-name and texture-mode collisions, absent hashes, reference coverage, defensive copies and invalid record fields.
- The three texture-focused test modules (`test_texture_pack_index_probe.py`, `test_texture_metadata_pixel_bridge.py`, `test_texture_variant_registry.py`) pass **52/52 tests together** locally.
- The real original Undercover PS2 CLI passes and reproduces all table values above.
- The **exact GitHub blob SHA-1s for the new registry and its tests** match the tested local files. No full clean-checkout GitHub CI run or Carbon PC runtime test is claimed.

## Important remaining blocker: PS2 indexed-pixel deswizzling

Source PS2 metadata has PSM values 0x13 (8-bit indexed) and 0x14 (4-bit indexed). Candidate platform swizzle flags vary, mostly 1, but **matching source palette colors and correct image ranges do not yet establish a correct image layout**. A preliminary private PS2 GS-deswizzle experiment, based on publicly available MIT-licensed Most Wanted PS2 research, produced image arrangements that did **not** reliably line up spatially with the corresponding Carbon PC DXT textures.

We deliberately **have not committed or enabled that experimental decoder as a validated conversion step**, nor have we claimed usable decoded donor images. Future work requires independent same-hash Carbon visual/pixel correlation controls, proper PS2 palette/GS layout verification, mip chain handling, texture-pixel format conversion, native PC texture-pack serialization and game runtime testing. Collision, traffic and a playable Undercover-in-Carbon world remain separate larger goals.
