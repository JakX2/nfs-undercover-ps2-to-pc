# V775: exercise complete transfer return observer on original code

The V774 read-only CPU witness now runs alongside the verified original V765 native translation, not merely a hand-simulated instruction sequence. The original save and disable leaves are observed through the preceding ACK witness, the exact current scheduler profile is acquired at disable BLR, and subsequent accesses use V772. Require one authenticated IRQ restore lane, original compiler restore, original LR and ABI, guest SI data, exact total tick count and all 16 native synthetic continuation labels. Includes eight valid cases per compilation mode and mask corruption refusal. Original caller continuation is synthetic; no full-image execution yet. Private CI pending.

## V776 actual translated predecessor ACK

First V773 private execution refused at the first synthetic caller label before original transfer (run 45553735167); the synthetic pre-staged ACK did not include the dispatcher's outer native tick. Instead generate an independent actual PPC `stw` to COMCSR, a NOP successor, and the linked original call. Arm at the native entry trace, acknowledge via the actual generated MMIO store and inherit at the real call label or disable return. No host-side tick rewind or fake W1C in either V773/V775 fixture. Existing V765 fixture geometry remains unchanged by default. Retest pending.

## Verified original execution

Run 45554070790, owner-context 139002582023, passed both split and nonsplit. Each mode executed 8 successful original return cases (4 idle/4 busy, 4 new native requests and exact MMIO) and refused mask corruption. The native predecessor W1C and all original transfer leaves execute with no fallback. V777 full-image execution is enabled in V779. The fixture is not continuous startup.
