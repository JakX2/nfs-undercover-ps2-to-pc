# V79: original reply-handler entry candidate

V77's verified fixture geometry is reused without additional original code
spans. V79 extends the ACK boundary through original scheduler enable,
reschedule and context-load calls. It requires actual restoration of the
original idle PC, MSR, all GPRs, LR, CTR and XER before a second external
interrupt is injected by the existing native IRQ entry helper. Only trace
counters are reset between the two interrupts, not guest or device state.

The original vector and dispatcher must independently route IPC IRQ 27 again,
with Y1 and the actual IOS reply header, and the original handler must enter
its reply processor at 0x805190C0. This does not claim execution of the reply
processor body, thread wakeup, OSInit return or main.

The exact-anchor overlay and runner are independently authored source only.
V77's authenticated fixture generation and geometry checks are reused.
The separate workflow publishes fixed Boolean predicates, ordinal trial
markers and the exact PASS checkpoint; private DOL, output and logs remain
temporary. Status: **verified, 16/16 owner-original trials**, run 44231647130.

## Owner-authenticated frontier (2026-11-18)

- V77 remains verified (run 44230303883). V79's first run 44230615569 passed the ACK predicates but stopped at an unrecognized subsequent dependency.
- The explicit original rescheduling tail at 0x80529950 targets SelectThread at 0x80529718; OSLoadContext contains the authentic rfi at 0x80522A88. Geometry and continuation metadata run 44231007344 passed. This is static metadata, not proof of executing that rfi.
- Second V79 run 44230956968 passed original ACK handling and reached the scheduler context getter at 0x80522928, failing its entry-state assertion. Commit 81af6df3 separates the first sleep from subsequent IRQ rescheduling and adds predicate-only diagnostics, preserving all checks. Owner run 44231229537 is the next verification gate.
- Original-free overlay mutation, deterministic derivation and no-overwrite tests passed in run 44231117597. V80 reply-wakeup candidate is deliberately separate and awaits V79 verification.

## Verified V79 result

Run [44231647130](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44231647130) on e7ac13d1 passed all 16 cold-start trials. Exact predicates: resume=1 regs=1 waiting=1; route=1 wire=1 waiting=1 pending=1. Checkpoint: 0x805190C0, stage 79. The original reply body is the V80 boundary.
