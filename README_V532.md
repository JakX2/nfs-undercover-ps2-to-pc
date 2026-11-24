# V532: original EXI return, SI entry and cold discovery continuation

## Confirmed original complete-image execution

* V513 Linux [45340918843](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45340918843): V510 original removable-card discovery, stages=8, prior ID=1, fallback=0, verified=1.
* V521 Linux [45343275397](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45343275397): V520 original EXI version tail and return, original SIInit version tail and initialization of four packet slots, SI sampling-rate entry, stages=6, fallback=0, verified=1. Complete original DOL translated and linked; this proves bounded original startup, not full OSInit or game boot.
* V523 Windows [45343470660](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45343470660): original EXI ID stages=13, handlers=1, fallback=0, verified=1.
* V524 [45343599846](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45343599846): source-only tests passed, both VI clock selectors and 24 negative controls. V525 [45343760903](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45343760903): actual pinned VI/SI MMIO observer order passed both selectors and twelve negative controls.
* V517 NAND [45342147666](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45342147666): bounded replay completed its audit; guest still aborted at known guard 1237 (rc=134). The workflow did not publish the V517 successor rows. Do not infer a resolved NAND path from workflow success.

## Changes

| Version | Scope | Evidence |
| --- | --- | --- |
| V526 | Linux complete-image SI sampling and IRQ setup with explicit VI clock=0 and absent SI ports | [Owner build](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45421009588); source-only gate passed, owner translating |
| V527 | Independent Windows absent-card and SI-entry scopes; exact inherited EXI and SI profiles, corrected native ticks | [Windows run](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45421104304); all scope pairs and synthetic Windows executable passed, owner run underway |
| V528 | Publish only bounded V517 successor guard ID, class and validated public source locations; never raw owner log | [NAND replay](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45421320861); original-free job passed, owner running |
| V529/V530 | Original cold SIInit query/transfer/start call census, four channels, one actual scheduled NOREP, three queued guest packets, return to SRAM entry | [Source-only tests passed](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45421761523), 17 negative controls; owner scope not yet launched |
| V531 | Native generated PPC exercises the exact discovery observer MMIO and scheduler hooks, split and nonsplit, 7 negative controls | [Pinned runtime job passed](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45421978125), both emission modes, ASan/UBSan, seven negative controls per mode, no fallback |
| V532 | Compose native dcbi data-cache trace/fence support after V456, exercise both RA forms, aliases, nonmutation, bounded trace and all existing cache operations | [Generated-code tests passed](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45422212965), both emission modes, ASan/UBSan, 8 valid and 3 invalid cache trials per mode, no fallback |

## Verification boundaries and remaining work

The complete-image SI entry contract stops before SI sampling. V526 stops at first SIGetType entry, not at SIInit return. V529 requires EE disabled during the cold query sequence. Its explicit absent profile must produce exactly one native no-response completion (not a guest callback), and original guest code must queue three additional type queries. No guest callback or delayed alarm path is bypassed; unexpected interrupt, callback or delayed alarm entry rejects the candidate.

The V529 observer accepts either zero or the channel-zero W1C mask at the cold status clear because both preserve the authenticated zero status. Subsequent command/control geometry and the final NOREP/TC/PI latch are checked precisely. The fixture uses native instruction latency rather than claiming cycle accuracy. Native input polling, live controller devices and full guest interrupt delivery remain future work.

V532 passed its independent generated-code tests and is ready as a candidate for the next SRAM DMA boundary. The existing full-image V456 emitter treats dcbi as an unimplemented cache hint; the new composition emits the existing V60 data-cache trace and host ordering without modifying RAM. It does not emulate actual cache contents. Install it in the later SRAM scope; leave the active V526 build unchanged.

After V526 and V531 are verified, enable the separate Linux SI-return scope, then authenticate the original SRAM read-only DMA and return using nonzero explicit host SRAM payload. Preserve all original-image data and binaries privately. The first rendered frame, original main, frontend and gameplay remain unverified.
