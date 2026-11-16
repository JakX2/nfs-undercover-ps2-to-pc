# V39: Original Wii `OSExceptionInit` prologue begins executing through native NWiiRecomp

**Status:** Verified **bounded original-game execution**, not completed Wii exception-vector setup, Wii OS initialization, or a bootable Windows game.

V39 extends the V38 owner-original direct `OSInit` execution through the real branch-and-link at **`0x805208A8`** into **`OSExceptionInit` at `0x80520BF4`**. The original function is 640 bytes long. Only its initial original PowerPC setup is executed in the verified paths; the exception-vector installation loop and actual exception handlers are not executed.

The tested fast path sets low-memory word `0x80000060` nonzero, follows the original branch at `0x80520C38`, executes the genuine setup instructions through `0x80520CA4`, and stops at a deliberate test-only syscall **`0x80520CA8`** before the per-vector setup loop. This is a continuous **direct `OSInit` -> original `OSExceptionInit`** native dispatcher call, not the earlier continuously bootstrapped original `__start` test.

The debug/copy path has a different condition: when the original low-memory word `0x80000060` is zero, the code falls through toward the real debug print and vector-copy sequence. V39 **stops before the original DBPrintf call at `0x80520C44`**. It does not pretend that debug printing, vector-copying or cache coherence succeeds.

## Newly verified behavior

- Original `OSExceptionInit` creates its **64-byte stack frame** inside the already verified `OSInit` 80-byte frame, saves the original return LR (`0x805208AC`), and calls the **genuine original `_savegpr_20`** helper a second time. All twelve saved nonvolatile guest-register words are checked against the independent pre-call register setup.
- The original code loads a word from **`0x80520F28`**, which is used as a source for later exception-handler installation. The owner's SHA-verified DOL supplies that word privately, and the test deliberately seeds guest text memory because the minimal NWiiRuntime fixture does not yet install the entire game DOL as guest RAM.
- Genuine source-address arithmetic, setup registers, intact previous MEM1/MEM2, IPC, time and interrupt state, and the absence of premature writes to the exception-vector page are asserted.
- An independently exercised **zero-word debug path** reaches the separate explicit `0x80520C44` stop, proving the unimplemented operation is not silently skipped.
- The authentic `__OSInitSystemCall` call at `0x805208AC` is another explicit test-only stop, never executed.

NWiiRecomp analyzes **31 function entries** in this bounded image (26 previously verified V38 entries, one genuine `OSExceptionInit` entry, and **four synthetic guarded roots** from conservative address-target recognition). Those four roots are source-independent **test guards**, not claims of four additional original game functions executed. The analyzer otherwise treats the exception routine's embedded absolute-address operands as entry points and follows thousands of test-filled NOPs. The new fixture prevents that through fail-closed syscall stubs. They are never dispatched in passing tests.

## Private validation

Input: user-owned Wii DOL with SHA-256
`16a09adcf1987c1f3617d10f3a1cb830f32886afb583f9f8f88e0963ae5fe1f4`.

| Verified check | Outcome |
| --- | ---: |
| Original-native assertions: six `OSInit` branches plus direct helper and exception-debug paths | **887/887** |
| SHA, DOL bounds, original-instruction mutations, guarded-return and output-overwrite checks | **256/256** |
| Existing V30 HID/FPSCR patch guards | **14/14** |
| Fresh upstream V29 performance SPR guards | **13/13** |
| Optimized GCC C++20 owner-native full runner | **Passed** |
| ASan/UBSan owner-native full runner | **Passed** |
| Fresh, unmodified upstream NWiiRecomp owner-native full runner | **Passed** |
| PPC interpreter fallback in verified paths | **Zero** |

All original game instruction bytes, private derived DOLs and generated game-derived C++ exist only in a temporary directory during the runner and are removed on exit. Six new V39 files are original-free: the private slice constructor, native analyzer/emitter driver, semantic tests, negative guards, runner and this README.

## Reproduce

From this directory, provide **an isolated NWiiRecomp checkout**, the owner-original Wii DOL, GCC with C++20 support and Python 3:

```bash
bash run_osinit_exception_v39.sh /private/NWiiRecomp-master /private/NfsMWRelease.dol.bin
V39_SANITIZE=1 bash run_osinit_exception_v39.sh /private/NWiiRecomp-master /private/NfsMWRelease.dol.bin
```

The runner installs the existing V15, V26, V29 and V30 independently authored patches where needed. It fails closed on upstream layout changes, uses `mktemp` for all private binary and generated C++ outputs, and refuses overwriting existing artifacts. The source-only ZIP includes earlier source prerequisites but **no proprietary executable or generated game translation**.

## Outstanding work

1. Continue genuine `OSExceptionInit` through `__DBIsExceptionMarked`, vector table memory copies, cache-management helpers, and handler setup, with source-backed memory/interrupt semantics.
2. Reach original `__OSInitSystemCall` and other Wii OS/IOS dependencies, without treating synthetic stops as hardware behavior.
3. Reconstruct and publish the **five missing V26 original-free runner/generator sources**. Until then, the GitHub branch alone does not reproduce the previously reported single `__start` chain.
4. Join V27–V39 genuine original `OSInit` work with a *single* native `__start` execution path. That complete chain currently remains verified only through V26's `0x805206B4`.

No complete Wii OS initialization, game `main` (`0x802D3F40`), native boot, rendered frame, frontend or playable racing has been achieved. Keep PR #36 in draft and preserve the Carbon adaptation work.
