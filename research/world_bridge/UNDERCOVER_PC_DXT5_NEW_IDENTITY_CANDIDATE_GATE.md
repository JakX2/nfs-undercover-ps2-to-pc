# Original Undercover PS2 image identities → Carbon PC-shaped DXT5 pack candidate

**Date:** 2026-11-04  
**Status:** SOURCE/CPU OFFLINE CANDIDATE, **NOT** CARBON PC RUNTIME REGISTRATION

## Problem

The original Undercover RB scenery materials reference **48** distinct texture
identities. The source-owner's `TRACKS/L2RB.BUN` and `STREAML2RB.BUN` contain
**46** source texture identities, shared between PS2 source sections **241**
and **3401**. A previously completed original-source RA/RB search found no
validated image-index entry for the remaining **2** within this TRACKS archive.
The Carbon PC RB image indexes likewise have **no shared identities** with the
48 used Undercover material identities, based on an earlier separate audit.
Do not invent either missing source image or assume that a Carbon PC texture
can be registered simply by creating a chunk with a matching hash.

## This milestone

`undercover_pc_dxt5_new_identity_candidate.py` builds an **in-memory**,
**new-identity** DXT5 texture root with the following strict properties:

* Maintains original Undercover texture IDs, validated ASCII names and dimensions,
  ordering the PC index by identity rather than importing PS2 image spans.
* Converts each original decoded PS2 indexed 4bpp/8bpp source to DXT5 alpha +
  color, and constructs a configurable, explicit mip chain (four mips for the
  present original-owner controls).
* Writes structurally consistent `0xB3300000`, `0xB3310000`, sorted
  `0x33310002`, variable-length `0x33310004`, `0x33310005` DXT5 FOURCC,
  and aligned `0x33320002` image payloads **in process memory only**.
* Uses the existing PC `parse_pack`, `aligned_pixel_array`, `_source_image_span`
  and `decode_dxt_base` to check **every** identity, name, image span, dimension,
  mip equation and decoded base-level RGBA length after construction.
* Counts missing source material identities explicitly. Reports contain only
  aggregate counts, not private image hashes, source paths, names, pixels,
  original game bytes or exact source placement offsets.
* Public CLI is **read-only**: it performs original ZIP member CRC checks,
  source table validation and archive SHA-256 before/after checks, without any
  file-write or installation command. A caller can deliberately use the returned
  private bytes in memory for further research, but must not publish them.

This is **not** a genuine Carbon PC loader/registration writer. The candidate
124-byte descriptor header, 24-byte pixel header, padding framing and tile-mode
choice contain **unverified synthetic values**. A PC parser accepting the
serialized byte envelopes does not prove the retail Carbon resource manager
will accept them. Never use this as a game patch.

## Private original-owner archive results

All original data was loaded directly from the owner's original Undercover PS2
`TRACKS.zip`, using CRC-checked ZIP members and bounded section-table rows.
The original archive was unchanged, and generated candidate bytes were not
written out, shared or committed.

| Measurement | Undercover PS2 3401 | Undercover PS2 241 |
|---|---:|---:|
| Original indexed image records | 46 | 46 |
| Original 4bpp / 8bpp source split | 34 / 12 | 34 / 12 overall |
| Source images converted in this run | **46/46** | **8/46 (bounded partial)** |
| Generated PC-shaped DXT5 root bytes | **1,176,688** | **1,100,672** |
| DXT5 image payload bytes | **1,169,648** | **1,098,880** |
| DXT5 mip levels per converted image | 4 | 4 |
| Original hashes/names/image spans pass PC parser readback | Yes | Yes |
| Base image DXT5 decodes pass | 46 | 8 |
| Proven retail texture registration | **No** | **No** |

The high-resolution test deliberately stopped after eight sorted source
identities. Its remaining 38 were **not** exercised by this specific candidate
pack builder; a previous separate high-resolution DXT5 codec audit covered
all 46 base textures but did not form this new-identity pack.

**Material coverage, source-local:** original geometry-strip references identify
**48 used IDs** (section 241 uses 48, section 3401 uses 46). Both image packs
have **the same 46 IDs**. Thus **46/48** used IDs have a PS2 RB image record
and **2/48** remain unrepresented in this candidate. The 46-image pack is
therefore explicitly **incomplete for all Undercover material references**.

**Carbon coverage:** this milestone did not independently reload and compare
Carbon PC's original registered indexes. The known **0/48** Carbon-RB overlap
is a prior independent source result, not a new registration test.

## Tests and limitations

The source-free regression module `test_undercover_pc_dxt5_new_identity_candidate.py`
adds **43 tests**, including metadata/index sorting, duplicate and malformed
hash rejection, image span/mip equation verification, RGB/alpha BC3 decode,
unknown/empty Carbon index distinctions, missing-material coverage, explicit
partial batches, deterministic output, and no runtime-claim/report leakage.
The local focused run together with the existing DXT5, PS2 decoder, and
synthetic PC pack tests passes **98/98**. Clean-checkout GitHub CI must be
checked independently once the new files are committed.

Remaining independent gates: recover or explain the **two** unresolved original
material IDs in additional original game archives or material semantics;
establish a Carbon PC compatible *registered* texture pack with native header
fields, alias handling and loader acceptance; validate actual material
shaders/blending and game rendering; integrate geometry packs with scene and
stream registrations, collision and gameplay. **No live PC game test or
playable Undercover world is established.**

## Reproduction (owner-supplied original archive required)

```sh
python research/world_bridge/undercover_pc_dxt5_new_identity_candidate.py \
  --undercover-ps2-tracks-zip /PRIVATE/OWNER/TRACKS.zip \
  --source-section 3401 --mip-levels 4
```

For an intentionally partial higher-resolution control:

```sh
python research/world_bridge/undercover_pc_dxt5_new_identity_candidate.py \
  --undercover-ps2-tracks-zip /PRIVATE/OWNER/TRACKS.zip \
  --source-section 241 --mip-levels 4 --max-textures 8
```

Do not commit, attach, upload or distribute source-owner originals, generated
private texture roots, material hash lists or decoded pixels.
