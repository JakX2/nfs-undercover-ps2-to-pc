# V93 candidate: original resource initialization return

V92 returned real /dev/fs fd 2 via original IOS interrupt/scheduler code.
V93 preserves this transaction, executes the genuine next buffer-low setter
and initializes the separate filesystem resource heap through its original
allocator and interrupt controls. Verify original heap metadata, heap
handle independent of IPC, and return to the parent NANDInit (public API
identity confirmed in metadata run 44245069668). Restore exact next
resource wrapper, check its genuine /dev/es open request. Stop before
performing that request. No generic ES service or NAND completion claimed.
