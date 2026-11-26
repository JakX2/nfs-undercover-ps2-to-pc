# Need for Speed: Undercover (Wii/PS2) → Native PC

**An experimental native Windows PC port of the Wii/PlayStation 2 version of *Need for Speed: Undercover*.**

The project's primary approach is **ahead-of-time (AOT) static recompilation of the original Wii PowerPC executable** using [NWiiRecomp](https://github.com/NWiiRecomp/NWiiRecomp), together with a native runtime that recreates the Wii environment the game expects. The aim is to preserve the Wii/PS2 game's behavior while running it natively on PC, rather than substituting the existing PC version or running the game through an emulator.

> **Current status: native executable linked and running bounded original startup code. Not playable yet.** A complete translated executable has been compiled and linked on Linux x64 for private testing. Windows boot, the original game's `main()`, frontend, first rendered game frame and gameplay have not been verified.

## Project status

| Area | Status |
| --- | --- |
| Wii executable analysis | Original Wii DOL and symbol-rich ELF examined in owner-private workflows |
| PowerPC → native C++ translation | Whole-image AOT translation demonstrated with NWiiRecomp |
| Native executable build | Full Linux x64 object build and link verified (411/411 build units); not a Windows release |
| Continuous original startup | Bounded execution from the genuine Wii `__start` (`0x8000403C`) through OS initialization, interrupt handling and SI transfer/callback processing, reaching wireless-ID call classification |
| CPU, memory and Wii OS | Selected PowerPC, exception, interrupt, cache, timer, IPC, filesystem and system-service behavior tested; coverage remains incomplete |
| Hardware compatibility | Selected SI, EXI/SRAM, DSP/ARAM and interrupt paths have runtime implementations or controlled test profiles; full device parity is not established |
| Callback and interrupt return | Original-code register restoration, handler return and RFI verified in focused private tests; continuous integration remains in progress |
| Game `main()` and resource loading | No verified uninterrupted startup into the original game's main loop |
| Graphics, audio and input | Native PC game-facing backends and full compatibility are still development goals |
| Frontend, gameplay and Windows release | Not verified; no playable or installable build |

**A test checkpoint is not a boot.** Native tests may stop deliberately at a known original instruction and use controlled device responses. Passing such a test proves that specific execution path and its assertions, not a complete Wii hardware implementation or a running game.

