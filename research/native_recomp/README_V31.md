# V31: Original Wii OSInit boot-info handoff executes natively

**Status: source-grounded, SHA-pinned owner-original bounded OS initialization.
Not a complete Wii OS boot, original game `main`, first frame, frontend or gameplay.**

V31 extends the V30 directly entered original `OSInit` function at guest address
`0x80520670`. The previous test-only syscall at `0x80520700` is replaced by
the original 120-byte/30-instruction continuation, ending after the authentic
`lwz r3,0x310C(r4)` at `0x80520774`. An explicit synthetic test-only syscall
at **`0x80520778`** prevents execution of the following memory-arena logic.
The generated native C++ dispatcher still analyzes **21 entries**, including
known synthetic boundaries. No original PowerPC interpreter is used.

## Verified guest-visible behavior

The newly reached code reads Wii low memory and updates existing OS globals.
Four independent startup shapes are tested, alongside all V30 direct-helper
and performance-register regression checks:

| Boot info at `0x800000F4` | Fallback flag at `0x80000034` | Verified behavior |
| --- | --- | --- |
| zero | zero | OS boot-info pointer cleared, fallback globals untouched |
| zero | nonzero | low-memory bytes `0x30E8`/`0x30E9` copied to fallback globals; pointer targets the fallback storage |
| valid MEM1 pointer | zero | boot-info pointer advanced by 12, 32-bit field copied from offset 36 and two low bytes written to `0x30E8`/`0x30E9` |
| valid MEM1 pointer | nonzero | boot-info path takes precedence over legacy fallback |

All cases check initialization of the global boot base pointer, the final
mode flag, preservation of source boot-info words and canaries, and the last
real load of the MEM1 arena hint from `0x8000310C`. Earlier original timebase,
MSR/interrupt, `__OSGetExecParams`, `memcpy`, MMCR/PMC, HID0/HID4, speculation,
FPSCR and stack/GPR results are revalidated.

**Test-boundary correction:** V31's normal terminal `sc` deliberately throws
an owner-harness-only C++ `NativeStop` signal after recording the precise guest
PC and setting `is_running=false`. A mere `sc; blr` sentinel can otherwise
continue to execute the following `blr`, overwriting `ctx.pc` with a stale LR.
The explicit exception prevents that false-positive stop. The genuine game
`OSInit` instruction bytes are unchanged; the stop itself is synthetic.
The older deliberately synthetic `OSReport` stop remains an exception guard
for the separately tested HID4 error path.

## Reproduce

Requires Python 3, a C++20 GCC toolchain and a *private isolated* NWiiRecomp
source checkout. Installers modify that checkout in place. Provide your
SHA-verified original Wii `NfsMWRelease.dol.bin` as the second argument.

```bash
bash run_osinit_lowmem_v31.sh /private/NWiiRecomp-master /private/NfsMWRelease.dol.bin
V31_SANITIZE=1 bash run_osinit_lowmem_v31.sh /private/NWiiRecomp-master /private/NfsMWRelease.dol.bin
```

The owner input must match SHA-256
`16a09adcf1987c1f3617d10f3a1cb830f32886afb583f9f8f88e0963ae5fe1f4`.
The builder extracts original instructions **only inside local private test
slices**. Input source, generated translated game code, build artifacts and
other proprietary resources are not committed or distributed. `mktemp` scratch
is automatically removed on runner exit.

The six new V31 files use unchanged earlier source-only prerequisites V15,
V26, V28, V29 and V30. The ZIP includes their required source-only installers,
builders and guard suites. The V26 long `__start` runner remains unpublished;
V31 is **direct `OSInit` entry**, not end-to-end `__start` verification.

## Verified tests (2026-11-14)

| Test | Observed result |
| --- | ---: |
| Original Wii native `OSInit`, four low-memory paths plus original direct-helper regressions | **449 / 449 assertions** |
| Owner-DOL SHA, malformed test-image, opcode, branch, output-safety and truncation checks | **112 / 112** |
| Reused original-free V30 HID4/FPSCR patch checks | **14 / 14** |
| Clean unmodified upstream source checkout V29 prerequisite patch checks | **13 / 13** |
| NWiiRecomp analyzed entries / PPC interpreter fallback | **21 / 0** |
| C++20 release runner on owner-original DOL | **Passed** |
| C++20 ASan + UBSan runner on owner-original DOL | **Passed** |
| Fresh, unmodified upstream NWiiRecomp ZIP reproduction | **Passed** |

## Boundary and next work

The genuine original `OSInit` next branches through memory-arena selection and
calls `OSSetMEM1ArenaLo` at `0x80521D60`, followed later by
`OSSetMEM1ArenaHi` at `0x80521D48`. Those paths and the remainder of Wii
OS/IOS hardware startup are not yet natively verified in this milestone.
Future development should extend the bounded original path into arena setup,
then connect V27–V31's isolated `OSInit` tests to V26's continuous `__start`
path. Five V26 harness sources remain absent from the public branch, so its
full private startup test cannot be reproduced from GitHub alone.
