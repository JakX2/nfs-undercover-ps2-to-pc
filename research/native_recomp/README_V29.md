# V29: original Wii OSInit initializes MMCR0, MMCR1 and PMC1–PMC4 under native AOT dispatch

**Status:** genuine bounded original-game Wii PowerPC execution, **not** complete `OSInit`, original `__start` integration or Windows game boot.

V29 extends the owner-original `OSInit` native entry from V28's test-only stop at
`0x805206C0` through the **six genuine original consecutive PPC performance
register initialization calls**, stopping at a new explicit test-only `sc; blr`
at `0x805206F0`. The original `OSInit` instruction immediately after this
stop would call `PPCMthid4` at `0x804B7A30`; that later helper has not executed.

The six complete **original**, not synthetic, 8-byte guest helpers are:

| Guest function | Address | Wii SPR | Tested outcome |
| --- | --- | ---: | --- |
| `PPCMtmmcr0` | `0x804B7964` | 952 | Native MMCR0 register store |
| `PPCMtmmcr1` | `0x804B796C` | 956 | Native MMCR1 register store |
| `PPCMtpmc1` | `0x804B7974` | 953 | Native PMC1 register store |
| `PPCMtpmc2` | `0x804B797C` | 954 | Native PMC2 register store |
| `PPCMtpmc3` | `0x804B7984` | 957 | Native PMC3 register store |
| `PPCMtpmc4` | `0x804B798C` | 958 | Native PMC4 register store |

The owner DOL is SHA-256-pinned as
`16a09adcf1987c1f3617d10f3a1cb830f32886afb583f9f8f88e0963ae5fe1f4`.
The independent `make_osinit_perf_v29.py` uses V28's independently authored
builder and **extracts the additional 48 original PPC bytes only at test time**.
Neither the test package nor GitHub includes the DOL, executable ELF, game
asset, extracted original instruction body or game-derived generated C++.

## Runtime work

`apply_perf_sprs_v29.py` adds native guest CPU storage for MMCR0, MMCR1 and
PMC1–PMC4, and teaches the NWiiRecomp emitter to translate `mtspr` and
`mfspr` against those six SPR numbers instead of silently ignoring `mtspr`.
The patch also wires these fields into existing `BackupState` and two IOS
callback backup / generated-dispatch restoration source paths. Those callback
paths were **source-patched but not dynamically tested as actual IOS callbacks**.

**Limit:** only register *values* are modeled. There is **no** implementation
of performance-event counting, MMCR control side effects, overflow interrupts,
cycle-accurate clocks or PowerPC hardware performance monitoring. No claim
of full hardware fidelity follows from a value-backed `mtspr`.

## Reproduction

From this source-only directory with Python 3 and GCC C++20:

```bash
bash run_osinit_perf_v29.sh /private/NWiiRecomp-master /private/NfsMWRelease.dol.bin
V29_SANITIZE=1 bash run_osinit_perf_v29.sh /private/NWiiRecomp-master /private/NfsMWRelease.dol.bin
```

The runner idempotently applies V15 non-split dispatcher, V26 syscall guest-PC,
and V29 performance SPR patches to an **isolated** NWiiRecomp checkout. Because
these patch scripts modify the supplied source, do not point them at a checkout
you need to keep pristine. It creates a temporary directory for private game
slices and native C++ emission and removes those files on exit. It fails closed
on altered owner DOL, malformed bounded sections, mutation of essential
original PPC callsites and helpers, inconsistent emitter source, or nonempty
output directories. Generated native C++ is compiled with C++20; only the
**generator** is built at `-O0` to reduce compilation time.

## Verified on 2026-11-14

| Test | Actual result |
| --- | --- |
| Original PPC analyzed functions (incl. test-only `ALT` stop) | **15** |
| Native original `OSInit`, four initialized-pointer/timebase cases | Passed |
| Direct native original `mtspr` calls with six distinct **nonzero** values | Passed |
| Native checks total; no interpreter fallback | **343/343** |
| Original DOL SHA, mutated PPC and no-output-overwrite guards | **60/60** |
| Source-only SPR patch safety and idempotency guards | **13/13** |
| GCC optimized native binary | Passed |
| GCC ASan/UBSan native binary | Passed |
| Fresh unmodified upstream NWiiRecomp ZIP reproduction | Passed |

The native test starts directly at original `OSInit=0x80520670`, executes the
authentic time, interrupt and exec-params helpers and all six newly executed
performance helpers. Four OSInit paths verify exact synthetic stop location,
register saves and stack, timestamp range, guest MSR interrupt state, all
exec-params destination bytes and all six performance SPRs being set to zero.
Six **additional direct native** entries to the real six `mtspr; blr` helpers
verify arbitrary nonzero operand writes update only the intended register.
All twelve previously analyzed V28 behavior boundaries remain guarded.

## Remaining boundary and V30 priority

`OSInit` stops at `0x805206F0` **before** `PPCMthid4`, speculation controls and
non-IEEE FP initialization. The genuine `PPCMthid4` path branches based on
bit 31 and may call `OSReport`; it needs source-grounded HID4 and branch
handling with guarded tracing. Other IOS/OS services, later original `OSInit`,
`main` at `0x802D3F40`, first frame, frontend and gameplay remain unverified.
The original continuous `__start` checkpoint is still separately V26 through
`0x805206B4`; V28/V29 are isolated, not yet integrated into that chain.
The five V26 source/runner files not published to GitHub remain a separate
reproducibility gap. Preserve draft PR and independent Carbon adaptation work.