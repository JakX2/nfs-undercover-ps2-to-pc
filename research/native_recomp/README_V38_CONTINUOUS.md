# V38 candidate: original exception-vector memcpy under continuous Wii __start

Status: **candidate, owner-original native CI not yet verified**. The previous
V37 continuous original-game stage is independently verified by GitHub Actions
run 44015047562, exact test-only PC 0x80520D80, stage=37. V42's direct
OSInit-entry exception-vector copy result is a separate existing proof.

## Native execution and exact boundary

This continuation restores the nine authentic owner-original PowerPC
instructions at 0x80520D80..0x80520DA0, reaching the original BL from
0x80520D98 to genuine original memcpy at 0x80004338. The native
PowerPC-to-C++ dispatcher follows previous original V26–V37 startup
and exception-template loops from __start (0x8000403C).

On the authentic Wii unmarked exception index-zero path, original
OSExceptionInit computes vector target 0x80000100 and copies exactly
0x98 = 152 bytes of the original exception-handler template from guest
source 0x80520EC0, after the original CTR/BDNZ template-clear sequence
changes a single source instruction to 0x60000000 (NOP). Tests verify
the entire output byte-for-byte, original source bytes, adjacent canaries,
helper dispatch count, guest LR/SP, original PPC registers, no interpreter
fallback, and all prior native Wii startup assertions in sixteen cases.

The owner-private SHA-pinned builder adds one non-executable DOL data
section at fixture-only MEM2 guest address 0x90050000 to hold the exact
owner-original 152-byte template as an oracle. The first original
__init_data startup relocation data segment at MEM1 0x80006420 (0xB0
bytes) is preserved separately and never repurposed. Native test setup
seeds the Wii MMU text memory from the second original-private section;
the independent test's result oracle uses the original handler template
with only documented source-memory seed/canary overrides.

The original DCFlushRangeNoSync BL at 0x80520DA4, target 0x80522320,
is replaced by a strict test-only syscall at 0x80520DA4 and not
executed. Therefore functional cache coherency, ICInvalidateRange,
additional exception-vector installation, IOS, game main(), Windows
frontend, first frame, and playable gameplay are NOT claimed.

## Reproduction and safety

The source-only fixture, geometry verifier and mutation tests check the
SHA-pinned owner original, exact original BLs, all genuine copied
instructions, original handler bytes and both DOL data sections.
Unimplemented debug services remain fail-closed syscall guards.
Proprietary original binaries, game PPC bytes, handler contents and
recompiler-generated game C++ exist only in private ephemeral Actions
scratch and are never committed or uploaded.

The original-game CI first verifies V26–V37 checkpoints, then requires
a new instrumented continuous entry 0x8000403C, exact stop 0x80520DA4,
stage 38 and sixteen passing owner-native trials. Failure diagnostics
use only fixed independently authored stage names and numeric
assertion IDs.

After the preceding continuous stages have prepared an isolated
NWiiRecomp checkout, reproduce in owner-private conditions:

    bash run_v38_continuous_vectorcopy.sh /private/NWiiRecomp /private/NfsMWRelease.dol

This is a bounded AOT execution test, not a complete bootable game port.
