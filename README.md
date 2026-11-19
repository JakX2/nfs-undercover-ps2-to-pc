# Need for Speed: Undercover (Wii/PS2) → Native PC

**An experimental native Windows PC port of the Wii/PlayStation 2 version of *Need for Speed: Undercover*.**

The project's primary approach is **ahead-of-time (AOT) static recompilation of the original Wii PowerPC executable** using [NWiiRecomp](https://github.com/NWiiRecomp/NWiiRecomp), together with a native runtime that recreates the Wii environment the game expects. The aim is to preserve the Wii/PS2 game's behavior while running it natively on PC, rather than substituting the existing PC version or running the game through an emulator.

> **Current status: research and active development. This is not a playable port.** There is no downloadable Windows game build, working frontend, rendered game frame, or verified gameplay yet.

## Project status

| Area | Status |
| --- | --- |
| Wii executable analysis | Original Wii DOL and symbol-rich ELF examined in owner-private workflows |
| PowerPC → native C++ translation | NWiiRecomp AOT translation exercised; whole-image translation and C++ syntax checks demonstrated, but not a complete linked game |
| Continuous original startup | Authenticated, bounded native execution from the Wii `__start` entry (`0x8000403C`) through substantial Wii OS initialization and later service paths |
| Wii OS and runtime | Selected CPU, memory, interrupt, cache, IPC, filesystem and system-service paths tested; device support remains incomplete |
| System Configuration (SC) | Original-data restoration verified in a focused owner-private test; newer nonempty-path continuation remains experimental |
| Game `main()` | Not reached in a verified full startup |
| Rendering, frontend and gameplay | Not implemented or verified as a working Windows game |

**A test checkpoint is not a boot.** Native tests may stop deliberately at a known original instruction and use controlled device responses. Passing such a test proves that specific execution path and its assertions, not a complete Wii hardware implementation or a running game.

Track development in [the native recompilation research branch](https://github.com/JakX2/nfs-undercover-ps2-to-pc/tree/research/wii-native-recomp-preflight), [draft PR #36](https://github.com/JakX2/nfs-undercover-ps2-to-pc/pull/36), and [GitHub Actions](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions). The status here summarizes verified work as of **November 19, 2026**; individual experiments and branch commits move faster than this overview.

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
             +----> Graphics / audio / input compatibility (future work)
             |
             v
      Native Windows game
         (long-term goal)
```

**Wii is the current executable baseline.** The PS2 version is relevant to the project's intended game content and compatibility goals, but PS2 binaries are not being presented as already recompilable by the Wii pipeline. Work on the Carbon PC resource bridge is a separate, lower-priority experiment, not the main port architecture.

### What has been demonstrated

- Authentic original Wii PowerPC functions have been translated to native C++ and executed in owner-private tests. The continuous-startup lane begins at the game's genuine `__start`, not an artificially entered downstream function.
- Startup testing has exercised Wii OS initialization, exception and interrupt handling, cache and memory setup, and selected IOS, system-management, filesystem, title-service and System Configuration paths.
- The separate direct-entry `OSInit` V68 regression reached its controlled stop at `0x804EFA34`. It must **not** be confused with progress from continuous `__start` execution.
- A private full-image experiment translated the Wii executable into **112 C++ shards plus a dispatcher**, with **113/113 syntax-only checks passing**. That is not a full object build, link or functioning game executable.
- Focused V108 owner-original CI validated restoration of original initialized SC pathname data. V109 nonempty-path execution is still under validation and must not be described as completed game initialization.

The critical measurement is how far **uninterrupted original startup execution** reaches on the path toward `main()`, followed by a genuine first native frame. Internal stage numbers describe bounded tests; they are not a percentage-complete metric.

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

1. Continue the real Wii `__start` path through remaining OS, IOS and game startup dependencies, asserting exact observed guest PCs and original state transitions.
2. Replace test-only device callbacks where needed with faithful runtime semantics for interrupts, memory, IPC, storage, timers, audio and input.
3. Produce a complete native build that enters the original game's `main()` and survives its resource-loading sequence.
4. Render the first authentic native frame, bring up the frontend, then validate controls, world loading, physics, audio and gameplay.
5. Package and test a reproducible Windows build that works with legally obtained owner-provided game data.

The immediate goal is **working game startup**, not a higher milestone counter.

## Earlier Carbon PC experiments

Before the Wii native-recompilation work became the priority, this repository investigated reusing *Need for Speed: Carbon* PC's resource formats to bring across Undercover PS2/Wii content. That separate work includes eSolid geometry and texture decoding, world-stream comparisons, offline model conversion and a reversible in-game texture-staging experiment.

These experiments did **not** establish a working Undercover world import, native model rendering or playable Carbon-based port. Historical references include [V6 world-stream findings](research/CARBON_PC_POSTSCENE_V6_VARIANT_AND_RA.md), [V9 material coverage](research/UNDERCOVER_PS2_EXTERNAL_MATERIAL_IMAGE_V9.md), and [V12 eSolid header controls](research/UNDERCOVER_PC_V12_NATIVE_ESOLID_HEADER_CONTROL.md). Broader work remains in [draft PR #33](https://github.com/JakX2/nfs-undercover-ps2-to-pc/pull/33).

## Downloads, rights and distribution

This repository is a research and development project. **It does not distribute Nintendo/EA game executables, ELF/DOL files, extracted game assets, proprietary PowerPC instruction dumps, or generated C++ containing translated original game code.** Any owner-original analysis is performed on separately provided files and its public outputs are limited to independently authored code and safe validation summaries.

There is currently **no installable or playable native Windows release**. This project is unofficial and is not affiliated with or endorsed by Electronic Arts, Nintendo or the original game's developers.
