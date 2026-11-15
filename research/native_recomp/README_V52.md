# V52: Original Wii interrupt-mask and MMIO-write prefix executes natively

**Milestone type:** bounded owner-original PowerPC execution through NWiiRecomp-generated C++20; **not** hardware-accurate Wii interrupt delivery, complete `OSInit`, a native boot, or a playable Windows game.

## Newly verified original execution

From a SHA-256-pinned owner's Wii `NfsMWRelease.dol.bin`, the directly entered original `OSInit` executes through the genuine `__OSInterruptInit` prefix at `0x8052661C` up to and including the original instructions at `0x80526670`. V52 replaces only the previous V51 synthetic syscall at `0x8052664C` with the next **10 original PowerPC instructions**, then places a new explicit **test-only terminal `sc; blr` at `0x80526674`**, before the original `__RAS_OSDisableInterrupts_begin` call.

The additional original code:

* Clears both original 32-bit low-memory interrupt-mask words at `0x800000C4` and `0x800000C8`.
* Performs a 32-bit store of `0x000000F0` to guest MMIO `0xCC003004` (runtime's canonical physical address `0x0C003004`).
* Performs a 32-bit store of `0x40000000` to guest MMIO `0xCD000034` (canonical `0x0D000034`).
* Retains V51's original `memset`/`__fill_mem` execution, zeroing the 128-byte interrupt table, as well as previously integrated exception-vector, system-call, alarm, and module initialization.

The actual `MMU::write32` dispatches these stores to `HW_Reg_Write32` callbacks. The **test implementation only records and strictly validates the exact guest write sequence**; it does not emulate the PI interrupt controller, IOS hardware, register readback, interrupt signal generation or acknowledgement. All unrecognized MMIO accesses in this test throw. No fabricated device responses are used to advance execution.

## Verification

- **17,638/17,638 native semantic assertions**, spanning six directly entered original `OSInit` shapes (including three normal MMIO paths and three earlier marked-debug stops), the original code's guest-register side effects, both MMIO values and ordering, two mask words and adjacent canaries, and inherited native-execution checks.
- **348/348 original SHA, PPC mutation, private DOL geometry, source-template, and safe-output checks**, including every original instruction through the new test boundary.
- **16/16 V44 cache trace patch guards**. Clean-upstream prerequisites also verify V29, V30, V43 and V44 source patches.
- Optimized C++20 and ASan/UBSan native test runs pass. Original execution is through NWiiRecomp's native non-split dispatcher, **48 analyzed entries, zero interpreter fallback** on the six tested paths.
- The owner DOL must match SHA-256 `16a09adcf1987c1f3617d10f3a1cb830f32886afb583f9f8f88e0963ae5fe1f4`. The script refuses existing destination images, unknown sections and a nonempty emitted-source output directory.

Run with an **isolated** NWiiRecomp source checkout because patch installers modify that checkout:

```bash
bash run_osinit_mmio_v52.sh /private/NWiiRecomp-master /private/NfsMWRelease.dol.bin
V52_SANITIZE=1 bash run_osinit_mmio_v52.sh /private/NWiiRecomp-master /private/NfsMWRelease.dol.bin
```

The runnable source-only bundle also requires the prerequisite original-free V15, V26, V29, V30, V43, V44, V48, V49, V50, and V51 scripts. The owner-private test DOL and emitted original-game translation are created in temporary local paths and deleted by the runner.

## Strict boundaries and priorities

1. The very next original Wii instruction at **`0x80526674`** calls `__RAS_OSDisableInterrupts_begin`; its subsequent `SetInterruptMask` control flow and interrupt-controller MMIO reads/writes have **not** run as part of V52.
2. The test still **starts directly at `OSInit`**, not at the original Wii `__start`. V26 remains the last verified continuous `__start` sequence through its `0x805206B4` boundary; five V26 harness sources are still unpublished in the PR.
3. The existing test-only `DBPrintf` callback and simplified/cache-trace-only service state remain. No original Wii OS/IOS completeness or native application `main` has been demonstrated.
4. Next: execute interrupt disable/mask setup with narrow, explicit MMIO semantics; connect the tested `OSInit` chain to the original `__start`; replace synthetic services with verified native implementations.

Only independently written source, scripts, fixtures and documentation belong in GitHub. Do **not** commit proprietary DOL/ELF, extracted PowerPC function bodies, generated translated-game C++, private fixtures or original game assets. Preserve the draft PR.
