# V97 verified: original ES close return

V96 verified both original ES metadata requests. V97 executes the
original directory copy, ES close wrapper and IOS_Close, checking
the authentic request, native descriptor closure, IRQ/scheduler
return, original cleanup and preserved FS/STM state. Stop at
shutdown callback registration 0x80527B4C, not full NANDInit.
Synthetic title fixture remains explicitly configured; no actual
title identity or real NAND filesystem contents are inferred.

Verified owner run 44251108152 on bdd3de290818ed8338bfea544b57f16974d1980f: 16/16 trials; directory copy, native descriptor closure, original IRQ/scheduler resume and preserved device state all passed. V98 executes the original already-translated shutdown registration; no fixture code changes needed.
