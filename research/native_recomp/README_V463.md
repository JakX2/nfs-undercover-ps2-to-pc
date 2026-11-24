# V463: propagate stopped guest execution across native call boundaries

V461 verified opcode-17 handler transfer and CPU stop in both actual
native output modes and the runtime interpreter. A further upstream
defect exists at native call boundaries: a generated caller compares
only the returned PC, not CPU running state. When a stopped child
returns its exact expected PC the caller may continue guest writes.
The outer dispatcher also invokes pending callbacks before dispatch
without checking whether a callback stopped the CPU.

V463 adds running-state guards to direct native call continuation,
micro-interpreter continuation and both outer dispatchers, preserving
existing PC checks. No guest state is altered by those guards. Tests
use independently authored nested original-free PPC and a synthetic
syscall handler, compare baseline and fixed in split and non-split
output, and verify normal returns, propagation at two call depths and
a dispatcher callback stop. No original game behavior is claimed yet.
