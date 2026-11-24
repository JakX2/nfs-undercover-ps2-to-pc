# V477–V481: complete-image exception initialization and native IRQ banks

2026-11-24. Branch: `research/wii-native-recomp-preflight`.

## Authenticated owner execution

* [Windows original first vector, run 45328707080](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45328707080): native PE/x64 link, strict DOL loader equivalence, IPC predecessor, six prelude checkpoints and all four first-vector stages verified. Zero interpreter fallback. This brings Windows to the previous Linux frontier.
* [Linux complete exception pack, run 45328136774](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45328136774): the original complete-image startup executed all 15 exception-vector copies, the syscall overlay and original exception epilogue, then reached alarm initialization. All 113 generated translation syntax checks passed. Zero fallback. Alarm entry is not alarm completion.
* [V471 owner NAND, run 45328558334](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45328558334): restored a 48-word exact original function. Prior missing span and NOP repairs verified. The selected original callback now executes BLR and resumes its original caller. 25 distinct observed entry spans, 25 original; no remaining non-original observed entry. The later diagnostic process still aborts with rc=134 at call 44, so NAND init and full guest boot are not proven.
* [V475 pinned runtime, run 45329574082](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45329574082): real MMU/PI/IPC wrappers, Hollywood mask and alias readback, exact two-write sequence, original-free negative controls all passed. No scheduling or IOS service result was fabricated. [V476 source-only tests](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45329652685) passed.

## New changes

- V477 `cfe6b5bc09e896ee8732bfd82d6418a8fdb9fb5d`: promote Windows default owner scope to full exception pack. Separate alarm, IRQ-table and IRQ-MMIO contracts with exact log and launch-flag isolation. [Windows pack run 45330660533](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45330660533).
- V478 `cd69264881206971d2790bccb7801b6df2ca394e`: classify the actual NAND post-BLR terminal failure. A narrow one-shot continuation is eligible only if the original direct link and intact caller/callee spans authenticate, the private log proves an obsolete region stop, and the exact old public assertion matches. Otherwise preserve the stop and report sanitized category. Original-free tests passed; [owner run 45330765282](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45330765282).
- V479 `23550e0fce1a94a1dde655dad2d3e2f9ab335f0c`: select complete-image Linux `os-mmio` scope and pass the native IRQ bootstrap environment only in this scope. Existing `os-vector`, `os-pack`, `os-alarm`, `os-irq` scopes remain separately selectable. [Queued owner run 45330878839](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45330878839), behind active [alarm/IRQ table run 45329217660](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45329217660).
- V480 `9d958245e514f12b2a5547de9984cf12d03d60ff`: independent register-level MI mask/status, EXI CSR control/mask/status/presence and stopped Wii AI control/status models. Pending bits persist while masked and W1C is explicit. Shared PI ownership only for the modeled sources; unrelated bits, including Hollywood, are preserved. The MI mask is a bounded five-bit source model, not full memory-protection semantics. No device events are spontaneously invented.
- V481 `5dfe26df46391610285cde8da243cbe6d0b43adb`: optional CPU-thread bindings to the real pinned MMU and hardware wrappers after V475. Exact widths, physical/cached/uncached/mirrored aliases and PI refresh; reject unsupported EXI and AI accesses. [Pinned test run 45331144348](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45331144348) pending at this writing. Not yet selected by a complete-image owner scope.

## Public hardware references

- https://wiibrew.org/wiki/Hardware/Memory_Interface
- https://wiibrew.org/wiki/Hardware/External_Interface
- https://wiibrew.org/wiki/Hardware/Audio_Interface
- https://wiibrew.org/wiki/Hardware/Processor_Interface

The Wii AI control register uses the Wii CD aperture rather than the upstream GameCube-only CC aperture. The EXI channels have separate mask and latched W1C status fields. The current cold models deliberately do not implement EXI transfer/data/SRAM/RTC, memory protection, active audio playback or sample timing.

## Next work

Await the active owner alarm/IRQ-table evidence before changing that path. Integrate V481 only after the real wrapper tests pass; verify original interrupt-disable return and the seven-bank SetInterruptMask loop, then the original restore and exception-handler registration followed by OSInit resume. Diagnose V478 actual post-return stop before allowing broader NAND progression. Keep all owner originals, generated code, raw private logs and executables private and ephemeral. None of complete OSInit, original main, rendering, or gameplay has been verified.
