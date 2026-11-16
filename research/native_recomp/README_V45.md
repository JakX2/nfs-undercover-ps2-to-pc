# V45: Original Wii `__OSInitSystemCall` executes natively with both cache services

**Scope: independent bounded original-game native execution, not a complete Wii boot.** This milestone tests the original 96-byte `__OSInitSystemCall` at guest `0x805290C8` as a direct entry through NWiiRecomp's actual generated C++ non-split dispatcher. Unlike the earlier V44 `OSInit` path, this V45 fixture starts **at `__OSInitSystemCall` itself** and returns to a deliberate synthetic test stop, without pretending that the preceding `DBPrintf` has executed.

## Original Wii PowerPC behavior verified

- From the owner's **SHA-256 pinned original Wii DOL**, the private builder copies the authentic 28-byte `__OSSystemCallVectorStart` region (`0x805290A8`), the complete original `__OSInitSystemCall` body (`0x805290C8` to `0x80529124`), and the full original `memcpy`, `DCFlushRangeNoSync` and `ICInvalidateRange` helpers. None of these original instruction bytes are present in the distributed source.
- The native `__OSInitSystemCall` copies exactly **28 original system-call handler bytes** to guest address `0x80000C00` through its unmodified direct `bl memcpy` and preserves all remaining bytes in the surrounding **256-byte cache-maintenance range**.
- The genuine PPC data-cache flush and instruction-cache invalidate routines process **eight 32-byte cache lines each** at `0x80000C00` through `0x80000CE0`, followed by the original `sync` and `isync` ordering instructions. The diagnostic runtime records **2 sync and 1 isync** during each complete original call. This confirms **instruction dispatch and observable ordering** only, not real Wii hardware cache/coherency or AOT host-code invalidation.
- Six independent guest-state configurations verify every copied byte, the untouched remaining 228 bytes, source preservation, neighboring memory canaries, all cache-line addresses, saved `r31`, guest stack pointer and LR, original native helper-dispatch counts, controlled stop PC, and zero PPC interpreter fallback.
- NWiiRecomp analyzes **seven private image entries**, including five required entries `__OSInitSystemCall`, `memcpy`, `DCFlushRangeNoSync`, `ICInvalidateRange` and the synthetic stop. Other inferred analyzer roots are not claimed as newly executed original functions.

## Reproduce with owner-original Wii DOL

Requires C++20 GCC, Python 3, and an isolated copy of the original NWiiRecomp source archive. The original DOL SHA-256 is:

`16a09adcf1987c1f3617d10f3a1cb830f32886afb583f9f8f88e0963ae5fe1f4`

```bash
bash run_osinit_systemcall_v45.sh /private/NWiiRecomp-master /private/NfsMWRelease.dol.bin
V45_SANITIZE=1 bash run_osinit_systemcall_v45.sh /private/NWiiRecomp-master /private/NfsMWRelease.dol.bin
```

The driver idempotently installs the existing original-free V15/V26/V29/V30/V43/V44 NWiiRecomp patches in that isolated checkout when needed, builds a temporary private DOL, checks its original bytes/geometry/callgraph before emitting, compiles generated C++ and the native semantic suite, and removes all private intermediate code/slices when the script exits. The output directory must be empty; malformed and mutated sources are rejected **before** game-derived C++ is emitted. Never run the modifying patches against an unrelated working tree.

## Verification (2026-11-15)

| Check | Verified result |
| --- | --- |
| Native Wii function execution across six guest configurations | **1,894 / 1,894 assertions** |
| Malformed DOL, original source/mutation, pinned SHA, output-preservation guards | **92 / 92 checks** |
| V44 source-only diagnostic trace patch checks | **16 / 16 checks** |
| Fresh NWiiRecomp prerequisites: V43 cache, V30 HID/FP, V29 SPR | **14 / 14, 14 / 14, 13 / 13** |
| Full optimized native runner | **Pass** |
| Full AddressSanitizer + UBSan native runner | **Pass** |
| Full optimized runner from freshly extracted, unmodified NWiiRecomp source | **Pass** |
| Interpreter fallback in tested path | **0** |

## Required files and boundaries

The six new original-free files are: `make_osinit_systemcall_v45.py`, `generate_osinit_systemcall_v45.cpp`, `test_osinit_systemcall_v45.cpp`, `test_osinit_guards_v45.py`, `run_osinit_systemcall_v45.sh` and this README. The companion source-only archive retains prerequisite V15/V26/V29/V30/V43/V44 patch installers and their prior tests. The original DOL, ELF, temporary private DOL, extracted original PPC bytes, assets, and generated original-game C++ are **never committed**.

**Critical unresolved integration:** V44's direct `OSInit` test stops at the original final `DBPrintf` dependency at `0x80520E58` after installing fifteen exception vectors; V45 demonstrates the independent next system-call initializer, but **does not bridge that debug service or the `OSInit` call at `0x805208AC`**. The continuous original `__start` execution remains verified only through V26's `0x805206B4`; five V26 harness source files are still unpublished. No game's original `main`, frontend, frame, or gameplay has executed. Keep PR #36 draft until actual native Windows boot is verified.
