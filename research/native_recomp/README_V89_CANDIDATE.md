# V89 verified: original post-STM subsystem

V88 verified 16/16. Restore the genuine OSInit call at 0x80520968 and the
authenticated 0xa0-byte next subsystem at 0x8052F790, with all eight
direct call edges verified in owner-local scratch. Its remaining new
children are explicit nonreturning test boundaries, never success stubs.
Execute the original interrupt disable/restore, subsystem version
registration (existing explicit diagnostic sink), and original queue
initializer. Stop before the original console classification helper
0x8051FD44, entered from 0x8052F7DC. Check the running thread, persistent
original deferred STM event, queue state and ABI. No complete new
subsystem or OSInit completion claimed until verified.

Verified owner run 44241947300 on 69c838ce1397bb45723c70b04267e244296e8b0d, all 16 trials and all five terminal predicates passed. V90 follows the original classifier into one of the two authenticated new child callsites.
