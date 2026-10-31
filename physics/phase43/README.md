# Phase 43: Carbon PC candidate-offset static review

**Status:** read-only, source-only research on the Code / AI / Gameplay draft PR. **No installable patch**, runtime steering measurement, original-executable Phase 43 report, or field mapping was produced in this session.

## Why this phase

Phase 40 identifies two exact instruction operands in the supported Carbon PC steering routine:

| Verified instruction address | Syntax | Unverified interpretation |
| --- | --- | --- |
| 0x006EF7B9 | mov DWORD PTR [esi+0x104], eax | 32-bit ESI-relative write, field meaning unknown |
| 0x006EF7C0 | mov DWORD PTR [esi+0x118], edx | 32-bit ESI-relative write, field meaning unknown |

Phase 42 inventories all simple explicit ESI-relative memory operands in the function. Phase 43 provides a focused review of accesses at exactly **+0x104 and +0x118**, with nearby instruction context, static read/write counts, and conservative barriers between consecutive uses.

It does not assume these are the same Undercover PS2 fields as +0x188 or +0x19C. It does not infer actual execution frequency or a runtime value.

## Method

1. Call the Phase 42 SHA-gated original-executable auditor, which inherits Phase 31's exact Carbon PC SHA-256 and byte/call-site verification. The game executable is only read.
2. Independently use Phase 41's GNU objdump decoder on the same bounded steering-function bytes. Require the second disassembly's entire ESI-relative census to **match Phase 42** before producing a report.
3. Require the two known instruction stores at their exact addresses, using known directions and offsets, before reviewing any candidate.
4. Count *static* read, write, read/write and unknown-direction occurrences for the two offsets; include nearby other ESI access instructions within 48 bytes for researcher context.
5. For each pair of consecutive static accesses of the same offset, determine whether the lexical interval crosses a control-flow boundary, encounters a detected ESI register write, or contains an instruction whose effects are unknown.
6. The initial memory-access instruction itself is checked, too. For example, MOV ESI,[ESI+offset] changes ESI after reading its operand; this prevents a false "stable ESI" span even when no intervening instructions write it.

A clean interval gets the deliberately limited label `no_detected_esi_write_in_same_linear_region`. This is **not proof** that both accesses execute along one path, that the two ESI values represent the same game object, or that an offset denotes a particular steering variable.

## Run

Requires Python 3.11+, GNU binutils objdump and a locally owned **exact supported** Carbon PC NFSC.exe (SHA-256 `baaaaec33873d4ba7e4dbae6a5212049ffdcf9679a35d865d7625b4189952fd3`). From the repository root:

~~~sh
python physics/phase43/carbon_pc_candidate_access_review.py /local/NFSC.exe --output phase43_pc_candidate_review.json
python -m unittest discover -s physics/phase43 -p 'test_*.py' -v
~~~

As in Phase 42, the CLI refuses unsupported binaries **before disassembling**, never starts or modifies the game, and refuses an existing JSON destination unless `--overwrite` is given. It also refuses to write over the input executable itself.

## Validation and boundaries

- **33 synthetic Phase 43 regression tests** include exact candidate counts, neighboring static accesses, control-flow changes, ESI clobbers, unknown operations, disassembly agreement, rejected unsupported executables, and byte-free JSON.
- Tests cover the subtle case in which the **first memory-access instruction changes ESI** (including a partial/unknown-value load and XCHG).
- The GitHub workflow runs asset-free research tests for Phases 36 through 43. A green workflow validates test behavior only; it cannot establish real field semantics without the authenticated original game input.
- The algorithm performs **no full dataflow analysis**, does not track indirect registers derived from ESI, does not merge paths, and does not compare original PS2 and Carbon PC layouts.
- Results must remain marked *unknown*, *not proven*, or *candidate* until source-backed evidence supports stronger claims.

## Next evidence

Run the original exact Carbon PC executable privately, inspect the candidate access report, and examine the instruction boundaries and actual ESI definitions around the two stores. Compare to original PS2 steering-state inputs only after independently establishing the function objects and units. A future steering-only experiment should be **opt-in, reversible, version-gated** and tested in-game.

**Keep Phase 30's lateral tire-force hook disabled** because the upgraded CCX felt heavier with that experiment.
