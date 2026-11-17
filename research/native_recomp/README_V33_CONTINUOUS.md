# V33: continuous original Wii __start enters MEM2 arena initialization

Status: VERIFIED by owner-original GitHub Actions continuous-startup run
44008485203 on November 17, 2026. All V26–V33 owner-original stages
passed from authentic __start (0x8000403C), with stage=33 and exact
instrumented test-only stop at 0x805208A4. The earlier directly entered
OSInit V37 tests remain separate; the continuous path verifies the one
specified nonzero MEM2 low/high hint configuration over 16 native trials.

## Original execution scope

The existing owner-original V32 continuous checkpoint reaches OSInit guest
PC 0x80520818. V33 replaces that synthetic stop with 35 authentic original
PowerPC instructions from 0x80520818..0x805208A0, including the real BLs:
- 0x8052088C -> OSSetMEM2ArenaLo (0x80521D68)
- 0x805208A0 -> OSSetMEM2ArenaHi (0x80521D50)

Their actual two-instruction original PPC bodies are taken from the user's
SHA-256-pinned DOL and AOT-translated by NWiiRecomp. Each setter writes an
original guest r13-relative arena global and returns normally. All inherited
original PS/cache/time/interrupt/ExecParams/MMCR/PMC/HID4/MEM1 semantics remain
subject to sixteen case assertions.

The continuous native test deliberately selects a single valid MEM2 path:
- Low MEM2 hint at 0x80003124 is 0x90002000 + per-case delta, above the
  minimum 0x90000800 and within the valid 64 MiB Wii MEM2 window.
- High MEM2 hint at 0x80003128 is 0x93500000 + per-case delta.
- Both original arena setters must be entered exactly once, with authentic
  guest LR values. Guest global stores must match the original input hints.
- The empty boot record/no legacy fallback and nonzero MEM1-low hint from V32
  remain intact; unrelated guest memory and previous BSS canaries are checked.
- There is no PowerPC interpreter fallback and no stub standing in for the
  two MEM2 setter functions.
- An explicit test-only syscall at PC 0x805208A4 terminates **before**
  the original __OSInitIPCBuffer call (0x8052AE80). IPC is not implemented.

The existing directly entered V37 suite tests six additional MEM2 cases,
including the 0x90000800 lower-bound clamp and zero-hint skip branches.
Those results cannot be claimed for V33's continuous original __start
until such inputs are tested in the continuous harness.

## Safety and repeatability

The builder inherits verified V32 original-private DOL layout and
make_osinit_mem2_v37.check_source signatures, and verifies the exact original
35-instruction continuation plus both getter-independent setter bodies.
Source mutation, unexpected branch/operand, wrong SHA, overlapping DOL sections
or reused output files cause explicit failure.

Owner CI checks each preceding checkpoint V26..V32 before requiring
boot_progress.py --require-progress for V33, with exact original entry
0x8000403C, exact guest test boundary 0x805208A4 and stage=33.

A fresh isolated NWiiRecomp upstream checkout must have the V29/V18/V19/V20/
V26 source patches installed by the earlier continuous steps, and the V30
compatible HID4 patch from V30. Then reproduce privately:

    bash run_v33_continuous_mem2.sh /private/NWiiRecomp /private/NfsMWRelease.dol

Original Wii executables, game-derived PPC words/C++ and raw logs stay
ephemeral on the runner. A successful V33 is a bounded native OS initialization
step, not full boot, original game main, first frame, frontend or gameplay.
