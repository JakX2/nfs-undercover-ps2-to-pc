# V773: original transfer with exact device observer

V770 owner run 45552248840 passed 16 successful original __SITransfer trials and two corruption controls (both modes); the independently reproduced compiler collision was corrected, and the remaining generated diagnostic confirmed type-limits. V772 passed all 30 original-free observer controls. V773 reuses the same original translation and guest fixture but routes actual MMIO through V772. A real preceding controller transaction is completed and acknowledged through V668; then the observer inherits its exact device, PI objects and tick. Each generated label decodes its actual PPC effective address and store operand, each actual MMIO call consumes one authorization, and the original return plus 16 generated continuation labels verify the same request. Busy cases must not issue a transaction. Synthetic predecessor/caller, original transfer and compiler/OS leaves, no continuous boot claim. Owner CI pending.

## Verified exact MMIO execution

Run 45554070854, owner-context 139003573617, passed both split and nonsplit. Each mode executed 8 successful original cases (4 idle/4 busy) and refused mask corruption. Actual translated predecessor ACK and original native transfer, exact MMIO operands, no fallback. This remains a focused fixture.
