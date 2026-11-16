# V15: Upstream NWiiRecomp dispatcher compilation fix and real-game slice execution

This toolkit tests **NWiiRecomp's actual `Recompiler::generate_cpp` output** and its generated `run_game(nwii::runtime::CPUContext&)` loop on the host PC. The owner-original Undercover code is **never included** in this package. Game-derived sliced DOLs and C++ translation units are created only under `mktemp -d` and removed when the runner exits.

**This is a bounded, three-function test, not the original Undercover `__start` boot, renderer or a playable native port.** Two functions are taken from the owner's original Wii DOL; the third is a tiny wholly synthetic `sc; blr` fixture that makes the host-side test stop deterministically.

## Reproducible local test

Requires GCC 14 or compatible C++20 compiler, Python 3, and an owner-local NWiiRecomp source checkout. The runner will modify only the local recompiler emitter by applying the idempotent bug fix below. Existing V12 DOL-loader improvements are recommended.

```bash
bash run_v15_tests.sh /private/path/NWiiRecomp-master
bash run_v15_tests.sh /private/path/NWiiRecomp-master /private/path/NfsMWRelease.dol
V15_SANITIZE=1 bash run_v15_tests.sh /private/path/NWiiRecomp-master /private/path/NfsMWRelease.dol
```

`CXX=clang++` can select a different compatible compiler. Use an isolated copy of NWiiRecomp to avoid interfering with other local changes. The script runs strict `-Wall -Wextra -Werror` checks on emitted translation and executes synthetic and original-game tests; upstream analyzer/recompiler warnings are left visible during the generator build.

## Specific upstream bug

In `nWiiRecomp/src/recompiler.cpp`, the non-split (`split_output=false`) branch of `Recompiler::generate_cpp` emits an unmatched `try {` near the start of `run_game`. The generated output ends the inner switch block without a `catch` and leaves the generated C++ function malformed. This is reproducible without any copyrighted game content by generating code for the original-free synthetic DOL.

`apply_nonsplit_dispatch_v15.py` replaces the malformed block with `if (_setjmp(ctx.exception_jmp_buf) == 0) { ... } else { continue; }`, closes the while body, and retains the existing debug print. This matches the exception-return pattern used by the *split-output* emitter. The patch is **idempotent** and refuses unknown upstream shapes. The synthetic output now compiles, where the unpatched emitter fails with `expected 'catch' before 'std'`.

## What is actually executed

- **Synthetic DOL**: a PPC parent function `mflr/stw/bl/lwz/mtlr/blr` at `0x80004000`, a PPC child function `addi/blr` at `0x80004018`, and a dedicated original-free stop function at `0x80004200`. The upstream Analyzer recovers all three, and the upstream Recompiler generates a real single-unit `output.cpp` with real `run_game` dispatch, function bounds and return-to-caller cases. The native binary passes **3,077 behavioral assertions** over **512 calls**, including 512 native child executions and 512 controlled termination calls.
- **Original Undercover Wii slice**: owner's `NfsMWRelease.dol`, SHA-256 `16a09adcf1987c1f3617d10f3a1cb830f32886afb583f9f8f88e0963ae5fe1f4`, is read privately. From its original PPC text only, the slicer selects `NibbleChar` at `0x8007ADAC` (28 bytes) and `ValueToText` at `0x8007ADC8` (112 bytes). The third synthetic `sc; blr` endpoint is added at `0x80004200`. The upstream analyzer recovers the three spans and the upstream non-split generator emits its full `run_game`. The native binary passes **8,149 behavioral assertions**, executing **270 parent calls and 4,634 real translated cross-function calls**, with byte-exact expected string output, protected canaries, callee-saved registers, stack pointer, LR and test stop.
- Both binaries pass a normal strict-warning build **and** GCC AddressSanitizer/UndefinedBehaviorSanitizer builds with no reported memory violations.
- `test_guards_v15.py` passes **14 original-free safety tests** covering the emitter patch's reversibility/idempotence, failed closed inputs, nonempty output directory, incorrect function spans, and truncated DOL sections.
- The native test's `interpret_step` stub **throws** if invoked; neither test reaches it. The controlled stop endpoint uses a custom test-only `handle_syscall` hook, not a Wii IOS implementation.

## Source-only files

`apply_nonsplit_dispatch_v15.py` fixes the emitter; `make_dispatch_slice_v15.py` produces a small synthetic or private owner-derived test DOL with a synthetic stop function; `generate_dispatch_v15.cpp` calls the **real upstream Analyzer and Recompiler**, verifies exactly three expected code functions and a direct parent-to-callee BL edge; `test_full_dispatch_v15.cpp` links to the **actual generated run_game** for behavioral assertions; `test_guards_v15.py` checks malformed cases and idempotence; `run_v15_tests.sh` reproduces the build and deletes generated outputs.

## Next work

Expand the native link beyond two original gameplay helper routines to the authenticated `__start` path at `0x8000403C`. Record external Wii OS/IOS/GX dependencies as *missing*, not as successfully emulated. The complete translated codebase has **not yet been linked or entered at `__start`**. No native graphics, audio, controller or mission execution has been demonstrated by V15.
