# V482–V486: native IRQ return and context initialization

2026-11-24. Branch `research/wii-native-recomp-preflight`.

## Newly authenticated complete-image results

- Linux [V474 owner IRQ-table scope 45329217660](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45329217660): `V473_IRQ_CENSUS rc=0 alarm=1 stages=5 fallback=0 verified=1 boot_verified=0`. All alarm and module stages plus original IRQ table memset return completed. All 113 translation syntax checks passed. Stops before PI/Hollywood mask writes.
- Windows [V477 complete exception pack 45330660533](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45330660533): `V426_WINDOWS_LINK linked=1 platform=windows-x64 synthetic=0 boot_verified=0`; `V466_PACK_CENSUS rc=0 first_vector=1 vectors=15 syscall=1 alarm=1 fallback=0 reason=0 verified=1 boot_verified=0`; `V429_WINDOWS_OWNER_SCOPE scope=os-pack verified=1 boot_verified=0`. Original exception initialization returned and alarm entry reached. No boot claim.
- NAND [V478 owner 45330765282](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45330765282): V471 return proof reproduced with 25/25 original distinct entries, BLR and resume. `V478_NAND_FRONTIER calls=44 original=25 resumed=1 owner=0 edge=direct_link category=public_guard ready=0 boot_verified=0`. The exact-edge exception to the region observer was correctly not installed. Diagnostic abort persists; its precise public label was not previously reported.

## Implementation

- V482 `55b0c5b`: read-only transaction witness for the seven original interrupt-mask banks. Validates each actual read/write value, order, width, native/legacy backend identity, final mask readback, restore argument, dispatch handler and context entry. The code does not set any guest PC or modify guest state. Follow-up `8f89e89` instruments native IOS reads/writes too and adds real pinned DSP/PI/MI/EXI/AI integration. Original-free [pinned wrapper run 45332926757](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45332926757) and [rerun 45332973175](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45332973175) passed. The POSIX select name collision in the synthetic test was corrected at `2a0933a`. [Source suite 45332973134](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45332973134) passed, including 50 negative controls and V483 geometry, composition, log gate and MMIO-transform checks.
- V483 `db3d4cc`: prepare privately authenticated original IRQ return call/BLR geometry, compose V476 with V481 and V482. Stop at original OSContextInit entry only after seven banks, restore and vector-4 handler registration complete.
- V484 `973d1b1`: Linux and Windows selectable `os-irq-return` mode with explicit bounded native IRQ/MMIO and cold bank flags. Predecessor scopes remain independent. Windows push default now `os-irq`, since original pack passed. [Linux IRQ return queued 45333067322](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45333067322) behind active [Linux V476 MMIO 45330878839](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45330878839). [Windows IRQ table 45333067332](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45333067332).
- V485 `27ef622`: strict known-source guard labels, numeric catalog ID, actual stop and guest-exit census only; unknown exception text is never emitted. No change to the original route. [NAND diagnostic owner run 45333157740](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45333157740) running; original-free job passed.
- V486 `158e2ea`: authenticated context initializer candidate after IRQ return. Extract private stack-frame size from original prologue, verify context handler setter and debug leaf callsite, preserve other dispatch entries and neighboring low-memory words, verify current-context word clear and native return to original cache initialization entry. [Source run 45333318665](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45333318665) pending at writing. Not yet wired into owner scopes to avoid superseding the queued V483 owner run.

## Next steps

1. Inspect the active V476 owner outcome before changing its assumptions. Do not claim IRQ hardware register writes executed in the whole image until its census passes.
2. Run the new complete-image V483 IRQ return scope, preserve V476 as an independently selectable control. Fix actual failures instead of increasing a cap or forcing a guest branch.
3. After source tests and the IRQ return owner job pass, wire the V486 context continuation; then cover original cache init L1/L2 paths.
4. Use V485 to identify the actual NAND abort label before authorizing any further continuation.

The cold MI/EXI/AI implementation is not full device emulation, and no audio playback, EXI transfers, SRAM, OSInit completion, original main, first frame or gameplay is proven. Keep all game code, raw logs, private ELF/DOL, generated C++, and binaries private.
