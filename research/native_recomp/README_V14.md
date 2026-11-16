# Undercover Wii native recomp V14: genuine two-function PPC call graph

**Milestone:** NWiiRecomp emitted two real owner-original Undercover Wii functions from a private DOL into separate C++ translation units. Compiled x86-64 code executed a guest PowerPC `bl` call from `ValueToText` to `NibbleChar` twice per input byte, then returned through the caller's saved link register, without interpreter fallback. This is isolated function execution, **not a full native game boot**.

All code, synthetic fixtures and tests here are original-free. No original game machine code, generated game-derived C++, ELF, DOL, symbols archive or game assets are committed or included in the ZIP.

## What is tested

- Owner's original `NfsMWRelease.dol` SHA-256: `16a09adcf1987c1f3617d10f3a1cb830f32886afb583f9f8f88e0963ae5fe1f4` (used privately; not distributed).
- Caller `ValueToText__6AttribFPCvUiPc` at `0x8007ADC8` (112 bytes, 28 PPC instructions); callee `NibbleChar__6AttribFUc` at `0x8007ADAC` (28 bytes, seven PPC instructions). Original ELF symbol names and direct `bl` call edges were checked using the owner's own binary.
- Both functions were regenerated with NWiiRecomp's actual `Recompiler::generate_function_cpp`, compiled as separate host C++20 objects and linked with real NWiiRuntime `CPUContext` / guest MMU structures.
- **8,419 assertions** passed on **270 input arrays**, including zero-length, all 256 possible input byte values, and longer binary data up to 1,024 bytes. This exercised **4,634 actual translated guest `bl` calls**, caller LR save/restore, guest stack memory, callee-saved registers, NUL termination and output canaries.
- **5,123 assertions** passed on independently authored synthetic PowerPC parent/child functions: **1,024 linked `bl` calls**, checked register arithmetic, guest stack and LR recovery.
- **17 source-only negative cases** reject duplicate/overlapping/unmapped selections, incomplete last instruction, unsupported control flow and unknown external call targets. No generated output is written on these failures.
- Both real and synthetic C++ executables also passed separately with GCC AddressSanitizer and UndefinedBehaviorSanitizer enabled. The complete combined sanitizer runner was not completed in one invocation due to an execution time limit; do not treat that combined run as passed.

## Files

`recompile_callgraph_v14.cpp`: owner-local, bounds-checked multi-function PPC emitter, permitting only branch targets inside a selected function or direct `bl` to a second selected entry. It validates complete `blr` ends, linked conditional branches, `sc`, indirect control flow and unsupported emitted trap markers. It does not publish source output: all generated files go to a caller-selected local temporary directory.

`make_synthetic_callgraph_v14.py`, `test_synthetic_callgraph_v14.cpp`: synthetic PPC DOL with a `bl` parent/child pair and executable host-native regression.

`test_callgraph_guard_v14.py`: invalid-input and non-publication checks.

`test_real_callgraph_v14.cpp`: original-free behavioral contract. Needs locally generated C++ for the two original game functions.

`run_v14_tests.sh`: creates a temporary build directory, builds the actual NWiiRecomp emitter, runs synthetic guards and generated-code execution, optionally runs owner-original callgraph tests and deletes private generated code at exit.

## Reproduce without game files

```bash
bash run_v14_tests.sh /path/to/NWiiRecomp-master
```

## Reproduce with your own original Wii DOL

```bash
bash run_v14_tests.sh /path/to/NWiiRecomp-master /private/path/NfsMWRelease.dol
```

The tested NWiiRecomp checkout includes the earlier V12 bounds-checked DOL loader patch. The generated code is stored transiently under `mktemp -d`; no original instructions or generated bodies are committed. For sanitizers, set `V14_SANITIZE=1` (may take longer to compile).

## Next gate

Expand the verified callgraph toward the actual `__start` entry and native `run_game(CPUContext&)` dispatcher, with bounded trace output, full Wii service linkage and accurate startup state. We have **not** linked the complete Undercover game, initialized OS/hardware services, displayed a frame or run any gameplay. The V14 code establishes a genuine source-grounded **inter-function call seam**, not an end-to-end Windows port.
