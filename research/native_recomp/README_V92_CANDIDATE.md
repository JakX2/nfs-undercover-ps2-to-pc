# V92 candidate: original filesystem open return

V91 verified the genuine /dev/fs request in 16 owner trials. V92 mounts an
explicit empty read-only guest resource filesystem at the beginning of
each trial and executes the third original IOS_Open continuously with all
prior original STM state. Reuses the verified synchronous request
allocation, flush, submission, ACK, sleep, two original external IRQs,
scheduler wake/RFI, and free path. Observer counters may restart, but CPU,
guest RAM, mailbox, descriptors and outstanding asynchronous request do not.
The terminal call is the original buffer-low setter at 0x8051908C from
0x804F0DC0. Verify fd 2 stored by the original initializer and unchanged
STM output, request/result and event pending state. No complete filesystem
initialization is claimed until owner verification passes. No host paths
or proprietary files are mounted.
