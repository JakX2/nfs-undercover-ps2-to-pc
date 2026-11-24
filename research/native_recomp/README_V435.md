# V435: complete-image cold OSInit system-time candidate

V430 passed authenticated complete-image execution through the original data
initializer and all 963,456 BSS bytes. V433 independently attempts original
DBInit and OSInit entry. V435 reuses the V25/V26 owner-proven call graph in
the complete-image lane, not a sliced or seeded game fixture.

The new os-time scope keeps all previous native gates, then allows the
unmodified OSInit prologue, 80-byte frame, register-save helper, init-once
flag, original system-time routine, timebase read, and interrupt restore
to execute. The observer stops on entry to the next interrupt-disable call,
with LR 0x805206B8, before that helper's second invocation executes.

Six exact native edges, 12 observed register spills, preserved SDA bases,
MSR restoration, two timestamp stores, and the return value within the
observed timebase window plus the unchanged low-memory offset are required.
The source preparer authenticates original callsites, helper returns and
both timestamp store destinations. No guest data is seeded or rewritten.
The runtime clock remains virtual; this is not hardware timing accuracy.

Local C++20 ASan/UBSan: four positive configurations, 52 negative controls
and four duplicate-stop controls. The independent Python audit tests pass.
Source-preparation integration and original-image execution require CI.
No original DOL, translated game code, private logs or executable is published.

Reproduce using the existing complete-image owner workflow, selecting
`os-time`. This is a candidate, not evidence that full OSInit or main runs.
