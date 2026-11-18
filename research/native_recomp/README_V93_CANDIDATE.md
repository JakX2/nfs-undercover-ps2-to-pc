# V93 verified: original resource initialization return

V92 returned real /dev/fs fd 2 via original IOS interrupt/scheduler code.
V93 preserves this transaction, executes the genuine next buffer-low setter
and initializes the separate filesystem resource heap through its original
allocator and interrupt controls. Verify original heap metadata, heap
handle independent of IPC, and return to the parent NANDInit (public API
identity confirmed in metadata run 44245069668). Restore exact next
resource wrapper, check its genuine /dev/es open request. Stop before
performing that request. No generic ES service or NAND completion claimed.

Verified owner run 44245316015 on b120d547cf105bfbe90f31a844fc912b106d8b93: 16/16 trials; original heap entry, initialized independent heap/handle, FS state, preserved earlier service state, and original /dev/es pathname all verified. The native read-only ES metadata fixture passed separate sanitizer tests in run 44245407821.
