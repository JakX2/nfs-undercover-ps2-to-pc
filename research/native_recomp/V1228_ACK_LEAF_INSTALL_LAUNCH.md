# V1228: authenticate IRQ-enable leaf and OSInit caller

Derive the original previous-EE extract/BLR and caller from matching DOL/ELF, prove the native dispatcher cases, add only opt-in post-tick observers at BLR and caller with the old V616 trace preserved, and compose edits when they share a shard. Strict terminal audit requires the full original third IRQ sequence and return to OSInit; no caller instruction is executed yet. Original private run gated; CI pending.
