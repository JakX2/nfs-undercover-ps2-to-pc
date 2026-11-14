# V30: Original Wii HID4, speculation and non-IEEE FP startup execute natively

**Scope: owner-original, bounded native OSInit execution only. This is not a complete
Wii OS initialization, continuous game `__start`, original game `main`, or a
bootable Windows PC port.**

Building on V29, the SHA-256-pinned owner-original Wii Undercover DOL now enters
`OSInit` at `0x80520670`, executes its real timebase/interrupt, exec-params,
MMCR/PMC setup and now the following **original PowerPC functions**, all emitted
by NWiiRecomp and run as native host C++:

| Wii address | Original function | Verified guest-visible behavior |
|---|---|---|
| `0x804B7A30` | `PPCMthid4` | bit-31-set route writes full 32-bit HID4 value |
| `0x804B7A00` | `PPCDisableSpeculation` | reads HID0, ORs bit `0x200`, writes HID0 |
| `0x804B7920` | `PPCMfhid0` | reads guest HID0 into r3 |
| `0x804B7928` | `PPCMthid0` | writes r3 into guest HID0 |
| `0x804B7A28` | `PPCSetFpNonIEEEMode` | `mtfsb1 29` sets FPSCR bit `0x4` |

The original `OSInit` calls those three hardware services at `0x805206F4`,
`0x805206F8` and `0x805206FC`, and reaches a new **synthetic test syscall at
`0x80520700`**. It executes **21 analyzed function entries**, including two
explicitly synthetic boundary functions. The normal original OSInit supplies
`0x83900000` to `PPCMthid4`, so its bit-31-set path does not invoke `OSReport`.

`PPCMthid4` also has an original bit-31-clear path that calls `OSReport` at
`0x80522F00` before correcting the value and writing HID4. The test image has
an **explicit synthetic OSReport boundary**, and does **not** execute OSReport,
print a report, return from that routine or claim success for that path.
Because an ordinary `sc; blr` placeholder can still return to its caller even
if `is_running` is cleared, the test callback throws a dedicated test-only
C++ stop signal at this boundary to prevent any post-report code from running.
Direct original `PPCMthid4` tests verify both routes and the absence of an
unauthorized HID4 write before the stop.

## Runtime source patch

`apply_hid4_fp_v30.py` is an idempotent, fail-closed installer layered onto
the existing V29 patched NWiiRecomp source. It adds `hid0` and `hid4` to
CPUContext and callback backup/restore storage, translates SPR 1008/1011
`mtspr` and `mfspr` as value-backed guest register operations, and implements
single-bit FPSCR updates for `mtfsb1` and `mtfsb0`. The original guest test
exercises **mtfsb1 only**, not mtfsb0.

This is **not a hardware-accurate model**. It does not model HID4 hardware
latencies, speculation behavior, MMU effects, host instruction-cache changes,
FP exception delivery, FPSCR exception flags or hardware event counting.
The IOS callback save/restore wiring is source-patched but not dynamically
exercised by actual IOS callbacks.

## Original provenance and reproduction

Owner DOL SHA-256:
`16a09adcf1987c1f3617d10f3a1cb830f32886afb583f9f8f88e0963ae5fe1f4`

Test locally with Python 3, GCC C++20 and an **isolated** NWiiRecomp source
checkout (the runner installs source patches in-place):

```bash
bash run_osinit_hid4_v30.sh /private/NWiiRecomp-master /private/NfsMWRelease.dol.bin
V30_SANITIZE=1 bash run_osinit_hid4_v30.sh /private/NWiiRecomp-master /private/NfsMWRelease.dol.bin
```

The seven new implementation/test sources and runner use pre-existing
source-only V15, V26, V28 and V29 prerequisites. The builder reads the
original DOL only in local owner-private scratch, rejects wrong SHA, and
checks original callsites and relevant opcode shapes. Test-only derived DOL
and emitted original-game C++ live in `mktemp` and are deleted on exit.
No proprietary DOL/ELF, game assets, original PPC function body or translated
game C++ is published or included in source-only archives.

## Verified local tests, 2026-11-14

| Check | Result |
|---|---:|
| Native original OSInit, 4 configurations plus direct helper tests | **403/403** assertions |
| Owner SHA, mutated source/DOL, bounds and no-overwrite guards | **82/82** |
| V30 HID4/FPSCR patch safety/idempotency tests | **14/14** |
| Original analyzed entries, interpreter fallbacks | **21, zero** |
| Optimized native C++20 test | **Passed** |
| ASan/UBSan native C++20 test | **Passed** |
| Fresh unmodified NWiiRecomp source ZIP | **Passed** (including 13 V29 prerequisite checks) |

These are **bounded private original-code tests** and do not mean the full
Windows game has booted. The earlier continuous owner `__start` chain still
stops at V26's `0x805206B4`. The current V30 integration starts directly at
original `OSInit`. Five unpublished V26 startup-generator/harness sources
remain an independent reproducibility gap.

## Next engineering target

The genuine `OSInit` instructions at `0x80520700` onward initialize low
memory/global fields and branch according to the contents of physical Wii
low memory at `0x800000F4` and other startup flags. Continue through those
original instructions in a bounded, SHA-pinned test with explicit paths,
then integrate V28–V30 into the continuous `__start` dispatcher. Preserve
proprietary game bytes, the draft PR and the separate Carbon adaptation work.
