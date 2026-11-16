# V26: Genuine original Wii system-time and interrupt initialization under native dispatch

**Verified bounded original-game execution, not complete Wii OS initialization or a bootable Windows game.**

V26 extends the V25 continuously translated original Wii Undercover `__start`
through the `OSInit` prologue. It removes the synthetic `__OSGetSystemTime`
service boundary and executes **four original PowerPC functions** using the
real NWiiRecomp Analyzer, native C++ emitter, `run_game(CPUContext&)` dispatcher
and guest CPU/MMU state:

| Original Wii guest function | Address | Size | Status |
| --- | --- | ---: | --- |
| `__OSGetSystemTime` | `0x8052A844` | 100 bytes | Native-executed, full original body |
| `OSGetTime` | `0x8052A824` | 24 bytes | Native-executed, full original body |
| `__RAS_OSDisableInterrupts_begin` | `0x805265AC` | 20 bytes | Native-executed, full original body |
| `OSRestoreInterrupts` | `0x805265D4` | 36 bytes | Native-executed, full original body |

The original `OSInit` prefix is extended by **two authentic guest stores** at
`0x805206AC` and `0x805206B0` that copy the returned 64-bit system timestamp
(`r3:r4`) to its OS globals (`0x8070DB30:0x8070DB34`). Its next original
instruction, another interrupt-disable call at `0x805206B4`, is replaced by an
**explicit test-only `sc; blr` boundary**. V26 does not execute the remaining
`OSInit` body or anything beyond this controlled stop.

The original source is the owner's Wii DOL only, SHA-256
`16a09adcf1987c1f3617d10f3a1cb830f32886afb583f9f8f88e0963ae5fe1f4`.
The owner DOL is never copied to GitHub. All private extracted DOL slices and
game-derived translated C++ are created in a temporary directory and removed
at runner exit. The ZIP contains only independently written scripts/tests and
documentation, plus previously published original-free support patches.

## Key runtime discovery: syscall PC reporting

NWiiRecomp's existing non-split instruction emitter handled `sc` by invoking
`handle_syscall(ctx)` **without updating `ctx.pc` to the syscall instruction**.
After an ordinary branch-and-link returned inside `OSInit`, an `sc` at
`0x805206B4` therefore incorrectly appeared to callbacks as
`0x805206AC`, its previous call-return address. That defect was uncovered by
a deliberately strict stop-location assertion rather than worked around in
the tests.

`apply_syscall_pc_v26.py` applies a small, idempotent, fail-closed patch to the
original-free upstream emitter. For PowerPC opcode 17, the generated C++ now
sets `ctx.pc` to `inst.address` **before invoking the syscall callback**.
The patch refuses unknown upstream source layouts. Re-running it is a no-op.
Other runtime/hardware behavior is unchanged by this patch.

## Original owner-game behavior verified

- One native startup path starts at `0x8000403C` and executes register, hardware,
  paired-single/FPR/cache, BSS/data and debug initialization, original `OSInit`
  prefix, original system-time and interrupt helpers, then stops at the stated
  post-time boundary. NWiiRecomp analyzes **31 functions**, including known
  test-only service boundaries. No PPC interpreter fallback is used.
- `OSGetTime` reads the high/low/high halves of the guest timebase, retrying
  when a low-half rollover crosses the high-half read window. It obtains time
  from the **existing NWiiRuntime virtual timebase (`inst_count`)**, not
  hardware-accurate wall-clock ticks. Test-only `trace_call(OSGetTime)` seeds
  deterministic ticks; there is no production runtime clock override.
- `__OSGetSystemTime` adds the Wii low-memory system-time offset at
  `0x800030D8:0x800030DC` using authentic PowerPC `addc`/`adde`, preserving
  carry into the high word. The two authentic `OSInit` guest stores are checked
  against independently calculated 64-bit expected results, including low-word
  overflow and timebase high-word rollover with the `OSGetTime` retry path.
- Both initial states of MSR.EE are tested: interrupts are disabled during the
  time read and restored to their exact previous state by the original native
  helper. Other MSR bits remain unchanged aside from previously verified
  hardware initialization.
- All original BSS and neighboring canaries, original one-time OS flag, 12
  nonvolatile GPR save slots, stack/LR, FP/paired-single state, FPSCR, GQR,
  HID0/HID2/L2CR state, and existing explicitly synthetic service boundaries
  are revalidated.

