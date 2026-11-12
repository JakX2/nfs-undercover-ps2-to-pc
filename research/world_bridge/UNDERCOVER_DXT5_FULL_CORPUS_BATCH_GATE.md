# Undercover PS2: complete 92-texture DXT5 base-level quality gate

**2026-11-04. Original-source, read-only measurement.** All original texture bytes, palette contents, texture names and identifiers, archive files, and decoded images remain private. Only source-free code, synthetic tests, and aggregate findings belong in this research branch. This is **not** a Carbon PC loading or rendering test.

## Why a bounded audit

The established `synthetic_dxt5_texture_writer.py` and `undercover_to_pc_dxt5_bridge.py` accurately encode individual PS2 decoded RGBA images, but the previous high-resolution section-241 run covered only 8/46 textures because one continuous pure-Python process exceeded the execution budget. Rather than change a validated codec or quietly skip expensive samples, `undercover_dxt5_batch_gate.py` runs up to **12 sorted-index texture ordinals per invocation** and combines source-consistent, contiguous ranges. The new batch tool calls the **existing unchanged** decoder and DXT5 encoder. It does not create images, patches, modified streams, or game-file writes.

Each range report includes aggregate pixel counts, absolute RGB/alpha error sums, per-texture error sums and maxima, indexed-depth totals and swizzle counts. A private SHA-256 fingerprint of the full source *section* ensures that reports from different source bytes cannot be mixed while combining; **no texture identifier hashes** are exported. The final combined report omits this private source fingerprint. Validation rejects missing, duplicated, overlapping, oversized and cross-source ranges, malformed error totals and inconsistent depth/flag counts.

## Original Undercover PS2 results

Measured against the PS2-decoded base-level RGBA, then encoded to DXT5 and decoded with the independently implemented native DXT5 reference decoder. RGB MAE is the mean of absolute R/G/B byte differences; alpha MAE is the absolute A-byte difference. **Per-texture means weight every texture equally**, regardless of its area; **per-pixel means weight every texel equally**. The two averages are deliberately kept separate.

| Undercover PS2 section | Textures completed | Original pixels | Per-texture RGB MAE | Per-texture alpha MAE | Per-pixel RGB MAE | Per-pixel alpha MAE |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| **241 (higher resolution)** | **46/46** | **3,522,560** | **2.5446/255** | **0.4091/255** | **2.4677/255** | **0.3851/255** |
| **3401 (lower resolution)** | **46/46** | **880,640** | **2.6763/255** | **0.5193/255** | see repeatable combined JSON output | see repeatable combined JSON output |
| **Total** | **92/92** | **4,403,200** | two independently validated section cohorts | two independently validated section cohorts | | |

The maximum per-texture error in section **241** is **5.0850/255 RGB** and **1.1619/255 alpha**. Depth cohort: **34** PSMT4 textures (2,220,032 pixels, per-texture RGB **2.5258**, alpha **0.3916**); **12** PSMT8 textures (1,302,528 pixels, RGB **2.5980**, alpha **0.4585**). Swizzle flag is **1 for all 46**, and all 46 contain at least one nonopaque pixel under the explicit half-range alpha-doubling interpretation.

Section **3401** reproduces the prior complete-cohort results exactly (per-texture RGB **2.6763**, alpha **0.5193**, maximum RGB **5.9182**, alpha **1.4236**), with 34 PSMT4 and 12 PSMT8 images and 45 swizzle-flag-1 plus one flag-0 record.

The four high-resolution batches covered ordinal ranges `[0,12)`, `[12,24)`, `[24,36)`, `[36,46)` with no overlap or gaps; the lower-resolution section passed the same four-range pattern. All eight batches were read from the owner's original PS2 `TRACKS.zip`. Both complete combined reports are aggregate-only; source archives are neither modified nor included in the package.

## Synthetic regression tests

`test_undercover_dxt5_batch_gate.py` contains **25 synthetic-only tests**, including exact single-pass versus multi-batch summary equivalence and rejection of cross-source, corrupted, repeated, missing, out-of-range or inconsistent reports. In the available local workspace, **303/303 synthetic tests pass** across the assembled research modules, including 278 pre-existing tests. This workspace was assembled from published research ZIPs and current repo-derived dependencies. **No claim is made that GitHub CI or the game's Windows runtime executed these tests.**

## Reproduction (owner's local source archive only)

From the repository root, run once for each section, substituting the absolute path to your original Undercover PS2 `TRACKS.zip`:

```sh
python research/world_bridge/undercover_dxt5_batch_gate.py audit --undercover-ps2-zip /private/Undercover_PS2/TRACKS.zip --section 241 --start 0 --count 12 > private_241_0.json
python research/world_bridge/undercover_dxt5_batch_gate.py audit --undercover-ps2-zip /private/Undercover_PS2/TRACKS.zip --section 241 --start 12 --count 12 > private_241_12.json
python research/world_bridge/undercover_dxt5_batch_gate.py audit --undercover-ps2-zip /private/Undercover_PS2/TRACKS.zip --section 241 --start 24 --count 12 > private_241_24.json
python research/world_bridge/undercover_dxt5_batch_gate.py audit --undercover-ps2-zip /private/Undercover_PS2/TRACKS.zip --section 241 --start 36 --count 10 > private_241_36.json
python research/world_bridge/undercover_dxt5_batch_gate.py combine private_241_0.json private_241_12.json private_241_24.json private_241_36.json
```

Repeat using `--section 3401` for the lower-resolution texture population, keeping the private JSON files for the local merge only. The published technical report includes no source-derived fingerprint, individual image score table, texture hash list or image pixels. The `combine` command emits only aggregate metrics.

## Still unproven

- **In-game Carbon PC rendering, texture cache registration, new texture identities and game-file search precedence.** This gate writes no loadable PC asset and has no Windows game-process evidence.
- **Material blending semantics**, despite low DXT5 alpha *byte* reconstruction error. Doubling PS2 palette alpha is a color-channel candidate, not proof of correct shader/blend use.
- **Full native PC resource assembly beyond one pre-existing DXT5 slot**, arbitrary resolution/format conversion, matching UV sampler modes and original multi-mip visual semantics.
- **World compatibility:** streaming geometry, instances, collision, navigation, traffic and fully playable Undercover Tri-City Bay remain separate project milestones.

**Decision:** the *base-level DXT5 format-quality gate* is complete for both original Undercover PS2 texture populations, **92/92**; runtime validation remains open. Keep PR #33 draft and `main` untouched.
