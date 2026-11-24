# V525: original EXI ID verified and complete-image SI continuation

## Verified original execution

* Linux V507 [45340033230](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45340033230): SHA-verified DOL/ELF, 27,941 ELF function symbols, 112 ephemeral translation shards, syntax 113/113, linked Linux x64, V504 EXI ID stages=13, fallback=0, verified=1. Actual scheduled synthetic device command and response, guest cache copy and unlock are established; the device profile is explicitly synthetic, not a claim of real hardware identity.
* Windows V516 [45342083001](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45342083001): linked Windows x64, V500 original EXI handler stages=12, prior polling=1, fallback=0, verified=1. Strict loader equivalence and bounded launch verified.
* Native SI profile and correct MMIO/controller ownership V518/V519 passed their pinned-runtime jobs [45342249671](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45342249671), [45342341946](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45342341946).
* None of the above establish full EXIInit return, complete SIInit, full OSInit, first frame, main or gameplay.

## Changes in this session

| Version | Change | Evidence |
| --- | --- | --- |
| V520 | Read-only original EXI version tail to SIInit, SI version tail, cold packet slots and sampling-rate entry | [Source-only suite passed, including 12 C++ negative controls](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45343216904) |
| V521 | Complete-image os-si-entry Linux scope; V515 native tick emitter, V512 SI MMIO, V518 explicit four-port absent profile, inherited EXI device profile and verification | [Owner run queued](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45343275397) |
| V522 | Explicit 16-bit native VI clock register and strict access; 0=27 MHz, 1=54 MHz; no VI timing or display generation | [Pinned runtime test](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45343393954) |
| V523 | Windows complete-image os-exi-id next boundary | [Owner run](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45343470660) |
| V524 | Original sampling-rate, TV format and XY calls; native clock read, polling write, idle read and TC acknowledgment; IRQ installation/unmask and first SI type-query entry | [Source-only tests](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45343599846); candidate not yet wired to owner scope |
| V525 | Verify V524 observers against actual pinned runtime MMU and real modeled device register operations for both clocks and 12 negative controls | Candidate CI |

V522 hardware reference: [YAGCD section 5.3](https://hitmen.c02.at/files/yagcd/yagcd/chap5.html), VICLK at 0xCC00206C. A clock selection register is not an implemented video interface or display backend.

The V513 absent-card owner run [45340918843](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45340918843) remains independent. The existing V521 pending run must not be displaced by V524 before its predecessor is evaluated. NAND V517 successor-guard owner replay [45342147666](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45342147666) remains outstanding. V508 authenticated historical ACK; it did not complete NAND initialization.

## Next original boundary

Once V521 verifies, enable a separate os-si-sample scope with explicit cold VI clock=0 and the SI profile. Inspect V524 source-only and V525 pinned tests before launching. Verify original IRQ handler install and actual PI mask update, then extend through original first SIGetType/SITransfer and queued controller queries. Earlier reduced V59 fixture showed one immediate transfer and three queued packets with an explicit synthetic delay guard; the complete-image scope must not rely on that guard. The pinned runtime already initializes Wii bus/CPU clocks and timebase frequency; validate actual guest timestamps and alarm paths rather than inject them.

Keep owner binaries, assets, translated original code, symbol tables and private logs ephemeral. Report bounded verification separately from a full game boot.
