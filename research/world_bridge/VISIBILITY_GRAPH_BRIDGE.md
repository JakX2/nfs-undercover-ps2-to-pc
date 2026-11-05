# Five-platform visibility-manager and drivable-section reference audit

**2026-11-03. Verified from read-only owner-owned original Carbon PC, Carbon PS2, Carbon Wii, Undercover PS2 and Undercover Wii TRACKS archives.** No extracted game bytes or proprietary files are included. This audit does not prove the Carbon PC runtime will accept an Undercover section.

## Reproduction

Run from repo root:

```sh
python research/world_bridge/visibility_edge_bridge.py \
  --pc-volumes /private/carbon_pc/TRACKS.z01 /private/carbon_pc/TRACKS.z02 /private/carbon_pc/TRACKS.z03 /private/carbon_pc/TRACKS.zip \
  --carbon-ps2-zip /private/carbon_ps2/TRACKS.zip \
  --carbon-wii-volumes /private/carbon_wii/TRACKS.z01 /private/carbon_wii/TRACKS.zip \
  --undercover-ps2-zip /private/undercover_ps2/TRACKS.zip \
  --undercover-wii-zip /private/undercover_wii/TRACKS.zip
python -m unittest discover -s research/world_bridge -p 'test_*.py' -q
```

The tool reads only small `L5RA/L5RB/L2RA/L2RB.BUN` archives and validates each `0x80034150` visibility root and its five fixed-order child chunks: `0x34151, 0x34152, 0x34156, 0x34155, 0x34153`. It decodes two empirical candidate variable-length row formats, does strict in-bounds and duplicate checks, and emits **aggregate JSON only**.

## Exact child-payload equality between original platforms

| Comparison | RA child payloads identical | RB child payloads identical |
| --- | ---: | ---: |
| **Carbon PC vs Carbon Wii** | **5/5** | **5/5** |
| **Carbon PC vs Carbon PS2** | **4/5** | **5/5** |
| Carbon PS2 vs Carbon Wii | 4/5 | 5/5 |
| **Undercover PS2 vs Undercover Wii** | **5/5** | **5/5** |

The sole Carbon PC↔PS2 discrepancy is `0x34153` in the **main RA** visibility manager, not the boundaries, which are byte-identical. Carbon PC's main RA `0x34153` matches Carbon Wii exactly. Both Undercover visibility roots match byte-for-byte across Wii and PS2, not just structurally.

**Do not infer cross-game interchangeability** from same-game platform equality: Carbon vs Undercover's RA visibility contents differ materially, reflecting different world geography and drivable-section links.

## Two validated candidate serialized record formats

- `0x34152`: **48 fixed bytes + NumPoints × 8 bytes**, with section ID as signed 16-bit at +0x08 and NumPoints as unsigned byte at +0x0A. Supports 1..16 points; all ten input chunks decode to exact end-of-payload positions with unique positive section IDs and finite candidate coordinate values.
- `0x34153`: **20 fixed bytes + MaxVisibleCapacity × 2 bytes**, with signed 16-bit section ID at +0x0C, MostVisible byte at +0x0E, MaxVisibleCapacity byte at +0x0F, NumVisible signed 16-bit at +0x10 and NumVisible signed 16-bit references beginning at +0x12. Every input chunk decodes to exact end of payload, with unique positive section IDs and no duplicate or nonpositive references in any single section.

**Important version difference:** The reconstructed Most Wanted 2005 code defines a maximum of 72 visible entries in `DrivableScenerySection`. The original **Undercover** `0x34153` actually reserves up to **84** entries in a record. Hard-coding the older game's 72-entry limit would reject valid Undercover rows. The source-only parser uses a bounded defensive limit of 128 and otherwise follows the *observed actual per-record capacity*.

The same reconstructed Most Wanted source has a different nominal visible boundary image header size; the **48-byte** boundary base reported here is grounded in the original Carbon/Undercover archive frames, **not assumed from that other game's C++ layout**.

## Counts across original files

| Game and track region | Boundaries (`0x34152`) | Drivable sections (`0x34153`) | Validated visibility references | Largest reserved visibility capacity |
| --- | ---: | ---: | ---: | ---: |
| Carbon PC RA | 642 | 572 | 17,778 | 72 |
| Carbon PC RB | 12 | 10 | 40 | 12 |
| Carbon PS2 RA | 642 | 572 | 17,770 | 72 |
| Carbon PS2 RB | 12 | 10 | 40 | 12 |
| Carbon Wii RA | 642 | 572 | 17,778 | 72 |
| Carbon Wii RB | 12 | 10 | 40 | 12 |
| Undercover PS2 RA | 595 | 579 | 17,102 | **84** |
| Undercover PS2 RB | 1 | 1 | 4 | 10 |
| Undercover Wii RA | 595 | 579 | 17,102 | **84** |
| Undercover Wii RB | 1 | 1 | 4 | 10 |

The counts reflect **candidate, bounded serialized relationships**. Some visibility target IDs are not present in a region's `0x34110` streaming table. This is not an automatic error: many target IDs may address alternate LOD classes, section overlays, or files not included in the region. The decoder **does not** reject those targets or silently rewrite them.

## Practical conversion implications

1. **Preserve the Undercover visibility root and its own section IDs/edge lists.** Same section number across Undercover and Carbon can indicate a different real-world location, as proven by previous five-platform spatial comparison.
2. Do **not** substitute Carbon's 72-entry capacity into Undercover's 84-entry donor record. Preserve variable per-record layout and adapt only after actual loader behavior is established.
3. Carbon PC and Carbon Wii's byte-identical visibility chunks are a strong control for format comparison, but the **loader registration and linked model/stream/collision references remain unverified**.
4. Pair a real `0x34153` drivable section with its `0x34152` boundary, corresponding `0x34110` stream row(s), and an authenticated `0x80034100` scenery root. Do this for at least two independent Carbon PC controls before any reversible writer.
5. Keep binary game files private and read-only; publish only original analyzer source, synthetic tests, and aggregate evidence.

**Quality:** 17 new synthetic-only tests pass and the full world-bridge suite passes **135/135** locally. All ten real visibility root comparisons completed. Neither test type establishes an installable playable Undercover map.

Additional source reference for context only: [reconstructed Most Wanted VisibleSection.hpp](https://github.com/dbalatoni13/nfsmw/blob/main/src/Speed/Indep/Src/World/VisibleSection.hpp).
