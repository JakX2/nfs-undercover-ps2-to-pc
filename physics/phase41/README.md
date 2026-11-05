# Phase 41: Carbon PC steering-store register tracing

**Status:** Source-only, read-only static research. No gameplay ASI, memory hook, handling patch, source-game-binary upload, or verified original-file Phase41 report was created in this session.

## Objective

Phase 40 identified two instruction-addressed Carbon PC stores in the previously verified steering counterpart at virtual address 0x006EF540:

| Verified instruction PC | x86 instruction | Register traced |
| --- | --- | --- |
| 0x006EF7B9 | mov dword ptr [esi+0x104],eax | eax |
| 0x006EF7C0 | mov dword ptr [esi+0x118],edx | edx |

The instructions and displacements are established **syntax**, not verified semantic steering-variable names. PS2 +0x188/+0x19C are **not** assumed equivalent to PC +0x104/+0x118.

Phase 41 uses GNU binutils objdump to disassemble the **bounded 729-byte** Carbon PC steering function and runs a conservative local backward trace for the two source registers.

## Verification and algorithm

1. Call Phase 40 extract_from_verified_image, which invokes Phase 31 verification of the exact Carbon PC executable SHA-256 (baaaaec33873d4ba7e4dbae6a5212049ffdcf9679a35d865d7625b4189952fd3), PE32 layout, known instruction bytes and external call targets.
2. Extract only virtual addresses 0x006EF540..0x006EF818, without running or modifying the executable.
3. In a temporary directory removed after the call, use GNU objdump in 32-bit Intel x86 mode. Require gap-free coverage with exactly matching instruction bytes.
4. Validate each known six-byte store independently appears at the **same instruction boundary** with its previously established ModRM source register.
5. Add conservative boundaries at all control transfers, their following instructions and in-range direct branch targets; reject direct jumps into the middle of a decoded instruction.
6. Trace backward only within a local region. Recognize a narrow whitelist of GPR moves and unaffected instructions; stop on unknown opcodes, partial-register writes, arithmetic definitions, implicit clobbers, memory loads of unknown values and missing predecessors.
7. Return JSON with local instruction addresses, uncertainty status and strict nonclaims.

This is **not** whole-function SSA, dynamic branch-frequency measurement, control-flow proof, memory aliasing or proof that particular instructions execute during gameplay.

## Running

Requires Python 3.11+ and GNU binutils objdump on PATH (Windows users can use WSL or compatible binutils). From the repository root:

    python physics/phase41/carbon_pc_register_trace.py /local/path/NFSC.exe --output phase41_carbon_register_traces.json
    python -m unittest discover -s physics/phase41 -p 'test_*.py' -v

Unsupported executables are rejected **before disassembly**. The tool extracts a bounded temporary local code slice for objdump; temporary bytes are not included in the JSON, GitHub or public tests. The game is never started or modified. Report files are created exclusively unless --overwrite is explicitly passed, and the original executable cannot be the output destination.

## Testing and evidence limits

- Public tests use asset-free synthetic x86 bytes and the two previously documented tiny anchor signatures. GNU objdump is exercised in GitHub Actions.
- Regression cases include branch cutoff, unknown instructions, partial-register writes, control-flow targets, incomplete decode, single-operand imul implicit EAX/EDX clobber, and pop changing ESP.
- Tests prove the research tool's behavior, **not** the unknown origin or in-game role of the source registers. The original executable was not provided in this session.
- A register chain is not proof of a semantic field identity. These PC stores are not yet verified counterparts to PS2 steering outputs.
- Any future handling patch requires independently verified field identities, a reversible in-game experiment and an exact version gate.

## Next step

Run the auditor on the privately held, SHA-matched original Carbon PC executable. Investigate unknown local register roots using actual instruction-boundary and branch evidence, then independently establish Carbon PC object identity before making a steering-only modification.

**Phase 30's CCX tire-force experiment stays disabled** because it made handling feel heavier.
