# V66: Original OSInit enters EXIInit polling natively in one startup chain

**Status:** owner-original directly entered `OSInit`, not continuous original `__start`, not full EXI initialization and not a playable Windows port.

This milestone integrates V65's independent `EXIInit` prefix with V64's validated original Wii `OSInit` through the genuine `bl EXIInit` at `0x805208C4`. The authentic PowerPC instructions at **`EXIInit 0x804EF9BC` through `0x804EFA10`** execute via NWiiRecomp-generated C++. The explicit test-only synthetic syscall at **`0x804EFA14`** stops the run immediately before the unresolved `__OSMaskInterrupts` service call. Owner-derived PowerPC opcodes are extracted privately at runtime from the SHA-256-pinned owner's Wii DOL and are never included in this source.

## Verified regression results

- **18,070/18,070 guest semantic assertions**, including six integrated OSInit configurations, inherited original native helper tests, and checked EXI MMIO transaction ordering. Three regular `OSInit` configurations reach the new EXI stop; debug branches continue stopping before unimplemented debug behavior.
- **240/240 original-word mutation, owner-image SHA, DOL geometry, output-overwrite, and malformed-image guards**. The new private DOL seventh text slot holds the original 22-instruction EXI prefix and synthetic terminal without relocating any guest code.
- **65 analyzed function entries**, including previous conservative/synthetic roots and the new EXI stop. Zero PowerPC interpreter fallback on tested paths.
- Full **optimized**, **ASan/UBSan** and **fresh, unmodified NWiiRecomp ZIP** runs passed. Fresh checks include prerequisite V29 13/13, V30 14/14, V43 14/14, V44 16/16, V60 26/26, V62 10/10 patch guards.
- The original EXI polling loop consults test-injected values from three registers `0xCD00680C`, `0xCD006820`, `0xCD006834`. Scenarios include busy channel zero, one, two and immediate ready, and exact read order is checked. These are **test-device values**, not a native Wii EXI implementation or assertion of hardware behavior.
- The original EXI prologue creates a 32-byte nested stack frame and saves r28–r31. The memory oracle verifies the resulting stack reuse and original LR `0x805208C8` rather than suppressing prior regression assertions.

## Private reproduction

Given the independently installed NWiiRecomp source and an original Wii executable matching SHA-256 `16a09adcf1987c1f3617d10f3a1cb830f32886afb583f9f8f88e0963ae5fe1f4`:

```bash
bash run_osinit_exi_bridge_v66.sh /private/NWiiRecomp-master /private/NfsMWRelease.dol.bin
V66_SANITIZE=1 bash run_osinit_exi_bridge_v66.sh /private/NWiiRecomp-master /private/NfsMWRelease.dol.bin
```

The runner deletes all generated game-derived translated code, private fixtures, and compiled binaries on exit. No proprietary executables, assets, or executable slices are committed or included in this archive.

## Remaining work

The original `EXIInit` continues at `0x804EFA14` with `__OSMaskInterrupts`, then MMIO register initialization, eight interrupt-handler registrations, and device-detection paths. None of those execute in V66. The full Wii EXI/IOS runtime, continuous entry-point `__start`, original game `main`, first frame, and gameplay remain unfinished. The last continuous `__start` chain was independently validated only to V26's `0x805206B4`; five V26 source-only harness files remain missing from the PR. V64/V65/V66 source packages should be committed together only after full GitHub readback verification. Keep PR #36 draft.
