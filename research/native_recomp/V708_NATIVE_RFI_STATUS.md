# V708: generated native full integer-context SI exception return control

Build independent synthetic PPC vector saving all scratch GPRs, saving and deliberately changing CR, writing actual SI status and COMCSR W1C, restoring CR and GPRs and executing native rfi. Uses actual native external exception entry, V706 pre-RFI snapshot witness, both real generated callback boundaries and exact native resume label. 16 varied register patterns per split/non-split mode, sanitizers, no interpreter. No original program bytes and no original context-loader execution claim. CI pending.
