# V79: original reply-handler entry candidate

V77's verified fixture geometry is reused without additional original code
spans. V79 extends the ACK boundary through original scheduler enable,
reschedule and context-load calls. It requires actual restoration of the
original idle PC, MSR, all GPRs, LR, CTR and XER before a second external
interrupt is injected by the existing native IRQ entry helper. Only trace
counters are reset between the two interrupts, not guest or device state.

The original vector and dispatcher must independently route IPC IRQ 27 again,
with Y1 and the actual IOS reply header, and the original handler must enter
its reply processor at 0x805190C0. This does not claim execution of the reply
processor body, thread wakeup, OSInit return or main.

The exact-anchor overlay and runner are independently authored source only.
V77's authenticated fixture generation and geometry checks are reused.
The separate workflow publishes fixed Boolean predicates, ordinal trial
markers and the exact PASS checkpoint; private DOL, output and logs remain
temporary. Status: candidate; require 16 owner-original trials to verify.
