# V457: complete-image first original exception vector candidate

V456 actual pinned compiler run 45324280130 passed all five valid RAM
cases and three rejected non-RAM cases in each output mode, including
cache ordering, exact ticks, neighboring bytes and no interpreter fallback.

V457 prepares a read-only complete-image continuation from the V446
OSExceptionInit entry through the first original unmarked vector copy
and both original cache helper returns. It privately extracts actual
DOL vector offsets, template bytes, callsite/entry words and terminal
word. No synthetic vector offsets, forced debug flag, seeded mark mask,
stubbed debug routine or replacement instructions. It permits only
authentic direct prelude call edges inside the original function;
unexpected nested calls or marked first vector fail closed.

The observer requires original stack/SDA and interrupt state, source
template equality before initialization, exact first-vector source after
the original one-word clear, exact 152-byte copy and adjacent canaries,
five data-cache and five instruction-cache line events in sequence,
two syncs and one isync, and authentic original return to the next
instruction. It also fails closed if the existing bounded trace capacity
cannot retain all events. No hardware cache coherency claim is made.

The independent synthetic C++ witness covers two paths and 34 negative
controls; CI verification is pending. The preparer and strict chained
audit are ready for integration but not yet enabled in the full-image
runner. Existing queued hardware and IPC owner controls are preserved.
