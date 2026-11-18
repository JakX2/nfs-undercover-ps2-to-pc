# V95 verified: original synchronous title query

V94 verified all four original IOS opens and first ES query entry.
V95 restores original IOS_Ioctlv and its vector preparation helper
privately, checks both original cache flushes and the actual IPC
vector table, then lets the native read-only ES backend respond to
the real request using the explicitly configured synthetic title
metadata. Reuses original submission, IRQ, wake, context restoration
and free path. Tests output and vector invalidation, complete original
return to NANDInit at the next directory helper 0x804F0AD8.
No actual title identity or filesystem store inferred from synthetic
data; no further NAND completion claimed until owner execution passes.

Verified owner run 44248584573 on 1e13c496b44fdb1aba38ddaf5901ecb0f7fbb348: 16/16 trials; original vector preparation/cache flush, wire request, native output, original IRQ and scheduler return, restored vector, allocator cleanup and all earlier device state passed. Metadata is the explicit synthetic test ID, not an inferred real title. Native synthetic IRQ tests in 44248452744 also passed both generator modes for ES title vectors.
