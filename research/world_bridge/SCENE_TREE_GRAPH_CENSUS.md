# Validated Z0 tree nodes and five-platform RB scenery graph census

**2026-11-03. Source-only, read-only research on the owner's original game archives.** This is not a native Carbon PC map writer, proven engine ABI, gameplay port, collision proof, or runtime/render test. No game bytes, names/inventories, models, textures, executable dumps, asset-derived hashes, or binaries are distributed.

## Reproduce privately

From the repository root, with Python 3.10+ and the original owner's archives:

```sh
python research/world_bridge/z0_tree_graph_probe.py \
 --pc-volumes /local/carbon_pc/TRACKS.z01 /local/carbon_pc/TRACKS.z02 /local/carbon_pc/TRACKS.z03 /local/carbon_pc/TRACKS.zip \
 --carbon-ps2-zip /local/carbon_ps2/TRACKS.zip \
 --carbon-wii-volumes /local/carbon_wii/TRACKS.z01 /local/carbon_wii/TRACKS.zip \
 --undercover-ps2-zip /local/undercover_ps2/TRACKS.zip \
 --undercover-wii-zip /local/undercover_wii/TRACKS.zip

python research/world_bridge/rb_scenery_graph_census.py \
 --pc-volumes /local/carbon_pc/TRACKS.z01 /local/carbon_pc/TRACKS.z02 /local/carbon_pc/TRACKS.z03 /local/carbon_pc/TRACKS.zip \
 --carbon-ps2-zip /local/carbon_ps2/TRACKS.zip \
 --carbon-wii-volumes /local/carbon_wii/TRACKS.z01 /local/carbon_wii/TRACKS.zip \
 --undercover-ps2-zip /local/undercover_ps2/TRACKS.zip \
 --undercover-wii-zip /local/undercover_wii/TRACKS.zip

python -m unittest discover -s research/world_bridge -p 'test_*.py' -v
```

The first tool reads the complete, small `Z0` scene root in both RA and RB using `0x34110` offsets. The second reads **only secondary-area RB** streaming bundles, each bounded to 128 MiB *uncompressed*, scans plausible root chunk signatures, validates a complete six-child frame and a graph, then requires the entire root to be contained in exactly one `0x34110` section. It emits **aggregate JSON only**.

## Candidate fixed-size scenery structures

**Observed on all ten Z0 scenes and a further 42 valid RB scenes (47 distinct RB roots in total):**

| Child ID | Observed structural layout | Verified constraints |
| --- | --- | --- |
| `0x34103` | 4-byte `0x11111111` prefix + 96 bytes per scenery instance | Positive count; downstream hierarchy references are in range |
| `0x34102` | 72 bytes per scenery-info record | Exact size multiple |
| `0x3410D` | 32 bytes per associated instance | Record count equals number in `0x34103` |
| **`0x34105`** | **48 bytes per candidate scenery tree node**, optionally preceded by **eight bytes of `0x11` filler** | Finite ordered bounds, child count 0..10, valid signed node/instance references, no cycles, exactly one reference to each instance, exactly one parent for each non-root node |
| `0x34107` | Unknown, all zero in these validated scenes | No nonzero payload found, hence no serialized field decoding possible |

