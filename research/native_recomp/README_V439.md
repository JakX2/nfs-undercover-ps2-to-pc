# V439: complete-image OSInit hardware-value continuation candidate

The authenticated V435 Linux owner run 45315489018 passed all six OS time
stages, exit zero, no interpreter fallback. Its terminal is the entry to
the second interrupt-disable call, before that helper's body executes.

The new os-hardware scope continues from this exact verified boundary
through the original exec-params helper (including the optional genuine
28-byte memcpy tail), six performance SPR helpers, HID4, nested HID0
speculation control and FPSCR non-IEEE bit setup. It ends at the original
OSInit return label 0x80520700, before executing the next instruction.
The previous isolated V27–V30 original-game results establish the expected
semantics, not full-image execution.

The runtime composition adds the earlier V29 performance-SPR value patch
before V18/V20, verifies the combined state, then applies the V30 HID4/FP
patch. It retains V435's entire prefix. No guest code or memory is seeded.
The witness verifies exact call and return words, the actual exec-params
copy or first-word clear, unchanged neighboring bytes, masked MSR, SDA and
stack, timestamp, all six zero SPRs, HID4, HID0 and FPSCR. These are value
models, not performance-event or hardware timing simulation.

Local ASan/UBSan: four parameter modes, 44 negative controls, eight passing
paths and duplicate-stop checks. The private preparer and combined native
runtime still require owner CI. Existing scopes are preserved, and V438's
independent timing patch is not yet applied here. No game main, full OSInit
or first frame claimed. No private game material published.
