# V80 candidate: original reply processor to waiting-thread wakeup

Depends on a **verified V79** two-interrupt path. The owner-authenticated
control-flow probe (run 44231007344) confirms that the reply processor calls
the original wake routine at 0x805192D0 -> 0x8052A51C and the synchronous
submit body has its original continuation after OSSleepThread.

This candidate extends the source-only V79 harness to execute the original
reply body. It requires an actual ARMMSG register read selecting the same
physical request, original data-cache invalidation covering its reply header,
the native IOS return header, and the original waiting queue argument at
OSWakeupThread entry. The handler is not replaced, and no thread is awakened
by host code. It stops *before* executing the wake routine, then the original
scheduler and default thread return will be tackled separately.

Status: source-only candidate. V79 passed run 44231647130; V80 focused owner execution is now enabled for changes to its own files. No new original bytes or generated C++ are
published.
