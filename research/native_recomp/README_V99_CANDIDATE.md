# V99 candidate: post-NAND original sibling memory preparation

Authenticated V100 metadata run 44252913524 established that the
original post-NAND sibling at 0x8052F94C has four direct calls:
memset, two memcpy calls, and the next helper at 0x8051DFF4.
V99 restores only the sibling body plus an explicit next guard.
The original memory operations execute natively; the observer checks
every written byte against the actual source or fill argument.
Retains shutdown-list, copied NAND directory, original scheduler and
IOS state checks. No claim of a full NAND/OSInit return until tests pass.
The conditional NAND helper 0x8051E5BC remains separately mapped, not
forced by changing any guest branch.
