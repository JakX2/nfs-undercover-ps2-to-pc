# Visibility → streaming → validated scenery cross-reference

**2026-11-03. Read-only audit of owner-provided Carbon PC, Carbon PS2, Carbon Wii, Undercover PS2 and Undercover Wii archives.** This is **not** proof of a working Undercover world in Carbon PC. No original game assets, extracted chunks, texture/model payloads or executable patches are committed.

## How to reproduce

Run from repo root with local source archives (all paths are examples; the owner keeps the game files private):

```sh
python research/world_bridge/visibility_stream_join.py \
  --pc-volumes /private/carbon_pc/TRACKS.z01 /private/carbon_pc/TRACKS.z02 /private/carbon_pc/TRACKS.z03 /private/carbon_pc/TRACKS.zip \
  --carbon-ps2-zip /private/carbon_ps2/TRACKS.zip \
  --carbon-wii-volumes /private/carbon_wii/TRACKS.z01 /private/carbon_wii/TRACKS.zip \
  --undercover-ps2-zip /private/undercover_ps2/TRACKS.zip \
  --undercover-wii-zip /private/undercover_wii/TRACKS.zip
python -m unittest discover -s research/world_bridge -p 'test_*.py' -q
```

The checker combines independently validated candidate records: 92-byte `0x34110` stream-section rows, variable `0x34152` visibility boundaries, variable `0x34153` drivable reference lists, and the previously validated 47 **RB** scenery roots associated with stream rows. A scene root not appearing as a `0x34153` reference is **not** treated as corruption.

**Local reproduction:** 155/155 synthetic world-bridge tests pass. The five-source original-archive check completed and reproduced the previously captured comparison exactly. The tool prints numeric-identifier aggregate statistics; it does not export the original payloads or attempt a writer.

## Coverage of actual RA (main-area) visibility graphs

| Source | Streaming rows | Boundary rows | Drivable rows | Ref occurrences | Unique target IDs | Targets in this RA stream | Targets outside this RA stream |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Carbon PC | 962 | 642 | 572 | 17,778 | 1,442 | 959 | 483 |
| Carbon PS2 | 1,191 | 642 | 572 | 17,770 | 1,442 | 960 | 482 |
| Carbon Wii | 1,194 | 642 | 572 | 17,778 | 1,442 | 963 | 479 |
| Undercover PS2 | 2,041 | 595 | 579 | 17,102 | 1,337 | 833 | 504 |
| Undercover Wii | 2,067 | 595 | 579 | 17,102 | 1,337 | 859 | 478 |

The **Carbon PC↔Wii 572 drivable rows are identical**. Carbon PC vs PS2 differs in only four rows, which insert exactly two existing target IDs each and increase per-row capacity/MostVisible accordingly. The total target-ID universe stays the same:

| Drivable section | PC count / PS2 count | Additional PC/Wii target IDs | PC capacity / PS2 capacity |
| --- | --- | --- | --- |
| 315 | 59 / 57 | 130, 170 | 66 / 64 |
| 1008 | 52 / 50 | 1005, 1045 | 58 / 56 |
| 1009 | 45 / 43 | 1005, 1045 | 52 / 50 |
| 1415 | 48 / 46 | 1005, 1045 | 54 / 52 |

All four PS2 reference lists occur as **order-preserving subsequences** of the corresponding PC/Wii lists. This is a precise packaging/visibility difference, not evidence that only these four sections need modification to substitute an entirely new map.

Undercover Wii vs Undercover PS2: all **579/579** RA drivable visibility rows have identical parsed reference/capacity/MostVisible values, and the **entire target-ID set is identical**, even though the Wii `0x34110` table has 26 extra stream section IDs. All **26 extra Wii streaming section IDs appear somewhere in the visibility target universe**. This means an ID's presence in visibility data does **not** establish that a corresponding section is in the local PS2 stream.

## Cross-referencing real RB scenery roots

The prior bounded RB parser structurally validated **47** scenery roots across the five secondary-area streams. Every one is associated with a parent `0x34110` stream section, but not all appear in the regular drivable visibility target list.

| Original RB stream | Validated roots | Root section IDs in visibility targets | Valid roots without regular visibility target |
| --- | ---: | ---: | --- |
| Carbon PC | 13 | 12 | 1 (`Z0`, ID 2600) |
| Carbon PS2 | 14 | 12 | 2 (IDs 1335, 2600) |
| Carbon Wii | 14 | 12 | 2 (IDs 1335, 2600) |
| Undercover PS2 | 3 | 1 | 2 (IDs 2600, 3401) |
| Undercover Wii | 3 | 1 | 2 (IDs 2600, 3401) |

The `Z0` scene, section 2600, is **not** a regular `0x34153` target in any of these five RB archives. This is an observed counterexample to requiring every valid scenery section to appear in the drivable visibility graph. Such sections might have special loading, LOD, or other graph relationships; **those mechanisms are not proven yet**.

All 47 validated RB roots have parent stream rows. The reported 47 are supported finds under the scanner's known six-child structure and size bound, **not** a guaranteed exhaustive census of every possible scenery encoding.

## Safe conversion constraints established so far

1. Keep Undercover's own section IDs, centre/radius values, visibility reference order and per-row capacities. Identical numeric IDs in Carbon and Undercover may represent different physical world locations.
2. Do **not** reject a valid scene because it is absent from the drivable visibility target list. Investigate special or alternative loading paths.
3. Do **not** force references absent from the **current region's** stream table to zero; some may be resolved by other stream types/LODs/overlays. This audit cannot distinguish those cases.
4. Rebuild donor stream offsets, lengths and platform-specific resource packages only after validating Carbon PC's target layout and at least two matched scenery/model controls.
5. This audit is **numeric ID cross-reference evidence**. It does not establish Carbon PC runtime visibility-registration ABI, full geometry decoding, collision, AI traffic, texture/material resolution or a playable Tri-City Bay.

## Next falsifiable test

Use at least two independently verified **non-`Z0`** Carbon PC RB scenery roots to follow:

`0x34110 stream row → contained 0x80034100 scene root → 0x34103 instance → 0x34102 model hash → model resource`

Then compare the visibility targets and source model presence in the Carbon PC `STREAM*.BUN`/geometry-pack resources. Use the Carbon PC/Carbon PS2 identical control sections before evaluating any Undercover donor section. Keep original data read-only and publish only new source/test code.
