# V67: Original Wii `__OSMaskInterrupts` executes natively across interrupt banks

**Scope:** an **isolated direct entry** to authentic `__OSMaskInterrupts` at guest `0x8052693C`, not a continuation from `EXIInit`, `OSInit`, or `__start`. This is not a bootable PC port or an interrupt-controller implementation.

Using a SHA-256-pinned owner-provided Wii executable, the private fixture extracts the complete original PowerPC implementations of `__OSMaskInterrupts` (0x80 bytes), `__RAS_OSDisableInterrupts_begin` (0x14 bytes), `OSRestoreInterrupts` (0x24 bytes), and `SetInterruptMask` (0x25C bytes). None of these proprietary instruction bodies are included in this repository. An explicit, synthetic test syscall at `0x90050000` permits safe return assertions. The original instructions are **not modified**.

## Native execution results

- **176/176 semantic assertions** over twelve guest-mask/interrupt-state combinations; zero PowerPC interpreter fallback, with five expected native function entries.
- **818/818 fail-closed private-image checks** for every authentic and synthetic instruction byte, header/section geometry, SHA-256 of the owner DOL, appended/truncated image, and no output overwrites.
- Optimized C++20, standalone AddressSanitizer/UndefinedBehaviorSanitizer, and a **freshly extracted unmodified NWiiRecomp upstream source** run all passed.
- Confirms low-memory mask update at `0x800000C4`, unchanged `0x800000C8`, return of the previous mask, conditional bank traversal through original `SetInterruptMask`, nested disable/restore, preserved guest MSR, LR, r1, r13 and r29–r31, and stack canaries.
- The test uses **explicitly synthetic MMIO readbacks** to check each original read/write width, address, value and order across zero, full, partial and already-masked scenarios. It does not emulate real Wii register state, EXI device behavior, interrupt delivery, or IOS services.

## Reproduce privately

```bash
bash run_osmask_v67.sh /private/NWiiRecomp-master /private/NfsMWRelease.dol.bin
V67_SANITIZE=1 bash run_osmask_v67.sh /private/NWiiRecomp-master /private/NfsMWRelease.dol.bin
```

The runner applies only prerequisite V15/V26 source patches in its isolated NWiiRecomp checkout and deletes extracted original game instructions, generated game-specific translations, and binaries on exit. Original DOL SHA-256 is required to equal `16a09adcf1987c1f3617d10f3a1cb830f32886afb583f9f8f88e0963ae5fe1f4`.

**Next work:** integrate the original mask helper into the existing directly entered V66 `OSInit` → `EXIInit` path, where the original call at `0x804EFA14` currently stops. Extend EXI register initialization and interrupt-handler registration with bounded MMIO oracles, then recover continuous original `__start` execution (last verified separately at V26 `0x805206B4`). The original game `main`, first frame and gameplay remain unreached. Keep draft PR #36.
