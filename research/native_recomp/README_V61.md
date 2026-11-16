# V61: Original Wii L2 cache setup prefix executes natively, before the hardware completion poll

**Verification boundary:** genuine original Wii `OSInit` executes through `__OSCacheInit`'s L2 disabled-path register setup, with a **test-only terminal syscall at `0x805225EC`**. This is **not** L2 invalidation completion, a hardware-accurate cache, a continuous `__start` run, or a bootable PC game.

## Original PowerPC behavior now exercised

The SHA-256-pinned owner Wii DOL provides the genuine original instructions from `0x805225A0` through `0x805225E8`, without instruction rewriting. On the disabled-L2 path, `__OSCacheInit`:

1. Calls original `PPCMfmsr` and saves the guest MSR in `r30`, then calls original `PPCMtmsr` to temporarily set MSR to `0x30`.
2. Executes original PowerPC synchronization barriers.
3. Reads L2CR through original `PPCMfl2cr` and writes through original `PPCMtl2cr`, clearing bit 31 (L2 enable) and finally setting bit 21 (`0x00200000`, L2 invalidate request).
4. Stops **before** the original `0x805225EC` read-and-poll loop that waits on L2 hardware completion. No busy-bit clearing, asynchronous state changes, invalidation effects, timing, or real L2-cache coherency are simulated.

The L2-already-enabled path remains the V60 original branch to a separate **test-only stop at `0x80522644`**, before `OSSetErrorHandler`. The original L1 `ICEnable`/`DCEnable` and prior exception, syscall, alarm, module, interrupt, and context initialization remain in the same directly entered `OSInit` harness. The earlier `DBPrintf` callbacks are explicitly **test-only**. `__OSCacheInit` does not return to `OSInit` in these tested paths.

The original `PPCMfmsr` at `0x804B7910` and `PPCMtmsr` at `0x804B7918` were absent from V60's seven-slot private test DOL. V61 grows the existing helper section by 16 *owner-extracted* bytes, adjusts subsequent **file offsets only**, and preserves every original helper's **guest address**. The builder rejects unexpected DOL geometry, owner-image SHA changes, or existing output overwrites. The private test image, original PowerPC instruction bodies, extracted assets and emitted game-derived C++ are never published.

## Native verification

The original PowerPC implementation (not an interpreter) is exercised in the existing six directly entered `OSInit` scenarios and independent direct helper/cache tests. The test verifies L2CR writes and preservation of other bits, all four initial L1-bit combinations, both L2 enabled/disabled branches, guest MSR register transitions, six original barriers in the L2 setup, saved stack/frame state, and original helper dispatch counts. Synthetic test boundaries are checked independently.

- Native optimized C++20 assertions: **17,984/17,984**, zero PPC interpreter fallbacks.
- Original Wii private-image SHA, instruction-mutation, bounded DOL layout, and no-overwrite guards: **54/54**.
- V60 L2CR register-state source patch idempotency/ambiguity/fail-closed checks: **26/26**; V44 cache-trace patch guards: **16/16**. The fresh checkout also exercises V29 13/13, V30 14/14 and V43 14/14 prerequisite checks.
- Optimized full runner and full ASan/UBSan runner passed. The optimized runner also passed on a freshly extracted, **unmodified upstream NWiiRecomp ZIP**, after applying its independently authored source-only prerequisite patches.
- Analyzer: **59 entries**, including conservative and synthetic roots, not 59 independently executed original functions.

Expected original-owner Wii DOL SHA-256:

`16a09adcf1987c1f3617d10f3a1cb830f32886afb583f9f8f88e0963ae5fe1f4`

Reproduce with your own legitimate DOL and a writable isolated checkout of the matching NWiiRecomp version:

```bash
bash run_osinit_l2prefix_v61.sh /private/NWiiRecomp-master /private/NfsMWRelease.dol.bin
V61_SANITIZE=1 bash run_osinit_l2prefix_v61.sh /private/NWiiRecomp-master /private/NfsMWRelease.dol.bin
```

The runner deletes its temporary private extracted DOL, native generator, original-derived emitted C++ and compiled executable on completion. Do not commit proprietary input binaries or generated game-code translations.

## Next steps

- Research and implement explicit, bounded **L2CR invalidation completion semantics** using reliable Gekko documentation and synthetic device tests. Do not fake completion by silently changing L2CR during the game loop.
- After verified completion, run the original poll, MSR restoration, cache reenable and `OSSetErrorHandler`, then return from `__OSCacheInit` into the next original `OSInit` service (EXI/SI/SRAM/thread setup).
- Restore continuous original `__start` execution past the separate V26 boundary at `0x805206B4`; the five missing V26 harness sources remain a reproducibility gap.
- No original game `main`, first frame, frontend, IOS integration or gameplay is claimed. Keep PR #36 draft.
