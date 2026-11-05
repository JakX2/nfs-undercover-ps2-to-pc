# Phase 42: Carbon PC ESI-relative steering access census

**Status:** read-only static research on the existing Code/AI/Gameplay branch. No installed game patch, changed handling values, or actual original-executable run in this session.

## Purpose

Phase 40 verified that Carbon PC's inferred steering routine contains two static x86 writes: mov [esi+0x104],eax at 0x006EF7B9, and mov [esi+0x118],edx at 0x006EF7C0. Phase 41 introduced exact-executable gated disassembly and conservative register tracing. This Phase 42 inventories other **syntactically ESI-relative** memory operands in the same Carbon PC steering routine, so we can later look for accesses that might help identify the two fields.

This is a **candidate instruction census**, not a recovered C++ class layout, a claim of equivalent PS2 fields or a measurement of execution frequency. ESI may be redefined on different control-flow paths.

## Input verification and method

1. Use the Phase 40 auditor to reject all Carbon PC executables other than the supported exact SHA-256 `baaaaec33873d4ba7e4dbae6a5212049ffdcf9679a35d865d7625b4189952fd3`. It checks known instruction bytes, call targets and PE32 layout.
2. Extract the fixed bounded Carbon PC steering range 0x006EF540 to 0x006EF819 and disassemble it through Phase 41's GNU objdump integration.
3. Require both verified Phase 40 instruction-byte sequences at actual disassembly boundaries.
4. Collect explicit memory operands whose address is simply `[esi]`, `[esi+constant]` or `[esi-constant]`. Preserve the exact instruction address and signed displacement. Group static instructions by displacement.
5. Separate complex/indexed ESI uses (e.g. `[esi+ecx*4+0x20]`) from simple fields. Do not collapse them to a false constant offset. Keep malformed or unsupported memory expression forms in an uncertainty list.
6. Classify only recognized memory operations as read, write or read_write. Unknown instructions stay `unknown`. LEA computes an effective address and is **not** a memory dereference, even when its operand mentions ESI.
7. Check that the two Phase 40 stores appear as writes at their expected displacements in the output, otherwise reject the report.

## Run on your exact original Carbon PC executable

Requires Python 3.11+, GNU objdump (binutils) installed and available on PATH, and your privately held original supported NFSC.exe. From the repository root:

```sh
python physics/phase42/carbon_pc_esi_access_census.py /path/to/NFSC.exe --output phase42_pc_esi_accesses.json
python -m unittest discover -s physics/phase42 -p 'test_*.py' -v
```

No game code is executed and no game files are modified. The JSON report can be written to stdout instead. Existing report files cannot be replaced unless --overwrite is explicit, and the original executable cannot be used as the output path.

## Validation and limits

- **40 synthetic tests** cover operand parsing, signed displacements, indexed expressions, direction classification, LEA exclusion, XCHG read/write handling, real objdump decoding on tiny synthetic bytes, anchor checks and unsupported-executable rejection.
- The GitHub workflow runs all source-only Phase 36–42 tests. A successful workflow does not mean the original Carbon executable was analyzed.
- The analyzer cannot infer indirect accesses through registers initially derived from ESI. It also does not infer values, actual code-path execution or the object type behind ESI.
- Console PS2 offsets (+0x188 and +0x19C) must not be transplanted into Carbon PC, or equated with PC (+0x104 and +0x118).
- No original executables, extracted code bodies, live memory logs or proprietary assets are committed.

## Next handling investigation

Run Phase 42 on the verified user-owned Carbon PC executable. Look for other loads of +0x104 and +0x118, and the surrounding control flow and ESI assignments. Pair these with Phase 41's EAX/EDX traces and the original PS2 field evidence only after establishing **independent object semantics**. A later opt-in steering-only experiment may follow that verification.

**Phase 30's lateral tire-force hook remains disabled.** It made the upgraded CCX feel heavier and is unrelated to this read-only work.
