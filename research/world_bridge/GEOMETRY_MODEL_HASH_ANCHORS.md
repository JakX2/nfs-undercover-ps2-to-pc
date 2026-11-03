# Original geometry-pack model-hash bridge: Carbon PC, Carbon PS2 and Undercover PS2

**2026-11-03. Original-file, read-only audit.** Original game binaries, model payloads, material/texture resources, per-model hash lists and extracted assets remain private. This is not a playable Undercover-in-Carbon build or a vertex conversion tool.

## How to reproduce

The source-only checker reads selected sections from the owner's original Carbon PC split-PKZIP, Carbon PS2 and Undercover PS2 world archives. The PC reader honors the real split-volume disk-relative offsets.

```sh
python research/world_bridge/geometry_hash_control.py \
  --pc-volumes /private/carbon_pc/TRACKS.z01 /private/carbon_pc/TRACKS.z02 /private/carbon_pc/TRACKS.z03 /private/carbon_pc/TRACKS.zip \
  --carbon-ps2-zip /private/carbon_ps2/TRACKS.zip \
  --undercover-ps2-zip /private/undercover_ps2/TRACKS.zip

python -m unittest discover -s research/world_bridge -p 'test_*.py' -q
```

**191/191 synthetic tests passed together locally** (24 geometry-specific tests, plus 167 earlier world-bridge tests). The checker also completed the **original-archive comparison** for all six selected sections. Code and tests were committed to the research branch, with GitHub blob SHA-1s matching the locally tested source bytes.

## What was verified

The checker uses already authenticated 92-byte `0x34110` section tables and section-contained `0x80034100` scenery roots. In each selected section it discovers **one or more** complete `0x80134000` geometry packs. It validates the nested `0x80134001` header and sorted, unique 8-byte-per-entry `0x00134003` model-index table, then walks all `0x80134010` solid chunks.

Each indexed hash must match exactly one embedded `0x00134011` solid-header hash in the same pack. The solid header can begin with **0, 4, 8 or 12 bytes of `0x11` alignment filler**; hard-coding a fixed offset produces false mismatches. Solids may also contain an optional `0x0013401A` chunk before their platform group. The in-memory checker rejects truncated chunks, unsupported platform markers, unknown version words, duplicate/unsorted index keys, nonzero index pointers, and namehash mismatches. It never exports full model bytes.

### Exact Carbon PC ↔ Carbon PS2 controls

| Source section | Model-info hashes | Geometry packs | Distinct indexed solids | Matching actual embedded solid headers | Local model hash coverage |
| --- | ---: | ---: | ---: | ---: | ---: |
| Carbon PC `141` | 29 | 1 | 29 | 29 | **29/29** |
| Carbon PC `142` | 103 | 1 | 103 | 103 | **103/103** |
| Carbon PS2 `141` | 29 | 1 | 29 | 29 | **29/29** |
| Carbon PS2 `142` | 103 | 1 | 103 | 103 | **103/103** |

Both Carbon PC indexed solid-hash sets are **identical to the corresponding Carbon PS2 sets**, not merely equal in cardinality. Across the two independent source controls, that establishes **132 individual hash-to-index-to-real-solid matches** in each platform.

These are **same-game controls**. They do not prove that an Undercover model with a new hash would exist on Carbon PC.

### Undercover PS2: multiple geometry packs inside a single section

The Undercover donor sections **241** and **3401** each contain **four structurally validated geometry packs**. The first-pack-only heuristic was demonstrably wrong, and its apparent missing-model count was misleading.

| Donor section | Local scenery-info model hashes | Valid geometry packs | Solid resource occurrences | Distinct indexed hash values | Locally resolved info hashes | Not resolved **inside this section** |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Undercover PS2 `241` | 130 | 4 | 135 | 134 | **130/130** | **0** |
| Undercover PS2 `3401` | 130 | 4 | 133 | 133 | **129/130** | **1** |

The two Undercover scenes share the same 130 distinct scenery-info model identities. The union of their geometry packs has **134 distinct indexed solid hashes**, **130/130 of the donor info hashes are covered**, and 4 indexed hashes are not used by these two particular info tables. One Undercover solid hash is duplicated across geometry packs within section 241; this is a valid observed duplicate *across packs*, unlike a duplicate in one sorted index. The single local unresolved reference in section 3401 occurs in section 241's packs.

**Scope clarification:** local and two-section coverage show serialized model-resource presence, **not runtime residency, load dependency order, or geometry validity for rendering**. There may be further global or main-area models, textures, LOD dependencies, or shared resources not represented by these two groups.

## Native PC versus console mesh platform chunks

The validated solid roots use different platform-specific child IDs. Aggregate counts in our two Carbon control sections and two Undercover donor sections:

| Original source | 0x00134900 | 0x00134B01 | 0x00134B02 | 0x00134B03 | 0x00134C02 | 0x00134A00 | 0x00134A01 | 0x00134A02 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Carbon PC, 132 solids | 132 | 158 | 132 | 132 | 367 | 0 | 0 | 0 |
| Carbon PS2, 132 solids | 0 | 0 | 0 | 0 | 0 | 132 | 132 | 132 |
| Undercover PS2, 268 solid occurrences | 0 | 0 | 0 | 0 | 0 | 268 | 268 | 268 |

In the public **Most Wanted reconstruction**, these IDs are named PC platform-info, vertex data, mesh entry table, mesh entry data, material name, PS2 platform-info, PS2 strip-entry table, and PS2 strip data, respectively. See [SpeedChunks.hpp](https://github.com/dbalatoni13/nfsmw/blob/main/src/Speed/Indep/Src/Misc/SpeedChunks.hpp). Their presence in the owner's real Carbon PC/console data is directly verified here, while their **precise Carbon runtime and vertex-buffer semantics remain to be decoded**. In particular, do not infer that PC can consume raw PS2 strip data merely because both share the same parent `0x80134010` chunk ID.

This identifies a concrete remaining conversion gate: transform actual PS2 `0x00134A01`/`0x00134A02` strip/mesh representations and their materials into the Carbon PC variant's indexed vertex, mesh, and material representation, then validate on at least two known-good source model hashes.

## Engineering next steps

1. Decode **one genuine Carbon PC control solid** plus its identical-name Carbon PS2 counterpart at the level of mesh counts, vertex/index buffers, material references and texture IDs. Do not mistake other-game reconstruction types for a confirmed Carbon PC binary ABI.
2. Confirm at least a second distinct control solid and handling of repeated PC material/vertex subchunks before constructing a writer.
3. Use Undercover's actual multi-pack model/resource groups and shared hash identities to feed a **reversible, synthetic-only conversion experiment**. Preserve donor section coordinates, visibility relationships and per-instance info references.
4. Independently validate Carbon PC's runtime loader and rendering/collision before claiming an in-game port.

**Not achieved:** vertex decoding, topology conversion, PC model/material registration, texture reuse, native in-game rendering, collision, traffic, pursuit logic or a playable world. No original game asset bytes or modified game files are published.
