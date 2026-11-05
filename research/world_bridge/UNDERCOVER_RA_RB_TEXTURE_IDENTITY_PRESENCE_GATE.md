# Undercover PS2 RA/RB track image identity coverage gate

**Status:** Source-backed private Undercover PS2 TRACKS archive audit. **No runtime asset registration or rendering is established.** All original game data, texture IDs/names, raw pixels, proprietary offset lists and geometry bytes stay private.

## Why this gate exists

The four-partition PS2→PC geometry audit found **48 distinct source texture identities actually used by original Undercover RB scenery materials**, but only **46** of those identities in the original Undercover RB texture pack indexes. Two IDs were missing from both original RB image indexes, and the prior audit could not establish whether they were available elsewhere in Undercover's own resource system. This gate checks **the original RA stream** independently before deciding whether those two source-side references require outside-TRACKS lookup or an explicit, documented fallback.

## Original source controls

Only owner-supplied original Undercover PS2 `TRACKS.zip` was read. The ZIP stream-member reads are length/CRC32 checked. The original archive size/mtime/SHA-256 was checked before and after. No original or modified game asset is written, and no installation is modified.

| Source check | Result |
|---|---:|
| Original Undercover `STREAML2RA.BUN` uncompressed bytes | **231,735,296** |
| Original RA `0x34110` 92-byte section rows | **2,041** |
| RA section rows passing nonoverlap, 2 KiB alignment and bounds | **2,041/2,041** |
| Original RA root-marker candidates investigated | **2,057** |
| Complete PS2 texture-root frames independently accepted | **1,661** |
| Accepted roots wholly inside declared RA stream rows | **1,521** |
| Accepted roots outside declared RA stream row intervals | **140** |
| Distinct indexed PS2 image identities in all accepted RA roots | **1,361** |
| Distinct indexed identities within declared RA rows | **1,361** |
| Distinct used material identities in original RB scenery | **48** |
| Distinct original Undercover RB image identities | **46** |
| Used material IDs absent from both RB image indexes | **2** |
| Those two IDs found in declared RA texture indexes | **0** |
| Those two IDs found only in RA roots outside declared rows | **0** |
| IDs still unresolved in validated RA and RB image indexes | **2** |
| `LOC2DYNTEX.BIN` stored member length | **0 bytes** |
| Original archive changed by audit | **No** |

The RA texture-root validator checks nested `0xB3300000`/`0xB3310000`/`0xB3320000` framing, the sorted `0x33310002` identity index, all `0x33310004` variable-length texture metadata, all 84-byte PS2 platform records and correctly bounded 128-byte-aligned image/palette spans. Its implementation **reuses the actual checked-in** `texture_metadata_pixel_bridge.parse_pack` and `texture_pixel_base_alignment.aligned_pixel_array` helpers. The source-only audit's 2,057 markers are not counted as images unless those full validations succeed.

A fully framed texture root in a gap **is not automatically a registered streamed section**. The 140 such original RA root frames are separately counted rather than merged into section-table registration claims. Their indexed image identities are still checked against the two unresolved material IDs, with zero hits.

### Model-material usage of the unresolved references

A separate private source-material strip audit found that the two absent identities are actually used by original PS2 strip geometry, not merely unused eSolid table entries. In **each** of source sections 241 and 3401, one unresolved material has **23 strip references / 374 candidate faces across 4 eSolids**, and the other has **45 strip references / 601 candidate faces across 16 eSolids**. Combined across both source sections this is **1,950 source face occurrences** out of **76,348** reconstructed triangles. Because the sections repeat many models, that total must **not** be interpreted as 1,950 independent visible in-game faces. The supplementary usage numbers came from a private direct-source strip-table mirror, not from an independently running Carbon renderer.

## New source-only implementation

- `undercover_ra_texture_presence_gate.py` accepts only an owner-supplied original ZIP. It obtains the two RB **used** material identity sets through the existing pack- and strip-validated `source_partition_roots` and `parse_ps2_mesh` readers. It then reads the two original RB image indexes and scans original RA using the **full existing PS2 texture parser**.
- The result is aggregate-only JSON: counts, separately classified declared-section versus unassigned RA roots and an explicit unresolved-identity count. It cannot print or serialize original identity values, names or pixel bytes.
- This tool checks **index presence**, not image sampling correctness, texture shader semantics, source material alpha, Carbon material-table registration, texture pack creation, engine resource lifetime or runtime rendering.
- `test_undercover_ra_texture_presence_gate.py` has **63 new synthetic-only tests** covering complete PS2 image fixtures, stream-table invariants, disjoint section membership, invalid markers, missing source images, cross-section deduplication, used-material strip index semantics and ZIP source immutability.

Private original-source verification ran the new archive/RA scanner with exact byte-for-byte local copies of the checked-in texture metadata and pixel-alignment parsers; the older established RB eSolid/material decoding was supplied through a private **local mirror**, and its output counts independently agreed with the previously completed owner-original four-partition audit. Original assets are deliberately absent from CI. The GitHub source-only tests verify the new program against the actual repository modules, but do not reproduce the original-source audit or demonstrate game compatibility.

## Reproduce on the owner's machine

From the repository research branch with the owner's original Undercover PS2 TRACKS archive available locally:

```bash
python research/world_bridge/undercover_ra_texture_presence_gate.py \
  --undercover-ps2-zip /private/UndercoverPS2/TRACKS.zip
```

This is read-only; the output contains no private file path, model hash, texture hash or image data. Run the synthetic tests independently:

```bash
python -m unittest discover -s research/world_bridge -p 'test_*.py'
```

## What this does not establish

**Neither unresolved identity occurs in a fully validated indexed PS2 texture root in the supplied Undercover RA or RB track streams.** This is a narrower conclusion than "those textures do not exist in the game." Other original-game archives, global texture resource tables, dynamically resolved material semantics and engine-created resources were **not** examined by this gate. The zero-byte `LOC2DYNTEX.BIN` entry is not evidence that all dynamic textures are absent from the game.

The original Carbon PC RB texture pool still has **0/48 identity overlap** with these source material IDs. The intended path forward is to locate any external original resources or establish whether the two values have special material semantics, then design an explicit registration/remap plan for all 48 material identities. Original model/texture identifiers and game data must **not** be committed or published. Keep PR #33 in **draft**; do not merge it and do not claim a playable Undercover world.
