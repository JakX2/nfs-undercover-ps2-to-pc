# Phase 45: One-command Carbon PC steering evidence bundle

**Status:** source-only, read-only, version-gated research. This is a working tool for a user-owned original executable, **not** a validated handling patch or completed Undercover PC port.

## Why Phase 45

Phases 40–44 progressively built exact-byte store checks, conservative EAX/EDX traces, ESI-relative memory-access counts, candidate-offset reviews and bounded control-flow analysis. Each had a separate CLI. Phase 45 combines them into **one authenticated disassembly pass and one JSON evidence report**, so the privately owned executable needs to be scanned only once.

### Inputs and verification

The only supported input is the original Carbon PC NFSC.exe with exact SHA-256:

    baaaaec33873d4ba7e4dbae6a5212049ffdcf9679a35d865d7625b4189952fd3

The Phase 31/40 verifier checks this digest, PE32 layout, known instruction bytes, and call targets **before any objdump call**. Phase 45 independently validates the two store instruction boundaries at 0x006EF7B9 and 0x006EF7C0, verifies the instruction operands against Phase 40's anchored decoding, and requires complete disassembly coverage of Carbon PC's inferred DoHumanSteering function from 0x006EF540 through 0x006EF818 (729 bytes).

The two previously verified instruction shapes remain:

| PC address | Exact instruction syntax | Interpretation |
| --- | --- | --- |
| 0x006EF7B9 | mov dword ptr [esi+0x104],eax | 32-bit write, underlying object and field **unknown** |
| 0x006EF7C0 | mov dword ptr [esi+0x118],edx | 32-bit write, underlying object and field **unknown** |

These are **not** established counterparts of Undercover PS2 +0x188 or +0x19C.

## Running privately

Requires Python 3.11+ and GNU binutils `objdump` on PATH. From the repository root, substitute your *own* supported Carbon PC executable:

```sh
python physics/phase45/carbon_pc_steering_evidence_bundle.py /local/path/NFSC.exe --output phase45_steering_evidence.json

python -m unittest discover -s physics/phase45 -p 'test_*.py' -v
```

The report can also be printed to stdout by omitting `--output`. Files are created exclusively by default; pass `--overwrite` only to replace an earlier report. The original executable is never a permitted report destination, including via symlink. The game is never executed or modified. Temporary local code slices used by GNU objdump are removed automatically.

### What the JSON contains

- A strict evidence manifest recording source SHA, verified checks, function bounds and disassembler.
- **Register-origin evidence**: conservative local traces for EAX and EDX before the two anchored writes.
- **Explicit ESI memory accesses**: static counts of read/write shapes at +0x104 and +0x118, plus complex and unparsed operand forms that could hide other accesses.
- **Control-flow evidence**: candidate path results from Phase 44 distinguishing no detected ESI write, an ESI definition, and unknown effects. Calls, indirect transfers and unrecognized instructions are not silently treated as safe.
- A manual next-step checklist. All PS2/PC field-equivalence, runtime, and gameplay-modification flags remain **false**.

A reference to an instruction is not a steering-field name. A static ESI-relative access does **not** prove its object identity at runtime, or that the same memory is used on all branches. The report does **not** embed the original executable, extracted function bytes or memory dumps.

## Tests and limits

- **34 Phase 45 synthetic tests**, including original SHA rejection, independent anchor checks, metadata disagreement, register traces, candidate counts, synthetic GNU objdump disassembly, incomplete-function rejection, JSON serialization and output overwrite safety.
- GitHub Actions runs asset-free suites for Phases 36–45. Passing CI validates the source tooling, **not** results from the original game.
- Original Carbon PC NFSC.exe was not available in this session, so no actual Phase 45 source-backed report was generated. Do **not** claim the field identities or handling differences are verified.
- The core still uses conservative linear objdump decoding plus a bounded CFG, not an authoritative x86 decompilation or a dynamic path trace. Indirect memory access and pointer aliasing may escape this census.

## Next milestone

**Run the exact game-original executable locally and inspect the resulting JSON.** Then investigate unresolved register origins and PC object types, compare against original PS2 steering only after independent type/field validation, and prepare a reversible, strictly version-gated steering-only in-game prototype.

**Keep Phase 30's lateral tire-force modification disabled**: it made the upgraded CCX feel heavier, and this research does not change tire grip or steering limits.
