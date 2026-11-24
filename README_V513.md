# V513 — EXI device discovery and native serial-interface groundwork

## Authenticated original execution (2026-11-24)

- Linux V500: original EXI initialization completed four native CSR writes and installed eight IRQ handlers before entering uncached EXIGetID. All 113 generated translation syntax checks passed; 112 private shards, 12/12 witness stages, zero interpreter fallback. [Owner run](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45337663816).
- Windows V486: linked x64 executable passed all four original context-initialization stages and reached the second cache initializer, zero fallback. [Owner run](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45337663813).
- These are bounded original execution witnesses, not completed OSInit, full boot, a rendered frame or gameplay.

## V507–V513 changes

| Version | Implementation | Evidence |
| --- | --- | --- |
| V507 | Linux os-exi-id, native scheduler before translation and explicit profile after translation; synthetic test device ID, RTC and SRAM data, not an asserted console identity | [Full owner build](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45340033230) running |
| V508 | NAND historical IRQ acknowledgment witness: latch verified W1C event and verified successor once each, retain ordering and original downstream guards; keep final IRQ snapshot diagnostic | [Original-free tests passed; owner replay running](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45340216490) |
| V509 | Windows os-exi-id support; native instruction ticks mandatory for profile path; default owner scope advances to os-exi-poll | [Windows synthetic passed; owner running](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45340319188) |
| V510 | Original absent-card probe witness for channels 0/1, native CSR presence reads, zero return values, timestamp clears, preserved ID cache and entry into OSRegisterVersion; no invented replies or writes | [Geometry, probe composition, audit and 12 negative controls passed](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45340531886) |
| V511 | Native SI cold sampling, communication registers, 128-byte big-endian RAM, explicit request tokens and completion, per-channel errors, W1C, shared PI IRQ | [24 explicit transfer cases passed](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45340692607) |
| V512 | Opt-in native SI binding to Wii MMIO aperture and mirror, strict integer widths/alignment, PI refresh without disturbing unrelated interrupt owners | [Pinned actual runtime passed](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45340830028) |
| V513 | Independent Linux os-exi-absent owner scope; retains existing EXI ID scope and profile contract | [Queued owner build](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45340918843) |

Earlier V504/V505 regression evidence: [ID witness and profile writer tests](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45338579249), including 12 negative controls. V506 [owner evidence](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45338504587) established successful historical ACK, verified successor, ordered callback history and failed final snapshot; it does not establish why the IRQ changed later. V508 tests the lifetime distinction without changing guest code or supplying fabricated IRQ state.

## SI limitations

SI is a cold controller-interface model and MMIO binding, not a complete controller or periodic polling implementation. No controller endpoints, VI-based periodic sampling, game input, or owner-original SI initialization have been verified. The opt-in binding is off by default. Native completion requires an explicit token and response; polling cannot manufacture completion. GameCube aliases and unsupported register access are rejected.

Hardware references: [WiiBrew Serial Interface](https://wiibrew.org/wiki/Hardware/Serial_Interface), [Processor Interface](https://wiibrew.org/wiki/Hardware/Processor_Interface), [YAGCD hardware](https://hitmen.c02.at/files/yagcd/yagcd/chap5.html).

## Next verification boundary

Finish the independent original EXI ID transaction, including guest cache store and unlock; then verify absent-card probes and version-registration entry. Preserve the independently tested prefix on both platforms. Only advance to original SI initialization once the EXI path is verified. Investigate NAND replay's next genuine stop without bypassing the existing downstream guest guards.

No original game binary, asset, generated private translation or raw private owner log belongs in the repository. All results above distinguish independent runtime tests, authenticated bounded original execution and pending owner verification.
