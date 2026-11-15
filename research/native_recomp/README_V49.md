# V49: Original Wii module initializer executes in the native OSInit chain

**Scope:** Bounded execution of source-grounded original Undercover Wii startup code. **Not** a complete Wii OS startup, a native Windows boot, or a playable port.

## New execution

From the owner-original PowerPC DOL (SHA-256 pinned in the fixture builder), the complete genuine **`__OSModuleInit`** at Wii guest `0x80526D30` (24 bytes, 6 instructions) now executes inside the original `OSInit` entry sequence. The V48 test-only termination at `0x805208B4` is replaced with the **unmodified original Wii `bl __OSModuleInit`** at that address, and a new **test-only terminal syscall at `0x805208B8`** stops before the unverified `__OSInterruptInit` service.

The original six-instruction function clears the three 32-bit low-memory module-list globals at `0x800030C8`, `0x800030CC`, and `0x800030D0`, and returns normally. The independent native regression verifies all three stores, surrounding memory canaries, the original `li`/`lis` register results (`r0=0`, `r3=0x80000000`), the return PC and guest stack/interrupt state. The tests also call the genuine module initializer directly with three different nonzero initial-state patterns, in addition to six longer original `OSInit` configurations.

All previously verified V48 OSInit integration continues running, including original system time, interrupts, performance registers, memory arenas, IPC buffer setup, complete exception-vector loop, genuine `_restgpr_20` return, system-call vector initialization, and alarm setup with original shutdown registration. This is **not** continuous execution from the Wii executable's `__start`: that independently verified chain still stops at V26 `0x805206B4` and five of its source-only harness files remain unpublished.

## Verification

| Verification | Result |
| --- | --- |
| Owner-original native semantic assertions (six OSInit paths + 3 direct module calls and existing direct helpers) | **16,792/16,792 passed** |
| Original PPC mutation, owner SHA, DOL geometry, and no-output-overwrite guards | **266/266 passed** |
| NWiiRecomp analyzed native code entries | **45** (includes conservative synthetic guards) |
| PowerPC interpreter fallback | **0** on tested paths |
| Optimized C++20 | **Pass** |
| ASan/UBSan native binary and guard suite | **Pass** |
| Untouched upstream NWiiRecomp ZIP checkout, patched from source-only prerequisite scripts | **Pass** |
| Pristine V29 / V30 / V43 / V44 source-patch safety checks | **13 / 14 / 14 / 16 passed** |

The initial V49 oracle incorrectly expected the previous return-address stack slot to be rewritten by the new call, and expected `r3` to retain the alarm-list result. The native tests showed both assumptions were wrong: the slot still contains the original previous call's return address (`0x805208B4`), while `__OSModuleInit` explicitly writes `r3=0x80000000`. Both expectations were corrected to match genuine PowerPC behavior before all verification runs.

### Reproduction

Requires Python 3, a C++20 compiler (GCC used for verification), the original owner game DOL with the pinned SHA-256 and a **separate** NWiiRecomp checkout because the source-only patches modify its runtime and C++ emitter.

```bash
bash run_osinit_module_v49.sh /private/path/NWiiRecomp-master /private/path/NfsMWRelease.dol.bin
V49_SANITIZE=1 bash run_osinit_module_v49.sh /private/path/NWiiRecomp-master /private/path/NfsMWRelease.dol.bin
```

The runner creates a private temporary slice from the real owner DOL, uses NWiiRecomp's own analyzer and native C++ generator, then compiles and tests the generated dispatcher. A temporary build directory is deleted on exit. The independent builder refuses output overwrites and a mismatched original DOL SHA. The generator verifies section geometry and source bytes **before writing generated source**, including the complete original module body.

This source-only milestone contains exactly six new files: `make_osinit_module_v49.py`, `generate_osinit_module_v49.cpp`, `test_osinit_module_v49.cpp`, `test_osinit_guards_v49.py`, `run_osinit_module_v49.sh`, `README_V49.md`. The cumulative archive includes previous original-free prerequisites. **Never commit the owner's original DOL/ELF, private test slice, original PowerPC function bodies, game assets, or the game's generated translated C++.**

## Remaining dependencies

The next original `OSInit` instruction calls `__OSInterruptInit` at **`0x8052661C`**. It is not yet executed in V49. Other original OS/IOS subsystems still need to run. Most urgently, the newer verified directly-entered `OSInit` path must be integrated into the continuous original `__start` dispatcher, and the missing five V26 source-only harness files should be restored before claiming full repository-only reproducibility of that earlier checkpoint.

The debug output path still contains a **test-only `DBPrintf` return callback**; full original debug service behavior remains unimplemented. Cache operation telemetry is a value-backed approximation, not hardware-accurate Wii cache coherency. There is no verified game `main`, first frame, frontend, racing or playable native Windows application. Preserve PR #36 as a draft.
