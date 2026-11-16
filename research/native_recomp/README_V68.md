# V68: Original `OSInit` reaches EXI MMIO configuration through native `__OSMaskInterrupts`

**Scope:** authentic original Wii PowerPC code executed from a **direct `OSInit` entry** (`0x80520670`), not continuous execution from original `__start` or a bootable game. This milestone extends V66's genuine `OSInit → EXIInit` path beyond EXI control-register polling.

The original EXI call at `0x804EFA14` now branches to the **complete original `__OSMaskInterrupts` at `0x8052693C`**. The function calls the original interrupt-disable and -restore helpers, updates the mask state and returns to `EXIInit`. The original four subsequent PowerPC MMIO stores run at guest PCs `0x804EFA20`, `0x804EFA24`, `0x804EFA28`, and `0x804EFA30`. The explicit synthetic terminal is at **`0x804EFA34`**, before the first `__OSSetInterruptHandler` call.

The previous `__OSInterruptInit` masks all supported interrupt banks (guest mask `0xFFFFFFF0`), so in **this integrated OSInit test** the EXI mask request is already covered and the original `SetInterruptMask` loop is not entered. V67 separately verifies all the original `__OSMaskInterrupts → SetInterruptMask` register-bank paths. No claim of EXI interrupt-handler registration or physical interrupt-controller behavior is made for V68.

## Verified results

- **18,085/18,085** native semantic assertions across six original `OSInit` configurations and inherited direct helper tests. Earlier exception, syscall, alarm, interrupt, context and cache regressions remain passing. Zero PowerPC interpreter fallback on tested branches.
- **280/280** original Wii opcode mutation, owner DOL SHA, private DOL geometry, output-overwrite and malformed-image safety checks. Full authentic 0x80-byte mask function and the additional EXI original instructions are pinned by private-image hashes and original call-target checks.
- **66 analyzer entries** including conservative and synthetic roots. All tested paths execute NWiiRecomp-generated native C++.
- Full **optimized C++20**, **ASan/UBSan**, and **fresh unmodified NWiiRecomp release archive** runs passed. Clean prerequisites: V29 **13/13**, V30 **14/14**, V43 **14/14**, V44 **16/16**, V60 **26/26**, V62 **10/10** patch/source guards.
- Normal integrated scenario confirms one authentic `EXIInit → __OSMaskInterrupts` dispatch, additional nested register saves in guest stack memory, return-state restoration, low-memory mask unchanged at `0xFFFFFFF0`, and exactly **four** EXI MMIO writes after the earlier nine startup writes. The EXI writes clear three channel control registers and set channel zero control to `0x2000`. Each MMIO address, width, value and ordering is checked against independently written expectations.
- Synthetic EXI-ready MMIO responses are explicitly supplied by a bounded test callback. `DBPrintf` still uses explicitly identified test-only callback returns, and L2 polling completion is supplied by the existing opted-in test device. This does **not** establish an actual EXI device controller, IOS services, interrupt delivery or hardware-realistic caches.

## Reproduce privately

Provide an owner DOL with SHA-256 `16a09adcf1987c1f3617d10f3a1cb830f32886afb583f9f8f88e0963ae5fe1f4` and isolated NWiiRecomp release source:

```bash
bash run_osinit_eximask_v68.sh /private/NWiiRecomp-master /private/NfsMWRelease.dol.bin
V68_SANITIZE=1 bash run_osinit_eximask_v68.sh /private/NWiiRecomp-master /private/NfsMWRelease.dol.bin
```

All original code extraction, runtime compilation and generated game-derived C++ happen in a temporary private directory and are deleted when the runner exits. Never distribute owner DOL/ELF, private slices or generated Wii game translation.

**Next:** progress through original EXI handler registrations at `0x804EFA40` and later `EXIGetID`, subject to verified Wii MMIO and callback behavior; integrate ongoing `OSInit` into continuous original `__start` (last verified separately at V26 `0x805206B4`). Original game `main`, rendered frame, frontend and gameplay remain unreached. Keep PR #36 draft.
