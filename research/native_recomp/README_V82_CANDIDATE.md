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

Status: V81 verified, V82 owner test 44236312898 reproduced a failed direct-load assumption after the original reply IRQ returned (clear=1, ready=1, route=1). The default thread's saved context remained valid, but the next context load did not select it. V82 now recognizes a possible legitimate intermediate idle-context return, requires the genuine second RFI to restore the interrupted idle registers, and observes the original idle-loop interrupt disable, context clear and eventual default-thread load. This is a candidate, not a verified resume. No guest state edits or forced selection.
