# V34 continuous original Wii __start: IPC-buffer low-memory initializer

Status: new candidate, owner-original continuous native validation pending.
The older direct-entry V38 test is a separate original OSInit experiment.

## Authentic original game code under test

Building on the owner-original V33 continuous __start checkpoint at
0x805208A4, the exact authentic PowerPC BL at guest 0x805208A4 enters
__OSInitIPCBuffer at guest 0x8052AE80. This genuine 24-byte helper
loads the original Wii low-memory IPC buffer pointer words at
0x80003130 and 0x80003134 and writes them into the original OS small-data
globals at r13-16336 and r13-3352.

The helper's original BLR must return to OSInit at 0x805208A8.
The continuous test stops at an **explicit synthetic syscall at 0x805208A8**
before the original OSExceptionInit at 0x80520BF4. The IPC helper does
not perform IOS communication, DMA, IPC queueing or pointer validation,
and the test does not claim these services are implemented.

Sixteen authentic SHA-256-pinned owner-original startup trials test real
native AOT dispatcher execution and demand:
- Exactly one original IPC-buffer helper dispatch per trial.
- The authentic guest link-return address 0x805208A8.
- Preservation of both original 32-bit low-memory IPC pointer inputs,
  with distinct per-trial values and neighbor canaries.
- Identical copies into guest r13-relative IPC globals; preservation
  of unrelated guest state and original BSS zeroing contracts.
- All previous continuous V26–V33 original CPU register, FPU, cache,
  system-time, interrupt, executable-parameter, performance-register,
  HID4, MEM1 and MEM2 source and native behavior checks.
- No interpreter fallback or unexpected unimplemented native service.

## Private CI

The original-only fixture is built from the exact owner DOL in ephemeral
GitHub Actions scratch, requiring the existing SHA pin and original
call graph. The independent source-only constructor inserts only
the authentic original 24-byte function into previously unoccupied,
NOP-padded guest memory of the existing seven-section Wii fixture.
The fail-closed private geometry check verifies original bytes,
the caller edge, data table, non-overlap and exact stop PC.

The workflow requires all prior checkpoints V26 through V33, then
boot_progress.py --require-progress for V34, expected original entry
0x8000403C and test stop 0x805208A8. Only passing all sixteen native
owner-original trials emits stage=34.

Run in an isolated upstream NWiiRecomp checkout after V29/V18/V20/V26
and the compatible HID4 patch were prepared by earlier continuous steps:

    bash run_v34_continuous_ipc.sh /private/NWiiRecomp /private/NfsMWRelease.dol

No original DOL, ELF, game code, extracted PowerPC bodies, generated
C++ or private logs are committed or uploaded. Bounded native execution
is NOT full original OSInit, a linked native PC game, main(), a
rendered frame, frontend, or gameplay.
