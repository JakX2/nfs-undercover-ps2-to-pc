# V54: Wii scenery mask-correlation sensitivity and source-uniqueness gate

**Scope:** NFS Undercover Wii/PS2 → Carbon PC, Map & World Conversion / Geometry. **Offline, read-only, source-only** research, not a playable port.

## Why this is a useful V53 follow-up

V53 measured an exploratory negative relationship between candidate `0x34107` mask similarity and the spatial distance between the original Wii scenery objects that reference those masks. All previous tests used the same 8,488-byte original Wii RedBuilding scenery ROOT (SHA-256 `cb08ca728a9b76992aaaefe32b450565ef53246f090cfe296f77d96c5d272e7f`). We still have **no independent authenticated second Wii scenery scene** and **no original Carbon PC world stream or V42 scene pair**. V54 does not claim to have acquired either.

V54 addresses two narrower failure modes: (1) whether a single candidate mask drives the apparent spatial association, and (2) whether the association persists after preserving the **source scenery-info-6 group identity** during label permutations rather than shuffling every mask across unrelated scenery-info cohorts. It also flags duplicate source bytes, without confusing distinct SHA-256 hashes with independently authenticated original game sectors.

## Original-Wii-fixture results, not Carbon PC disk format proof

Verified using the **one exact original Wii RedBuilding scene**:

| Comparison | Source candidate groups | Observed Spearman rho | 9,999 group-constrained label permutations, `rho <= observed` | One-sided plus-one estimate |
|---|---:|---:|---:|---:|
| Nonzero-position candidate masks, moving only scenery-info-6 labels | 22 (13 movable, 9 held fixed) | −0.590018 | 0 | 0.0001 |
| Same, stripping candidate bit positions common to all 22 masks | 22 (13 movable, 9 held fixed) | −0.568045 | 0 | 0.0001 |

The **leave-one-block-out** sensitivity calculation does not retrain or reinterpret visibility fields. It recomputes rank correlations after excluding one candidate block at a time:

| Comparison | Candidate groups | All-groups rho | Lowest leave-one-out rho | Highest leave-one-out rho | Sign reversal? |
|---|---:|---:|---:|---:|---|
| Nonzero-position masks | 22 | −0.590018 | −0.679821 | −0.564487 | No |
| Exclusively source scenery-info-6 masks | 13 | −0.780412 | −0.798451 | −0.745754 | No |

The negative spatial association in this one scene is **not solely one block's artifact** and persists under a narrower shuffling null. These values are **exploratory/post-hoc** and are not independent samples. The permutation p-values are conditional on these chosen comparisons and on one fixture, not a general guarantee of another scene's spatial visibility or proof of bit semantics.

## Source uniqueness safety

A second identical byte-for-byte copy of the scene is detected as **one distinct root** and cannot be counted as replication. Two different files may have different hashes, but their originality or independent provenance does not follow from the hashes; consequently the script *never* reports that independent original scenes were authenticated. Actual cross-scene replication requires a newly authenticated original second Wii scene, preferably with different candidate instance/node/block counts, and then separate Carbon PC donor data to verify Carbon's own serialization.

## Reproduce (Python 3.10+, standard library only)

These scripts import `research/v53/v53_preculler_spatial_controls.py` and `research/v50/v50_scenery_index_crosscheck.py` from earlier research branches. They **do not** include copyrighted game data. `--report` refuses to overwrite an existing output or input.

```bash
# Public tests: 28 synthetic tests; 8 private original-fixture tests are skipped.
python -m unittest discover -s research/v54 -p 'test_v54.py' -v

# Private tests using YOUR original verified scene:
NFS_UC_WII_SCENE=/private/UC_Wii_RedBuilding_Original_Scene.chunk \
  python -m unittest discover -s research/v54 -p 'test_v54.py' -v

# Read-only evidence report, new filename required:
python research/v54/v54_spatial_robustness_gate.py \
  --scene /private/UC_Wii_RedBuilding_Original_Scene.chunk \
  --expected-root-sha256 cb08ca728a9b76992aaaefe32b450565ef53246f090cfe296f77d96c5d272e7f \
  --permutations 9999 --seed 540 --report /tmp/new_v54_evidence.json
```

For auxiliary inputs supply each `--additional-scene` with a paired independently known `--additional-sha256`. That pair checks exact bytes but does **not** authenticate the purported game provenance. Cross-scene claims remain disabled until stronger external evidence is available.

## Validation status

V54: **28/28** synthetic and **8/8** pinned-Wii-source tests. Previous independently rerun selected suites: V41 **18**, V43 **30**, V44 **30**, V45 **34**, V46 **52**, V50 **24**, V52 **29**, V53 **31**. Total **284/284 selected offline tests**. These exclude V51's direct original-fixture regression against the newer V49 GitHub branch, which is a separately tracked follow-up. GitHub's public CI runs synthetic V54 tests only.

**Not proven:** Carbon PC serialized `0x34105`/`0x34107`, in-game visibility/streaming, scene insertion, relocation, textures, collisions or navigation. **Not installable.** No game assets are published.