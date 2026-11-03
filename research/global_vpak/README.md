# Carbon PC / PS2 / Undercover PS2 GLOBAL VPAK audit

**Status: offline, read-only investigation. Not a playable port, verified loader ABI, or completed gameplay converter.**

This directory contains a standard-library Python tool for comparing indexed string regions in user-supplied `GLOBAL.zip` archives. It **never writes modified game data or exports extracted game assets**.

## Run

From the repository root, with Python 3.10+:

```sh
python research/global_vpak/audit.py /local/Carbon_PC_GLOBAL.zip /local/Carbon_PS2_GLOBAL.zip /local/Undercover_PS2_GLOBAL.zip
python -m unittest discover -s research/global_vpak -p 'test_*.py' -v
```

Outputs contain aggregates and archive fingerprints, not extracted original game data. Synthetic tests do not require original game files.

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

## Deeper structural research (2026-11-03)

The name-pool audit above is a historical baseline. The following **read-only, source-only** probes now validate individual serialized ranges and cross-region references, without claiming a working PC loader:

| Research | Script | Notes |
| --- | --- | --- |
| Same-index and cross-index name alignment | `record_alignment.py` | [RECORD_ALIGNMENT.md](RECORD_ALIGNMENT.md) |
| Six VPAK auxiliary chunks | `chunk_layout.py` | [CHUNK_LAYOUT.md](CHUNK_LAYOUT.md) |
| NpxE entry-chain relationship | `export_table_probe.py` | [EXPORT_TABLE.md](EXPORT_TABLE.md) |
| Shared .vlt/.bin resource identities | `resource_identity.py` | [RESOURCE_AND_POINTERS.md](RESOURCE_AND_POINTERS.md) |
| NrtP two-section source/target tables | `pointer_sections.py` | [RESOURCE_AND_POINTERS.md](RESOURCE_AND_POINTERS.md) |
| Verified NpxE object ranges and NrtP source bases | **`object_reference_map.py`** | **[OBJECT_REFERENCE_MAP.md](OBJECT_REFERENCE_MAP.md)** |

The latest read-only analysis verified **767** indexed records, **21,224** positive-length NpxE object ranges, **23,068** group A reference slots and **73,996** group B reference slots across Carbon PC active, Carbon PC backup, Carbon PS2 and Undercover PS2. All source slots are zero-valued and inside their respective text or auxiliary domains; all group B slots belong to exactly one delimited object. These are **structural invariants**, not decoded racing-game logic.

**Correction to earlier probe:** The five apparent NpxE range overruns arose from using an NtaD-local bound for offsets that were actually relative to the auxiliary stream start. The zero-marked final entry also has a positive data length and must not be discarded as an empty sentinel. Read [OBJECT_REFERENCE_MAP.md](OBJECT_REFERENCE_MAP.md) before using the older exploratory counts.

Run the new probe:

```sh
python research/global_vpak/object_reference_map.py /local/Carbon_PC_GLOBAL.zip /local/Carbon_PS2_GLOBAL.zip /local/Undercover_PS2_GLOBAL.zip
```

## Limits and next steps

This parser inspects `VPAK` index fields and leading `ErtS` name pools. It **does not** decode complete attribute values, gameplay record payloads, checkpoint coordinates, police AI, serialization compatibility, or Carbon PC runtime loading. Matching names are not evidence of interchangeable binary records. One header field remains semantically unknown.

Next: determine the internal object field schema and distinguish name/string references from post-string structured references. Cross-check against both PS2 executables, then build a reversible synthetic fixture before attempting a PC runtime experiment. The large Carbon PC `TRACKS.zip` still exceeds the connector's 256 MiB single-file download limit.

Do not commit proprietary game archives, extracted binary chunks, assets or executable patches.