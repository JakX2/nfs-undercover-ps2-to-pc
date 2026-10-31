# V53: Wii scenery zero-position controls and exploratory mask spatial correlation

**Research branch:** Map & World Conversion / Geometry, offline only. This is **not** a Carbon PC serialized-format, bit-layout semantics, streaming, or in-game validation. No original game data is distributed.

## Why V53 was necessary: correcting V52

The exact original Wii RedBuilding scene is 8,488 bytes, SHA-256:

`cb08ca728a9b76992aaaefe32b450565ef53246f090cfe296f77d96c5d272e7f`

Its candidate `0x34103` array has 31 aligned 96-byte instances, four of which (slots **0, 1, 2, 30**) store an exact `(0,0,0)` position while their AABBs are **not at the origin**. Slot 0 (preculler block 1) has flags `0x6C0`, as do slots 1 and 2 (block 0); slot 30 (block 0) has flags `0x400`. Ordinary placed records generally have `0x80`. The labels *unplaced* or *anchor* are hypotheses, not proven meanings of these flag values.

V52 compared candidate mask blocks **1 and 11** and described them as ~4,161 source-coordinate units apart with Jaccard ~0.942. That distance used block 1's **stored zero position**, not its true AABB location, so **the old far-distance counterexample is invalid as a world-space test**. An expressly heuristic substitution of slot 0's AABB midpoint for the zero coordinate yields ~**58.67** units, with the same mask Jaccard. The bounding-box midpoint is a *proxy*, not the proven engine placement transform.

## Five exploratory controlled comparisons

Wii `0x34107` here has 24 candidate 128-byte blocks, 23 nonzero; only each block's first 68 bytes were interpreted as a *candidate* LSB-first set of bit positions. For groupings with multiple referencing instances, their source positions are averaged. A comparison of block IDs, rather than all 31 original instances, avoids giving extra weight to repeated indices.

| Comparison | Candidate blocks | Pairwise values (dependent) | Spearman rho |
|---|---:|---:|---:|
| Original raw positions, including zero-position group | 23 | 253 | −0.474497 |
| Exclude mask blocks touched by zero-position rows | 22 | 231 | −0.590018 |
| Replace zero-position coordinates with AABB midpoints | 23 | 253 | −0.581739 |
| Exclude zero-position blocks and remove bits shared by all remaining masks | 22 | 231 | −0.568045 |
| Only blocks referenced exclusively by scenery-info index 6 | 13 | 78 | −0.780412 |

**Important:** Pairwise distances are not independent observations. For each comparison, V53 performs a Mantel-style **whole-mask label permutation**, keeping spatial positions fixed and relabeling full masks, using seed `533` and **9,999 permutations**. No shuffle in those deterministic runs reached a correlation at least as negative as the observed correlation, yielding a one-sided Monte Carlo estimate **(0+1)/(9999+1) = 0.0001**. The comparisons were selected after observing the fixture and reuse the same scene and masks. These values are exploratory, **not** multiple-scene replication, calibrated evidence for a causal mechanism, or a verified visibility algorithm. No attempt to infer per-bit meaning is justified.

Independent Carbon PC `0x34105`/`0x34107` on-disk layouts, loader assumptions, world-stream registration, spatial updates after insertion, TPK/shader and collision/nav remain **unverified**. No native writer or installable patch is produced.

## Reproduction

The V53 source-only research script imports `research/v50/v50_scenery_index_crosscheck.py` from the preceding public research branch. No game files are included in the repository.

```bash
# Public synthetic test suite (no game assets):
python -m unittest discover -s research/v53 -p 'test_v53.py' -v

# Optional source-backed local tests, only with your own original game files:
NFS_UC_WII_SCENE=/private/UC_Wii_RedBuilding_Original_Scene.chunk \
  python -m unittest discover -s research/v53 -p 'test_v53.py' -v

# Full report (never overwrite an existing report or game asset):
python research/v53/v53_preculler_spatial_controls.py \
  --scene /private/UC_Wii_RedBuilding_Original_Scene.chunk \
  --expected-root-sha256 cb08ca728a9b76992aaaefe32b450565ef53246f090cfe296f77d96c5d272e7f \
  --permutations 9999 --seed 533 --report /tmp/uc_v53_new_report.json
```

## Regression test scope

- V53: **31/31** (**23 synthetic**, **8 original pinned-Wii fixture**).
- Independently rerun V41 **18/18**, V43–V46 **146/146**, V50 **24/24**, V52 **29/29**.
- **248/248** selected tests across those sets, not a full historical test of every research milestone. (Direct fixture-dependent V51 vs GitHub's corrected V49 reader is still pending; V51 public CI previously passed.)
- Carbon PC original-world-stream tests: **none**. Carbon PC in-game tests: **none**.

## Next: V54

The best discriminating next input remains a second authenticated Wii scenery ROOT with a different instance/group distribution, followed by an original Carbon PC root and master stream. Then repeat V53 correlations and verify **disk-level** `0x34105` and `0x34107` indexing independently of Carbon RTX's 128-byte **runtime** preculler structure. Do not turn these correlations into installation logic.