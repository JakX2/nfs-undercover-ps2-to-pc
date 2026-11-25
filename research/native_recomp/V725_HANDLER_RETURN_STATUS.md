# V725: authenticated SI-handler integer ABI return witness

V718 owner execution (run 45541619108) establishes the exact masked local conditional-backward-branch poll refusal after all three original leaves and nested return. V719 implements that boundary; its full execution run remains separate.

V725 introduces an independent, read-only witness for a subsequent handler suffix. It captures entry ABI state, begins only at the second-helper return, checks each exact instruction label and expected branch outcome (including CTR/CR tests), requires an unchanged masked callback boundary, rejects unknown linked/indirect/external branches and checks preserved r1/r2/r13/r14-r31 and CR2-CR4 at the original return. It verifies the two-tick outer-dispatch resume geometry separately. SI/PI state is supplied by the surrounding authenticated ACK witness. This is a synthetic witness control, not yet a complete-image installer or original handler return. It is intentionally not allowed to enable a scheduler, manufacture MMIO state or claim FPU restoration.

V724 independently corrected the scheduler fixture's overlapping-root problem and waits for owner tests.
