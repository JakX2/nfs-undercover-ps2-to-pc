# V94 verified: authentic fourth service open and title query

V93 verified original FS initialization and /dev/es open entry. V94
explicitly configures a synthetic metadata fixture at trial start;
the actual owner title ID is NOT inferred from that value. Execute
the original fourth IOS_Open through original IRQ/scheduler/allocator
path, check native ES fd 3 and all earlier device and deferred state.
Restore the original next wrapper (0x804F0B70, size 0x98) and validate
its actual command 0x20, zero input/one output vector, 8-byte output at
the original IOS_Ioctlv entry 0x8051A62C. No title reply is performed in
V94. The runtime supports only explicitly configured read-only title
metadata; no title changes, entitlement checks or title launches.
The owner's Drive currently contains extracted game data, DOL/ELF,
and banner but no disc header in that folder. A real title ID should
come from authenticated original disc metadata or owner configuration.

Verified owner run 44245632393 on 1cd6051be554bba3f9f34eda5a0d0e55b8da4633: 16/16 trials; exact fourth original open completed and command 0x20 output-vector ABI verified. All prior descriptors and asynchronous STM state preserved. No title response in V94. V95 dependency metadata run 44248186373 verified original vector helper geometry.
