# V444: prepare complete-image boot-info and MEM1 arena continuation

V443 passed the pinned split/nonsplit compiler root-identity regression.
Its original-game hardware continuation remains a separate owner gate.

The new manually selectable os-arena scope extends the V439 hardware
return through the V31 boot-info handoff and V32 original MEM1 low/high
setter calls. Both previously verified source validators are reused on
the unchanged SHA-pinned DOL. The original branch and store instructions
remain unmodified. The witness checks all three boot-record paths, the
low-memory source bytes/words, boot globals, preserved stack/SDA/MSR,
exact high-bound selection, low/high setter arguments and actual stores,
neighbor guards and valid ordered MEM1 bounds. A direct low hint is
checked exactly. A zero hint is limited to the previously verified
fallback candidates or the original low-memory override; this does not
claim exhaustive low-selector branch semantics.

The endpoint is the real second setter return label 0x80520818, before
MEM2 setup. No original low-memory state is seeded or replaced.
Local GCC C++20 ASan/UBSan: six positive paths, 66 negative controls and
duplicate stops passed. Python composition/audit and the private
installation remain CI gates. This is not evidence of a new owner
execution milestone yet.

Manual owner workflow scope: os-arena. Preserve the in-flight V443
hardware run as the independent prior gate. No private game data or
generated code is committed.
