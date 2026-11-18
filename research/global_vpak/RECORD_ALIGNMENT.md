# Indexed GAMEPLAY name-pool alignment

**Status:** read-only research. Name-list similarity does **not** establish compatible gameplay payloads, events, coordinates, engine ABI, or a working PC port.

Run from the repository root with Python 3.10+:

```sh
python research/global_vpak/record_alignment.py /local/Carbon_PC_GLOBAL.zip /local/Carbon_PS2_GLOBAL.zip /local/Undercover_PS2_GLOBAL.zip
python -m unittest discover -s research/global_vpak -p 'test_*.py' -v
```

The analyzer reads local archives and prints aggregate comparisons. It does not export proprietary strings, binary assets, or patches. It strips **only** the exact `NFS-VltEd 4.6.0.0 by nfsu360` marker from the entry-local name lists before comparing them. It does not assume the Carbon PC `.BAK` is verified pristine retail data.

## Verified on the supplied GLOBAL archives, 2026-11-03

| Pair | Result |
| --- | --- |
| Carbon PC `GAMEPLAY.BAK` vs Carbon PS2 `GAMEPLAY.BIN` | **186/190** same-index entries have identical ordered name lists; differing zero-based indices **74, 118, 179, 180** |
| Carbon PC active `GAMEPLAY.BIN` vs its backup | **189/190** same-index entries have identical name sets after marker removal; differing index **169**. Only **3/190** have identical ordered name lists |
| Undercover PS2 vs Carbon PS2 | **0/190** same-index name sets match. Undercover has 197 entries, Carbon has 190 |
| Undercover PS2 vs Carbon PS2, all cross-index pairs | **37,430** pairs checked. Best Jaccard **0.524906**, **1,823** shared distinct names at Undercover index **166** / Carbon index **169**. Runner-up Jaccard **0.155875** |

The highest-scoring pair is a **large common-name pool**, not proof of equivalent event definitions. The four Carbon PC backup / PS2 exceptions should be examined before any record mapping.

## Engineering implications

1. Carbon PC backup and Carbon PS2 have a strong same-index name-list relationship, but payloads may still differ.
2. Carbon PC active data has editor-related changes; keep active and backup sources distinct.
3. Undercover cannot be ported by naïvely substituting the same numbered gameplay records.
4. Next: decode and validate the secondary per-entry payload structures and references, then connect race definitions to independently verified spatial/track data.

The analyzer's synthetic tests run without game files. No proprietary game data is committed.
