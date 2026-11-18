# V81 candidate: original wake-to-ready transition

V80 verified 16/16 owner-original trials, run 44232553013, commit
a626ac618e8052c1d79930bdac778f3f8d8a4c6a. V81 executes the original wake body
and stops at its authenticated scheduler call (0x8052A5EC -> 0x80529718).
The nested interrupt disable must execute; the wait queue must be empty, the
original default thread READY, and its ready queue must contain that thread.
The idle context must still be current. No host writes to the thread or queue.
This is not yet an actual context switch or completion of IOS_Open.

Status: candidate until all 16 private original trials pass.
