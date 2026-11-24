# V550 native startup status (2026-11-24)

## Verified results

- V526 full original Linux startup reached SI sampling checkpoint 5/6, rc=106, fallback=0, verified=0, boot_verified=0 (run 45421009588). The final witness rejected the state; this is not completed SIInit.
- V544 SHA-authenticated private DOL geometry classified the sole SI initialization flag store as after all four SIGetType calls (run 45425445343). No proprietary bytes are published.
- V546 corrects the witness to require flag 0 during queries and flag 1 at final return. Preparation requires authenticated original store ordering. The correction changes observer expectations, not guest instructions or memory. Source-only regression run 45426293091 passed: 32 sampling/IRQ negative controls and 20 discovery negative controls, with original-free test fixtures.
- V543 emits a bounded invariant-failure bitmask without disclosing guest data. Source-only run 45425351959 passed.
- V547 native PI/SI external exception path passed run 45426466181: split and non-split each ran 32 generated synthetic PowerPC trials, with 16 SI deliveries and guest acknowledgments per configuration, strict vector/source guards and no interpreter. V545 first failed because low-memory vectors defaulted to interpreter; V547 uses the existing explicit authenticated AOT vector opt-in. This is not original-game IRQ handler verification.
- Prior SRAM witness correction source regression 45424520761 passed; original SRAM execution remains unverified.

## Candidate changes

- V548 tracks corrected SI geometry in Windows owner workflow.
- V549/V550 prepare original thread initialization witness, including direct and indirect guest calls, initialized callback pointer, thread/context setup, stack sentinel and return ABI. Dedicated source test run 45426881769 was queued at this checkpoint; candidate is not installed in the owner startup lane.
- Original-image corrected Linux run 45426293326 and Windows run 45426502167 are pending behind earlier immutable builds (45422869760 and 45424294180 respectively). Earlier runs may still contain the superseded SI flag expectation.
- V542 NAND callback continuation: public unit tests passed; private replay 45424690450 remains in progress. No new original NAND execution result.

## Next gates

1. Verify corrected original SIInit sampling/discovery/return on complete image.
2. Enable the authenticated SRAM witness only after verified SI return.
3. Validate thread candidate regression and enable it after verified SRAM return.
4. Integrate and validate the actual original external interrupt handler, not merely the synthetic exception round trip.

Original main, rendered frame and gameplay are not yet verified. No boot claim is made.
