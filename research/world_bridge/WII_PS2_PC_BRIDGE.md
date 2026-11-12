# Wii data received: controlled PS2/Wii/Carbon PC world and gameplay comparison

**Date:** 2026-11-03. Read-only inspection of owner-supplied originals. No original asset bytes, full name inventories, executable dumps, extracted GAMEPLAY files or game archives are committed. No in-game result has been demonstrated.

## Input provenance

The owner's Drive now contains both **UC WII** and **CARBON WII**. Undercover Wii `TRACKS.zip` is an ordinary single-volume ZIP. Carbon Wii `TRACKS.z01` plus `TRACKS.zip` is a two-volume PKZIP archive. Both `GLOBAL.7z` archives were readable using a local libarchive reader, and their `GLOBAL/GAMEPLAY.BIN` members were extracted **privately** for structural comparison.

| Source | Verified SHA-256 |
| --- | --- |
| UC Wii `TRACKS.zip` | `10132c2371196e77c63e76a2c36ec26d1065739f275086c7bade2ab02bfad1a4` |
| Carbon Wii `TRACKS.z01` | `3ea6ef19f71dd76b18f89a3bf48709585ab32fc35b23d0b6bc1254b2e786d15b` |
| Carbon Wii final `TRACKS.zip` | `e51d753c49124c6abe527a7b1d686dffdeb3ccb2b773740caa2d4c3d9e9c7eb8` |
| UC Wii `GLOBAL.7z` | `d2ed794059a80d38e72abe6b3ead1b2a3f3a9d7d1bcc5b903e7872db527c8421` |
| Carbon Wii `GLOBAL.7z` | `196730c26500c03de5a55358d02626d3a1d60d7fd86f112f58bbba37647f4ceb` |
| UC Wii extracted `GAMEPLAY.BIN` | `2bc52b0aaf25d4f5a821bc2998fe6ff66b62720ccbf902b3b7ca9883e2007645` |
| Carbon Wii extracted `GAMEPLAY.BIN` | `ace3691c92201bbe81e936ac7489bbf4772ee9e8a453df3690f47c691af20eae` |

## Direct track-bundle comparisons

Each `.BUN` bundle was walked as complete top-level `<little-endian chunk ID u32, payload size u32, payload>` records. Comparisons require identical chunk ID and occurrence plus SHA-256 equality over the **entire chunk including the header**.

| Wii vs matching PS2 source | Wii/PS2 top-level chunks | Exact complete chunks | Exact **nonempty** chunks |
| --- | ---: | ---: | ---: |
| UC `L2RA.BUN` | 34 / 34 | **30** | **25** |
| UC `L2RB.BUN` | 20 / 20 | **18** | **8** |
| Carbon `L5RA.BUN` | 25 / 24 | **15** | **11** |
| Carbon `L5RB.BUN` | 21 / 21 | **19** | **9** |

Both Undercover Wii and PS2 `TROUGHBOUNDARY.BIN` resources match byte-for-byte for the RA (356,100 bytes) and RB (948 bytes) sections.

Notable source differences: Undercover RA changes are confined to complete chunks `0x34110` (size differs), `0x34113` (PS2 nonempty versus Wii empty), `0x3414D` (size differs), and `0x3B800` (equal size but different bytes). Undercover RB changes are **only** `0x34110` and `0x3B800`, both equal-size but different bytes.

Both Wii and PS2 streaming bundles contain `0x80134000` within the first 128 uncompressed bytes, but **Wii RA may start with additional framing**, and streaming sizes differ. No full streaming graph or geometry is decoded yet.

## Gameplay VPAK endian bridge

The original Wii `GAMEPLAY.BIN` contains the same *outer little-endian* `VPAK` index layout as PS2/PC. Wii *record interior* chunks instead encode reversed ASCII tags (`ErtS` is `StrE`, `NpxE` is `ExpN`) and **big-endian** lengths and 32-bit table words. The NrtP row's middle field is **two packed 16-bit fields**, whose word-half order must also be normalized; treating it as one scalar 32-bit enum falsely reports reference mismatches.

A new source-only script `wii_gameplay_bridge.py` verifies the six chunks in every record, normalizes numeric `NpxE` entries and `NrtP` triples and compares each same-index record's index, initial ErtS string bytes, resource-name tail, export entries and references.

| Normalized field match | UC Wii / UC PS2 | Carbon Wii / Carbon PC backup | Carbon Wii / Carbon PS2 |
| --- | ---: | ---: | ---: |
| Outer record indexes | **197/197** | **190/190** | 74/190 |
| Initial string pools | **197/197** | **190/190** | 186/190 |
| NpeD resource-name tails | **197/197** | **190/190** | **190/190** |
| Entire NpxE entry tables | **197/197** | **190/190** | 188/190 |
| Entire NrtP reference tables | **197/197** | **190/190** | 182/190 |

- UC Wii vs UC PS2: all **4,048** normalized NpxE entries match numerically.
- Carbon Wii vs Carbon PC backup: all **5,726** normalized NpxE entries match numerically.
- Carbon Wii vs Carbon PS2: NpxE differs only at record indexes **74,118**. ErtS initial pools differ at **74,118,179,180**. NrtP differs at **74,118,173,174,178,179,180,182**.
- These Carbon Wii vs PS2 exceptions match the existing Carbon PC backup vs Carbon PS2 exception set, substantially strengthening the Wii-as-bridge hypothesis.
- **Important:** Carbon PC `GAMEPLAY.BAK` is a useful reference baseline but is not independently certified as pristine retail. Equality of normalized tables does **not** mean the opaque `NtaD` serialized payload is field-for-field interchangeable; there can be platform-endian fields, pointers and alignment differences.

### Reproduce without committing originals

Extract the Wii `GLOBAL/GAMEPLAY.BIN` files **privately** from each corresponding Wii `GLOBAL.7z` and run, from repository root:

```sh
python research/world_bridge/wii_gameplay_bridge.py \
  /private/uc_wii/GAMEPLAY.BIN /private/carbon_wii/GAMEPLAY.BIN \
  /private/UC_PS2_GLOBAL.zip /private/Carbon_PS2_GLOBAL.zip \
  /private/Carbon_PC_GLOBAL.zip
python -m unittest discover -s research/world_bridge -p 'test_wii_gameplay_bridge.py' -v
```

The script prints comparison aggregates and differing record indices only. **12/12 synthetic-only unit tests passed locally** and the entire five-source audit completed successfully.

## Practical port direction

1. Use Undercover PS2 and Wii to identify *platform-stable world metadata*; avoid reimplementing fields already identical in the source variants.
2. Use Carbon Wii and Carbon PC backup's normalized gameplay/reference identity to establish mappings between same-name resources on console and PC.
3. Investigate `0x34110` streaming section indexes and `0x3B800` collision-related records as the **specific Wii/PS2 differences**, rather than treating the entire world representation as incompatible.
4. Decode Carbon PC world's loader/index semantics against multiple authenticated scene roots before attempting any changes to its original files.

**This is evidence of shared structures, not a completed port, PC runtime loader proof, or working Undercover collision in Carbon PC.** No original copyrighted assets or modified game files were published.
