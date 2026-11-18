# V82 candidate: original ready thread resumes

Depends on V81 passing. Allows the nested wake scheduler to return while
disabled, then checks original reply IRQ completion and original scheduler
selection of the default thread. Requires the original saved context load,
and stops only when the resumed OSSleepThread calls the original nested
interrupt-restore helper (callsite 0x8052A500, return LR 0x8052A504).

No host switch, no host writes to thread state or queue, and no interpreter
fallback. The first exact candidate checks saved PC and stack against the
original context. If any predicate differs, diagnose it, don't force a return.
The dedicated owner workflow is manual pending verified V81.

Status: source-only candidate, not a claimed owner execution result.
