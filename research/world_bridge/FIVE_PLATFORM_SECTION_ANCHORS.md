# Five-platform 0x34110 world-section spatial/stream-header audit

**2026-11-03. Read-only evidence from original owner-supplied archives; not a converted world, a verified Carbon PC runtime loader, or gameplay/collision proof.** No original game assets, archive bytes, full section lists, proprietary symbols, executable patches or binaries are published.

## Reproduce

Run from repo root with Python 3.10+ and the locally held original archives:

```sh
python research/world_bridge/section_identity_anchor.py \
  --pc-volumes /local/carbon_pc/TRACKS.z01 /local/carbon_pc/TRACKS.z02 /local/carbon_pc/TRACKS.z03 /local/carbon_pc/TRACKS.zip \
  --carbon-ps2-zip /local/carbon_ps2/TRACKS.zip \
  --carbon-wii-volumes /local/carbon_wii/TRACKS.z01 /local/carbon_wii/TRACKS.zip \
  --undercover-ps2-zip /local/undercover_ps2/TRACKS.zip \
  --undercover-wii-zip /local/undercover_wii/TRACKS.zip \
  --sample-prefix-mib 32
python -m unittest discover -s research/world_bridge -p 'test_*.py' -v
```

The tool reads only small L5RA/L5RB/L2RA/L2RB bundles and **at most 32 MiB uncompressed from each of ten** `STREAM*.BUN` sources by default. It never materializes the ~1.24 GiB Carbon PC STREAML5RA member. Its split-PKZIP reader follows per-disk local-header offsets. It emits only aggregate statistics and section-type categories. Source filenames in commands must be real local paths.

**Tests:** 20 new synthetic-only tests passed locally. All **45/45** selected world-probe tests passed together; the original five-platform audit also completed.

## The 92-byte section-row candidate is consistent across all five versions

The `0x00034110` table in each RA and RB bundle is divisible into 92-byte rows, consistent with the public Most Wanted reconstruction's `TrackStreamingSection` structure. Each row includes a name at +0, signed 16-bit section number at +8, 32-bit file offset at +0x14, two 32-bit length fields at +0x18/+0x1c, candidate priority at +0x24, candidate 2D centre at +0x28, radius at +0x30 and a checksum field at +0x34.

| Source | RA rows | RB rows |
| --- | ---: | ---: |
| Carbon PC | 962 | 15 |
| Carbon PS2 | 1,191 | 18 |
| Carbon Wii | 1,194 | 18 |
| Undercover PS2 | 2,041 | 8 |
| Undercover Wii | 2,067 | 8 |
| **Total** | **7,455** | **67** |

Every one of **7,522** rows has candidate status 0, candidate file type 1, two equal file-size words, a file offset divisible by 2,048 and an in-bounds, ordered, nonoverlapping byte range within its matching original uncompressed stream. This validates the candidate layout *structurally*. The meaning of Carbon PC's runtime fields and loader acceptance still need independent evidence.

## Spatial identity: same game vs cross-game

Raw bytes at +0x28 through +0x33 were compared for each **shared signed section number**. These are the candidate float32 XY centre and radius from the Most Wanted reconstruction; comparing exact source bytes avoids tolerances or inferred coordinate transforms.

| Comparison | Sector | Shared section IDs | Exact spatial triples | Both triples zero | Matched **nonzero** triples | Different triples |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Carbon PC ↔ Carbon PS2 | RA | 957 | 957 | 203 | 754 | 0 |
| Carbon PC ↔ Carbon PS2 | RB | 15 | 15 | 3 | 12 | 0 |
| Carbon PC ↔ Carbon Wii | RA | 958 | 958 | 203 | 755 | 0 |
| Carbon PC ↔ Carbon Wii | RB | 15 | 15 | 3 | 12 | 0 |
| Carbon Wii ↔ Carbon PS2 | RA | 1,190 | 1,190 | 324 | 866 | 0 |
| Carbon Wii ↔ Carbon PS2 | RB | 18 | 18 | 5 | 13 | 0 |
| Undercover Wii ↔ Undercover PS2 | RA | 2,041 | 2,041 | 1,347 | 694 | 0 |
| Undercover Wii ↔ Undercover PS2 | RB | 8 | 8 | 7 | 1 | 0 |
| **Undercover PS2 ↔ Carbon PS2** | **RA** | **700** | **203** | **203** | **0** | **497** |
| **Undercover PS2 ↔ Carbon PS2** | **RB** | **6** | **5** | **5** | **0** | **1** |

