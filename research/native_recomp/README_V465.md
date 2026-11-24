# V465: advance Windows native owner verification to MEM2 and IPC

Authenticated V450 run 45323172768 passed the complete original
Windows x64 hardware startup scope: all 13 stages, 14 matched records,
exit zero, zero fallback, strict DOL loader equivalence and corrected
native ticks. This is bounded original native execution, not OSInit
completion or game boot.

Advance the default Windows owner scope to os-ipc, using the existing
V450 scope contract, exact dispatcher correction and full ancestor
auditors. Hardware and MEM1-only scopes remain available as controls.
Include their actual runtime/preparation dependencies in Windows
push triggers. No change to the running Linux control or pending
Linux first-vector build. Owner Windows IPC verification pending.
