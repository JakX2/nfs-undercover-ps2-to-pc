# V87 verified: deferred STM event registration

V86 verified 16/16. Continue through the original asynchronous submission
body, request cache flush, masked queue and mailbox writes, nested
interrupt restore and original wrapper return. The native IOS bus accepts
the actual event hook request at the original STM outer interrupt-restore
call, and must report Deferred with an ACK pending, no queued completion
and both original descriptors preserved. The guest thread must remain
RUNNING throughout. No fabricated return, forced branch, thread write,
request rewrite or IRQ delivery before the outer restore. The next phase
must handle the ACK against the active original thread context, rather than
the idle context used for synchronous requests.

Verified owner run 44240452107 on b603f0f6a4d041491b0727eb72784da46f8a2fbe: 16/16 trials, all eight terminal predicates passed. Independent expanded synthetic regression 44240497192 passed both AOT modes under ASan/UBSan (256 entries, 96 synchronous pairs, 32 deferred ACKs, 32 later replies).
