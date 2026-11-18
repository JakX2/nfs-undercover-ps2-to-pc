# V95 candidate: original synchronous title query

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
