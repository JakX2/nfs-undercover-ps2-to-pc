# V46: Original `OSInit` returns from exception setup and executes `__OSInitSystemCall`

**Status: verified owner-private, directly entered original Wii `OSInit` integration. Not a native Windows boot or continuous execution from the original game `__start`.**

V46 bridges the two previous bounded execution milestones. Starting at the genuine `OSInit` at `0x80520670`, NWiiRecomp-generated C++ now executes the authentic `OSExceptionInit` 15-vector installation loop, the **original exception epilogue and `_restgpr_20` function**, and then the **entire original `__OSInitSystemCall`**. The next test-only terminal syscall is at **`0x805208B0`**, before the still-unimplemented `__OSInitAlarm` at `0x805210CC`.

## Exact test-only substitution

The original exception epilogue calls `DBPrintf` at `0x804E50B8`. **This original function is not executed or implemented**. A test-only private `sc; blr` callback occupies that address and returns immediately. This allows the original epilogue, `_restgpr_20`, caller return and subsequent `OSInit` call into `__OSInitSystemCall` to execute without silently fabricating debug-service behavior. The earlier marked-exception debug branches remain fail-closed synthetic stops.

The private test image preserves every original PowerPC instruction address in the tested functions. It combines existing DOL text sections with only unexecuted synthetic NOP gap-filling, retaining original bytes extracted solely from the SHA-pinned owner's Wii DOL. The original exception handler source is supplied privately through the same source-backed fixture as V44. The real 28-byte system-call handler source is seeded from the owner-original code in the private slice, never embedded in the distributable test code.

## New native semantics verified

- **All 15 original exception handlers** are copied by the real original `memcpy` and processed by the original `DCFlushRangeNoSync` and `ICInvalidateRange` loops.
- The authentic `OSExceptionInit` epilogue restores guest register state with the real 52-byte `_restgpr_20` at `0x80545134`, restores the nested stack frame and returns to `OSInit`.
- `OSInit` calls the complete original 96-byte `__OSInitSystemCall` at `0x805290C8`. The genuine routine copies 28 PowerPC system-call handler bytes to `0x80000C00`, then processes the full 256-byte cache-maintenance range.
- The system-call vector **overlays the first 28 bytes of exception vector index 11**. The native test verifies this expected overwrite while asserting that the remainder of that handler and all neighboring memory canaries are preserved.
- A normal path produces **83 guest dcbf traces, 83 guest icbi traces, 32 sync events and 16 isync events** (75 handler cache lines plus eight system-call cache lines). These traces model original instruction ordering only, **not Wii hardware cache coherency or AOT self-modifying code invalidation**.
- Six original `OSInit` cases verify the normal exception/setup path, marked-exception strict rejection path, guest stack/LR re-use between nested functions, original saved registers, MEM1/MEM2 arenas, hardware registers, IPC globals, system time and boot-information behavior. No interpreter fallback in the tested paths.
- The native analyzer sees **40 roots**, including synthetic service boundaries and conservative guard entries, not 40 new original functions.

## Reproduction

Requirements: isolated NWiiRecomp source root, Python 3, GCC supporting C++20, and the owner's legitimate original Undercover Wii DOL with SHA-256:

`16a09adcf1987c1f3617d10f3a1cb830f32886afb583f9f8f88e0963ae5fe1f4`

```bash
bash run_osinit_syscall_bridge_v46.sh /private/NWiiRecomp-master /private/NfsMWRelease.dol.bin
V46_SANITIZE=1 bash run_osinit_syscall_bridge_v46.sh /private/NWiiRecomp-master /private/NfsMWRelease.dol.bin
```

The driver verifies the original-owner SHA **before applying original-free patches** to the isolated recompilation checkout. As required, the V15, V26, V29, V30, V43 and V44 source patches are idempotent and fail-closed for unknown revisions. The original game instructions and private test fixtures are translated/compiled inside a temporary directory, removed by a trap on exit, and never included in the source-only package. Don't run the modifying scripts against an unrelated working tree.

## Verification (2026-11-15)

| Test | Result |
| --- | ---: |
| Integrated native `OSInit` semantic assertions, six OSInit paths and direct helper regressions | **16,711 / 16,711** |
| Malformed-image, pinned-original-SHA, PPC mutation and no-overwrite guards | **194 / 194** |
| V44 diagnostic cache trace patch checks | **16 / 16** |
| Clean-checkout source patch guards: V43, V30, V29 | **14 / 14, 14 / 14, 13 / 13** |
| Optimized GCC C++20 full native runner | **Pass** |
| Full ASan + UBSan native runner | **Pass** |
| Freshly extracted unmodified NWiiRecomp full optimized runner | **Pass** |
| Interpreter fallback in tested native path | **Zero** |

## Scope and next integration boundaries

The six new independent original-free files are `make_osinit_syscall_bridge_v46.py`, `generate_osinit_syscall_bridge_v46.cpp`, `test_osinit_syscall_bridge_v46.cpp`, `test_osinit_guards_v46.py`, `run_osinit_syscall_bridge_v46.sh` and this README. The accompanying source-only ZIP includes previously published V45/V44 prerequisites. No original DOL or ELF, proprietary game assets, original PPC function bytes, private slice, or game-derived emitted C++ is published.

**Not yet executed:** the real `DBPrintf`; authentic `OSInit` beyond the next `__OSInitAlarm` call at `0x805208B0`; a continuous `__start` chain beyond V26's `0x805206B4`; the original game `main` at `0x802D3F40`; any native first frame, frontend or gameplay. Five V26 harness source files remain missing from PR #36, a separate GitHub-only reproducibility gap. Preserve the draft PR and previously completed Carbon adaptation work.
