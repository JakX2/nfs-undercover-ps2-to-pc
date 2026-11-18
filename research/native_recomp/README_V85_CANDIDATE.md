# V85 verified: both original synchronous STM opens complete

V84 passed 16/16. V85 reuses the verified original IRQ and scheduler
execution checks for a second transaction. Its expected IOS result is 1
instead of 0; the host does not write that result into the guest outside
the already implemented IOS device service. The harness reinitializes
only its own observation counters after confirming first completion.
CPU, RAM, device descriptors, IRQ latches and all scheduler state persist.

The second original reply, wakeup, scheduler restoration, interrupt
restore, and allocation cleanup must all execute before the authenticated
STM interrupt-disable callsite (0x8052B0D0, return 0x8052B0D4).
Stop at 0x805265AC with both descriptors open and no outstanding request,
IRQ or deferred event. This is not yet STM or OSInit completion.

Verified in owner-original run 44239400611 on 63ae42ae928195793236427d6bdcacf777a7fd8b, 16/16 trials. Final descriptor, idle, cleanup, ABI and route checks all passed.
