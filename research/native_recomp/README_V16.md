# V16: First original Undercover Wii startup instructions execute natively

This source-only kit builds a tightly bounded test of the original Wii
`__start` at **0x8000403C**. It copies only the owner's first **two original
`__start` instructions** and the complete **144-byte original
`__init_registers`** into a **private temporary test DOL**, runs the actual
NWiiRecomp analyzer and non-split code generator, and compiles the resulting
`run_game(CPUContext&)` dispatcher as host-native C++20.

**Deliberate boundary:** the original `__init_hardware` at **0x800042E0** is
**NOT** included or executed. An independently authored `sc; blr` synthetic
stop function occupies that address only in the temporary test DOL. Its
`handle_syscall` callback terminates the controlled run. This is not Wii IOS
or a runnable port. Game-derived PPC and generated C++ stay in a private
`mktemp` directory and are deleted at script exit. Do not commit generated
C++ or the private DOL slices.

## Reproduce without game files

```bash
bash run_v16_tests.sh /private/path/NWiiRecomp-master
```

## Reproduce against the owner's original Undercover Wii DOL

```bash
bash run_v16_tests.sh /private/path/NWiiRecomp-master /private/path/NfsMWRelease.dol
V16_SANITIZE=1 bash run_v16_tests.sh /private/path/NWiiRecomp-master /private/path/NfsMWRelease.dol
```

The script makes only the local upstream NWiiRecomp source change from V15:
`apply_nonsplit_dispatch_v15.py` fixes the incomplete non-split generated
`run_game` exception-return structure. Prefer an isolated checkout, since the
fix is applied idempotently to the local checkout's recompiler source.
Compiler needs C++20, Python 3; GCC 14 tested. `CXX=clang++` can select Clang.
The V12 validated DOL loader patch is useful but not mandatory for the
small synthetic test image.

## Owner-original validation

- Original file SHA-256:
  `16a09adcf1987c1f3617d10f3a1cb830f32886afb583f9f8f88e0963ae5fe1f4`.
- The **real original PowerPC** `__start` first BL at `0x8000403C` targets
  `__init_registers` at `0x800041A8`. Its second BL at `0x80004040`
  targets `__init_hardware` at `0x800042E0`.
- The full native-translated `__init_registers` correctly sets `r1` to
  `0x80751CB8`, `r2` to `0x80715EE0`, and `r13` to `0x8070E8E0`. All
  other general-purpose registers are cleared.
- The synthetic hardware boundary is reached exactly once per run. The
  native guest link register becomes `0x80004044`, and after the test
  boundary returns, the stopped guest `PC` is `0x80004044`, the instruction
  immediately after the second BL. No full-game instruction at that address
  is executed in this test.
- **512 owner-original** iterations produced **20,481 passing assertions**;
  the **512 synthetic** iterations also produced **20,481 passing assertions**.
  The upstream analyzer discovers exactly three functions in both DOLs; its
  actual non-split `run_game` invokes the native code without PowerPC
  interpreter fallback. Both binaries passed with GCC normal/strict warnings
  and AddressSanitizer/UndefinedBehaviorSanitizer enabled.
- **24** independent original-free input and safety checks passed. These
  include corrupted first/second branches, partial or corrupt DOL sections,
  missing return/syscall, wrong mode, nonempty destination, and SHA mismatch.
  Rejected inputs do not create generated output files.

## Original startup call dependencies

`audit_startup_v16.py` reads the exact owner-provided DOL and lists direct
BL targets without exposing original instructions. It confirms 11 direct
calls in original 364-byte `__start`, including `__init_registers`,
`__init_hardware`, `__init_data`, `DBInit`, `OSInit`, `__init_user`, and
finally `main` at **0x802D3F40**. The original 36-byte `__init_hardware`
contains calls to three Wii OS services:

| Guest target | Symbol | Status |
|---|---|---|
| `0x80520FB4` | `__OSPSInit` | Not executed / native fidelity unverified |
| `0x8051FBB0` | `__OSFPRInit` | Not executed / native fidelity unverified |
| `0x80522540` | `__OSCacheInit` | Not executed / native fidelity unverified |

The original `__init_data` requires `memcpy` at `0x80004338`, cache
flushing at `0x80004304`, and `memset` at `0x8000443C`. These are
**identified dependencies only**. The V16 tests do not execute them.

## What V16 does not prove

We have **not** executed the full 364-byte `__start` body, entered the real
`__init_hardware`, initialized Wii hardware or OS services, reached game
`main`, linked all translated game shards, displayed a frame, or booted a
playable game. V16 demonstrates the exact *first original startup call path*
through the native dispatcher. The next gate is to implement or faithfully
translate `__init_hardware` and its first three Wii OS dependencies, then
continue through `__init_data` and `OSInit`.
