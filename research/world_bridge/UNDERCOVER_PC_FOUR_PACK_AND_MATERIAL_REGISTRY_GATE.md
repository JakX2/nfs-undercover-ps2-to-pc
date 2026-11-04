# Undercover PS2 four-pack sector assembly and Carbon PC material-registry gap

**Date:** 2026-11-04  
**State:** Owner-original private **offline source / parser** research. **Not installed, engine-loaded or rendered.**

## What changed

The previous experimental `undercover_pc_geometry_bridge.py` validated one Undercover PS2 eSolid occurrence at a time as a newly constructed Carbon-PC-shaped indexed `0x80134000` root. Flattening everything by model identity is lossy because Undercover section 241 repeats one model hash in different geometry packs. This milestone instead retains the actual *pack ordinal → eSolid occurrence ordinal → model identity → local texture-table entry* structure, merging the single-model PC candidates into **four independent PC-shaped indexed geometry roots per original source section**. The combined index is sorted, but each eSolid child retains its original occurrence order and its bytes are unchanged by merging.

New source-only code: `undercover_pc_partition_registry_gate.py`.  
New synthetic-only tests: `test_undercover_pc_partition_registry_gate.py` (73 tests).  
All original texture/model hash values, geometry bytes, stream offsets and scene-space coordinates are kept private and excluded from the repository, report and downloadable ZIP.

The new script validates `0x80134000`/`0x80134001`/`0x80134010` root/index/solid structure with the existing Carbon PC parsers. Each source model still runs through the preceding native-PC-shaped 36-byte vertex/index/UV/material encoder and exact float32 face-corner multiset round-trip. Combining eSolids into one geometry root per source pack does **not** establish a retail Carbon loader-compatible section or world registration. The 144-byte geometry-pack header is still a **zeroed candidate**, and original PS2 eSolid header fields and generated normals are not validated against retail PC engine semantics.

## Full owner-original archive controls

The owner supplied an original Undercover PS2 `TRACKS.zip` and Carbon PC split `TRACKS.z01` ... `TRACKS.zip` archives, examined read-only. Member uncompressed sizes and CRC32 were checked. The Carbon test pool is **only** the original `L5RB.BUN` texture sections 141/142, not every Carbon game texture or global registry. Original archives were SHA-256 checked before/after the audit.

| Source section | Original geometry-pack partition sizes | Source eSolid occurrences | Distinct identities within section | Candidate PC packed-root bytes | Preserved faces |
|---|---|---:|---:|---:|---:|
| Undercover 241 | 114 / 16 / 3 / 2 | 135 | 134 | 2,272,112 | 38,205 |
| Undercover 3401 | 113 / 16 / 2 / 2 | 133 | 133 | 2,266,292 | 38,143 |
| **Total** | **8 independent packs** | **268** | **134 distinct across both sections** | **4,538,404** | **76,348** |

Every one of the **268 original eSolid occurrences** was converted in memory and reassembled into one of eight candidate PC geometry roots, all source-parser accepted in the private audit, with model occurrence order preserved. The 268-model candidate data was **not written to disk** or distributed. The parent/root packing eliminates redundant per-model wrapper headers, hence the combined 4,538,404 bytes differ from the previous 4,588,324-byte sum of 268 individually wrapped roots. Per-model checks retained **109,356 input vertex occurrences**, **313 candidate material meshes**, **6,346 degenerate source geometric faces** and **80 candidate-normal fallbacks**.

The owner-original full-archive audit used **private local mirrors of previously established readers** for PS2 VIF, geometry, and texture metadata to reconstruct all source records. The source-free GitHub Actions tests independently exercise the new code against the **actual checked-in Carbon PC parser/writer modules**. A CI success is **not** an independently repeated full original-archive audit, because no original game data is on GitHub.

## Model identity / scenery link reconciliation

The candidate PS2 scenery-info primary-detail model identity comes from the already studied 72-byte source record's +0x1C slot. Both original source sections contain **130** such scenery-info references.

