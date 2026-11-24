# V458: original debug stack behavior instead of synthetic return

Authenticated V455 run 45323990982 found the actual original DBPrintf
has 20 instruction words and is not a NOP/BLR leaf. Its retail vector
table is initialized, non-overlapping and includes the syscall slot.
The original routine did not qualify for the leaf execution gate.
No owner debug return has yet been verified.

V458 is a new narrow stack-only candidate. The private preparer verifies
the same original four direct exception callsites and exact owner ELF
extent, then allows only bounded r1-based stack stores, stack adjustment,
NOP, forward non-link direct branches without CTR side effects and one
final BLR. No unknown instructions or external calls are substituted.
Unsupported source shapes are reported without owner opcode disclosure.

An independent bounded test oracle computes the expected register state,
conditional branches, big-endian GPR/FPR spills and all 512 stack bytes
from the actual private words. The game executable still runs the
actual AOT-emitted code, not the oracle. The synthetic and owner lanes
exercise eight configurations per output mode under ASan/UBSan,
both condition paths, stack guards, original return LR, preserved
condition bits and exact dynamic ticks, without interpreter fallback.
No debug output or full exception initialization is claimed.
The private program and generated C++ remain ephemeral. CI pending.
