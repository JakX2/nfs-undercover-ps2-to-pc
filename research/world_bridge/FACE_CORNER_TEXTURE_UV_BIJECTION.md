# Carbon PC ↔ PS2: per-triangle XYZ, UV and texture-label correspondence

**2026-11-03. Read-only analysis using the owner's original Carbon PC split-PKZIP TRACKS volumes and Carbon PS2 TRACKS archive.** No original game asset bytes, VIF packets, UV data, mesh buffers, texture files, individual proprietary hash lists or patched game executables are distributed. This establishes a source-controlled conversion constraint, **not** a loadable Undercover PC model.

## Reproduction

Run from repository root with the four real Carbon PC ZIP volumes in order and the separate Carbon PS2 TRACKS archive:

```sh
python research/world_bridge/triangle_corner_uv_control.py \
  --pc-volumes /private/carbon_pc/TRACKS.z01 /private/carbon_pc/TRACKS.z02 \
               /private/carbon_pc/TRACKS.z03 /private/carbon_pc/TRACKS.zip \
  --carbon-ps2-zip /private/carbon_ps2/TRACKS.zip \
  --xyz-tolerance 0.01 --uv-tolerance 0.01

python -m unittest discover -s research/world_bridge \
  -p 'test_triangle_corner_uv_match.py' -v
python -m unittest discover -s research/world_bridge \
  -p 'test_triangle_corner_uv_control.py' -v
```

The new integration tool requires **independently validated originals**: signed section rows, scenery roots, same-hash geometry index/solid pairs, Carbon PC 36-/52-byte vertex and 144-byte mesh records, PS2 VIF/ADC decoded strip vertices, and **exactly equal whole per-solid texture-hash tables**. Those controls are in the earlier world-bridge research. It processes Carbon PC/PS2 RB sections **141** and **142** only.

For each PS2 triangle, the pure-stdlib matcher finds a PC face inside the **same local texture-table index** with three corresponding XYZ corners, each within **0.01 game units**, and three corresponding float UV pairs within **0.01 UV units modulo integer U/V offsets**. It searches all six corner permutations, then uses iterative alternating-path matching so no PC face is reused by different PS2 faces.

## Results from the real original archives

| Carbon original RB control | Paired indexed models | PC triangles | PS2 ADC triangles | Distinct PC face + texture + corner XYZ/UV matches | PC-only faces |
| --- | ---: | ---: | ---: | ---: | ---: |
| **141** | **29** | **54,484** | **54,484** | **54,484 / 54,484** | **0** |
| **142** | **103** | **60,233** | **60,217** | **60,217 / 60,217** | **16** |
| **Total** | **132** | **114,717** | **114,701** | **114,701 / 114,701** | **16** |

Further source-backed diagnostics:

- **0/114,701** PS2 faces lack any PC candidate satisfying all XYZ, UV and texture-label constraints.
- **2,674** PS2 faces have multiple PC candidates satisfying all constraints (637 in section 141, 2,037 in section 142). The distinct-face assignment resolves these ambiguities instead of reusing a single PC triangle.
- The selected complete matches require periodic U/V tile offsets for **142** faces in total (78 in section 141, 64 in section 142). These are *match-dependent* counts of selected witnesses, not claims about which GPU sampler modes the textures use.
- Maximum chosen **XYZ corner witness** distance: approximately **0.009959 game units**. Maximum chosen **periodically adjusted UV corner witness** distance: approximately **0.009291 UV units**. Both fall within the stated 0.01 source-match tolerances. These are witness upper bounds, **not globally minimal or exact-nearest distances**.
- Only **57 selected matches** use an odd corner permutation; this is *provisional, assignment-dependent* and must not be treated as proof of 57 winding errors. Duplicate/near-degenerate faces can admit multiple valid pairings.
- **130/132 models** have equal triangle counts and complete two-way matching at the face level. The other two are the already-known cases with **2 and 14 extra PC triangles**. Both PS2 face sets still embed completely in their PC counterparts.
- Before accepting a local texture-table index as the same resource identity, the integration checks the two original per-solid texture-hash tables are **exactly equal**. A matching index from two *different* tables would not qualify.

This is stronger than earlier per-vertex UV witnesses, per-texture triangle budgets and unconstrained triangle matches: **the same triangle's three corners, UVs and texture identity are checked jointly**.

## Important limitations

1. Geometry-corner equality with periodic UV offsets does **not** establish the runtime sampler wrap/clamp behavior, byte-identical material commands, texture-pixel formats, shader flags, lighting or normal/tangent-space conventions.
2. Matching is geometric **without imposing face winding**; the source graph has not proved correct final PC index orientation or triangle-strip parity in all cases.
3. The PC-only 16 triangles in two control solids are still unexplained and must be accounted for as known negative cases, rather than discarded silently.
4. The Undercover PS2 donor solid reuse problem remains: one model hash can refer to two different valid texture tables in different pack occurrences. **Material context cannot be keyed solely by model hash.**
5. Neither this tool nor the other research tools write Carbon PC geometry resources or modify game archives; there has been **no Carbon PC runtime/render test** for any converted Undercover mesh and no playable Tri-City Bay port.

## Verification scope

**22/22 new synthetic-only tests passed locally**: 16 face matcher tests and 6 original-control integration tests. They cover wrong UV corner data despite matching geometry, different texture indices, nonidentical texture tables, duplicate or missing face witnesses, periodic UV offsets, unexpected source-hash collisions and malformed input.

An independent full original-file inspection script and the new integrated source-backed checker both passed all **132** control solids, each retaining only aggregate counts. The integrated run used minimal **local compatibility adapters for older helper modules** to access the original split archives; it is *not* evidence of a clean-checkout end-to-end GitHub CI pass. The committed source-only modules should be rerun against a clean checkout with the same owner-held archives before building an installable converter.

## Next falsifiable step

Construct a deliberately **synthetic-only 36-byte PC vertex/index and 144-byte mesh-record writer**, using no proprietary model or texture bytes. Validate its output using the current native PC parser, including material-group and index-buffer constraints, then stress it with duplicate UV seams, texture-index changes and invalid winding. Only after that success should an owner-local prototype use Undercover model data to create one reversible PC-format resource for a controlled Carbon PC runtime test.

**No source game files, textures, meshes or binaries were changed or published.**