Track development in [the native recompilation research branch](https://github.com/JakX2/nfs-undercover-ps2-to-pc/tree/research/wii-native-recomp-preflight), [draft PR #36](https://github.com/JakX2/nfs-undercover-ps2-to-pc/pull/36), and [GitHub Actions](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions). The status here summarizes verified work as of **November 26, 2026**; individual experiments and branch commits move faster than this overview.

## How the port is being built

```text
Owner-provided Wii DOL + ELF
             |
             v
   Verify SHA-256 / analyze PPC
             |
             v
       NWiiRecomp AOT
             |
             v
    Native C++ game functions
             |
             +----> PowerPC CPU state and memory runtime
             +----> Wii OS / IOS / IPC / filesystem services
             +----> Selected Wii device/runtime services
             +----> PC graphics / audio / input compatibility (future work)
             |
             v
      Native Linux x64 test executable (verified link)
             |
             v
      Native Windows game (target)
```

**Wii is the current executable baseline.** The PS2 version is relevant to the project's intended game content and compatibility goals, but PS2 binaries are not being presented as already recompilable by the Wii pipeline. Work on the Carbon PC resource bridge is a separate, lower-priority experiment, not the main port architecture.

### Verified development milestones

- **Whole-image translation and native linking:** earlier syntax-only coverage passed 113/113 checks. The later V1160 owner-private run completed all 411 native build units and successfully linked a Linux x64 executable, then launched it through the native runtime. The link itself succeeded even though the subsequent execution test stopped at a failed runtime assertion. [Build and execution evidence](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45768545484).
- **Continuous original startup:** the linked executable ran from the genuine `__start` through original Wii OS and service code, exception dispatch, SI interrupt acknowledgement, completion-helper execution, a third transfer and alarm return, the original indirect callback prologue and system-time calculation. It reached the wireless-ID setter call boundary but did not complete that continuation.
- **Focused original-code tests:** later private tests independently exercised the wireless setter/unlock return, callback suffix, compiler register restoration, handler return and native RFI (return from interrupt). Each of these selected paths passed 16 cases in split mode and 16 in non-split mode, with zero interpreter fallback in those tests. These are not evidence of an uninterrupted boot or blanket fallback-free execution. [Focused verification](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45774586243).
- **Source-only runtime verification:** the held interrupt/callback regression suite reached 568/568 passing isolated synthetic cases at V1206. Newer live integration and handler-return work remains under development; passing this suite does not mean the entire runtime is complete. [Synthetic verification](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45774586243).
- **Earlier OS and System Configuration work:** separate direct-entry `OSInit` and SC pathname-restoration tests remain useful regression references, not substitutes for continuous startup evidence.

### Current startup blocker

The last completed continuous original-code run stopped when the runtime rejected the unchanged wireless-ID setter path. This is a Nintendo SDK controller/SRAM service, not Wii Remote Bluetooth or online multiplayer.

A source-only regression reproduced the exact admission failure using the original patterned synthetic SRAM fixture. A scoped zero-wireless-ID profile passed the corresponding synthetic continuation without changing the other 56 SRAM bytes or pretending that a changed-ID EXI operation succeeded. The [regression results](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45773327881) support the proposed repair; the [continuous original-code retry](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45773050058) has not yet confirmed it as of this update.

Current integration work extends the verified callback and handler return paths toward a genuine interrupt resume and continued game initialization. The changed wireless-ID path and other unimplemented device behavior remain separate compatibility work.

```text
Original Wii entry point
  -> OS and service initialization       [continuous execution verified]
  -> SI interrupt / transfer processing  [continuous execution verified]
  -> Callback prologue and system time   [continuous execution verified]
  -> Wireless-ID call boundary           [continuous execution verified]
  -> Setter / SRAM unlock / return       [focused tests passed; continuous retry pending]
  -> Callback and interrupt return       [focused tests passed; integration ongoing]
  -> Original game main()                [not verified]
  -> First native game frame             [not verified]
  -> Playable Windows port                [not available]
```

The critical measurement is how far **uninterrupted original startup execution** reaches on the path toward `main()`, followed by a genuine first native frame. Internal milestone numbers and synthetic test counts are not percentage-complete metrics.

## Testing and CI

The repository separates two kinds of evidence:

**Public, source-only checks** use independently authored synthetic inputs to test translator/runtime code, checkpoint reporting, script integrity and regression guards. They do not require any retail game files and cannot establish a new original-game boot checkpoint.

**Owner-private original-code checks** stage SHA-256-verified Wii inputs in temporary CI workspace storage, generate translated C++ locally, run native regression tests and report bounded results. Proprietary inputs, generated game code, raw original instruction slices and private traces must not enter public Git history, logs or artifacts.

Useful entry points:

- [`research/native_recomp/`](https://github.com/JakX2/nfs-undercover-ps2-to-pc/tree/research/wii-native-recomp-preflight/research/native_recomp) contains the Wii recompilation research, native runtime helpers, original-free tests and per-stage notes on the research branch.
- [`boot_progress.py`](https://github.com/JakX2/nfs-undercover-ps2-to-pc/blob/research/wii-native-recomp-preflight/research/native_recomp/boot_progress.py) handles exact entry/stop-PC reporting and comparisons without claiming progress from a failed or uninstrumented run.
- [Continuous startup CI](https://github.com/JakX2/nfs-undercover-ps2-to-pc/blob/research/wii-native-recomp-preflight/.github/workflows/wii-continuous-startup.yml), [PowerPC runtime CI](https://github.com/JakX2/nfs-undercover-ps2-to-pc/blob/research/wii-native-recomp-preflight/.github/workflows/wii-ppc-runtime.yml) and [full-image translation probe](https://github.com/JakX2/nfs-undercover-ps2-to-pc/blob/research/wii-native-recomp-preflight/.github/workflows/wii-full-recomp-probe.yml) provide complementary checks.
- [Boot-first runbook](https://github.com/JakX2/nfs-undercover-ps2-to-pc/blob/research/wii-native-recomp-preflight/research/native_recomp/BOOT_FIRST_RUNBOOK.md) explains checkpoint interpretation and the difference between continuous-start and direct-entry tests.

For a source-only checkpoint-driver test after checking out the research branch:

```bash
python3 -m unittest discover -s research/native_recomp -p 'test_boot_progress.py' -v
```

This command tests the reporting driver only. It does **not** launch or recompile *Undercover*.

## Development priorities

1. Resolve the continuous startup blocker, integrate the verified callback/interrupt returns and resume the original execution path.
2. Continue the real Wii `__start` path through remaining OS, IOS and game startup dependencies, replacing controlled device responses with faithful runtime behavior where necessary.
3. Reach the original game's `main()` and resource-loading sequence in a reproducible native build, then validate the Windows host build and runtime.
4. Implement and validate PC graphics, audio and input backends; render the first authentic native frame and bring up the frontend.
5. Validate world loading, physics, handling, AI, career progression and gameplay against the Wii/PS2 game, then package a reproducible Windows release using legally obtained owner-provided game data.

The immediate goal is **working game startup**, not a higher milestone counter.

## Earlier Carbon PC experiments

Before the Wii native-recompilation work became the priority, this repository investigated reusing *Need for Speed: Carbon* PC's resource formats to bring across Undercover PS2/Wii content. That separate work includes eSolid geometry and texture decoding, world-stream comparisons, offline model conversion and a reversible in-game texture-staging experiment.

These experiments did **not** establish a working Undercover world import, native model rendering or playable Carbon-based port. Historical references include [V6 world-stream findings](research/CARBON_PC_POSTSCENE_V6_VARIANT_AND_RA.md), [V9 material coverage](research/UNDERCOVER_PS2_EXTERNAL_MATERIAL_IMAGE_V9.md), and [V12 eSolid header controls](research/UNDERCOVER_PC_V12_NATIVE_ESOLID_HEADER_CONTROL.md). Broader work remains in [draft PR #33](https://github.com/JakX2/nfs-undercover-ps2-to-pc/pull/33).

## Downloads, rights and distribution

This repository is a research and development project. **It does not distribute Nintendo/EA game executables, ELF/DOL files, extracted game assets, proprietary PowerPC instruction dumps, or generated C++ containing translated original game code.** Any owner-original analysis is performed on separately provided files and its public outputs are limited to independently authored code and safe validation summaries.

The private Linux x64 executable is a development/test build, not a distribution artifact. There is currently **no installable or playable native Windows release**. This project is unofficial and is not affiliated with or endorsed by Electronic Arts, Nintendo or the original game's developers.
