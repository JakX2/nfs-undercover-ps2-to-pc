# V91 verified: original resource initialization

V90 verified 16/16, all four modes naturally choose 0x8051E7E4.
Restore that original subsystem, its resource initializer 0x804F0CDC,
and original 0x8054B4B4 leaf from the authenticated owner DOL. Extend
only bounded original-free NOP space without changing prior mapped
bytes or data. All 26 linked call edges are checked; later unimplemented
children remain explicit guards. Execute initialization state change,
interrupt restoration, original IPC bounds queries and native buffer
preparation. Validate the actual device path/mode at the next original
IOS_Open entry 0x80519944 (caller 0x804F0D68), with ongoing STM state
preserved. No open, NAND, file I/O or further subsystem is claimed yet.
The owner metadata run 44243683005 verified the new child geometry.

Verified owner run 44244293103 on 8b67b0c4740958edf0cdba03ba878043b5befa3e: all sixteen trials, actual original /dev/fs pathname in MEM2, buffer and ABI predicates passed. The original leaf creates the pathname after restoring the exact owner-initialized literal. Native filesystem runtime and independent generated IRQ roundtrip tests passed separately; V92 integrates the actual game request.
