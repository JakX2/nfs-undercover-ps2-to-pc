# V31 continuous original Wii __start: low-memory boot-information handoff

Status: VERIFIED in owner-original GitHub Actions run 44004845948
(November 17, 2026). All six continuous-startup stages V26 through V31
passed on the genuine SHA-pinned Undercover Wii DOL. V31's instrumented
native callback reached 0x80520778 as an advancement from V30's 0x80520700.
The previous directly entered OSInit V31 tests remain separate and do
not expand the continuous route's verified boot-record/fallback cases.

The verified continuous path has reached V30, stopping at 0x80520700
after original system time, interrupt setup, ExecParams, six MMCR/PMC writes,
HID4/speculation and non-IEEE floating point setup.

## Proposed original code continuation

- Exact original PowerPC 0x80520700..0x80520774 inclusive, 30 original
  instructions, copied exclusively at runtime from the owner's SHA-pinned
  Wii DOL. The code reads original Wii low memory and updates OS globals.
- The existing original code section, seven function-code segments and
  genuine startup BSS relocation table are preserved.
- The independent original-free function verifier from direct-entry V31
  checks each low-memory load/store opcode, base register, signed displacement,
  and the authenticated original conditional/direct branch destinations.
- New explicit test-only syscall at 0x80520778, immediately after the real
  low-MEM1 arena-hint load at 0x80520774.
- The normal continuous entry test seeds low-memory boot pointer
  0x800000F4=0 and fallback flag 0x80000034=0. This selects the *no boot
  record/no fallback* branch. It independently seeds the low-memory arena
  hint at 0x8000310C per trial.
- After original native execution the test requires guest r13's small-data
  base, the arena hint returned in r3, boot base pointer 0x80000000,
  a cleared boot-record pointer, unchanged empty fallback/field globals,
  OS boot mode=1, intact original low-memory flags, BSS and canaries.
- Sixteen native owner-game cases preserve V30's prior original startup,
  cache/GQR/FPU, system-time, MMCR/PMC and HID4/SPRG assertions. No
  PowerPC interpreter fallback is allowed.

## Limits

The existing *direct-entry* V31 research separately executes other
boot-record/fallback flag configurations, but this continuous harness
is restricted to the verified empty-boot-pointer path. Other branch
combinations are NOT claimed for the continuous __start test.

All original code, private game DOL/ELF, derived machine code and
NWiiRecomp C++ remain temporary on the private CI runner and are deleted
after tests. Only an internally validated sixteen-trial native PASS may
emit BOOT_PROGRESS stage=31 pc=0x80520778. GitHub Actions requires
advancement over the V30 report with the original entry=0x8000403C.

Reproduction on the isolated exact-pinned NWiiRecomp checkout after the
V30 continuous runner installs verified original-free runtime changes:

    bash run_v31_continuous_lowmem.sh /private/NWiiRecomp /private/NfsMWRelease.dol

No complete original Wii OSInit, game main, frontend, frame or gameplay
has been reached by this candidate.
