# V89 candidate: original post-STM subsystem

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
