# V99 verified: post-NAND original sibling memory preparation

Authenticated V100 metadata run 44252913524 established that the
original post-NAND sibling at 0x8052F94C has four direct calls:
memset, two memcpy calls, and the next helper at 0x8051DFF4.
V99 restores only the sibling body plus an explicit next guard.
The original memory operations execute natively; the observer checks
every written byte against the actual source or fill argument.
Retains shutdown-list, copied NAND directory, original scheduler and
IOS state checks. The V99 owner-original run 44253242304 passed all 16 trials at checkpoint\n0x8051DFF4, including the original memory operations and earlier\nIRQ, IOS and NAND regressions. This is not a completed OSInit/game boot.
The conditional NAND helper 0x8051E5BC remains separately mapped, not
forced by changing any guest branch.

Owner-original V99 CI run 44253242304 verified 16/16 original SCReloadConfFileAsync memory preparation, 2 copies and original call into SC initialization. Public SDK symbol matches established these function identities after V99. No complete SC initialization was claimed.

Next validated research milestones: V100-V103 follow the original SC\nstatus, configuration pathname and asynchronous file-open wrapper.\nThe V104 owner test is investigating the original IOS_OpenAsync cache\nand request submission. No IOS callback or full game startup is claimed.\n