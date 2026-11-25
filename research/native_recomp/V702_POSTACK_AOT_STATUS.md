# V702: generated PPC continuation beyond actual SI W1C

Independent translated PPC control executes real COMCSR load/W1C, then actual status W1C, calls nested helper after ACK, reads cleared status and writes communication RAM through actual MMU. Native LR save/restore and ABI return observed. Stop-at-ACK regression and a deeper-call refusal are tested separately; split/non-split compilation uses production V699/V693 patches and sanitizers. No original program bytes. Original-free CI pending.
