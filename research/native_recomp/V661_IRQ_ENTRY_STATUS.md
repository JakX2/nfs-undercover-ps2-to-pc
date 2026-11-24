# V661: continuous startup IRQ entry refusal

V653 owner run 45506973808 verified 4/4 SC, 5/5 DSP, 20/20 MI, 17/17 report and 24/24 arena checkpoints, fallback=0. IRQ entry refused with exit 119 before any IRQ checkpoint. The actual failure is not yet known.

V660 owner run 45508871063 verified 8/8 original heap, request construction, submission and native ACK trials, 522 authenticated translated words, no fallback. These are isolated tests, not complete-image startup or guest reply delivery.

V661 preserves all IRQ entry predicates and exports only a bounded refusal bitmask and the enabled pending PI bits, on the exact failure. Bit values: 1 previous stage/error; 2 not running; 4 PC/LR; 8 EE already enabled; 16 saved dispatch context; 32 pending enabled PI interrupt; 64 call word; 128 DBInit pointer; 256 SDA; 512 resume geometry; 1024 opt-in absent. No pending interrupt is cleared and no guest state is changed. The original V68 fixture explicitly verified DBInit writes the expected low-memory pointer, so it is not removed on speculation.

Next: inspect actual V661 diagnostic, correct the specific source of the mismatch, and continue original execution through IRQ, IPC and STM. Windows report owner run remains separate. NWiiRecomp remains pinned and primary; no third-party runtime source copied.
