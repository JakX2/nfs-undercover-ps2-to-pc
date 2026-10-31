# Phase 40: Carbon PC steering-store anchors (read-only)

**Status:** Source-only tool, exact-original-file gate, synthetic tests. No ASI, memory reading, handling patch, or new original-executable scan in this phase.

## Evidence inherited from Phase 31

Phase 31 mapped the inferred Carbon PC SuspensionRacer::DoHumanSteering function to 0x006EF540. Its exact-byte verifier includes two **instruction-addressed** byte signatures:

| PC virtual address | Phase 31 bytes | Restricted x86 decoding |
| --- | --- | --- |
| 0x006EF7B9 | 89 86 04 01 00 00 | mov dword ptr [esi+0x104], eax |
| 0x006EF7C0 | 89 96 18 01 00 00 | mov dword ptr [esi+0x118], edx |

These interpretations were independently checked with GNU objdump on the already documented instruction bytes, **not a freshly available NFSC.exe**. Both are syntactic 32-bit writes in the Carbon PC routine. Neither field's actual meaning is known. They are NOT verified equivalents to Undercover PS2 +0x188 or +0x19C.

## New analyzer

`carbon_pc_store_audit.py` decodes only the two six-byte `MOV r/m32,r32` anchors. It rejects unsupported opcodes, ModRM patterns, SIB addressing, invalid lengths and altered bytes. It does not scan arbitrary instructions or claim an exhaustive store listing.

The CLI first invokes Phase 31's full `verify` on the locally supplied Carbon PC executable, validating the exact supported SHA-256 `baaaaec33873d4ba7e4dbae6a5212049ffdcf9679a35d865d7625b4189952fd3`, PE32 identity, instruction anchors and known call targets. Only then does it create a limited JSON store report. Both `ps2_field_equivalence_verified` and `semantic_field_names_verified` are false.

Run from the repository root using Python 3 standard library:

```sh
python physics/phase40/carbon_pc_store_audit.py /path/to/NFSC.exe --output phase40_pc_steering_stores.json
python -m unittest discover -s physics/phase40 -p 'test_*.py' -v
```

The program never writes to the executable or reads the live game. It refuses to overwrite an existing report unless `--overwrite` is explicitly supplied, and also refuses to use the original executable as the report destination (even through a symlink). With no `--output`, JSON goes to standard output.

## Validation and limitations

- 25/25 local synthetic unit tests passed, covering supported and malformed ModRM encodings, signed offsets, synthetic PE file sections, rejection of unknown versions, report overwrite safety and symlink protection.
- Synthetic PE tests explicitly mock only Phase 31 authentication when checking the extraction routine; the real CLI is never mocked.
- No exact original Carbon PC executable is present in this session, so a fresh source-verified Phase 40 JSON report has **not** been generated.
- Passing CI on public fixtures proves regression behavior, not an in-game result or field semantics.
- Original executables, extracted game assets and runtime dumps are not included.

## Follow-up handling investigation

Trace the definitions of EAX and EDX before the two PC stores using **real instruction-boundary evidence from the exact supported executable**, then independently identify the values' semantic roles. Only compare those PC findings against PS2 steering calculations after validating object identity and data type. Phase 30 tire-force replacement remains disabled because it made the upgraded CCX feel heavier.
