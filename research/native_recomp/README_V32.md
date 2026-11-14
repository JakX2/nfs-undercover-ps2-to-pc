# V32: Original Wii `OSInit` reaches real MEM1 arena setters natively

**Milestone type: isolated, bounded original Wii PowerPC execution through
NWiiRecomp-generated native C++**. Not full Wii OS initialization, continuous
`__start` execution, native game `main`, a rendered frame or a playable PC port.

## New original-code coverage

V32 extends the SHA-pinned owner-original `OSInit` entry `0x80520670`
through the original MEM1 arena selection at `0x80520778`–`0x80520814`.
The native dispatcher executes the original `OSSetMEM1ArenaLo` at
`0x80521D60` and `OSSetMEM1ArenaHi` at `0x80521D48`, each containing an
original global store and return. Execution ends at a **synthetic, explicit
terminal syscall at `0x80520818`**, before the subsequent MEM2 initialization.
The parent V31 run stopped earlier at `0x80520778`.

The original low-arena selection consults the low-memory hint at `0x8000310C`
and, when absent, follows the binary's original boot/global selection tree.
The high-arena selection checks `0x80003110`, then the legacy low-memory word
at `0x80000034`, and finally an original fallback high bound. These are
**actual guest instruction effects**, not hand-written HLE replacements.

Six deterministic original `OSInit` test configurations cover direct hints,
legacy fallback, no boot record, record-backed alignment, nonqualifying record
values and nonzero low-memory override. Direct calls into both original setter
helpers additionally verify nonzero argument preservation, independent arena
globals and guest call/return conventions. The host runtime does not yet
validate arena ranges against Wii SDK allocation constraints or model the
whole memory allocator.

## Reproduction

Requires a private original Wii `NfsMWRelease.dol.bin` matching SHA-256
`16a09adcf1987c1f3617d10f3a1cb830f32886afb583f9f8f88e0963ae5fe1f4`,
Python 3, C++20 GCC and a **separate isolated NWiiRecomp checkout**. The runner
patches the supplied checkout in place using existing V15/V26/V29/V30 source
installers, writes private extracted slices and generated game C++ only to
`mktemp` scratch, and deletes them at exit.

```bash
bash run_osinit_arena_v32.sh /private/NWiiRecomp-master /private/NfsMWRelease.dol.bin
V32_SANITIZE=1 bash run_osinit_arena_v32.sh /private/NWiiRecomp-master /private/NfsMWRelease.dol.bin
```

The `make_osinit_arena_v32.py` builder verifies the pinned owner SHA, V31
source constraints, all new MEM1 branch targets and both actual setter bodies
before extraction. The C++ generator validates a private section geometry,
all expected functions and calls, and the complete new 160-byte arena decision
interval plus setter bodies using original-source-pinned hash checks. Hashes
alone aren't a substitute for source ownership and the primary input SHA.
The corruption suite rejects mutated helper opcodes, changed branch and source
instructions, unsafe DOL sections, a wrong original SHA and output overwrites.

## Verification (November 14, 2026)

- **679/679 owner-original native assertions**, six `OSInit` cases and direct
  original performance, HID4, speculation, FP and MEM1 helper checks.
- **156/156 negative/corruption/output-safety checks**.
- **23 original-native analyzed functions, 0 PowerPC interpreter fallback**.
- V30 patch idempotency/fail-closed suite: **14/14** checks.
- Optimized GCC C++20 native runner: **passed**.
- Sanitized C++20 ASan/UBSan run: **passed**, with 679/679 native and
  156/156 corruption/safety checks.
- Fresh unmodified NWiiRecomp ZIP checkout: **passed** the full optimized
  V32 runner, including 13/13 V29 prerequisite patch checks.

No original DOL/ELF bytes, game asset files, translated original-game C++ or
extracted PowerPC bodies are distributed in this source-only toolkit.

## Next technical gates

1. Reconnect these V28–V32 directly entered `OSInit` paths into the V26 single
   original `__start` dispatcher (still bounded at `0x805206B4`). This remains
   blocked partly by the five V26 owner/synthetic runner sources missing from
   the public PR.
2. Continue through the authentic MEM2 arena setters and subsequent service
   calls, verifying guest register and memory state against the private DOL.
3. Expand OS/IOS, interrupts, filesystem, cache semantics and GX/audio as
   demanded by real guest execution before claiming native game boot.
