# V59: Original Wii L1 cache enable paths execute natively inside OSInit

**Scope:** Owner-original, directly entered Wii `OSInit` executed through NWiiRecomp-generated native C++ on a bounded private test DOL. This is **not** a continuous original `__start` boot, a full `__OSCacheInit`, a hardware-accurate cache model or a playable Windows game.

## Genuine original code now executed

The SHA-256-pinned Undercover Wii DOL provides the exact original PPC call at `0x805208C0` from `OSInit` to `__OSCacheInit` at `0x80522540`. This replaces only V58's synthetic terminal at the old `OSInit` stop. V59 restores the original first 84 bytes of `__OSCacheInit` and the **complete five-instruction original helper functions** `ICEnable` at `0x805223BC` and `DCEnable` at `0x80522280`. Calls to the genuine `PPCMfhid0` at `0x804B7920` read the runtime's guest HID0 register through the previously validated V30 compiler/runtime patch. The original branch logic checks HID0's instruction-cache enable bit `0x8000` and data-cache enable bit `0x4000`.

With the integrated test's caches initially disabled, authentic `ICEnable` executes the PowerPC `isync`, reads HID0, sets `0x8000` and writes HID0. Authentic `DCEnable` executes `sync`, reads HID0, sets `0x4000` and writes HID0. Both original `DBPrintf` calls are handled **exclusively by the pre-existing explicit test-only callback**, not by genuine Wii debug services. The new private **synthetic terminal syscall at `0x80522594`** stops before the original `PPCMfl2cr` call and the unverified L2 cache state machine. The original cache initializer has **not returned** to `OSInit`.

The native generator pins the private DOL geometry, per-section FNV hashes and 55 analyzer roots, including three newly analyzed authentic entries (`__OSCacheInit`, `ICEnable`, `DCEnable`). The root count includes old conservative/synthetic entries and must not be presented as 55 executed original functions. No interpreter fallback occurs on tested paths.

## Reproducible verification

- **17,892/17,892 native assertions:** six integrated `OSInit` configurations plus prior original-helper tests, and four direct authentic L1 initializer cases with initially neither/either/both cache-enable HID0 bits set. Verifies selected helper calls, exact HID0 result, unrelated bit preservation, sync/isync ordering, retained original MMIO/cache data and new guest LR/stack frame.
- **43/43 V59 negative/safety checks:** mutate every original L1 helper/prologue instruction and synthetic stop, mutate private DOL geometry, reject modified owner input SHA, and refuse unsafe builder/generator overwrites. Previous milestone safety suites are independent.
- **16/16 V44 cache trace patch guards**, plus clean-checkout **13/13 V29**, **14/14 V30**, and **14/14 V43** patch safety checks.
- Full optimized C++20 and ASan/UBSan native runners passed. A newly extracted, otherwise unmodified NWiiRecomp ZIP successfully reproduced the 17,892 native assertions and all safety/patch guards.
- Original owner DOL SHA-256: `16a09adcf1987c1f3617d10f3a1cb830f32886afb583f9f8f88e0963ae5fe1f4`.

Run using this source-only archive, your authorized original DOL and a **dedicated writable checkout** of the matching NWiiRecomp version:

```sh
bash run_osinit_cache_l1_v59.sh /private/NWiiRecomp-master /private/NfsMWRelease.dol.bin
V59_SANITIZE=1 bash run_osinit_cache_l1_v59.sh /private/NWiiRecomp-master /private/NfsMWRelease.dol.bin
```

The runner holds the source-backed private DOL, generated original-game C++, and native test executables in a temporary directory removed upon completion. None belong in Git. No proprietary executable bytes, original function bodies, assets, private test image or game-derived translated output are published with this kit.

## Next priorities

1. Continue the original L2 cache initialization at `0x80522594`, replacing the present **L2CR stub** with verified guest register state and timer/polling semantics before executing its original loops. Do not model hardware cache invalidation as a host-native equivalent without evidence.
2. Execute the original `OSSetErrorHandler` and finish authentic `__OSCacheInit` return to `OSInit`.
3. Connect the latest tested direct `OSInit` progress to continuous original `__start` execution. Its last confirmed checkpoint remains V26's `0x805206B4`, with five earlier V26 harness files still missing from the public branch.
4. Native boot, original game `main`, first frame, frontend and gameplay **remain unverified**. Keep PR #36 draft.
