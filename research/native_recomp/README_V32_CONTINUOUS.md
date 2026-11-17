# V32 continuous original Wii __start: MEM1 arena setters

Status: CANDIDATE, owner-original continuous CI still pending.

This independently authored source-only test extends the actual Wii original
__start at 0x8000403C through V26/V27/V28/V29/V30/V31 and the following
authentic OSInit MEM1 arena-selection PowerPC code.

## Source-grounded new scope

- Exact 160-byte, forty-instruction original guest block 0x80520778..0x80520814.
- Original guest branches and both real calls: OSSetMEM1ArenaLo at
  0x80521D60, OSSetMEM1ArenaHi at 0x80521D48. Each genuine setter writes
  the selected 32-bit guest value to its actual r13-relative OS global.
- New explicit synthetic stop syscall at 0x80520818, before the subsequent
  MEM2/other Wii OS initialization logic is executed.
- The same original-code constructor validates all PPC branch and memory
  operand classes, genuine setter body geometry and owner SHA-256.
- Both helper functions are extracted only from the owner-original private
  DOL at runtime, stored in an expanded previously unused test-DOL text
  region with no overlap with any existing original startup function.
- Sixteen original-game trials from the original continuous __start path
  continue to seed the zero boot-record and zero legacy fallback flags.
  This test selects direct nonzero MEM1-low hints from guest address
  0x8000310C and zero MEM1-high hint 0x80003110. It requires original
  low setter to use the low hint and high setter to select original fallback
  0x81700000. Both guest global stores and source guards are asserted.
- The preexisting directly entered OSInit V32 suite covers six different
  arena/memory scenarios; this continuous test only claims the verified
  input path described above, not all combinations.
- All earlier continuously validated PSInit/FPSCR/cache/MMCR/PMC/HID0/HID4,
  BSS, OS timebase, interrupt and boot-info state contracts remain active.

## Private CI and limits

The Wii Continuous Startup Checks workflow first establishes an instrumented
V31 baseline and then requires a *new* exact V32 guest PC 0x80520818,
original entry 0x8000403C and stage=32 using the fail-closed
boot_progress.py --require-progress mechanism. A V32 PASS marker is emitted
only after every native assertion passes for sixteen owner-original trials.

Reproduction in an isolated NWiiRecomp checkout after the V30 compatible
original-free HID4 patches have been applied:

    bash run_v32_continuous_arena.sh /private/NWiiRecomp /private/NfsMWRelease.dol

No raw original game PPC bytes, DOL, ELF, generated C++, symbols or private
logs are uploaded; private inputs are deleted from the runner after the job.

This milestone, even if confirmed, will be a bounded native startup stage,
not full original Wii OS initialization, original main(), a rendered frame,
frontend, or playable Windows game.
