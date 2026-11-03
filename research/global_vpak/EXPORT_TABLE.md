# NpxE entry-table structural probe

**Status: verified offline on supplied `GLOBAL.zip` archives.** This tool discovers a deterministic **entry-boundary relationship** but does not decode object types, coordinate fields, event semantics, or PC runtime behavior.

## Run

From the repository root with Python 3.10+:

```sh
python research/global_vpak/export_table_probe.py /local/Carbon_PC_GLOBAL.zip /local/Carbon_PS2_GLOBAL.zip /local/Undercover_PS2_GLOBAL.zip
python -m unittest discover -s research/global_vpak -p 'test_*.py' -v
```

The probe validates the six-chunk VPAK structure before reading `NpxE` and prints only aggregate counts and record indices. No proprietary strings or binary payloads are exported.

## Empirical entry layout

The `NpxE` block is 16 bytes of header followed by `count` entries, each 16 bytes long. Each entry contains four little-endian 32-bit words:

| Word | Empirical observation | Interpretation status |
| --- | --- | --- |
| 0 | Identical value across all 21,224 inspected entries | Unknown signature/identifier |
| 1 | Multiple of 4 | **Length candidate** |
| 2 | Multiple of 8 | **Offset candidate** |
| 3 | Nonzero except exactly one final zero per record | **Terminal marker candidate**; other values not decoded |

For every consecutive entry pair, across **all 20,457 transitions** in the four source variants:

```text
next.word2 == align_up(current.word2 + current.word1, 8)
```

The terminal entry has word3 = 0, and all preceding entries have word3 != 0. Every nonterminal word2 lies below the length of its associated `NtaD` chunk. The terminal entry must not be counted as a regular serialized object without further proof.

| Source | Indexed records | NpxE entries (including terminal entries) | Verified transitions | Final zero markers |
| --- | ---: | ---: | ---: | ---: |
| Carbon PC active | 190 | 5,726 | 5,536 | 190 |
| Carbon PC backup | 190 | 5,726 | 5,536 | 190 |
| Carbon PS2 | 190 | 5,724 | 5,534 | 190 |
| Undercover PS2 | 197 | 4,048 | 3,851 | 197 |
| **Total** | **767** | **21,224** | **20,457** | **767** |

## Boundary caveats

Five nonterminal entries have `word2 + word1` greater than the entire `NtaD` chunk length: two in the active Carbon PC source (record indices 87 and 88) and three in Undercover PS2 (166, 192, 196). These still satisfy the exact next-offset alignment rule. Therefore **do not use this relationship alone to slice or rewrite original bytes**; the offset base and treatment of end-of-data entries remain unresolved.

The tool reports these exceptions without rejecting the whole archive. Seven new synthetic tests passed locally, covering normal chains, alignment, misplaced markers, broken offsets, and the boundary caveat.

## Next experiment

Correlate the `NpxE` offset/length pairs with `NtaD` structure, `NrtP` pointer-like tables and known name hashes. Only after independently confirming the offset base and object type semantics should a reversible record writer be attempted.

No original game archives, binary chunks, or executable patches are included in the repository.
