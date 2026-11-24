# V533–V542: SI completion, SRAM DMA, audio register groundwork and NAND successor lifetime

## Verified results (2026-11-24)

- Windows original complete-image SIInit entry passed, six of six stages, no interpreter fallback; strict loader and instruction timing checks passed. [Owner run](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45421104304).
- V536 explicit nonzero synthetic 64-byte SRAM profile: actual generated PPC in both split and nonsplit modes drove native profile-backed MMIO and DMA; five negative controls passed in each mode. [Pinned integration](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45423479753).
- V537 stateful Hollywood audio ACR register subset: 16 seed profiles passed read/modify/write preservation, strict access width and device isolation. This is opt-in register state, not PLL timing or DSP/audio playback. [Pinned integration](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45423895395).
- V534/V535/V541 SRAM witness: actual modeled EXI scheduler and DMA, exact guest call edges and original return-label checks; 18 negative controls passed. Earlier C++ fixture incorrectly assigned different entry words to repeated calls to the same target; V541 corrected the fixture, not the original witness checks. [Corrected witness](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45424520643).

## Original execution candidates

- V533: independent Linux os-si-return scope, four original SI queries, immediate native NOREP and three queued guest packets, ending at SRAM initializer entry. [Run](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45422869760), pending at documentation time behind [V526 sampling](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45421009588). The predecessor remains independently testable.
- V540: Windows os-si-sample scope with explicit VI selector and SI/EXI profiles. [Run](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45424294180), in progress.
- SRAM witness and DMA prerequisites are prepared and independently tested. Original complete-image SRAM entry/return scope is not yet enabled, pending the original SI return and broader regression results.
- V542: [V528 replay](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45421320861) confirmed guard 1237, post_ack, at the old post-run successor assertion. Guest candidate rc=134; CI success signifies a successful audit, not guest boot. V508 historical ACK witness succeeded with 44 calls, 25 unique original call targets, one begin, one BLR and one resume; the later live snapshot no longer matched the earlier successor. V542 checks the historical successor using the existing event-time latches, preserves the legacy stop comparison as a diagnostic and retains later guest guards. No guest state is mutated. [Candidate replay](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45424690450), not yet verified.

## Boundaries and next steps

Keep private owner binaries and translated game code outside the repository. Synthetic hardware profiles are explicit and deterministic, not retail hardware detection. The port does not yet demonstrate original SIInit return, SRAM initialization return, OSInit completion, main, a rendered frame or gameplay. Continue in original startup order; enable the SRAM owner scope only after SI return and relevant regression checks succeed. Then investigate the remaining OS services and audio clock/DSP behavior.
