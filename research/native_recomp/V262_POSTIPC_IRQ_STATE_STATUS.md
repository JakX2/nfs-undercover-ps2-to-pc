# V262: original Wii post-IPC guest-call IRQ/IOS state, owner verified

Date: 2026-11-22. Branch: `research/wii-native-recomp-preflight`.
Verified public and owner-original workflow:
https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44967631257

## Native original-game result

**16/16** original-owner Wii DOL / NWiiRecomp-generated C++ native trials
passed. V262 observes the *same* 64 guest function-call entries as the
verified V260/V261 experiments, with the same `PC=0x805265D4`,
`LR=0x8052F92C` terminal call.

The observed read-only host/device state is identical across all trials:

```text
V262_IPC_STATE verified=1
V262_IPC_STATE trials=16 calls=64 stable=1 distinct=1 ee_edges=38 irq_edges=0 request_edges=0 queue_edges=0 sc_edges=0 irq_ever=0 request_ever=0 queue_max=0 reply_all=1 sc_first=1 sc_last=1 digest=2cd3996a9e2720bd
V260_CALL_FRONTIER guest=1 coherent=1 mapped=1 calls=64 sc=1 pc=805265d4 lr=8052f92c
PASS: 16 owner-original IPC state-census trials
```

The original PowerPC interrupt-enable bit (`MSR_EE`) changed 38
times between consecutive observed guest calls. In that window:

- Native external IRQ level stayed **deasserted**; no IRQ edges.
- No new native IOS request was pending; no request-state edges.
- The native IOS reply queue remained empty; no queue-state edges.
- Guest small-data SYSCONF status `r13-3176` stayed `1`.
- The original first IOS reply remained visible for every sample.
- All 16 independent trials had an identical guest-observed state
  sequence; no extra PowerPC calls were executed beyond the V260 bound.

## Interpretation and limits

Combining V261's 10 distinct PC/LR callsite pairs (54 repeat entries)
with this V262 profile identifies a **small repeated guest-call set**
that enters and leaves interrupt-enabled state repeatedly while there
is no *new* observable IPC mailbox intake, reply queue activity or
external IRQ assertion.

This may be normal polling, scheduler work or a missing emulated source
of progress. It **does not by itself prove** deadlock, missing IOS
hardware behavior, or an infinite loop. The small-data SC byte did not
change within the sampled interval. Inspect the actual repeated
callsite, timebase/alarms and guest wait condition before modifying
runtime semantics.

The second original `/shared2/sys/SYSCONF` request has **not** been
re-observed in this restored callback path. Existing negative `-4`
IOS reply behavior from the earlier reduced callback test remains the
authentic failure and must not be overwritten with a fake descriptor.

## Source and workflow

- `derive_v262_ipc_state_harness.py`: inserts read-only IRQ, EE,
  native pending-request, queued-reply and SC status sampling at the
  already-authenticated 64 guest calls.
- `analyze_v262_ipc_state.py`: checks 16 complete 64-sample traces
  with mapped SC, consistent authentic last state, and outputs only
  aggregate transitions/digest.
- `derive_v262_ipc_state_runner.py`,
  `run_v262_ipc_state.sh`, `test_v262_ipc_state.py`: preserve V260/
  V261 owner-original trial invariants and regression tests.
- `.github/workflows/wii-v262-ipc-state.yml`: owner SHA staging,
  pinned NWiiRecomp, public regression and private guest checks,
  restricted failure summaries, and private data cleanup.

### Derivation-chain engineering correction

The initial V262 owner job failed before compiling due to a
`RecursionError` in the stacked Python milestone generator. The final
V262 derivation **composes V261/V262 sampling directly on the
known-good V260 source seam and runner**, avoiding another recursive
transformation layer. The green owner-original run proves this approach
can derive, compile, link and execute the correct private fixture.
No extra test bypass, synthetic guest branch or fabricated IOS reply was
introduced.

## Recommended next original-game investigation

1. Classify the most frequent PC/LR pair and source caller in V261's
   64-call window, retaining raw code and operands privately.
2. Verify whether the repeated loop checks a timer, OS thread flag,
   NAND callback completion, or an IRQ/IPC condition. Compare
   instrumented guest registers/memory against an authentic reference.
3. Implement missing real Wii runtime behavior only when supported by
   an original-code discrepancy, then require progression beyond this
   call window and to the eventual authentic PPCMSG packet.
4. Continue the larger startup/full-link effort. Game `main`, first
   native frame, frontend and gameplay are **not** achieved.

The existing hourly Undercover automation is unchanged.
