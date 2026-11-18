# V104 candidate: native original IOS_OpenAsync request construction

V103 verifies genuine SC file-open wrapper and enter original
IOS_OpenAsync at 0x8051982C. V104 restores this 0x118-byte original
function with exact private owner DOL edge validation. The original
generated C++ must execute its GPR-save helper, IOS allocator,
interrupt disable/restore and DCFlush. Before it calls the existing
native IPC submission function at 0x805195EC, the observer compares
the actual guest request with the previously captured SC file path
and mode. It does not call the dispatcher or invent a success reply.
Pending STM event, FS descriptor, and scheduler context are preserved.
Native async IPC submission and callbacks remain separate next stages.
