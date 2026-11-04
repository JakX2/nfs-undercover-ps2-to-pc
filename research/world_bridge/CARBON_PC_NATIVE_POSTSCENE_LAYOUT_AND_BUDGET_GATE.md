# Carbon PC native RB post-scene frames and conservative Undercover section budget

**Date:** 2026-11-04  
**Scope:** Original owner-provided Need for Speed Carbon PC `L5RB.BUN` / `STREAML5RB.BUN` sections **141/142**, versus original Undercover PS2 `L2RB.BUN` / `STREAML2RB.BUN` sections **241/3401**. **Read-only** offline parsing. No retail game was launched or patched, and no new texture or model identity was registered. Do not commit or distribute original game assets, privately converted resources, archives or per-resource IDs.

## New evidence: Carbon PC's post-scene records are real, structured data

Both selected original Carbon PC streaming sections contain a framed PC texture root (`0xB3300000`), one indexed native PC geometry root (`0x80134000`), a scenery root (`0x80034100`), and a **separate post-scene sequence**. Carbon section 142 also contains an explicit 20-byte *zero-tag, 12-byte zero-payload* frame between geometry and scenery. This inter-root chunk is **not** arbitrary alignment padding.

| Original Carbon PC source | Section 141 | Section 142 |
|---|---:|---:|
| Source section-table row bytes | 8,473,604 | 7,624,644 |
| PC texture root bytes | 4,508,032 | 3,844,224 |
| PC geometry root bytes | 3,958,176 | 3,758,092 |
| PC scenery root bytes | 6,392 | 22,104 |
| Explicit zero-tag intermediate chunk bytes | 0 | 20 |
| PC-specific post-scene sequence bytes | **1,004** | **204** |
| PC scenery info / instance records | 29 / 29 | 103 / 103 |
| `0x372xx` repeated post-scene record groups | **6** | **1** |

The post-scene sequence is **eight zero bytes**, followed by one `0x00037220` 24-byte header, then *N* sets of `0x00037260` prelude (12 bytes for first group, 8 for later groups), `0x00037250` 120-byte payload and `0x00037270` 8-byte end frame. The header has two `0x11111111` words and three matching group-count words. The reader requires the **exact sequence and complete bounds**, and refuses to silently discard unexpected trailing bytes. The 24/12/120/8-byte payloads remain opaque; **do not infer registration semantics, pointer ABI, material meaning or relocation behavior** from the observed IDs alone.

The original Undercover PS2 sections do **not** have the same native PC `0x372xx` suffix. Both instead contain different post-scene data. The scanner validates their ordinary root framing and scenery-info references but deliberately does not reinterpret the PS2 suffix as a compatible PC resource list:

| Original Undercover PS2 source | Section 241 | Section 3401 |
|---|---:|---:|
| Section table row bytes | 3,491,408 | 1,670,512 |
| Original PS2 texture root bytes | 2,447,616 | 630,016 |
| Four PS2 geometry roots combined | 1,012,864 | 1,010,000 |
| PS2 scenery root bytes | **28,664** | **28,664** |
| Different PS2 post-scene suffix bytes | 2,264 | 1,832 |
| Scenery info / instance records | **130 / 136** | **130 / 136** |
| First scenery detail hash slot | Empty in all 130 source info records | Empty in all 130 source info records |

The corresponding original Carbon PC 141/142 scenery has a nonzero first detail slot equal to the nonzero second slot for all 29/103 info records. The older source-only hash-slot promotion control suggests an in-memory candidate transformation, **not** retail Carbon scene-loader acceptance. These sources do not establish collision, roads, AI, LOD selection or rendering.

## Conservative byte capacity, not insertion permission

Combining *previously measured* private offline outputs, without re-running the original full geometry/DXT5 encoders in this gate:

- Four PC-shaped donor geometry roots, source 241: **2,272,112 bytes**; source 3401: **2,266,292 bytes**.
- Complete 46-image lower-resolution new-ID DXT5 candidate root: **1,176,688 bytes**. This is a deliberate lower-resolution policy used for both source sections in this **size budget**, not a high-resolution 46/46 audit.
- One source-scene root: **28,664 bytes**.
- Reserve the original Carbon PC post-scene suffix **verbatim in the arithmetic** (1,004/204 bytes). Its opaque payload may not actually be safely transplanted or relocated.
- Reserve a conservative **75 bytes** for up to five 16-byte alignment gaps between one texture root, four geometry roots and the scenery root.

| Hypothetical pairing | Max candidate bytes including original PC suffix and alignment | Existing PC row bytes | Nominal headroom |
|---|---:|---:|---:|
| Undercover 241 → Carbon 141 | **3,478,543** | 8,473,604 | **4,995,061** |
| Undercover 3401 → Carbon 142 | **3,471,923** | 7,624,644 | **4,152,721** |

Both candidate resource groups **fit the nominal size limits** of existing Carbon stream rows. That is only a **necessary byte-capacity condition**. A retail engine could reject the candidate for multiple independent reasons: native post-scene controls, index registration and pointer relocation, the unexplained 20-byte inter-root control chunk, original scene fields, section-to-section lifetime, source model-hash duplication, shader/sampler ABI, normals, or collision. Also **1,950 of 76,348 candidate triangle occurrences still reference two unresolved original Undercover image identities**, as established in the earlier material binding gate. Neither source files nor native control blocks were rewritten or relocated in this audit.

## Reproducibility

This module uses **Python standard library only**. Given the owner's private *extracted, CRC-checked* Carbon PC BUN/STREAM pair and the original Undercover PS2 `TRACKS.zip` archive, run:

```powershell
python carbon_pc_native_postscene_layout_gate.py `
  --carbon-bun "C:\PrivateBackup\L5RB.BUN" `
  --carbon-stream "C:\PrivateBackup\STREAML5RB.BUN" `
  --undercover-ps2-zip "C:\PrivateBackup\UndercoverPS2_TRACKS.zip"
```

The tool reads both original Carbon PC section table rows, reads the two source Undercover archive members with ZIP CRC checking, verifies bounded 92-byte section-table rows and scene-info indexes, counts the exact original section root/postscene frames, and prints **aggregate counts and conservative budgets**. It does not print source paths, resource IDs/hashes, vertex bytes, original texture data or positions. It has **no game-file writing path**. Running it on a trusted original extraction is an **offline static audit**, not a test of Windows Carbon's loader. The source-only synthetic adversarial suite exercises malformed frames, unexpected postludes, dangling scenery references, invalid row tables, aliasing and private file-input safety.

**Observed private source result:** original split Carbon PC ZIP members `L5RB.BUN` (179,464 bytes) and `STREAML5RB.BUN` (82,837,504 bytes) were verified for complete size and ZIP CRC during local extraction. The Undercover PS2 original RB ZIP members were read with Python's CRC-verifying `zipfile` reader. Both Carbon and both Undercover sections passed the new static parser. This work must not be described as in-game world-port progress beyond proving *structural space and a new native-control blocker*.

## Next gate

Establish the purpose, resource dependencies and relocation semantics of the original PC `0x37220/0x37260/0x37250/0x37270` records by comparing more original Carbon sections and source-matched console versions. Only then attempt a **private, reversible** self-contained stream-section build. Native texture-ID registration and the two missing source images remain separate unresolved blockers. Keep PR #33 **draft**, base `main` untouched.
