# V110 candidate: original SC strlen and selected continuation

V109's authenticated nonempty SYSCONF pathname passed all 16 native
owner trials at 0x80544AC0 (run 44441261370). V110 executes that exact
original strlen function, validates its bounded guest input, and follows
the original control flow until the next verified SC child boundary.
The next call may select the configuration helper, asynchronous open
wrapper, or optional pathname helper; the harness records the actual
choice and never changes guest registers or branches.

This is not a native full boot. Owner binaries and generated translated
code remain exclusively inside the private job.
