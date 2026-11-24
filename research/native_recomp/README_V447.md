# V447: restore next observed nested NAND function privately

Authenticated V442 workflow 45320120913 exposed V437's actual result:
one restored-frame begin, no original BLR/resume yet, two nested calls
allowed, maximum call ordinal four, five unique entries (four original,
first non-original NOP). This is not a returned callback.

V447 requires that exact prior aggregate and ordered private entry route.
It restores only the last observed unique all-NOP original ELF span,
bounded by the existing V424 rules, and verifies byte-for-byte roundtrip
and original coverage of all five observed entries. It regenerates the
private image's AOT code and reapplies the exact V437 frame observers
after comparing the old observed source to its reproducible instrumentation.
The same compiled V437 harness, guard policy and 192-call cap are reused.
Any changed entry route before the restored fifth entry fails closed.
Only aggregate progress is emitted; no private game code, bytes or logs.

Synthetic source tests and authenticated owner execution remain CI gates.
No original return, boot or gameplay is claimed.
