# V96 verified: original ES data-directory query return

V95 verified genuine original IOS_Ioctlv with one output vector.
V96 executes the original second wrapper at 0x804F0AD8, passing
the preceding returned title ID through one input + one output vector.
Verify original cache flushes, request submission, native metadata
response, original IRQ/queue/scheduler resume, vector conversion and
request cleanup. Verify the exact directory string derived from the
explicit synthetic title fixture. Stop at original next string-copy
leaf 0x8054B4B4 (caller 0x8051E8A0). No ES closure or NANDInit
completion claimed until further verification.

Verified owner run 44248900760 on 4c2f72c8750e1038944da5f71aa3a8e2344c4f6b: 16/16 trials; original title-dependent directory query, cache flushes, native response, original IRQ/scheduler return and all earlier device state passed. The V97 NAND tail metadata run 44248956132 authenticated the close and subsequent callbacks.
