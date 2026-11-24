# V493–V498: complete IRQ return and native EXI devices

2026-11-24. Branch `research/wii-native-recomp-preflight`.

## Authenticated complete-image progress

- [Linux IRQ return owner 45333067322](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45333067322): `V483_IRQ_RETURN_CENSUS rc=0 mmio=1 stages=11 banks=7 fallback=0 verified=1 boot_verified=0`; `V483_IRQ_RETURN_AUDIT inspected=1`. 112 private generated C++ shards, 113/113 syntax checks. The genuine seven-bank mask loop, interrupt restore, exception-vector handler registration and native return to context initializer entry are verified. No guest instruction was replaced to force the return.
- [V491 source-only 45334849734](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45334849734): private geometry, probe composition, log audit and 10 negative controls passed, not yet a complete-image EXI poll.
- [Linux context scope 45334216118](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45334216118) is active. [Windows MMIO scope 45334215957](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45334215957) is active. [NAND V492 scope 45335019979](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45335019979) is active. Preserve all original-code artifacts privately.

## Native EXI runtime

- V493 `fb01c75`: optional physical-RAM-backed DMA in the native EXI controller. Explicit request geometry, token, transfer direction, RAM range and completion. Normalize original cached/uncached guest MAR aliases without permitting MMIO, bit-30 aliases, wraparound, empty or oversized spans. RAM remains unchanged until the endpoint explicitly completes a validated read. DMA writes expose the requested bytes to the endpoint, with no fabricated response. [Pinned test 45335467564](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45335467564) passed 36 DMA cases across MEM1/MEM2 and aliases.
- V494 `815e55f`: independently authored MX23L4005 subset. Host supplies the 64-byte SRAM image and RTC seconds in the console epoch. RTC data is latched at the original command; SRAM supports immediate read/write and explicit DMA read. Device ID endpoint separately requires a configured response. No real device ID asserted from synthetic fixtures, no ROM/font/UART emulation, no SRAM file persistence yet. [Pinned test 45335590696](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45335590696) passed.
- V495 `de4c660`: CPU-thread endpoint scheduler with explicit nonzero instruction-visit latency, monotonic time, chip-select epoch reset and exact transfer-token completion. No read of EXI CR can advance work. [Pinned test 45335673008](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45335673008) passed the controller, DMA, device and scheduler suites.
- V496 `5085919`: add independent `os-cache-reuse` and `os-exi-poll` complete-image scopes for both platforms. Select EXI poll for next Linux push-triggered owner build; Windows default advances to verified Linux IRQ-return boundary. [Linux EXI scope 45335771952](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45335771952) and [Windows IRQ-return scope 45335771911](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45335771911) queued behind predecessors.
- V497 `713c15c`: reversible, opt-in native emitter extension immediately after the V438 instruction-label counter, and thread-local RAII CPUContext scheduler binding. [Pinned test 45335848038](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45335848038) passed, using actual MMU wrappers and PI: SRAM command, 64-byte DMA, interrupt acknowledgement, and no transfer completion from repeated reads or unbound ticks. Both emitter and runtime patch idempotence passed. No automatic endpoint attachment to the complete-image owner route.
- V498 `08b74d7`: original-free test compiles actual NWiiRecomp-translated synthetic PPC loop in both split and nonsplit modes and exercises the device scheduler from emitted labels instead of manually invoking tick. [Run 45335945541](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45335945541) in progress at writing.

Protocol references: https://wiibrew.org/wiki/Hardware/External_Interface ; https://wiibrew.org/wiki/Hardware/RTC-SRAM-ROM ; https://hitmen.c02.at/files/yagcd/yagcd/chap10.html . The scheduler is instruction-visit based, not a timing-accurate Broadway bus clock.

## Next work

1. Inspect the actual context, Windows MMIO and NAND results. Do not promote later original-code stages without verifying their prefixes.
2. Preserve separate owner scope for EXI cold polling; then authenticate original EXI interrupt-mask/handler registration and ID transaction.
3. Wire explicit host profile/clock/SRAM persistence and the V497 scheduler into a separate complete-image device scope. Use real hardware/documented behavior for unused EXI slot response and hardware-revision MMIO; do not claim the synthetic endpoint ID matches a retail Wii.
4. Continue to original SRAM initialization, then remaining OSInit services. The native Windows executable links and runs original code but complete OSInit, main, first frame and gameplay remain unverified.
