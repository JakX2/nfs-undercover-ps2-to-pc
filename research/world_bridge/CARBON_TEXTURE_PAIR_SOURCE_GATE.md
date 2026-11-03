# Carbon PC↔PS2: original-archive texture-pair hypothesis gate

**2026-11-03. Source-only draft PR research. No original game pixels or hash/name inventories are committed.**

## Purpose and hard boundary

The existing six-pack `texture_metadata_pixel_bridge.py` validates indexed PS2/PC image spans, palettes, metadata and mip budgets; the previous experimental `ps2_texture_layout_candidates.py` and `pc_dxt_reference_decode.py` can decode *explicit hypotheses* on caller-owned bytes. Neither establishes the correct Undercover PS2 swizzle/CLUT interpretation.

This milestone adds **a falsifiable same-hash Carbon PC/PS2 image comparison** and **read-only source archive streaming**. It is a scoring tool, **not a verified PS2→PC texture decoder**, no automatic selection, no game texture pack writer, and no runtime game loader test.

## New modules

- `texture_visual_pair_gate.py`: given validated original Carbon PC and Carbon PS2 **same-section** texture packs (`0xB3300000` roots), parse both with the existing metadata parser; match by source hash; reject same-hash entries when ASCII names or candidate texture-mode flags disagree; isolate each record's **base mip** from the validated image span and its private PS2 palette. Decode native DXT1/3/5 base levels in memory and compare against separately specified PSMT4/PSMT8 index-layout / palette candidates. Return only counts and mean absolute color/alpha differences.
- `texture_original_archive_pair_audit.py`: consumes locally available original Carbon PC split `TRACKS.z01`/`.z02`/`.z03`/`.zip` **in volume order** and Carbon PS2 regular `TRACKS.zip`. It parses bounded `TRACKS/L5RB.BUN` `0x34110` rows and targets matching sections `141` and `142` from `TRACKS/STREAML5RB.BUN`. ZIP stream members are **fully** decompressed in bounded chunks for CRC and byte-count verification, while only the two selected sections remain resident in memory. No extracted member or texture is written to disk.

The split archive branch reuses existing `track_bundle_probe.SplitZip` metadata/header validation and adds CRC-checked **chunked streaming** rather than calling its prefix mode with large uncompressed prefixes. The regular ZIP branch uses Python `zipfile`, verifies all members read, and relies on its CRC enforcement. Both reject duplicate section IDs, unsafe/overlapping section ranges and oversized inputs.

## Comparisons and protections

Each sampled source identity can yield up to **24** candidate combinations for PSMT8 (`linear`, `gs_vram`, `ct32_transfer` × `linear`/`csm1` CLUT × `raw`/`double` alpha × `rgba`/`bgra` channels), or **12** for PSMT4 (its 16-entry CLUT needs no CSM1 bank permutation). Candidate failure is counted instead of replacing it with another layout. Nearest-neighbor scoring uses the PS2 resolution grid; it retains RGB MAE and alpha MAE **separately**. Result ordering must never be treated as a winning decoder without inspection and independent controls.

The tool samples at most 12 matching textures per source section (default 8), rotating among index bit depths and identical/different PC/PS2 dimensions. It counts spatially uniform PC reference textures as weak evidence. It also reports an aggregate histogram of the **unverified** PS2 platform-record byte at `+0x17`, without presuming that byte determines storage layout. No individual hash, name, pixel value, offset or image file appears in the JSON report.

**Limitations:** Only base mip levels are scored. Mipmap sublevel offsets/padding, TFX/TCC/sampler modes, UV reflections/rotation, DXT color loss, resampling differences, platform-specific artwork and GPU alpha semantics can affect spatial or color agreement. A low RGB error is a candidate observation, not a proof of source GPU semantics. Samples without sufficient visual variation are explicitly marked. The reader does not download the user's Drive files automatically; originals must exist locally for an actual archive-backed audit.

## Synthetic-only verification

The new tests construct source-free standalone texture packs, per-section `0x34110` tables, regular PS2 ZIP archives, and **valid synthetic two-disk split PKZIP archives** with central directory on the last disk. They exercise successful RGB equality for a deliberately linear palette, alternate 4-bit and 8-bit images, wrong channel order, unsupported layout failures, section CRC mismatches, incomplete intervals, duplicate/overlapping entries, identity collisions, and privacy of aggregate output. A complete **synthetic** PC split-ZIP versus PS2 regular-ZIP archive run returns a two-section candidate report.

**24/24 new regression tests passed** (13 candidate comparison + 11 archive tests). **62/62 texture-decoder-related synthetic tests passed together** in the local sandbox. Source files in the draft PR's previous milestone were used for integration; no original CARBON or UNDERCOVER ZIP archives were present in this sandbox's local filesystem, so **no real-texture scoring has yet been performed**. No GitHub Actions result is claimed.

## Run with original local archives

From the repository root, with the original archives downloaded locally:

```sh
python -m unittest discover -s research/world_bridge \
  -p 'test_texture_visual_pair_gate.py' -v
python -m unittest discover -s research/world_bridge \
  -p 'test_texture_original_archive_pair_audit.py' -v

python research/world_bridge/texture_original_archive_pair_audit.py \
  --pc-volumes /private/carbon_pc/TRACKS.z01 \
               /private/carbon_pc/TRACKS.z02 \
               /private/carbon_pc/TRACKS.z03 \
               /private/carbon_pc/TRACKS.zip \
  --carbon-ps2-zip /private/carbon_ps2/TRACKS.zip \
  --max-pairs 8
```

The only output is aggregate JSON: each same-ID section's source-pair count, sampled provisional flag distribution, spatially informative sample count, per-hypothesis supported/failing pair counts, and RGB/alpha error means. The verdict is always `UNVERIFIED` until independent original-source image analysis and verified runtime use exist.

## Next source-backed falsification

1. Run the archival CLI on original **Carbon PC and PS2** section 141 and 142 packs. Confirm full stream CRCs, expected shared identities and adequate informative samples.
2. Inspect the per-section candidate scores for consistency **across independent textures and both sections**, including the `+0x17` provisional flag distribution. Use additional private visual controls when candidates tie or disfavor the expected source-byte layout.
3. Only after robust same-hash evidence, run the same explicit decoding candidate on the **section-aware Undercover PS2 241/3401** versions; preserve source-section and mip provenance and never collapse same-hash variants.
4. Keep actual native-PC texture pack serialization, loss-aware DXT encoding, shader sampling and an in-game rendering smoke test as separate gates. Nothing from this audit is installable into Carbon PC.