The source-byte equality is **complete across same-game platform comparisons**, even though almost all stream **offsets and serialized byte lengths** differ. Example: Carbon PC ↔ Carbon Wii RA has 958 shared section IDs, 958 matching exact spatial triples but only **1** equal stream-file offset and **13** equal stored lengths. This directly separates *stable world-section identity/spatial fields* from *platform-specific resource packing*.

**Important danger:** Carbon and Undercover share 706 section numbers across RA/RB, and all 706 corresponding names are identical, but their **498 matched-number sections with nonzero spatial coordinates do not have matching centre/radius bytes**. The 208 matching triplets are exclusively all-zero placeholders. Never use shared section numbers or names alone to place Undercover sections into Carbon's world.

The candidate priority fields (+0x24) match for every shared ID even across Carbon and Undercover. This is another reminder that metadata conventions can be shared while physical world locations differ.

## Original-stream resource anchors: first 32 MiB only

At every `0x34110` row whose stream offset fell inside the first 32 MiB of that original stream, we sampled the four-byte chunk ID at that **actual offset**. The classification names below come from the public Most Wanted source's `SpeedChunks.hpp`, independently corroborated by the original archive's bytes:

| Chunk ID | Most Wanted reference name |
| --- | --- |
| `0x80134000` | Geometry pack |
| `0x80034100` | Scenery section |
| `0xB3300000` | Texture pack |
| `0x0003B802` | CARP collision-grid island data |
| `0x0003BC00` | Emitter system |

Some section streams begin with zero-valued framing, with a geometry pack appearing within the first 128 bytes; those are classified separately and are not assumed to begin with a standard root.

**455/455 sampled offsets** produced one of these five recognized IDs or the specifically marked initial-framing pattern. By class:
- 298 texture-pack starts
- 131 direct geometry-pack starts
- 11 direct scenery-section starts
- 9 collision-grid island starts (within the Carbon PS2 RA sample)
- 2 emitter-system starts (Undercover PS2/Wii RB)
- 4 geometry packs after short special framing (PC/Wii initial sections)

**Sampling limitation:** The Carbon PC RA first 32 MiB contains only **3** section starts; Carbon PS2 RA contains **141**, Undercover PS2 RA **217**, and Wii RA **22** per game. These figures are strongly affected by platform-specific serialized sizes. The analysis does **not** validate every section boundary across the full streams, and the observed marker alone does not establish a complete chunk's valid extent or its loader behavior.

## Collision-grid descriptor clarification

The top-level `0x0003B800` resource appears once in each inspected RA and RB small bundle. **The Most Wanted source labels this ID `BCHUNK_CARP_WGRID`**, while `0x0003B801` denotes a collision-pack resource and `0x0003B802` denotes grid island data. The label `BCHUNK_UPPLE_UWORLD` is also assigned to `0x0003B800` in that source. These are external reconstructed-source names and do **not** prove an identical Carbon collision ABI.

The Wii vs PS2 `0x3B800` payload often changes due to platform-specific word representation, even when its size is equal. The Undercover PS2 vs Carbon PS2 RB payload of 520 bytes happens to be byte-identical, but **that does not establish a shared city collision map**.

## Implications and next experiment

A viable donor-world converter must preserve **Undercover's own** section centre/radius, per-section names and priority conventions, then rebuild stream-file offsets/lengths and linked visibility/collision structures into the **verified Carbon PC representation**. It cannot assign Undercover bytes to Carbon sections with the same number and assume spatial equivalence.

Next falsifiable test: choose two or more **distinct** Carbon PC scenery section anchors, validate their complete `0x80034100` frames using bounded source offsets and full source fingerprints, then verify the relevant `0x34110` rows and `0x34150` visibility references together. Only then consider a reversible synthetic writer. Keep original game archives unmodified.

References (other-game reconstruction, not Carbon proof):
- [TrackStreamer.hpp](https://github.com/dbalatoni13/nfsmw/blob/main/src/Speed/Indep/Src/World/TrackStreamer.hpp)
- [SpeedChunks.hpp](https://github.com/dbalatoni13/nfsmw/blob/main/src/Speed/Indep/Src/Misc/SpeedChunks.hpp)
- [Scenery.cpp](https://github.com/dbalatoni13/nfsmw/blob/main/src/Speed/Indep/Src/World/Scenery.cpp)
