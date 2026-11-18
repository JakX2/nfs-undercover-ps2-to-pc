# V86 next-stage preparation: original asynchronous STM IOS operation

The authenticated metadata run 44231007344 established the original call
from STM at 0x8052B104 to an async IOS routine at 0x8051A1A4, whose six direct
dependencies include allocation, two cache flushes and request submission.
The existing V77-V85 fixture still uses a synthetic stop for this routine.

A new owner-local fixture extension restores exactly its authenticated
0x138-byte span, verifies all six call edges and checks that no unrelated
fixture bytes change. The generator guard replaces the old synthetic-boundary
assertion with original call-geometry checks. A synthetic-only regression
covers both fixture and generator negative cases. The game body is never
published. This preparation does not yet claim execution of the async request.
