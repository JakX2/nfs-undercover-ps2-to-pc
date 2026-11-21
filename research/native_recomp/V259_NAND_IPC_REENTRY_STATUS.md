# V259: original NAND callback reaches IPC helper (verified)

Date: 2026-11-21. Branch: research/wii-native-recomp-preflight.
Owner-native workflow: https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44959441360

## Verified original PowerPC execution

The V259 workflow passed both public-original-free and owner-original jobs.
The private job passed **16/16** guest trials with the SHA-verified
owner DOL and NWiiRecomp-generated native C++.

The restored original NAND callback executed through its genuine child
at 0x8052FA60, returned to 0x8051E0B8 (V256), and subsequently entered
0x8051AD3C with LR 0x804F0F68 (V257). From that ongoing original
guest path, the native translator reached IPC helper entry
**PC 0x8051906C, LR 0x805192EC**, without forcing the CPU PC, LR,
registers, memory, IOS reply or any original game instruction.

    V259_SC_IPC_REENTRY verified=1
    V259_IPC_REENTRY guest=1 caller=1 mapped=1 coherent=1 reply=1 second=0 sc=1 pc=8051906c lr=805192ec
    PASS: 16 owner-original native NAND-to-IPC reentry checkpoints

The second=0 field is important. This probe observes a PowerPC
function entry, not the actual PPCMSG/MMIO store or a newly published
second request. The existing IOS reply was present (reply=1) and
small-data SC byte remained 1. The interrupt-pending/EE predicate was
coherent. No SYSCONF open success or complete NAND callback return
is claimed.

## Original-free sources

- derive_v259_ipc_reentry_harness.py: opt-in original-PC/LR-gated
  guest entry checkpoint and per-trial assertions.
- derive_v259_ipc_reentry_runner.py: inherited 16-trial driver
  with fail-closed source anchors and superseded final-state checks.
- run_v259_ipc_reentry.sh: ephemeral private owner runner.
- test_v259_ipc_reentry.py: source-only derivation, ABI, mutation and
  shell syntax regressions.
- .github/workflows/wii-v259-ipc-reentry.yml: private-gated original
  workflow, SHA-pinned staging, pinned NWii runtime, bounded public
  markers and explicit owner-private cleanup.

Proprietary DOL/ELF, AOT-generated game C++, assets and raw execution
logs remain private and are deleted by owner CI.

## V258 investigation

V258's direct return checkpoint for 0x8051AD3C to 0x804F0F68
did not complete within a bounded 32-call restored-callback phase.
Owner run https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44958637519
reported "V258 restored NAND bounded guest call budget exhausted",
not a guest-context or first-two-callsite mismatch. This does not
prove the callee never returns. V259 instead establishes the
already-observed original IPC entry without widening the budget
indefinitely.

## Next original-code milestone

1. Execute onward from the V259 IPC helper entry and locate the actual
   PPCMSG/MMIO store, recording the authentic guest and physical
   request addresses.
2. Compare the native IOS message at submission with the successful
   first open and previously malformed /shared2/sys/SYSCONF request.
   Probe MEM2 alias coherence and RAM visibility before changing IOS.
3. Preserve genuine -4 negative IOS replies and hardware interrupts.
   Do not synthesize descriptors, skip retries or alter game code.
4. Advance continuous original startup execution. Complete game main,
   first frame, frontend and gameplay are not achieved.

The existing hourly Undercover development task continues unchanged.
