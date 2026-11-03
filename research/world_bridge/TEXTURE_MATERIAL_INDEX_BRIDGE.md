# Source-verified texture-table and per-material polygon-budget bridge

**2026-11-03. Read-only analysis of owner-supplied original archives.** This is source-only research, not a Carbon PC-compatible Undercover texture pack, binary writer, loader patch, or a playable Tri-City Bay build. Original models, materials, pixel data, individual proprietary resource hash listings and executable bytes remain private.

## Run against local original sources

From the repository root, supply the exact owner-held original archives:

```sh
python research/world_bridge/texture_binding_control.py \
  --pc-volumes /private/carbon_pc/TRACKS.z01 /private/carbon_pc/TRACKS.z02 \
               /private/carbon_pc/TRACKS.z03 /private/carbon_pc/TRACKS.zip \
  --carbon-ps2-zip /private/carbon_ps2/TRACKS.zip \
  --undercover-ps2-zip /private/undercover_ps2/TRACKS.zip

python -m unittest discover -s research/world_bridge \
  -p 'test_texture_binding_control.py' -v
```

The tool authenticates parent streaming sections and geometry-pack indices using the existing read-only world bridge, then inspects only **Carbon PC/PS2 RB sections 141/142** and **Undercover PS2 RB sections 241/3401**. It reads validated eSolid header `0x00134011`, per-solid texture table `0x00134012`, and appropriate platform material/mesh descriptors. Its JSON output contains aggregate numbers only.

### Serialized texture-index links now corroborated

- The eSolid header has a candidate **texture-table entry count at +0x19** (after optional 0, 4, 8 or 12 bytes of `0x11` filler). The table consists of **8-byte entries** (u32 texture name hash followed by zero pointer word). Every original sampled solid satisfies the complete count/size equation; every sampled texture index points within its own local table.
- On Carbon PC, the **low byte at offset +0x18** in each 144-byte `0x00134B02` mesh record behaves as the local texture-table index. Its exact bytewise packing **must not** be assumed to be four repeated index bytes: **17 of the 367** PC mesh records have additional packed bits or a different word pattern. The parser preserves the source field and only reads the candidate low-byte index. The independent PC per-mesh triangle count remains at +0x60.
- On Carbon/Undercover PS2, the **signed byte at +0x0E** in each 16-byte `0x00134A01` strip record behaves as the texture-table index. The neighboring +0x0D field behaves as a polygon group. In all sampled PS2 solids, each observed polygon-group number consistently uses just **one** local texture index, though group numbering/order need not match Carbon PC mesh-record order.

## Carbon same-hash PC↔PS2 control comparison

| Source-backed measure | Result |
| --- | ---: |
| Original indexed solid model identities paired | **132** |
| Complete per-solid texture-hash tables byte-identical PC↔PS2 | **132 / 132** |
| Same set of local texture-table indices used by both platforms | **132 / 132** |
| Entire **per-texture-index polygon-count budgets** match | **130 / 132** |
| Valid Carbon PC mesh texture indices | **367 / 367** |
| Valid Carbon PS2 strip texture indices | **7,257 / 7,257** |
| Carbon PC native triangles | **114,717** |
| Carbon PS2 reconstructed strip polygons | **114,701** |

The two nonmatching polygon budgets are **+2** and **+14** PC triangles, respectively, assigned to local texture index 0 of their respective models. These are **exactly the two previously isolated geometry-count discrepancies**; no additional independent per-texture count discrepancy appears. The complete texture-hash lists are source-identical in all 132 same-hash model pairs despite differently serialized mesh geometries.

**What this proves:** the selected Carbon PC and PS2 solids preserve the same local texture-resource hash tables, and their model geometry is grouped by matching texture-table indices at the aggregate triangle-count level. It does **not** prove texture pixel availability, material-name equality, sampler modes, per-face material bijection, UV winding, shader equivalence or the Carbon PC renderer's acceptance of a converted PS2 eSolid.

## Undercover PS2 donor sections 241 and 3401

| Verified measure | Result |
| --- | ---: |
| Original streamed geometry packs | **8** (four per section) |
| Original indexed eSolid **resource occurrences** | **268** |
| Distinct model-name hashes across those occurrences | **134** |
| Valid complete eSolid texture tables | **268 / 268** |
| Texture-table entry occurrences | **323** |
| Valid PS2 strip-to-texture indices | **4,056 / 4,056** |
| Per-solid consistent polygon-group→texture indexes | **268 / 268** |
| Distinct polygon-group occurrences summed by solid | **317** |
| Reconstructed strip triangle occurrences | **76,348** |

**Important donor edge case:** one indexed model-name hash occurs **twice within section 241**, but the two eSolid occurrences carry **different texture tables (two entries versus one)**. Since both instances pass normal table/strip bounds checks, the converter must **not** key mutable per-solid texture bindings only by model hash and overwrite one with the other. It must preserve the source occurrence/pack context, distinguish material variants and determine how the game selects them. The report does not identify or distribute the original hash.

The table-entry, solid and triangle totals count **occurrences across two donor streaming sections**, not unique assets or polygons in the entire Undercover city.

## Quality and explicit next gate

- **19/19 new synthetic-only tests passed locally**: malformed texture-table counts, invalid resource pointers, hash zeroes, unsupported versions, duplicate-hash preservation, out-of-range PC/PS2 texture indexes, mixed-texture polygon groups, unexpected PC packed fields, PC↔PS2 texture table mismatches, per-texture count discrepancies and repeated donor model hash variants.
- The source-backed three-platform archive audit completed successfully with **minimal local compatibility adapters for previously committed helper modules**. The two committed new Python files were checked by GitHub blob SHA-1 against the exact tested local versions. This is **not** a full clean-checkout CI run.
- Existing research already established 114,701/114,701 one-to-one geometric triangle matches and complete bidirectional PC/PS2 XYZ + periodically wrapped UV witness coverage across the 132 models. **Those earlier geometric/UV matches have not yet been joined into a single per-face texture-label witness.**

**Next experiment:** use two independently source-pinned Carbon models and the established one-to-one triangle matcher to attach the local texture index to every face on **both platforms**, then compare *position + UV + texture-hash* per face. Account for ambiguous matching near duplicate geometry and wrapped UV tiles. After that, identify the actual underlying texture resources and their address modes in the original texture packs before any reversible synthetic PC material/mesh writer.

No game archives modified. No proprietary game content or patch files published.
