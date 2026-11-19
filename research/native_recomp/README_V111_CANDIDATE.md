# V111: original nonempty SC async wrapper to IOS_OpenAsync

V110 passed all 16 owner-original native trials at the original
selected 0x804F1E2C child. V111 continues from that same guest state
through the original wrapper and its original heap/allocator, IRQ,
pathname memcpy and IOS_OpenAsync callsite 0x8051982C. The test
compares copied bytes against the actual guest input before the copy
and retains STM, FS and scheduler invariants.

V111 stops before the asynchronous IOS request, which remains the
next actual transport milestone. No native full boot is claimed.
Private DOL/ELF, generated game functions and logs stay on the owner runner.
