# V71: original IOS_Open to synchronous IPC submission (candidate)

Restores authenticated owner IOS_Open at 0x80519944 (0x120 bytes), its original profiling leaf, and the original cache flush path. Stops explicitly at synchronous submission entry `0x805195EC` without injecting a fake IOS return. Native pathname cache flush, SC/rfi preservation, callsite and request argument shape are checked privately. Only bounded register-class masks are emitted. V70 remains independently verified. Owner CI pending.
