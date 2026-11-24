# V467: native indirect branch address alignment

The pinned interpreter correctly masks low two address bits for bclr
and bcctr, including linked variants. The native emitter does not.
V445's strict dispatch geometry therefore can reject an otherwise
valid indirect target if its LR or CTR contains low address bits.
V467 masks the emitted native target and the saved pre-link LR,
preserving existing BO/BI evaluation, CTR decrement, LR update and
the exact-zero linked-CTR compatibility guard. Zero-target policy
is not redesigned by this change.

The original-free pinned compiler regression compares seven indirect
branch forms with the actual interpreter, all four low-bit values,
both predicate states and conditional fallthrough. It checks the
same LR/CTR state, exact executed instruction count, and correct
taken/fallthrough PC. Baseline must reproduce 33 mismatches out of
44 taken cases; fixed must have zero. Both output modes run with
ASan/UBSan. No owner scope altered pending CI.

The first run 45327454427 failed the baseline instruction count. The
short fixture fallthrough tail was analyzed as local code and executed
its BLR, not an external dispatch. Place the independent tail target
outside the analyzer's 0x80000 local-branch window; this isolates the
indirect alignment behavior without altering the production analyzer.
The corrected fixture retains the exact tick assertion and emits a
bounded synthetic-only failure row. Verification pending.
