# V21: Original Wii ICEnable/DCEnable execute through the native game dispatcher

**Verified partial native startup, not a complete native port or playable boot.**
This change replaces two explicit V20 test-only Wii OS syscall placeholders
with the **original five-instruction `ICEnable` and `DCEnable` routines** from
the owner's SHA-pinned Wii DOL. NWiiRecomp translates the owner's original
PowerPC body privately into C++20; its actual `run_game(CPUContext&)` dispatcher
calls both routines from the already verified original `__OSCacheInit`.

No copyrighted game executable, generated game C++ or assets are included.

## What V21 runs

- `DCEnable` at `0x80522280`, **20 bytes**: guest `sync`, read HID0 (SPR 1008),
  OR `0x4000` (DCE), write HID0, `blr`.
- `ICEnable` at `0x805223BC`, **20 bytes**: guest `isync`, read HID0 (SPR 1008),
  OR `0x8000` (ICE), write HID0, `blr`.
- The original `__start`, `__init_registers`, `__init_hardware`, `__OSPSInit`,
  `__OSFPRInit` and `__OSCacheInit` routines, and the same original register/
  cache helper functions as V20, run together in an **18-function** bounded
  native dispatcher. The IC/DC enable routines no longer invoke synthetic
  syscalls. Their instructions are original game bytes, read only from the
  user's local verified DOL and never committed.
- In the independently authored synthetic Wii DOL, IC/DC use **r5/r6** rather
  than the original routine's register, so the tests check instruction meaning
  instead of matching the original sequence's incidental register allocation.

### Remaining boundaries

`DBPrintf` and `OSSetErrorHandler` still have test-only `sc; blr` bodies, and
the post-hardware `__start` continuation is still a **synthetic stop**. HID0
register-state operations are modeled; real host instruction/data cache
contents, coherency, cache invalidation and hardware latency are **not**
modeled. L2CR status-poll completion remains deliberately deterministic from
V20. The actual game's `__init_data`, `OSInit`, `main`, frontend and rendering
have not been entered.

## Build and test

Requires an owner-local NWiiRecomp checkout, Python 3 and a C++20 compiler.
All test output and translated proprietary C++ are written only in the
runner's temporary directory, which is removed on exit.

```bash
bash run_v21_tests.sh /private/path/NWiiRecomp-master
bash run_v21_tests.sh /private/path/NWiiRecomp-master /private/path/NfsMWRelease.dol.bin
V21_SANITIZE=1 bash run_v21_tests.sh /private/path/NWiiRecomp-master /private/path/NfsMWRelease.dol.bin
```

The runner applies the independently authored V15, V18, V19 and V20 runtime
patches idempotently to the provided local checkout. Use a separate checkout
for experiments. `make_icdc_slice_v21.py` rejects an existing destination and
refuses an owner DOL unless its SHA-256 matches
`16a09adcf1987c1f3617d10f3a1cb830f32886afb583f9f8f88e0963ae5fe1f4`.
Source corruption, missing return, broken HID access or wrong enable masks are
rejected before generated output is produced.

## Verified local results (2026-11-13)

| Test | Result |
| --- | ---: |
| Owner-original game, 128 starts, eight L1/L2 initial-state patterns | **12,418 assertions passed** |
| Independent synthetic PPC DOL, 128 starts | **12,162 assertions passed** |
| L2CR status-state unit regression | **3,584 assertions passed** |
| Owner-mode corruption, overwrite and patch checks | **31 passed** |
| Synthetic-only corruption, overwrite and patch checks | **30 passed** |
| Optimized C++20 runtime with original owner code | **Passed** |
| GCC AddressSanitizer + UndefinedBehaviorSanitizer original and synthetic tests | **Passed** |
| Fresh NWiiRecomp checkout with V15/V18/V19/V20 patch chain | **Passed synthetic tests** |

Original-game tests verify both HID0 enable bits, preserved unrelated HID0
bits, true cache-enable entry counts for each initial state, 704 L2CR reads,
320 L2CR writes, original guest LR/SP restoration, paired-single/FPR state,
GQR clearing, bounded stop and **no interpreter fallback**. Only two service
callbacks remain in the original cache routine, plus the synthetic post-start
stop. Original startup slices record 576 explicit synthetic callback calls
over the 128 starts, versus 704 in V20 when IC/DC enable were also stubs.

## Next step

Implement the original Wii `OSSetErrorHandler` global-state effects and
replace the `DBPrintf` diagnostic shim without asserting unsupported OS
functions. Then expand beyond the synthetic stop into `__init_data` and its
memcpy/memset/cache helpers. Avoid claiming full native startup until a
translated guest path actually reaches the original `main` and initializes
frontend/game systems.
