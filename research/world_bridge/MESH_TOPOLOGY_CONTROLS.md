# Actual Carbon PC ↔ PS2 mesh topology controls, with Undercover PS2 strip validation

**2026-11-03. Read-only original-file audit.** The owner's original Carbon PC, Carbon PS2 and Undercover PS2 `TRACKS` archives were inspected privately. Only this original analyzer, synthetic tests and aggregate results are committed; no geometry/texture/strip bytes, per-model hash inventories, private files, executable modifications, or game builds are committed.

## Reproduce

Run in repository root with locally retained original archives:

```sh
python research/world_bridge/mesh_topology_control.py \
  --pc-volumes /private/carbon_pc/TRACKS.z01 /private/carbon_pc/TRACKS.z02 /private/carbon_pc/TRACKS.z03 /private/carbon_pc/TRACKS.zip \
  --carbon-ps2-zip /private/carbon_ps2/TRACKS.zip \
  --undercover-ps2-zip /private/undercover_ps2/TRACKS.zip

python -m unittest discover -s research/world_bridge -p 'test_*.py' -q
```

**Verification:** 28 new synthetic-only tests passed and the complete **219/219 world-bridge synthetic suite** passed locally. The real-source probe completed on six source-authenticated RB streaming sections (two per game/platform source), with every selected embedded solid validated against its geometry pack's sorted model-hash index and embedded header hash. The exact locally tested Python sources were matched against their GitHub committed blob SHAs.

## Verified serialized platform layouts

### Carbon PC geometry, 132 original solids

- `0x00134900` is the PC platform-info child in each validated `0x80134010` solid. A candidate **u32 version = 0x12**, mesh-record count at platform-info +0x10 and triangle-index count at +0x2C (both offsets **after any initial 0x11 alignment filler**) agree with each corresponding serialized child.
- `0x00134B02`: exactly **4 leading 0x11 bytes + 144 bytes × mesh count**.
- `0x00134B03`: exactly **8 leading 0x11 bytes + 16-bit index bytes rounded up to the next 4-byte boundary**. Every examined index count is a **multiple of 3**, consistent with an indexed triangle list.
- `0x00134C02`: **one material-name chunk per candidate 144-byte mesh record** across all sampled PC solids.
- `0x00134B01`: PC vertex-data chunks have varying 0/4/8/12-byte alignment filler, and their non-filler lengths are divisible by **36 bytes, 52 bytes, or both**. That is a **stride candidate from length divisibility**, not yet a decoded vertex format, flag mapping, or verified PC loader ABI. A script assuming every vertex buffer has the same 36-byte stride will reject actual PC source data.

Totals from original Carbon PC sections `141` and `142`:

| Section | Solids | 144-byte mesh entries | 16-bit triangle indices | Candidate triangles (indices ÷ 3) | PC vertex-data chunks | Material-name chunks |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| **141** | 29 | 127 | 163,452 | **54,484** | 31 | 127 |
| **142** | 103 | 240 | 180,699 | **60,233** | 127 | 240 |
| **Total** | **132** | **367** | **344,151** | **114,717** | **158** | **367** |

Of 158 PC vertex-data chunks, the non-filler length admits **only 36-byte records in 125**, **only 52-byte records in 12**, and is **ambiguous between both in 21**. This does *not* establish actual per-vertex layout until the PC mesh entries and platform flags are decoded.

### Carbon PS2 and Undercover PS2 strip data

Within the `0x00134A00` platform-info child, after 0/4/8/12 bytes of leading filler, the candidate u32 values at +0, +4, +8 are **version 0x20**, number of strips, and strip-data byte count. All **400 examined console solid occurrences** pass both size equations:

- `0x00134A01`: exactly **4 leading filler bytes + strip count × 16-byte entry**.
- `0x00134A02`: exactly **8 leading filler bytes + declared strip-data bytes**.
- All **11,313** real strip descriptors (Carbon PS2 7,257; Undercover PS2 4,056) have zero descriptor flags, finite candidate material density, `NumVerts >= NumPolys + 2`, and their candidate `DataQWordOffset/Size` ranges fall within the declared platform strip-data blob.

The public reconstructed Most Wanted `eStripEntry` type provides plausible field labels for the same 16-byte record format. Those labels are **source-guided hypotheses cross-checked against the original serialization**, not confirmed Carbon/Undercover runtime C++ ABI. Importantly, bounded strip-table metadata does not decode the PS2 VIF/DMA payload's vertices, normals, UVs, texture assignment or final triangle winding.

Original PS2 source budgets:

| Section | Solid occurrences | 16-byte strip entries | Candidate strip polygons | Declared strip vertices | Strip-data bytes |
| --- | ---: | ---: | ---: | ---: | ---: |
| Carbon PS2 `141` | 29 | 3,521 | **54,484** | 100,464 | 1,703,008 |
| Carbon PS2 `142` | 103 | 3,736 | **60,217** | 104,539 | 1,779,152 |
| UC PS2 `241` | 135 (134 distinct) | 2,031 | **38,205** | 54,737 | 936,560 |
| UC PS2 `3401` | 133 | 2,025 | **38,143** | 54,619 | 934,448 |

Undercover totals intentionally **count resource occurrences within two separate streamed sections**; some model hashes/references are shared across the two sections. Do not interpret 38,205 + 38,143 as the number of unique polygons in Undercover's entire map.

## Actual paired topology-count check: 130/132 models

The two Carbon PC/PS2 controls share **exactly the same 132 model-hash identities**, established in the earlier geometry-index audit. The new probe matches each source model hash to its individually bounded real solid and compares:

- **PC count:** candidate u32 index-count at PC platform-info +0x2C, divided by 3.
- **PS2 count:** sum of byte `NumPolys` values from every 16-byte strip descriptor in the paired console solid.

| Same-hash PC/PS2 control | Exact per-model polygon counts | Mismatches |
| --- | ---: | --- |
| Section 141, 29 solids | **29/29** | 0 |
| Section 142, 103 solids | **101/103** | 2 |
| **Total** | **130/132** | **2** |

The two mismatches are **+2** and **+14** candidate polygons on PC, respectively. Therefore PC has **114,717** triangles, compared with **114,701** summed PS2 strip polygons across these 132 models. The entire 16-polygon difference is accounted for by those two individual model hashes; no source hash list is published.

**Interpretation limit:** equal polygon counts are evidence of a closely related mesh topology, but they **do not prove matching triangle connectivity, vertex order, winding, UVs or texture semantics**. The differing two source meshes could reflect LOD, reduction or another version/platform-specific cause. No cause has been established.

## Practical next converter gate

1. For two separately anchored Carbon PC/PS2 solids, decode the 144-byte PC mesh-record entries sufficiently to establish per-material triangle start/count ranges, vertex-buffer choice and index bounds.
2. Decode matching PS2 `0x00134A01` strip descriptors and `0x00134A02` VIF/DMA payload to recover actual positions, UVs, normals and strip winding, with bounded entries and explicit malformed-data refusal. Preserve ambiguity instead of guessing.
3. Compare *actual geometry* on the **130 count-matched controls** before claiming semantic equivalence or generating Carbon PC bytes; use the +2/+14 mismatches as regression negatives.
4. Once two complete paired original solids can be round-trip/structurally checked, design a synthetic-only triangle/vertex writer that meets **native Carbon PC** mesh/index/material requirements.
5. Only then attempt privately testing a donor Undercover model in-game. Collision, visibility, texture packs, AI and city-wide section integration are separate unmet goals.

**No playable port, PC runtime success, or converted model is claimed.** No additional user files are necessary for this step.
