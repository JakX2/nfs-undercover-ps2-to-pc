# First original-world three-way comparison (2026-11-03)

**Read-only offline audit.** This report describes the owner's supplied Carbon PC split-PKZIP `TRACKS.z01` / `.z02` / `.z03` / `TRACKS.zip` and the Carbon PS2 and Undercover PS2 conventional `TRACKS.zip` archives. No original game content is checked into GitHub. No executable loader behavior, game collision, racing AI, or working port is established by these comparisons.

## Reproduce

The script uses only Python 3 standard-library modules and performs bounded, read-only extraction:

```sh
python research/world_bridge/track_bundle_probe.py \
  --pc-volumes /local/TRACKS.z01 /local/TRACKS.z02 /local/TRACKS.z03 /local/TRACKS.zip \
  --carbon-ps2-zip /local/Carbon_PS2_TRACKS.zip \
  --undercover-ps2-zip /local/Undercover_PS2_TRACKS.zip
python -m unittest discover -s research/world_bridge -p 'test_*.py' -v
```

The PC reader locates compressed data via **disk-relative offsets from the split archive's central directory**, instead of naïvely concatenating volumes and treating them as a normal ZIP. It bounds full small-bundle inflation to 8 MiB, and only reads **4 KiB uncompressed prefixes** of the streaming bundles, so it does not extract the 1.24 GiB world stream. The small bundle scans are exact top-level `id:u32, payload_length:u32` walks, with SHA-256 digests used *only in memory* to compare chunks.

Source ZIP SHA-256s, as inspected locally:
- Carbon PS2: `f20863e42671a87501a38e83c29967ec3a695acac86222f3e41c4af576fec931`
- Undercover PS2: `27f941f284cae4462a73ce09654b710d9ff15d294f8208fb62e653e4151a02bf`
- Carbon PC **final split volume only**: `f5a2ffb460acf17a7d37d4ac5a3e753fbe5dc20348505771798396ab46247895`. This is **not** a fingerprint of the combined original world archive.

## Bundle geometry

| Source | RA bundle bytes | RA top-level chunks | RB bundle bytes | RB top-level chunks |
| --- | ---: | ---: | ---: | ---: |
| Carbon PC `L5` | 1,068,712 | 25 | 179,464 | 21 |
| Carbon PS2 `L5` | 1,049,016 | 24 | 179,736 | 21 |
| Undercover PS2 `L2` | 986,064 | 34 | 128,840 | 20 |

## Exact same-ID, same-occurrence, complete-chunk equality

| Compared source bundles | Shared occurrence keys | Byte-identical complete chunks | Identical **nonempty** chunks | Matching whole-file prefix |
| --- | ---: | ---: | ---: | ---: |
| Carbon PC RA vs Carbon PS2 RA | 24 | 15 | 10 | 67,860 bytes |
| Carbon PC RB vs Carbon PS2 RB | 21 | 18 | 9 | 4,772 bytes |
| Carbon PS2 RA vs Undercover PS2 RA | 24 | 6 | 2 | 12 bytes |
| Carbon PS2 RB vs Undercover PS2 RB | 20 | 15 | 6 | 564 bytes |

The PC and Carbon PS2 RA comparison has large byte-identical nonempty chunks including `0x80034147` (59,520-byte payload), `0x00034146` (7,448), `0x8003b600` (50,732), `0x8003b900` (172,400), and `0x00034158` (two separate, 424 bytes each). These are candidates for *structural comparison*, **not evidence of direct PC compatibility for Undercover's different chunks**.

The Carbon PC and Carbon PS2 RB pair agree on 18/21 chunks, including 9 nonempty. The notable differences in the RA bundles include `0x80034150` (visibility manager), `0x00034110` (track-streaming table), `0x00034108` (scenery overrides), `0x00034109` (barrier groups), and `0x8003410b` (model hierarchy). The labels are **cross-game reference terminology** based on the reconstructed Most Wanted source, not a verified Carbon PC ABI.

## Initial STREAM* prefixes, not the full stream

The first 4 KiB of each streaming bundle contains the `0x80134000` marker within the first 128 bytes.

| Source | RA marker offset | RA declared payload | RB marker offset | RB declared payload |
| --- | ---: | ---: | ---: | ---: |
| Carbon PC | 76 | 452,688 | 0 | 189,832 |
| Carbon PS2 | 0 | 9,608 | 0 | 86,216 |
| Undercover PS2 | 0 | 2,664 | 0 | 26,216 |

These markers alone do **not** establish a full streaming layout or scenery sector count. In particular, the 76-byte Carbon PC RA offset warns against assuming that every world stream begins with a scenery root at byte 0. The value at marker offset +16 is **only an unverified child-ID candidate** and must not be used to select an editor structure.

## Public reference implementation used only as context

The independent Most Wanted 2005 reconstruction `dbalatoni13/nfsmw` uses these same observed IDs for related systems:
- `0x00034110`: streaming section table
- `0x80034150`: visibility manager
- `0x80034147`: track path manager
- `0x00034108`: scenery override infos
- `0x00034109`: scenery barrier groups

Reference files: [SpeedChunks.hpp](https://github.com/dbalatoni13/nfsmw/blob/main/src/Speed/Indep/Src/Misc/SpeedChunks.hpp), [TrackStreamer.cpp](https://github.com/dbalatoni13/nfsmw/blob/main/src/Speed/Indep/Src/World/TrackStreamer.cpp), [Scenery.cpp](https://github.com/dbalatoni13/nfsmw/blob/main/src/Speed/Indep/Src/World/Scenery.cpp). **These are Most Wanted definitions**, not independently recovered Carbon PC runtime structures.

## Next falsifiable milestone

Build a bounded, read-only parser of `0x00034110` table rows in the **paired Carbon PC and Carbon PS2 L5RA bundles**, retaining source-specific size/stride and avoiding a hard-coded Most Wanted stride. Determine whether any source-pinned row fields point to real stream root offsets across **at least two distinct scene roots**, then compare Undercover PS2 L2RA candidates. Reject single-row coincidences, version drift, and ambiguous index interpretations.

This is **world-loader research only**. No proprietary BUN, asset, texture, model or executable bytes are committed; no game file is patched and no gameplay launch claimed.

## Tests

12/12 new synthetic-only unit tests passed in the local probe workspace. The real-archive read-only comparison also completed successfully for all six small bundles and six streaming prefixes.