An **independently authored synthetic PPC image** instead uses a different
16-instruction system-time implementation and its own interrupt helpers and
fixed 64-bit timestamp. It checks the native dispatch, guest stack, MSR
restoration, and synthetic timestamp stores without reproducing the original
function bytes. In this test mode the explicit `sc; blr` stop is at
`0x805206A0` and the analyzer discovers **26 functions**.

## Reproduce

Requires Python 3, GCC with C++20 support, and a *private* NWiiRecomp checkout.
The runner applies original-free V15, V18, V19, V20 and V26 patches to that
checkout. Prefer an isolated fresh clone, since the checked-in source
installer modifies the supplied checkout in place.

```bash
bash run_v26_tests.sh /private/NWiiRecomp-master
bash run_v26_tests.sh /private/NWiiRecomp-master /private/NfsMWRelease.dol.bin
V26_SANITIZE=1 bash run_v26_tests.sh /private/NWiiRecomp-master
V26_SANITIZE=1 bash run_v26_tests.sh /private/NWiiRecomp-master /private/NfsMWRelease.dol.bin
```

The runner makes temporary output using `mktemp -d`, removes it even on failure,
and refuses to overwrite files or write generated C++ to source directories.
The same older, generated-code-only GCC `-Wno-type-limits` workaround remains
necessary for unrelated unsigned comparisons in unreachable boot paths.

## Verified local results

| Test | Result |
| --- | ---: |
| Original Wii startup through original time+interrupt service, 16 starts | **15,417,628 passing assertions** |
| Independently authored synthetic startup, 16 starts | **2,200 passing assertions** |
| Original-image native analyzer function count | **31** |
| Synthetic-image native analyzer function count | **26** |
| Owner-mode malformed images / source patch fail-closed tests | **77 passed** |
| Synthetic-only malformed images / source patch tests | **55 passed** |
| Full optimized release runner, owner and synthetic images | **Passed** |
| Owner and synthetic *individually compiled* ASan/UBSan binaries | **Both passed** |
| Full synthetic-only ASan/UBSan runner | **Passed** |
| Fresh unmodified NWiiRecomp source checkout, synthetic-only runner | **Passed** |
| Full owner-mode ASan/UBSan runner | **Timed out during original binary compilation; not counted as a completed full runner** |

For the original-game test the standalone release and sanitizer binaries each
reported the same passing **15,417,628 assertions**. The complete owner-mode
sanitizer *script* timed out at compilation of its last original native binary
when rerun through the outer orchestration tool; that is a build-time resource
limit and **must not be reported as a successful complete script run**.

## Remaining real work

The `DBPrintf` and `OSSetErrorHandler` bodies are still explicit earlier test
substitutes, L2 invalidation timing and cache coherence remain unimplemented,
and the timebase default is virtual rather than accurate Wii wall-clock time.
The rest of original `OSInit` has not executed; the next calls include
interrupt masking, `__OSGetExecParams`, performance-counter setup and numerous
IOS/OS subsystems. The game's original `main` at `0x802D3F40`, graphics,
frontend, world, audio and gameplay **have not been reached or verified**.

**Next milestone:** preserve the original `OSInit` instructions after the two
time stores, execute its next interrupt setup and `__OSGetExecParams` boundary
with accurately tested guest-visible state, then advance to subsequent
services one by one. Do not equate these isolated native startup checkpoints
with a completed native Windows boot.

## Follow-up: independent syscall-PC regression (2026-11-14)

`test_syscall_pc_v26.py` adds **15 new original-free standalone checks** for
the V26 `sc` emitter patch. Run it in this directory with:

```bash
python3 test_syscall_pc_v26.py
```

It verifies exact source replacement, idempotency, five fail-closed/unchanged
source layouts, and compiles two small C++20 programs using the actual patched
emitter snippet. The first emits native statements for three distinct guest
PCs; the second executes those statements to confirm a syscall callback sees
the instruction PC even when `ctx.pc` initially contains a stale return PC.
The checks passed with Python 3 and GCC in an original-free isolated run.
They supplement, but **are not part of**, the earlier 77/55 V26 tests and
do not constitute a run of the complete NWiiRecomp game dispatcher.

**Reproduction limitation remains:** the branch has only the V26 patch,
documentation, and this added standalone test, not the five unpublished V26
generator/fixture/runner sources. Its original-game and full-suite V26 results
are owner-local, not independently reproducible from the GitHub branch alone.
