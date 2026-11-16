# V37: owner-original Wii OSInit MEM2 arena handoff executes natively

**Scope:** bounded, directly entered authentic `OSInit`, not continuous original `__start`, complete Wii OS startup, or a bootable Windows game.

Building on the six V32 MEM1 arena scenarios, this owner-original Wii AOT native
proof extends real `OSInit` from guest `0x80520818` through `0x805208A0` and
executes both genuine eight-byte Wii arena setter functions:

| Original function | Wii guest entry | Native effect |
| --- | --- | --- |
| `OSSetMEM2ArenaLo` | `0x80521D68` | `stw r3,-16396(r13)` |
| `OSSetMEM2ArenaHi` | `0x80521D50` | `stw r3,-3468(r13)` |

The original branch at `0x805208A4` into `__OSInitIPCBuffer` is replaced by a
**test-only terminal `sc; blr` stop at exactly `0x805208A4`**. The IPC buffer
initializer is **not** executed or implemented. No original PowerPC instruction
bytes are distributed; the builder extracts them only from the user's private,
SHA-verified owner DOL in a temporary local test image.

## Verified guest effects

- The original MEM2 low/high arena hints are read from `0x80003124` and
  `0x80003128`, respectively. Zero hints skip the corresponding setter and
  preserve the existing guest global.
- The real low-arena selection is tested for a zero hint, the `0x90000000` and
  `0x900007FF` boundary cases (both clamped to `0x90000800`), exact minimum,
  a larger MEM2 pointer and a lower-address non-MEM2 pointer. Nonzero high
  hints propagate unchanged to the original MEM2 high global.
- Direct original helper entry calls with nonzero operands validate both
  setter writes and register/LR/SP preservation. The original MEM1 results,
  boot-info source and timestamp state are checked during all six cases.
- `NWiiRecomp`'s actual non-split generated `run_game(CPUContext&)` dispatches
  **25 analyzed functions** and performs **zero interpreter fallbacks** in the
  tested execution paths.
- The generator pins the full 140-byte original MEM2 decision continuation,
  both original eight-byte setter bodies and the earlier V32 source checks.
  The negative suite mutates every new instruction, rejects malformed DOL
  headers and ensures failed builds do not overwrite output files.

## Reproduction

Unzip this **source-only** toolkit (V32 dependencies included), and use a
separately extracted, unmodified `NWiiRecomp-master` checkout plus the owner's
private `NfsMWRelease.dol.bin` matching SHA-256
`16a09adcf1987c1f3617d10f3a1cb830f32886afb583f9f8f88e0963ae5fe1f4`.

```bash
bash run_osinit_mem2_v37.sh /private/NWiiRecomp-master /private/NfsMWRelease.dol.bin
V37_SANITIZE=1 bash run_osinit_mem2_v37.sh /private/NWiiRecomp-master /private/NfsMWRelease.dol.bin
```

The runner patches its explicitly supplied **isolated upstream checkout** with
previously verified V15, V26, V29 and V30 original-free patches, generates the
private DOL and translated C++ only in a securely removed temporary directory,
and retains generated-code `-Wno-type-limits` for an unrelated upstream
unsigned-comparison issue. Sanitizer compilation uses `-O0 -g0` to avoid an
observed build-time resource timeout; it still instruments the emitted native
C++ and runtime loader with ASan/UBSan.

## Local verification (2026-11-14)

| Test | Result |
| --- | ---: |
| Original Wii native execution, six `OSInit` cases + direct helper tests | **719/719 assertions** |
| Malformed image, source-mutation, SHA and output-safety tests | **195/195** |
| Pre-existing V30 patch checks | **14/14** |
| Additional V29 pristine-checkout patch checks | **13/13** |
| Optimized GCC C++20 full owner runner | **Passed** |
| Full owner runner with native ASan/UBSan instrumentation | **Passed** |
| Fresh unmodified NWiiRecomp ZIP owner runner | **Passed** |

No original DOL/ELF, proprietary game assets, temporary extracted code or
recompiler-generated game C++ are included in the source-only ZIP or GitHub.

## Remaining boundary

This V37 test enters `OSInit` directly at `0x80520670`. The last **continuous**
owner-original `__start` dispatch still stops earlier at V26's `0x805206B4`,
and the five source/runner files missing from V26 are still needed for full
GitHub-only reproduction of that older continuous path. Wii MEM2 physical
allocation/coherency, IOS/IPC, actual hardware clocks, graphics, audio, game
`main`, first frame and gameplay remain unverified. The next runtime gate is
`__OSInitIPCBuffer` and neighboring Wii OS services; integration of V27–V37
into continuous `__start` should take priority before claiming native boot.

Keep draft PR #36 open. Preserve Carbon work separately.
