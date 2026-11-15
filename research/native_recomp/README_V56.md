# V56: Authentic original Wii `OSInit` executes through the seven-bank interrupt mask loop

**Verified milestone: the longer original direct-`OSInit` chain now reaches the end of the original `__OSInterruptInit` mask loop. This is not a single continuous original `__start` chain, a complete Wii interrupt-controller model, complete `OSInit`, native game `main`, frame or gameplay.**

## Original code executed

The owner-private fixture inherits all verified V53 original direct `OSInit` functions, including low-memory boot structures, genuine exception-vector installation, `_restgpr_20`, `__OSInitSystemCall`, alarm registration, module initialization and the interrupt-table/initial MMIO/interrupt-disable path. The original Wii code is read only from the SHA-256-pinned owner DOL. V56 **replaces the test-only stop at `0x80526698` with the original unmodified PowerPC instructions through `0x805266A8`**, then installs a new explicitly synthetic `sc; blr` stop at **`0x805266AC`**, just before original `OSRestoreInterrupts`.

The genuine 604-byte original `SetInterruptMask` at `0x805266E0`, newly placed into the inherited synthetic NOP-padded private section, is now called by the *original* `__OSInterruptInit` conditional branch loop seven times. The native guest mask progresses from `r3=0xFFFFFFF0` through every group to zero. All seven sets of MMIO outputs, including five 16/32-bit register reads and nine total hardware register writes per complete initialized run (counting the two original pre-loop writes), are verified against an independently authored numerical oracle. Eight guest `SetInterruptMask` branch categories were previously exercised by V54; V55 separately verified the complete real IRQ mask loop with eight MSR configurations.

V56 combines these capabilities into the authentic **longer `OSInit`-entered native C++ execution path**. Six original OSInit fixture configurations remain checked. The previous independent test-only `DBPrintf` return remains a **single explicit callback**, not a native game debug-service implementation. MMIO callbacks only supply deterministic test read values and validate recorded writes, not Wii hardware side effects or interrupt delivery. The AOT emitter analyzes **49 entries**, including synthetic/conservative roots, with no PowerPC interpreter fallback on tested paths.

## Verification

- **17,725/17,725 original native guest assertions**: previous complete exception-vector cache events, system-call handler copy, timer/arena state, alarms, module globals, saved CPU registers, 128-byte interrupt-handler table, exact seven-bank SetInterruptMask progression and 5 read/9 write MMIO oracles. The six original OSInit fixture runs and preexisting direct helper tests remain enabled.
- **513/513 fail-closed checks** covering source-owner SHA, actual guest opcode mutations including the new mask loop and all 151 original `SetInterruptMask` words, private DOL section bounds, negative fixtures and output overwrite controls.
- **Optimized**, **ASan/UBSan** and **fresh unmodified NWiiRecomp ZIP** reproduction passed. The fresh checkout also passed prerequisite patch tests **13/13 V29**, **14/14 V30**, **14/14 V43** and **16/16 V44**. V15 and V26 patch prerequisites were applied before generation.
- Owner DOL SHA-256: `16a09adcf1987c1f3617d10f3a1cb830f32886afb583f9f8f88e0963ae5fe1f4`.

Reproduce privately using a dedicated upstream checkout and your own original Wii DOL:

```sh
bash run_osinit_mask_bridge_v56.sh /private/NWiiRecomp-master /private/NfsMWRelease.dol.bin
V56_SANITIZE=1 bash run_osinit_mask_bridge_v56.sh /private/NWiiRecomp-master /private/NfsMWRelease.dol.bin
```

The runner deletes the temporary owner-private image, original-game translated C++ and native test binary on exit. Only independently written source/test/documentation and source patch tools are distributed; game DOL/ELF data, assets and generated original-game code remain private.

## Next work

1. Continue the authentic original interrupt initializer from the current controlled stop **`0x805266AC`** through `OSRestoreInterrupts`, original exception-handler installation (`__OSSetExceptionHandler`), its epilogue and return to `OSInit`, maintaining the previous semantic/mutation coverage.
2. Extend the guest Wii MMIO and interrupt-controller implementation with real services instead of deterministic callback telemetry, and progress to remaining original `OSInit` platform services.
3. Integrate this direct-`OSInit` execution with single **original `__start`**, still V26-bounded at `0x805206B4`; five V26 source-only harness files are not yet published in PR #36.
4. Only after verified boot progression, pursue game `main`, genuine first frame, frontend, world loading and playable gameplay.

Keep PR #36 in **draft** and retain the Carbon PC adaptation as parallel research. Never commit owner-proprietary executable instructions, game-derived translated code, assets or other copyrighted game data.
