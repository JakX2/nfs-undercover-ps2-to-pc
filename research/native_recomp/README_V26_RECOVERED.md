# Recovered continuous Wii V26 native startup harness

This source-only kit reconstructs the missing V26 *test harness* from the
committed V25 original-startup implementation. It does **not** embed original
retail game instructions, images, firmware, games, proprietary assets or
translated game C++.

## Exact scope

- Original entry: 0x8000403C.
- Genuine original time service: 0x8052A844, with original 0x8052A824
  timebase helper and two real interrupt helper functions.
- Genuine OSInit time-result stores at 0x805206AC and 0x805206B0.
- Explicit test-only syscall stop at 0x805206B4, before the next real
  interrupt-disable call. A synthetic branch-return follows the test stop.
- Old V25 independent synthetic fixture remains independently authored.
- Recovered generator and native C++ test are based on V25's existing,
  independently written helper checks, including full native original
  __start, BSS, MSR, cache and register-save assertions. New checks cover
  exact guest syscall PC, inter-function call graph, helper entries, and
  original 64-bit timestamp writes. The unit/timing model is test-only.

To test on an isolated source checkout:
    bash run_v26_recovered_tests.sh /private/NWiiRecomp-master
    bash run_v26_recovered_tests.sh /private/NWiiRecomp-master /private/NfsMWRelease.dol

The real-game test first checks exact original DOL SHA-256, slices code only
into a fresh temporary private DOL image and emits private generated native
C++ in a temporary directory. All private files and logs are destroyed at
runner exit. No original game bytes are committed.

The CI lane Wii Continuous Startup Checks executes a synthetic native
regression on every research-branch update and a gated owner-original native
regression on that branch when the existing Drive IDs and
WII_GHIDRA_PRIVATE_ENABLED repository variable are configured.

## Verification status

The new source-only recovered harness passed **genuine owner-original**
GitHub Actions run 43998534658 on November 17, 2026. Both synthetic and
owner-private jobs succeeded; no original code, game assets or generated
native source was published. The native C++ contract verifies every trial's
exact PowerPC syscall callback PC, original native call graph, register and
memory state, and genuine __start entry.

The subsequent workflow change makes the recovered runner emit an explicit
BOOT_PROGRESS entry=0x8000403C pc=0x805206B4 stage=26 marker **only after**
all 16 owner-original native trials pass and a strict anchored PASS marker
confirms the exact test stop. The boot-progress wrapper must reject any
missing/incorrect marker and record passed_instrumented. This additional
structured-checkpoint CI test still needs an authentic successful run to
prove the new marker end to end.

**V26 is reproduced, not exceeded.** The recovered harness ends before the
real bl to the interrupt-disable helper at 0x805206B4. The older V68 direct
OSInit path remains a separately entered fixture and has not been joined.

The direct V68 OSInit test at 0x804EFA34 is an independent entrypoint.
The next technical step is replacing this V26 test-only OSInit stop with
real interrupt-disable and __OSGetExecParams, then integrating larger V68
OSInit segments without resetting the authentic __start state.

No original main, full OSInit, first frame, frontend or gameplay is reached.
