# Shared-object fingerprints in the three cross-game GAMEPLAY resources

**Status: read-only offline research, 2026-11-03. Not a converter or verified PC runtime integration.**

This investigation extends [OBJECT_REFERENCE_MAP.md](OBJECT_REFERENCE_MAP.md). It compares `NpxE` objects in the three resource-name pairs found in both Carbon PS2 and Undercover PS2, using the Carbon PC active/backup archives as additional controls.

## Reproduce

From repository root with Python 3.10+ and your own local archives:

```sh
python research/global_vpak/shared_object_probe.py /local/Carbon_PC_GLOBAL.zip /local/Carbon_PS2_GLOBAL.zip /local/Undercover_PS2_GLOBAL.zip
python -m unittest discover -s research/global_vpak -p 'test_*.py' -v
```

The script uses `NpeD` names rather than hard-coded record indices. It first invokes the full read-only object/reference boundary validator, then calculates per-object signatures *in memory*. Only aggregate counts and the three explicitly named resource keys are emitted. It prints **no source object identifiers, full original name lists, payload bytes, or asset-derived digests**.

Twelve new synthetic-only regression tests passed, together with sixteen existing object-boundary tests in the local subset (28/28). The complete three-archive analysis was run successfully with local source fingerprints:

- Carbon PC: `4ff0fcd054dde813973490ea2e4fdfdf2db60338f8d76eb81bc349a96f750d66`
- Carbon PS2: `822868fa46a6c08f67cd81f0546c9b2145334c6e450240004c5186431ddfaaf0`
- Undercover PS2: `5455da78b615a50b493c0a9d323da319f258317f6d2698d15727535d7841d348`

## What is compared

The fourth 32-bit word of each `NpxE` entry is **nonzero and unique** within each resource, except the final entry, where it is zero. We treat nonzero values as **candidate object identifiers**, not as a proven hash algorithm. The zero-marked final object is **real and nonempty**, counted in total objects and the raw-byte multiset, but cannot be cross-matched by an ID.

For each shared candidate ID, the tool compares these independent dimensions:

1. Raw serialized object bytes only (a SHA-256 comparison calculated in memory).
2. Byte length and relative locations of `NrtP` group B reference source slots, classified as initial-string or post-string destinations.
3. Exact initial-string destination contents with their source-slot positions, without printing strings.
4. Raw structured/post-string target offsets separately, **not** assuming these positions have equal semantic meaning across games.

It also reports a *multiset* intersection of exact payload byte fingerprints **ignoring candidate IDs**. This count can be much larger because common generic blobs recur, so it is not proof of identical logical objects.

## Undercover PS2 vs Carbon PS2

| Shared resource | UC / Carbon object counts, including final zero marker | Shared nonzero candidate IDs | Same-size reference layouts among shared IDs | Same-ID raw payload bytes | Identical payload multiset, IDs ignored |
| --- | --- | ---: | ---: | ---: | ---: |
| `gpcore` | 2,171 / 2,105 | **1,480** | **940** | **134** | **1,440** |
| `race_bin_challenge` | 100 / 105 | **58** | **32** | **21** | **60** |
| `race_bin_quickrace` | 20 / 34 | **0** | **0** | **0** | **0** |

Within the 1,480 shared `gpcore` identifiers, only **142** have identical reference-site-to-initial-string target content mappings, and **140** have both these mappings and matching reference layouts. For `race_bin_challenge`, the corresponding figures are 21 and 21. `race_bin_quickrace` has no shared nonzero candidate IDs.

For **all 1,480** ID-matched `gpcore` objects and all **58** ID-matched challenge objects, at least one post-string/structured target offset is involved, and **none have identical structured-target offset tuples** across Undercover and Carbon PS2. Offsets are relative to the end of each record's own initial `ErtS` region. This is evidence of differences in reference arrangement, not proof that every underlying referenced entity is different.

**Important:** All 134 `gpcore` and 21 challenge objects that are byte-identical *by candidate ID* still need independent reference reconstruction. Byte-identical object slots alone are insufficient to copy gameplay definitions safely.

## Carbon PC backup vs Carbon PS2: control

| Shared resource | Shared nonzero candidate IDs | Same-ID raw bytes | Raw byte multiset matches, IDs ignored |
| --- | ---: | ---: | ---: |
| `gpcore` | 2,104 | 2,098 | 2,099 |
| `race_bin_challenge` | 104 | 104 | 105 |
| `race_bin_quickrace` | 33 | 33 | 34 |

All these shared IDs appear at the **same indices**, and their **reference layouts match**. Yet only 60/104 challenge ID matches have identical raw structured-target offset tuples. This shows why even PC/PS2 agreement on object payload bytes is not sufficient evidence for transplanting reference tables.

## Carbon PC active vs its backup: edited-source caution

| Shared resource | Shared nonzero candidate IDs | Same-ID raw bytes | Raw byte multiset matches, IDs ignored |
| --- | ---: | ---: | ---: |
| `gpcore` | 2,103 | 5 | 2,094 |
| `race_bin_challenge` | 103 | 5 | 101 |
| `race_bin_quickrace` | 32 | 6 | 34 |

The active PC source includes a VltEd editor marker. It frequently reorders and changes object-linked data even where the same raw payloads survive elsewhere. **Keep it separate from the backup baseline.** The backup has not been independently certified as a clean retail archive.

## Engineering interpretation

- The 16-byte `NpxE` table now offers a plausible matching key at the **per-object** level, much more informative than record index or raw byte pattern alone.
- A conversion plan should distinguish object identity, serialized bytes, pointer-source layout, initial-string targets, and post-string targets.
- Prioritize `gpcore` for reference-base and object-ID investigation, `race_bin_challenge` for a smaller controlled comparison, and use `race_bin_quickrace` as a **negative control** where no matching candidate IDs were observed.
- Do **not** treat shared markers as proof of stable semantic identity, target offsets as decoded pointers, or raw-object matches as loader-ready objects. Independently verify against console executable behavior or a safe reversible laboratory loader before writing original game files.

This public repository contains **only source code, synthetic tests and aggregate evidence**, not game assets or binary patches.
