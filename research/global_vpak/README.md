# Carbon PC / PS2 / Undercover PS2 GLOBAL VPAK audit

**Status: offline, read-only investigation. Not a playable port, verified loader ABI, or completed gameplay converter.**

This directory contains a standard-library Python tool for comparing indexed string regions in user-supplied `GLOBAL.zip` archives. It **never writes modified game data or exports extracted game assets**.

## Run

From the repository root, with Python 3.10+:

```sh
python research/global_vpak/audit.py /local/Carbon_PC_GLOBAL.zip /local/Carbon_PS2_GLOBAL.zip /local/Undercover_PS2_GLOBAL.zip
python -m unittest discover -s research/global_vpak -p 'test_*.py' -v
```

Outputs are aggregate counts and ZIP SHA-256 hashes, printed to stdout. The nine synthetic tests do not require original game data.

## Verified archive-specific results (2026-11-02)

These values were reproduced locally on the supplied archives, which are **not** committed to the repository.

| Source | Archive SHA-256 |
| --- | --- |
| Carbon PC | `4ff0fcd054dde813973490ea2e4fdfdf2db60338f8d76eb81bc349a96f750d66` |
| Carbon PS2 | `822868fa46a6c08f67cd81f0546c9b2145334c6e450240004c5186431ddfaaf0` |
| Undercover PS2 | `5455da78b615a50b493c0a9d323da319f258317f6d2698d15727535d7841d348` |

| Gameplay source | Indexed entries | Name occurrences | Distinct names | VltEd marker occurrences |
| --- | ---: | ---: | ---: | ---: |
| Carbon PC active `GAMEPLAY.BIN` | 190 | 7,042 | 6,679 | 190 |
| Carbon PC backup `GAMEPLAY.BAK` | 190 | 6,852 | 6,678 | 0 |
| Carbon PS2 `GAMEPLAY.BIN` | 190 | 6,846 | 6,676 | 0 |
| Undercover PS2 `GAMEPLAY.BIN` | 197 | 5,108 | 4,879 | 0 |

**Name-set comparisons:**

- Carbon PC backup and Carbon PS2: **6,676 shared**, 2 PC-backup-only, 0 PS2-only.
- Carbon PC active and backup: **6,677 shared**, 2 active-only, 1 backup-only.
- Undercover PS2 and Carbon PS2: **1,893 shared**, 2,986 Undercover-only, 4,783 Carbon-only.
- Carbon PC backup `FE_ATTRIB.BAK` and Carbon PS2 `FE_ATTRIB.BIN`: **214 shared names** and no name-set differences.
- Active Carbon PC `GAMEPLAY.BIN`, `ATTRIBUTES.BIN` and `FE_ATTRIB.BIN` contain the `NFS-VltEd 4.6.0.0 by nfsu360` marker; the corresponding backups do not. This suggests active files were editor-modified, **not** that backups are independently verified original retail assets.

## Limits and next steps

This parser inspects `VPAK` index fields and leading `ErtS` name pools. It **does not** decode complete attribute values, gameplay record payloads, checkpoint coordinates, police AI, serialization compatibility, or Carbon PC runtime loading. Matching names are not evidence of interchangeable binary records. One header field remains semantically unknown.

Next: reverse-engineer genuine VPAK payload record boundaries and reference relationships, independently cross-check against both PS2 executables, and inspect smaller original `TRACKS` members in a private workspace before attempting a reversible PC integration experiment. The large `TRACKS.zip` currently exceeds the connector's 256 MiB single-file download limit.

Do not commit proprietary game archives, extracted binary chunks, assets or executable patches.