| Source section | Primary-detail references | Resolved by same section packs | Resolved only by other source section | Missing across both sections |
|---|---:|---:|---:|---:|
| 241 | 130 | 130 | 0 | 0 |
| 3401 | 130 | 129 | 1 | 0 |
| **Total** | **260** | **259** | **1** | **0** |

The single section-3401 model reference missing locally is supplied by section 241. Also, one source model identity is repeated in separate geometry packs within section 241, giving an **ambiguous source occurrence** for one section-241 scene reference if a loader keys only on hash. This requires pack/lifetime semantics, not deletion or arbitrary deduplication. **Static source identity presence does not prove native PC scenery registration, visibility, in-game streaming, or LOD selection.**

## Material-to-PC-texture availability audit

The original Carbon PC sections 141 and 142 provide **110 distinct** texture index identities across **110 records**. The following counts are for texture IDs **actually used by material meshes**, not unused eSolid texture-table entries.

| Scope | Distinct used source material texture IDs | Found among tested Carbon PC RB texture IDs | Missing from tested PC RB texture IDs |
|---|---:|---:|---:|
| Undercover section 241 | 48 | 0 | 48 |
| Undercover section 3401 | 46 | 0 | 46 |
| **Both source sections, deduplicated** | **48** | **0** | **48** |

The sets contain **46 shared identities**, plus two only used by section 241. The 0/48 overlap proves a specific **RB-local identity registration/remapping gap**, *not* absence from every possible global Carbon PC texture pack or cache. The previous private DXT5 existing-slot smoke tests deliberately **retained Carbon's original hash** and changed only pixels; they do not solve the new texture-identity gap required by geometry/material porting.

**Important:** Even if new Undercover hash identities are eventually registered, full resource-table/framing ABI, texture container/header flags, material shader alpha/blending and sampler modes remain separate unverified tasks.

## How to reproduce privately

Run on a machine with the user's own original archives and a checkout of the draft research branch:

```bash
python research/world_bridge/undercover_pc_partition_registry_gate.py \
  --undercover-ps2-zip /private/UndercoverPS2/TRACKS.zip \
  --carbon-pc-volumes /private/CarbonPC/TRACKS.z01 \
                      /private/CarbonPC/TRACKS.z02 \
                      /private/CarbonPC/TRACKS.z03 \
                      /private/CarbonPC/TRACKS.zip
```

This is **read-only**. It prints counts and booleans, never original model/texture IDs, textures, positions, source archive paths, candidate root bytes, or a stage/install command. No game installation is accessed. Full original inputs are required; source-only unit tests need no copyrighted data:

```bash
python -m unittest discover -s research/world_bridge -p 'test_*.py'
```

The owner-source archives are SHA-256 checked before and after the audit. The script rejects missing/symlinked sources, duplicate archive paths, unsupported pack counts, duplicate model identity *inside* a pack, inconsistent native PC root framing, malformed material indexes, or incomplete scene-model reference accounting.

## What this does NOT prove and what comes next

- It does **not** generate an installable `STREAML5RB.BUN`, insert the eight roots into native section tables, edit `L5RB.BUN`, register textures in an engine pack, patch `NFSC.exe`, or touch game files.
- It does **not** establish retail eSolid header ABI, model occurrence disambiguation, resource lifetime/visibility, drivable roads, collisions, AI, traffic, normal correctness, alpha blending, or an in-game playable Undercover world.
- Candidate normals are area-weighted reconstructions; the PS2 ADC winding/UV interpretation still has provisional aspects even though original Carbon PC↔PS2 controls corroborate it.
- The path forward is **texture identity registration/remapping** for the 48 used Undercover IDs in the target area, plus a **private PC stream section/scene registration plan** that accounts for repeated or cross-section scenery model references. No new assets belong in the source-only PR.

Keep PR #33 **draft**, `main` unchanged. Report original-source measurements separately from source-free CI coverage and Windows runtime evidence.
