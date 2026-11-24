# V471–V473: Windows IPC verified; exception and IRQ continuation

2026-11-24. Branch: `research/wii-native-recomp-preflight`.

## Authenticated owner results

* Linux complete-image startup through MEM1/MEM2 and IPC: [run 45323907871](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45323907871). This remains the verified Linux boundary.
* Windows x64 complete-image link and bounded startup through IPC: [run 45326919896](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45326919896). The published markers include:

  ```
  V426_WINDOWS_LINK linked=1 platform=windows-x64 synthetic=0 boot_verified=0
  V446_IPC_CENSUS rc=0 arena=1 stages=4 clamp=0 fallback=0 reason=0 terminal=1 legacy_chain_complete=0 verified=1 boot_verified=0
  V429_WINDOWS_OWNER_SCOPE scope=os-ipc verified=1 boot_verified=0
  V436_WINDOWS_LOADER strict=1 equivalence=1 launch_verified=1 boot_verified=0
  V441_WINDOWS_TICKS corrected=1 launch_verified=1 boot_verified=0
  ```

  The canonical ancestor gate passed; `legacy_chain_complete=0` is the diagnostic legacy-normalization flag, not an indication that the canonical prefix failed. Original exception entry is verified, not exception initialization completion.
* V464 separate reduced NAND diagnostic: [run 45326821583](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45326821583). An exact missing 33-word original body was restored and reached. The trace grew from 6 distinct entries (5 original) to 23 (22 original). The guest still exited with 134 and no callback BLR/resume. The first non-original entry is now a NOP placeholder. A green diagnostic workflow is not a successful guest boot.

## V471

Commit `2ce463611e7263dbb26543145f9618aefc6e3ace`.

Reconstructs both earlier authenticated repairs and validates their generated-source identities before restoring the uniquely observed NOP span. Requires exact or unique interior ELF extent, complete all-NOP replacement, unique AOT body and dispatch, and reversible DOL changes. Preserves the original observed route through the repaired entry, but permits divergence after it. Original-free tests passed in [run 45328558334](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45328558334); owner result pending at this writing.

## V472

Commit `ba5d85b76b211bff5635a719c7c8f9610b14f8fd`.

Windows owner scope now supports `os-vector` and `os-pack`. The earlier `os-ipc` contract remains selectable. Vector scopes reuse the Linux cache patch composition plus the Windows portable emitter and strict loader. Default owner scope is first vector. Source/contract tests passed in [run 45328707091](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45328707091); Windows workflow [45328707080](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45328707080) pending completion.

## V473

Commits `c0d9cca8b46c87de35ae4d1867c20a09a9850aaa` and `ccc424fac18a67d653524678442e90b2a9730b78`.

Composes V470 alarm return with original module init, original IRQ init, memset and fill entry checks, and an exact instruction-label observer at the IRQ memset return. Checks three module low-memory words, IRQ-table pointer, all 128 cleared bytes, neighboring words, preserved OSInit frame and authenticated direct branches. No guest writes or host substitutions are introduced by the observer. Stops before IRQ mask/MMIO setup. Seventeen negative controls plus geometry, composed install, generated-header compile and audit tests. Source-only verification [45328925558](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45328925558) pending at this writing.

## Remaining work

Do not replace or cancel the already running first-vector Linux control [45325609248](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45325609248) or queued full pack [45328136774](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45328136774). V470 and V473 are prepared private observers; they are not yet selected by an owner full-image build scope. Promote them only after their test and predecessor gates pass. Diagnose any owner failure before adding unrelated checkpoints. Next priorities: alarm/module/IRQ completion, real interrupt mask and hardware services, full OSInit return, then original main. None of those later milestones, a first rendered frame or playable gameplay are verified.

All owner binaries, generated original-derived C++, raw private logs and extracted instructions remain private and ephemeral. No original game assets are distributed.
