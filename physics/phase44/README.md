# Phase 44: Carbon PC control-flow-aware steering access review

**Status:** read-only handling research. No binary patch, installed ASI, original-file scan in this session, or verified PC-to-PS2 field equivalence.

## Motivation

Phase 43 compares Carbon PC's two *candidate* ESI-relative memory offsets (+0x104 and +0x118) using instruction-order intervals. That is deliberately cautious, but the source-order view cannot tell whether a branch bypasses a register write. Phase 44 extends the review with a **bounded instruction-level x86 control-flow graph (CFG)** and an explicit uncertainty-state analysis.

The two underlying Carbon PC store instructions remain:

| PC address | Verified instruction syntax |
| --- | --- |
| 0x006EF7B9 | mov DWORD PTR [esi+0x104],eax |
| 0x006EF7C0 | mov DWORD PTR [esi+0x118],edx |

These syntactic locations are not yet named steering fields and are **not proven equivalent** to Undercover PS2 +0x188 / +0x19C.

## What the new CFG analyzer does

1. Validate the **exact supported Carbon PC NFSC.exe** using Phases 31, 40 and 42 (SHA-256 `baaaaec33873d4ba7e4dbae6a5212049ffdcf9679a35d865d7625b4189952fd3`, PE32 identity, instruction anchors and call sites). Unsupported binaries fail before disassembly.
2. Independently decode the bounded steering-function bytes using Phase 41's GNU objdump integration, and require the complete Phase 42 ESI-access census to agree with the recovered instruction boundaries.
3. Build control-flow edges for linear fallthrough, recognized conditional branches and direct jumps. The algorithm rejects branches into the middle of an instruction, records out-of-function exits, and flags unresolved indirect or unsupported control transfers.
4. Treat a subroutine call as an **unknown potential ESI effect** on the continuation. Avoid assuming that a callee preserves an object pointer merely because typical calling conventions might.
5. Traverse all modeled instruction/state pairs from an earlier candidate access to a later one with a bounded finite-state worklist, including loops. Each modeled route carries one of three states: no detected ESI write, ESI definition seen, or unknown ESI effect.
6. Annotate Phase 43's consecutive same-offset access pairs and the known anchor-to-anchor interval with the modeled states and any unresolved/exiting control-flow events.

**Critical interpretation:** A path classified as 'no detected ESI write' is only a property of the modeled static instructions. It does **not** prove that the path runs during actual driving, that two ESI values refer to the same object, or that a field has a given steering-related meaning. Indirect jumps, unusual x86 operations, calls, derived pointers and object aliasing remain unknown.

## Run

Python 3.11+ and GNU binutils objdump are required, along with your privately owned original supported Carbon PC executable. Run from the repository root:

```sh
python physics/phase44/carbon_pc_esi_cfg_audit.py /local/NFSC.exe --output phase44_carbon_esi_paths.json
python -m unittest discover -s physics/phase44 -p 'test_*.py' -v
```

An existing output file will not be overwritten without `--overwrite`; the source executable cannot be used as the output path. The original game is only read and never executed. Reports contain abstract instruction addresses and path statuses, not executable bytes.

## Verification and next evidence

- **36 synthetic unit tests** cover direct/conditional jumps, calls, loops, indirect and unsupported transfers, ESI writes, unmodeled instruction effects, partial registers, malformed instruction boundaries, the Phase 43 integration and failed-SHA/no-output behavior.
- GitHub CI covers the Phase 36–44 source-only suites, with no proprietary game binaries. Passing CI shows tested analyzer behavior, **not** authenticated game findings.
- The original Carbon PC NFSC.exe was not supplied in this session, so the Phase 44 results on the game have **not** been generated. No steering parameters were identified or changed.

Next: run the exact-version-gated tool privately on NFSC.exe and inspect whether other candidate-offset accesses coexist along modeled paths with the two known store anchors. Source-backed object identities, data types, runtime evidence and a reversible steering-only prototype are required before any gameplay adjustment.

**Leave Phase 30's lateral tire-force experiment disabled**, as it made the upgraded CCX feel heavier.
