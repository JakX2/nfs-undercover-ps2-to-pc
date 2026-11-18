# V88 verified: original STM initialization returns to OSInit

V87 passed all 16 owner trials. Continue from the original outer
interrupt restore into the deferred event's native ACK. Unlike the
synchronous device opens, the current running thread must be interrupted
directly, with the original external vector saving its actual context.
The original IPC handler clears the ACK without completing the event;
the original dispatcher reschedules and loads the saved running context;
the original RFI restores the CPU registers and returns to the original
STM caller. Stop only at the existing authenticated OSInit continuation
0x80520968 with both descriptors open and the event still deferred.
No host thread-state edits, fabricated event reply or IRQ bypass.
Original STM initialization has completed. OSInit has not yet returned.

Verified owner run 44240680204 on 919ae3eca2c662e4828470585ceaf55749f44c38: 16/16 trials, all seventeen final predicates passed.
