# V36 candidate: continuous original Wii __start calls __DBIsExceptionMarked

**Status:** owner-original V36 verification pending. V35 is independently
verified by GitHub Actions continuous-start run 44011635309, exact test-only
PC 0x80520CA8. The directly entered OSInit V40 marker results are a
separate existing original-game fixture, not a continuous startup proof.

## Authentic continuation

The source-only private constructor reuses V35's verified Wii __start ->
OSInit -> OSExceptionInit path. It restores the owner's original PowerPC
exception code from guest 0x80520CA8 through the original branch-and-link
at 0x80520CF0 to __DBIsExceptionMarked at 0x804E50A0.

The real 24-byte helper lives in the existing, previously synthetic NOP
gap between original DBInit and DBPrintf at 0x804E5020..0x804E50B8.
This eliminates the extra segment allocation/merging used by the older
direct-entry V40 research. Every authentic instruction is extracted only
from the SHA-256-pinned owner DOL into private runner scratch. The original
helper performs the original mark-bit shift, mask load and bitwise check.

The new continuous runner exercises sixteen normal boot paths. The genuine
original DBInit writes its debug-data pointer to 0x8070D8A0 and clears the
0x80000044 bitmask; V36 verifies that the original mark helper receives
exception index zero, returns zero after reading that state, and leaves the
guest debug structure unchanged. It also checks the authentic exception
template word stored at guest 0x80520F18, the nested OSInit/exception ABI
stack frame, original call LR, unchanged low-memory vector canary, all
V26–V35 CPU, FPU, hardware, BSS, memory, MEM1, MEM2 and IPC pointer
assertions, and no interpreter fallback.

An **explicit test-only syscall at 0x80520CF4** stops the native dispatcher
immediately after the original marker's BLR. A second fail-closed syscall
at 0x80520CC8 guards an alternative marked-boot path. The 0x80520C44
debug-print branch, conservative analyzer roots and the original
__OSInitSystemCall at 0x805208AC remain intentionally unimplemented.
Neither exception-vector installation nor functional OS/IOS IPC is claimed.

## Private reproducibility

The builder validates the exact original Wii DOL SHA, original BL targets,
whole 24-byte marker routine, contiguous original exception continuation,
NOP-only target slot, non-overlapping seven-section DOL geometry and
existing owner relocation table. The independent private geometry test
compares original bytes and exact synthetic stop replacements.

CI runs V26–V35 first and uses boot_progress.py --require-progress
with exact original guest entry 0x8000403C, expected stop 0x80520CF4 and
stage=36. Numeric assertion diagnostics are derived exclusively from
public independently authored test strings. Private logs, original DOL,
game PPC instructions and translated native C++ never leave runner scratch.

To reproduce against a privately staged owner DOL and a freshly patched
isolated NWiiRecomp checkout:

    bash run_v36_continuous_mark.sh /private/NWiiRecomp /private/NfsMWRelease.dol

A passing V36 is still bounded Wii startup, not full exception setup,
complete Wii OS, game main(), a linked Windows executable, first frame,
frontend, or playable gameplay.
