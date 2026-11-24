# V438: correct native instruction-visit counting on branch and resume labels

The pinned NWiiRecomp shared function emitter writes ++ctx.inst_count
immediately before each generated instruction's label. A local goto
or internal-PC dispatch lands after the increment. In a three-iteration
loop it therefore misses two visits; a mid-function resume also misses
its first tick. This matters because the runtime's default virtual
timebase is derived from inst_count, and code polls timers during loops.

The opt-in patch moves the existing increment below the label and
original opcode comment, preserving all guest statements, dispatch
logic, label/comment instrumentation seams and the two outer dispatcher
increments. It is idempotent and rejects ambiguous source geometry.
It is not a claim of cycle-accurate Wii timing or precise retired
instructions: interruptible attempts and dispatcher ticks still count.

Local original-free validation: three Python methods passed, including
a miniature C++ emitter compiled and run before and after the patch
with ASan/UBSan. Three execution paths (loop, mid-loop resume, tail
resume) have correct counts after the patch; the old placement fails.
All three exact source seams were confirmed unique against the actual
pinned upstream blob b8946e0fb38b577b5c9591ad60e1b0634abb92a4.

The new pinned CI control runs independent PPC loop and linked-call
functions in both output modes before and after applying the patch.
It tests register results, return PCs and exact virtual time deltas.
This is a separate candidate, not yet installed in the owner's full
image or NAND build. Existing V435/V436/V437 owner runs are untouched.
