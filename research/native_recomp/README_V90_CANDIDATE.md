# V90 verified: original next subsystem's console route

V89 verified all 16 owner trials. V90 executes the real, already
translated console identification helper and its authenticated MEM2
query. Instead of forcing all four original trial modes through one
assumed child, verify the actual original linked call to 0x8051E7E4
or 0x8052F94C, preserve the queue, running thread, ABI and deferred
STM request, and stop before that child. Both endpoints are explicit
nonreturning boundaries in the private V89 fixture. Report each actual
mode/endpoint and require four complete trials per mode.

The bounded metadata run 44242030992 has also authenticated the complete
remaining OSInit tail (0x80520968–0x80520BF4) and startup continuation
(0x80004160–0x800041A8). The original main call is 0x800041A0 to
0x802D3F40, following the original startup's other initialization calls.
This is a map, not execution or proof of main reached.

Verified owner run 44242254276 on 6fbe45a2daa69ce05c9325c915a0f9b05b32ec1f: all sixteen trials passed, all four console configurations selected the original 0x8051E7E4 dependency and preserved the prior deferred STM request.
