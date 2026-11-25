# V931: verified continuous IRQ return and cold IPC refusal diagnostics

## New verified evidence
* [V920 continuous owner run 45605112897](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45605112897), job 139174014767: actual original SI handler BLR, same-tick poll, exact outer dispatcher re-entry, preserved ABI and device state.
* [V921 continuous owner run 45605508743](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45605508743), job 139175419551: genuine captured pre-exception context remains intact through handler return, 32 GPR and six special-register fields. Latest verified continuous startup frontier.
* [V924 corrected private preflight 45606294966](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45606294966), job 139178052905: all 93 native labels and full-image syntax, no execution claim.
* [V927 focused owner run 45607942180](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45607942180), job 139183837427: 16/16 original loader + native RFI + original resumed extraction + original BLR, 4 corruption controls, split/nonsplit ASan/UBSan, zero fallbacks. Synthetic initial context and synthetic final caller.
* [V929 owner static run 45608278504](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45608278504), job 139184845404: one original direct BL immediately following IRQ enable, OSInit call ordinal 40, exact 45-word IPC client target, no intervening loads/stores/branches. Static only.

## Refusal diagnostics
The old V623 cold client admission conditions are unchanged for valid inputs. Capture the exact rejecting group as a bitmask: 1 already started/error; 2 CPU/PC/LR/MSR; 4 r3; 8 stack/SDA; 16 transport idle; 32 control/steps; 64 exact edge/word; 128 IRQ mask words; 256 mapped low-memory and IRQ table; 512 IRQ-table global; 1024 handler shape/word; 2048 heap range; 4096 SDA heap pointers; 8192 mapped heap; 16384 occupied handler slot. Report only the mask, not guest memory contents. Expanded existing V623 negative tests, and V930 workflow includes V623 regression. No mask or heap mutation is performed by this change.

V926 full continuous RFI execution and V928/V930 preparation still pending. No first native boot, main, frontend or rendered frame verified.
