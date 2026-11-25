# V849: callback return dispatcher seam

V847 owner preflight job 139068970996 passed 269 authenticated labels, 14 shared leaf labels, 18 direct edges and full-image syntax. V848 result audit also passed. V839 full-image execution remains in progress.

The previously verified V846 direct caller does not exercise the extra outer-dispatch poll and tick after a callback entered by bctrl. V849 adds an opt-in dispatcher mode to the same read-only return witness. It requires the original post-BLR PC and CPU state at the poll, exact +1 outer tick at a separately authenticated pre-label resume, then +1 at the real label. It does not alter guest state, manufacture a tick or permit an additional callback. Direct caller behavior remains unchanged. The original-free synthetic test covers both modes and eleven refusals. This is not a claim of live callback return.
