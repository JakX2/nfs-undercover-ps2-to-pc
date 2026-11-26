# V1409 asynchronous submit-to-queue observer

Source-only observer for the corridor following the original header flush. Requires the exact nested disable and queue call edges, original instruction identities and successor order, unchanged masked MSR, zero prior-EE return, helper nonvolatile ABI and exact request identity. Stack stores are limited to the already active submit frame; request writes and all MMIO are refused. The queue pointer must identify the request, allowing the ordinary physical/cached alias. The queue entry is a stop, not an enqueue or IOS transaction.

32 synthetic cases cover both paths and deliberate faults. Private integration and validation are separate, pending V1408. Queue argument provenance remains a hypothesis to confirm on the original path.
