# V60: Original Wii L2CR register helpers and L2 enable branch execute natively

**Status:** Verified bounded owner-original native execution via NWiiRecomp, **not** completed Wii cache initialization, continuous `__start`, original game `main`, first frame, or playable Windows build.

## What genuinely executed

The SHA-256-pinned owner-original Wii DOL supplies the original direct-`OSInit` code through `__OSCacheInit` at `0x80522540`. V60 restores the three authentic PPC instructions at `0x80522594`–`0x8052259C`: call `PPCMfl2cr`, test L2CR enable bit 31, and branch when enabled. Two original complete helper functions are present in the private test image at their original addresses: `PPCMfl2cr` at `0x804B7930` and `PPCMtl2cr` at `0x804B7938` (each eight bytes, including return).

The runtime previously hardcoded `mfspr 1017` (L2CR) as zero and silently ignored `mtspr 1017`. The original-free, idempotent and fail-closed `apply_l2cr_state_v60.py` replaces those stubs with an explicit guest `CPUContext::l2cr` value, including backup/restore paths. This is **only guest register-value storage**. It does **not** implement L2 cache data, hardware invalidation, automatic clearing of the invalidation/busy flag, polling/timing, exceptions, or other Gekko hardware side effects.

In the original cache initializer, L2CR bit 31 clear reaches the explicit **test-only `sc` stop `0x805225A0`** before `PPCMfmsr`, `PPCMtmsr`, `PPCMtl2cr`, or any L2 hardware setup. L2CR bit 31 set follows the original conditional branch to a second **test-only `sc` stop `0x80522644`** before `OSSetErrorHandler`. The full cache initializer does **not return** to `OSInit` in these tests. The original `PPCMtl2cr` guest-value write routine is additionally tested by independent direct calls, not yet by the hardware-configuration loop.

The other previous original code on the directly entered `OSInit` path remains unchanged: 15 exception vectors, cache maintenance, original syscall handler, alarm registration, module setup, interrupt mask programming, interrupt restore, context setup, and L1 cache enable. The pre-existing `DBPrintf` callback is **explicitly test-only**, not original debug-service execution. No PowerPC interpreter fallback is used on the tested paths. The analyzer's **57 roots** include conservative and synthetic guard entries, not 57 executed genuine game functions.

## Verified tests, 2026-11-16

- **17,960/17,960 original-native assertions** from six integrated `OSInit` configurations and inherited helper regressions plus original-direct L1/L2 status, L2CR read, L2CR write and branch tests. Both L2CR enable states execute the unchanged original PPC branch. Distinct nonzero L2CR values prove the register no longer reads as zero. Tests verify helper dispatch counts, guest stack/register state, and retained earlier game initialization side effects.
- **23/23 private-image safety checks:** mutation at every new original L2CR instruction and the synthetic stop/return words, private DOL geometry changes, owner-original SHA-256 pinning, trailing/truncated private images, and safe-output guards.
- **26/26 original-free L2CR runtime patch guards:** installation, repeated idempotency, invalid anchors, partial/mixed patches, duplicated anchors, and no modification on failure. **16/16** V44 cache-trace patch guards also passed.
- Full **optimized C++20** runner and full **ASan/UBSan** runner passed using the owner's original Wii DOL and isolated patched NWiiRecomp checkout.
- A **fresh extraction of the unmodified NWiiRecomp ZIP** passed the same 17,960 native assertions and both new safety suites, along with prerequisite **13/13 V29, 14/14 V30, 14/14 V43, and 16/16 V44** patch checks.
- Owner-original Wii DOL SHA-256: `16a09adcf1987c1f3617d10f3a1cb830f32886afb583f9f8f88e0963ae5fe1f4`.

## Reproduction and boundaries

With your authorized original Wii DOL and an **isolated writable** checkout of the matching NWiiRecomp source version, place the source-only V60 archive files together, then run:

```bash
bash run_osinit_l2cr_v60.sh /private/NWiiRecomp-master /private/NfsMWRelease.dol.bin
V60_SANITIZE=1 bash run_osinit_l2cr_v60.sh /private/NWiiRecomp-master /private/NfsMWRelease.dol.bin
```

The script validates the original DOL SHA, applies only independently written runtime patches, generates a short-lived private test DOL and original-code C++, runs independent safety tests and native assertions, and removes all private generated artifacts on exit. Do not publish original game DOL/ELF, extracted PowerPC code, private test images, game assets or generated game-derived C++.

## Next targets

1. Implement **controlled L2CR invalidation/polling semantics** grounded in Gekko hardware documentation, with explicit bounded behavior and tests, before running the original L2 initialization loop. Guest register-value storage alone cannot complete this step.
2. Execute `OSSetErrorHandler` and complete original `__OSCacheInit` return to `OSInit` at the existing next callsite, then continue EXI/SI/SRAM/thread initialization.
3. Connect V27–V60 directly entered `OSInit` execution to the original continuous `__start` chain. Its last verified checkpoint remains V26's `0x805206B4`, and five V26 reproduction sources are still absent from the current PR.
4. Do not claim genuine native game boot, `main`, first rendered frame, frontend or playable gameplay until those boundaries are executed and tested. Keep PR #36 in draft.
