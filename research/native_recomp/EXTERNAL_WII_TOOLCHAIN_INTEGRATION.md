# External Wii recompilation reference and integration plan

## Scope and provenance

The owner's Drive "Existing decomp/recomp tools" folder contains WiiCompiled 0.9.4 ZIP and installer, NWiiRecomp, Dolphin, Aurora and Dawn source ZIPs, GhidraRPXLoader and YAGCD. Inventory checked via Drive metadata. Archive contents and exact archived revisions have not been independently verified. The following public source revisions were inspected separately; no external code was imported.

| Project | Inspected revision | Role |
|---|---|---|
| [WiiCompiled](https://github.com/patchzyy/Wiicompiled/tree/6e41ad0495e9bb6e7c85817392ffc9a6711c38f9) | 6e41ad0495e9bb6e7c85817392ffc9a6711c38f9 | Reference native runtime and independent translator |
| [Aurora](https://github.com/encounter/aurora/tree/f77492f74b0a81895511220bafa6bdc7e8bb9734) | f77492f74b0a81895511220bafa6bdc7e8bb9734 | Candidate native GX, PAD and DVD compatibility layer |
| [Dolphin](https://github.com/dolphin-emu/dolphin/tree/0318069674bbd7971f0db434fe1f7bd9f1c5750e) | 0318069674bbd7971f0db434fe1f7bd9f1c5750e | Hardware behavioral reference, not game execution backend |
| [NWiiRecomp](https://github.com/BlackLineInteractive/NWiiRecomp/tree/595f176f1d24cc54ff2e8389feed12d7fb553cc2) | 595f176f1d24cc54ff2e8389feed12d7fb553cc2 | Existing pinned primary translator/runtime |

## Priority order

1. Keep continuous original Wii startup as the main execution lane. Compare the existing NativeIosTransport, IosBus, StmIos and yield scheduler against Dolphin HW/WII_IPC.cpp, HW/ProcessorInterface.cpp, IOS/STM/STM.cpp and IOS/FS. Check ACK/reply ordering, masks, event completion and request buffers. Do not replace the already implemented low-level native mailbox with an immediate-return API merely to pass a milestone.
2. Use WiiCompiled runtime/src/hle/os/os_scheduler.cpp, os_sleep.cpp, os_context.cpp and os_thread.cpp as references for guest-thread/host-fiber integration. Its scheduler uses game-specific addresses and layout assumptions; recover Undercover equivalents from the private ELF. Preserve guest save/restore and IRQ semantics. Prioritize one actual sleep/ACK/wakeup sequence over a large new suite of mock-only witnesses.
3. Compare IOS async completion and storage behavior in runtime/src/hle/ios.cpp, storage/nand_isfs.cpp, nand_async.cpp and dvd.cpp. Use documented interface behavior to independently implement the missing devices. OS reporting reference: os/os_report.cpp, particularly guest variadic integer alignment and FPR handling. Do not silently hook original report functions as a workaround for witness failures.
4. In parallel when practical, evaluate Aurora's GX compatibility layer as an optional native rendering backend. Inspect WiiCompiled runtime/src/hle/gx/gx_fifo.cpp and gx_dl.cpp as architectural references: source-level GX APIs alone do not accept arbitrary translated FIFO/display-list writes. Bridge the current NWiiRecomp FIFO parser and GX state to Aurora with explicit endian, pointer, texture, TEV and EFB semantics. Start with an original-free textured triangle and display-list readback, then an original game draw; do not claim first game frame from a synthetic draw. Dawn provides the WebGPU implementation, not a separate Wii runtime. Check pinned dependency compatibility and Windows build requirements before importing.
5. Use WiiCompiled's projects/examples/generic-dol.yml for an optional independent translation comparison of a bounded original DOL span with authenticated ELF function map and correct SDA bases. Its generic translator is not a generic complete playable runtime. Do not switch the primary translator or enable unsupported-instruction acceptance for production.
6. Compare AX/DSP audio after identifying the actual game sound path. WiiCompiled runtime/src/hle/audio and Dolphin HW/DSPHLE/UCodes/AXWii.cpp are useful reference points. The game may use a different microcode/backend. GhidraRPXLoader is for Wii U RPX, not this Wii DOL/ELF; YAGCD covers shared GameCube hardware but not the full Wii IOS architecture.

## License gate

WiiCompiled's inspected LICENSE is GPLv3. Dolphin is GPL-family; inspect file-specific notices before reuse. The pinned NWiiRecomp has a custom modified MIT license with commercial restrictions, not standard MIT. Direct GPL code incorporation into that combined runtime may be incompatible; resolve licensing before any copy/link distribution. Aurora itself is MIT licensed; preserve its notice and audit third-party dependencies. Use independently authored implementations based on documented behavior and tests where direct reuse is not licensed compatibly. This note does not authorize importing third-party or Nintendo proprietary code.

## Verification boundary

No changes to the translator, startup witness, build dependencies or guest code in this audit. No claim that any archived tool has been built, installed, or integrated. All original binaries, assets, generated code and private fixture material remain owner-local. Continue the full-image execution gate and use external references to fix actual blockers, not to inflate milestone counts.
