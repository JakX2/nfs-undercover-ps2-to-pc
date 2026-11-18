# V97 candidate: original ES close return

V96 verified both original ES metadata requests. V97 executes the
original directory copy, ES close wrapper and IOS_Close, checking
the authentic request, native descriptor closure, IRQ/scheduler
return, original cleanup and preserved FS/STM state. Stop at
shutdown callback registration 0x80527B4C, not full NANDInit.
Synthetic title fixture remains explicitly configured; no actual
title identity or real NAND filesystem contents are inferred.
