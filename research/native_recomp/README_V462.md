# V462: reusable full exception and syscall vector memory oracle

The V457 first-vector continuation now has its own full-image scope
(V460), after V451 authenticated all 13 hardware stages and V458
executed the original DBPrintf in both native output modes.

Prepare the next larger bounded continuation from original OSExceptionInit
through __OSInitSystemCall to the original alarm initializer. This header
is a read-only verification oracle, not an exception dispatcher. It
accepts authenticated original template bytes, syscall bytes and vector
offsets, snapshots real adjacent bytes and ABI at exception entry, and
takes its cache baseline at the first original memcpy (not before any
possible debug setup). It then validates the complete 15-vector memory
image, restored stack and nonvolatile registers, native handler-table
stores, exact original source preservation with the single expected
template clear and per-index OR, and 75 cache line events.

At original alarm entry, it additionally validates the 28-byte syscall
overlay, preserved surrounding 256-byte range, all 83 cache-line events,
32 syncs and 16 isyncs. The independent synthetic tests exercise two
table orders, 42 negative controls and duplicate terminal observations.
This oracle does not yet replace the V457 observer, does not patch the
guest and does not claim any new original execution. The first-vector
owner scope remains the next integration gate.
