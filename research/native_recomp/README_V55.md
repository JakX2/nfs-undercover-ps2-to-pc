# V55: Original Wii `__OSInterruptInit` executes its complete seven-bank mask loop

**Verified milestone: source-grounded original Wii PowerPC native execution from the original `__OSInterruptInit` entry. This is not full original `OSInit`, a continuous original `__start` boot, or a hardware-accurate Wii interrupt controller.**

## Original execution covered

This milestone advances the V50 isolated original `__OSInterruptInit` execution beyond V53's mask-prologue test stop at `0x80526698`. Starting directly at the **original `__OSInterruptInit` at `0x8052661C`**, the following authentic game instructions execute under NWiiRecomp-generated C++:

- The real `memset` at `0x8000443C` and `__fill_mem` at `0x80004388` clear the 128-byte guest interrupt-handler table and initialize its original `r13`-relative table pointer.
- The original interrupt mask globals at guest `0x800000C4` and `0x800000C8` are initialized; the native test records both original initial 32-bit MMIO writes.
- The original `__RAS_OSDisableInterrupts_begin` at `0x805265AC` returns the previous guest MSR EE state and clears the EE bit while preserving other guest MSR bits.
- The original `__OSInterruptInit` loop at `0x80526698`, `0x8052669C`, `0x805266A0`, `0x805266A4`, and `0x805266A8` calls the **entire original 604-byte `SetInterruptMask`** at `0x805266E0` **seven times**, iterating from `0xFFFFFFF0` through seven successively cleared mask banks to zero.
- Exactly **14 MMIO events** occur per normal execution: **five register reads and nine writes**. The independent numeric oracle verifies address, width (16 or 32 bits), operation type, value and order for every event, in addition to stack and callee-save register state, low-memory canaries, MSR, GPRs and the byte-for-byte zeroed interrupt table.

The fixture uses only instructions read from the owner's SHA-256-pinned original Wii DOL. The **single test-only terminal `sc; blr`** at `0x805266AC` stops **before** the original `OSRestoreInterrupts` call. This boundary is intentionally NOT claimed as a complete interrupt initialization or native runtime hardware model. MMIO callbacks supply deterministic synthetic register values and record writes; no interrupt delivery, IRQ acknowledgement, asynchronous scheduling or controller state machine is implemented.

The native analyzer includes **six entrypoints:** the five authentic original Wii functions (`__OSInterruptInit`, `SetInterruptMask`, `__RAS_OSDisableInterrupts_begin`, `memset`, and `__fill_mem`) and the synthetic test stop. No interpreter fallback is used on tested paths.

## Verification

- **1,299/1,299 native semantic assertions** across eight guest MSR configurations, including both initial enabled/disabled EE states.
- **312/312 SHA, all-original-and-test-instruction mutation, DOL segment metadata, truncated/appended fixture, and safe-output guards**. Mutation cases must fail before generating derived C++.
- Native harness passed in **optimized C++20**, **ASan/UBSan**, and a **freshly unmodified NWiiRecomp upstream ZIP** using the prerequisite original-free V15 dispatcher and V26 syscall-PC patch scripts.
- The private DOL is built and destroyed in a temporary directory by `run_irqmask_loop_v55.sh`. No original game DOL, ELF, asset, instruction body or owner-derived emitted C++ is included in source control or the source-only ZIP.
- Original user-owned Wii DOL SHA-256: `16a09adcf1987c1f3617d10f3a1cb830f32886afb583f9f8f88e0963ae5fe1f4`.

Run against your own owner-original DOL and a dedicated NWiiRecomp checkout:

```sh
bash run_irqmask_loop_v55.sh /private/NWiiRecomp-master /private/NfsMWRelease.dol.bin
V55_SANITIZE=1 bash run_irqmask_loop_v55.sh /private/NWiiRecomp-master /private/NfsMWRelease.dol.bin
```

## Next technical work

1. Integrate the verified IRQ loop back into the V53 **direct-`OSInit`** path, preserving its previous exception, system-call, alarm and module regressions. Resume at `0x805266AC` with original `OSRestoreInterrupts` and exception handler registration at `0x805266C0`, then finish `__OSInterruptInit` return into the rest of `OSInit`.
2. Develop Wii MMIO/device state semantics rather than using the current deterministic owner-private test callback recorder, before claiming real native interrupt operation.
3. Connect the longer direct-`OSInit` chain to **continuous original `__start`**. That separately remains bounded at V26 `0x805206B4` and still requires five missing V26 source-only harness files to reproduce its historical milestone.
4. Continue toward genuine original game `main`, actual first frame, frontend, world loading and gameplay. No complete Windows native boot has yet occurred.

Keep GitHub PR #36 draft; preserve the parallel Carbon PC adaptation and do not publish copyrighted game-derived code or binaries.