**Candidate 48-byte `0x34105` node layout:** offsets +0x00..+0x0B = three float32 lower bounding values; +0x0C = u32 child count; +0x10..+0x1B = three float32 upper bounding values; +0x1C..+0x2F = ten signed 16-bit child codes. Code `>=0` identifies a scene-instance index and code `<0` identifies node `-code`, consistently with the general algorithm in [Most Wanted 2005 reconstructed Scenery.cpp](https://github.com/dbalatoni13/nfsmw/blob/main/src/Speed/Indep/Src/World/Scenery.cpp). These are **empirical candidate fields**, not a Carbon PC reverse-engineered ABI.

The optional leading eight `0x11` bytes explain why some console `0x34105` chunks have an apparent 56-byte size for a single 48-byte node. **It is not evidence of a larger PS2 node stride.** All 47 RB trees are acyclic rooted trees, with 2,500 distinct instance leaves and 586 nested-node links (one parent per non-root node).

## Ten original Z0 scene roots

| Game | Main RA: nodes / instances / infos | Secondary RB: nodes / instances / infos |
| --- | --- | --- |
| Carbon PC | **3 / 12 / 7** | 1 / 3 / 3 |
| Carbon PS2 | 1 / 2 / 2 | 1 / 2 / 2 |
| Carbon Wii | 1 / 2 / 2 | 1 / 2 / 2 |
| Undercover PS2 | 1 / 3 / 3 | 1 / 3 / 3 |
| Undercover Wii | 1 / 3 / 3 | 1 / 3 / 3 |

The Carbon PS2/Wii `Z0` scene instance and tree bytes match exactly within each region. Undercover PS2/Wii `Z0` scene instance and tree bytes also match exactly. Carbon PC main RA has a larger and deeper tree and must **not** be treated as a byte-identical Carbon PS2 Z0.

All 10 `Z0` `0x34107` child payloads are **128 zero bytes**.

## Complete RB stream results

| Source | 0x34110 sections | Valid embedded/starting scenery roots | Tree nodes | Scene instances | Nodes with 8-byte prefix |
| --- | ---: | ---: | ---: | ---: | ---: |
| Carbon PC | 15 | **13** | 163 | 643 | 6 |
| Carbon PS2 | 18 | **14** | 166 | 655 | 7 |
| Carbon Wii | 18 | **14** | 166 | 654 | 8 |
| Undercover PS2 | 8 | **3** | 69 | 275 | 2 |
| Undercover Wii | 8 | **3** | 69 | 273 | 0 |
| **Total** | **67** | **47** | **633** | **2,500** | **23** |

- **42/47 scenery roots are embedded somewhere within their own streaming-section byte ranges**; only the five `Z0` roots begin exactly at a section start. This explains why sampling just the first chunk ID at the start of each `0x34110` section undercounts scenes.
- Every accepted root is entirely within exactly one `0x34110` section range, and no section contains two accepted roots.
- Two extra raw signatures in Carbon PS2/Wii have enormous invalid root lengths; both were **rejected**, not counted as scene roots.
- Every accepted root has a valid six-child frame, bounded graph, all instance indices occurring **once each**, nested-node links forming a strict tree, and zero-filled `0x34107` data.
- **A signature scan may miss true scenery roots with another child order/serialization or roots bigger than the 64 KiB frame limit.** The totals are validated finds, not proof of an exhaustive count of every scene in every game.

## Exact complete-child comparisons at matching RB section numbers

| Same-ID scenes | Common validated roots | Identical 0x34103 instance payload | Identical 0x34105 tree payload | Identical 0x34107 payload |
| --- | ---: | ---: | ---: | ---: |
| Carbon PC ↔ Carbon PS2 | 13 | **12** | **12** | 13 |
| Carbon PC ↔ Carbon Wii | 13 | **11** | **11** | 13 |
| Carbon PS2 ↔ Carbon Wii | 14 | **13** | **13** | 14 |
| Undercover PS2 ↔ Undercover Wii | 3 | **1** | **1** | 3 |
| Carbon PS2 ↔ Undercover PS2 | 2 | **0** | **0** | 2 |

The **12/13 Carbon PC↔PS2 byte-identical** results show that substantial scene geometry/culling index information is serialized unchanged on PC in **these specific RB sections**, despite differing whole-stream packaging. The exception includes the special `Z0` region. Identical scene-tree and instance payloads do not prove compatible textures, shaders, visibility, collision, resources or runtime state.

## Test evidence and next engineering gate

**101/101 synthetic tests passed together locally** in the `research/world_bridge` workspace (41 tests cover the new hierarchy and RB graph census, plus 60 earlier tests). The actual ten Z0 roots and five complete RB streams were also validated independently on private source archives. Re-run all commands against original sources locally before modifying any tools.

Next: choose two **non-Z0** Carbon PC/PS2 RB scene roots that are byte-identical, inspect their `0x34101` header, `0x34102` info, texture/material references, and linked `0x34150` visibility records. Cross-check a differing Undercover scene without assuming that matching section IDs represent the same world location. Only then attempt a **reversible synthetic** single-scene conversion, never an unverified installable patch.
