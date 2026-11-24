# V551–V553: NAND successor history, native ARAM DMA groundwork

## Verified evidence

- [V542 private original callback replay](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45424690450) completed the audit: `V542_FRAME_RESULT rc=134 begins=1 blr=1 resume=1 nested=2 max_calls=44 unique=25 original=25 first_nonoriginal=none boot_verified=0 history=1 final_clear=0 successor=1 legacy_stop=0`. The next exact public guard is 1242, traced to V391/V392 post-ACK successor checks. This is an audit success, not a completed NAND init or game boot.
- [V550 thread witness checks](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45426881769) passed original-free geometry, composition and gate tests, plus sanitizer runs covering 32 SI sampling, 20 SI discovery and 18 thread initialization negative controls.
- [Earlier Windows native owner build](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45424294180) linked the complete translated executable but stopped at the superseded SI checkpoint, 5/6, rc=106, fallback=0. The V546 correction requires flag zero during all four original queries and one only after SIInit return; the corrected Windows run is in progress.

## New source

- V551 is a **conditional** diagnostic/replay for guard 1242. The original V391 event must be unique, ordered after the authenticated V390 event, verified, owner-classified, and not a bounded non-owner stop. The previous V542 abort must match the exact public V391 guard. Only then is a historical boundary check substituted for the stale final PC/LR comparison, which remains a diagnostic. The event-time checks and subsequent guards remain. No guest state is changed. If the event is absent or invalid, no candidate is accepted.
- V552 implements bounded Wii MEM1/MEM2 ARAM DMA with explicit tick latency, 32-byte copies, bidirectional transfers, range checks, W1C completion latch and DSP PI bit ownership. It is a restricted mode-3 model, not a general DSP controller.
- V553 adds exclusive opt-in ARAM MMIO ownership, strict access widths, native instruction-boundary scheduling, and synthetic generated-PPC tests for both split and nonsplit emission paths. No game bytes are needed for those tests. There is no main/runtime activation in the original boot lane yet.

### Hardware references

- [WiiBrew DSP hardware](https://wiibrew.org/wiki/Hardware/DSP)
- [WiiBrew memory map](https://wiibrew.org/wiki/Memory_map)
- [WiiBrew PI](https://wiibrew.org/wiki/Hardware/Processor_Interface)
- [Dolphin DSP hardware implementation](https://github.com/dolphin-emu/dolphin/blob/master/Source/Core/Core/HW/DSP.cpp), consulted for Wii EXRAM backing and register behavior; V552 is independently written bounded code. Timing is a synthetic instruction-visit profile, not the hardware's measured cycle timing.

## Pending verification

- [Corrected Linux owner startup](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45426293326)
- [Corrected Windows owner startup](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45426502167)
- [V551 private replay](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45427637226)
- [V552 standalone DMA regression](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45427928478)
- [V553 generated native ARAM regression](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45428251593)

At this checkpoint these jobs had not completed. Original SRAM return, original thread return, audio clock/DSP bootstrap, full OSInit, main, frontend, frames and gameplay remain unverified in the complete-image lane. The V553 exclusive DSP register owner deliberately rejects reset/mailbox/audio accesses; full DSP register composition and timing are next requirements before original activation.
