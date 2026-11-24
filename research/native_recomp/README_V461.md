# V461: honor system-call callback transfer in native and interpreter paths

Upstream handle_syscall returns true when process_pending_callbacks has
transferred guest execution. The opcode-17 emitter ignores that result,
and the original interpreter likewise always advances PC by four. Both
can discard the handler's new PC; generated native code may also execute
later instructions after a handler stops the CPU.

V461 extends V26's exact syscall PC correction: if the handler transfers
or stops the CPU, return from the current generated function; the
interpreter returns without overwriting the handler's PC. The ordinary
false/running synchronous path is unchanged. This does not implement
new syscall IDs, hardware exception vectors, or the handler's own
interrupted-PC selection policy.

The independent pinned AOT regression compares baseline and corrected
code in both output modes with the V438 tick correction. It checks
a synchronous syscall, callback transfer with exactly-once continuation,
stopped CPU without later guest side effects, and actual interpreter
opcode-17 behavior. A synthetic handler supplies controlled outcomes.
The old compiler must reproduce the lost-transfer behavior, not merely
compile. New source edit tests require idempotence and refuse mixed
runtime/emitter revisions. No owner scope is changed until verification.
