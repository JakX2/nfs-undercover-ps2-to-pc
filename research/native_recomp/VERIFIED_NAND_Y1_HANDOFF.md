# Original Wii NAND -> native IOS reply -> Broadway Y1 handoff

> Status: verified **partial native Wii startup execution**, not game boot.
> Owner-private Wii binaries and recompilation outputs must not be published.

## Authenticated original-game evidence

The owner-original AOT lane uses the independently restored original Wii NAND
functions and an original guest IPC request. The host-side native IOS broker
dispatches only requests submitted by genuine guest PPCMSG/PPCCTRL.X1 writes.
Historical SC-only one-shot observers are phase-scoped, not used as a shortcut
or as proof of NAND callback completion.

| Milestone | Evidence | Limit |
|---|---|---|
| V361 | Real native Starlet ACK, queued IOS response | No automatic completion publication |
| V370 | Genuine guest Broadway PPC_FLAG write-one-to-clear | IRQ may be reasserted by subsequent IOS activity |
| V374 | Queued native IOS reply published; hardware Y1 and Hollywood IRQ asserted | No original guest handler execution proved |
| V373 after V374 | Earliest interrupt-eligible call sample **25** with guest MSR.EE enabled | Read-only timeline, not an exception entry |
| V375 | First observed eligible Y1 guest call boundary is preemptible; installed original vector byte-verified | Read-only probe, no guest PC change |
| V376 | Owner-original Y1 interrupt entered the installed PowerPC vector with saved SRRs and intact registers | Stops before executing the vector instructions |
| V377 | Translated original vector executed and reached the Wii OS exception handler at `0x80526CE0` | Stops at handler entry |
| V378 | Original Wii OS exception-handler body executed and reached the IRQ dispatcher at `0x80526A3C` | Dispatcher body not yet completed |
| V379 | Original IRQ dispatcher called genuine `OSGetTime` at `0x8052A824` | No registered IPC handler yet; first original helper not fully executed |
| V380 | Original `OSGetTime` to `OSDisableScheduler` continuation staged in owner CI | Pending authenticated original test |
| V381 | Registered IRQ slot 27 IPC handler continuation staged separately, unpublished pending V380 result | Not a verified NAND milestone |

### Repeatable sanitized outcomes

Owner run [45112677839](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45112677839)
reported:

```text
V374_NAND_REPLY_CENSUS rc=0 kind=zero size_band=1 sample_complete=0 samples=12 ready_any=1 blocked_y_any=1 blocked_flag_any=1 serviced_any=1 replied_any=1 y1_any=1 queued_any=1 irq_any=1 eligible_any=0
V373_IRQ_CENSUS rc=0 kind=zero size_band=1 sample_complete=0 samples=96 first_ee=25 first_irq=1 first_ready=25 ee_any=1 irq_any=1 eligible_any=1 safe_any=1 installed_any=1 y1_any=1 y2_any=1 flag_any=1 queued_any=1
```

The V374 census samples the scheduling call with EE initially masked,
so `eligible_any=0` **within that V374 gate** is consistent with V373
later reporting eligibility when the actual original guest enables EE.

Owner run [45114026372](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45114026372)
reported the V375 original guest boundary:

```text
V375_Y1_BOUNDARY_CENSUS rc=0 kind=zero size_band=1 sample_complete=0 samples=24 first_preemptible=1 call_any=1 running_any=1 free_any=1 aligned_any=1 mode_any=1 installed_any=1 preemptible_any=1 drained_any=1 site_mask=4
```

The site mask identifies a genuine non-IPC ordinary guest function entry
(category 3), not the special OSRestoreInterrupts or IPC callback entries.
`first_preemptible=1` means the earliest *sampled* original call entry
met the native exception-entry requirements; it does not identify a full
arbitrary instruction preemption mechanism.

These earlier authenticated jobs still reported an incomplete original
bounded-harness outcome. A native process exit code of zero is **not** a
successful full harness or proof of Wii boot.

### Verified original guest IRQ-chain checkpoints

Owner run [45114526907](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45114526907)
demonstrated a real NAND Y1 PowerPC exception entry, preserving SRR state:

```text
V376_NAND_VECTOR_CENSUS rc=134 kind=signal size_band=0 sample_complete=1 samples=1 eligible_any=1 safe_any=1 installed_any=1 entered_any=1 saved_any=1 regs_any=1 masked_any=1 queued_any=0 handler_executed=0
```

Owner run [45116268379](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45116268379)
verified execution of the actual installed guest vector through the Wii OS
exception-handler entry (the bounded log contains 13 paired observations):

```text
V377_NAND_HANDLER_CENSUS rc=0 kind=zero size_band=0 sample_complete=0 vectors=13 handlers=13 trials=13 vector_any=1 handler_any=1 trial_any=1 chain_verified=1
```

Owner run [45117070790](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45117070790)
verified that the translated original exception-handler body called the real
Wii OS IRQ dispatcher. Its first bounded dispatcher checkpoint succeeded,
although a later historical SC-phase assertion aborted the overall run:

```text
V378_NAND_DISPATCH_CENSUS rc=134 kind=signal size_band=0 sample_complete=1 entries=1 trials=1 entry_any=1 trial_any=1 dispatch_verified=1
```

The per-trial instrumentation counters were subsequently reset before each
authentic NAND replay. Owner run
[45118275944](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45118275944)
then verified 13 corresponding guest dispatcher-to-timebase observations:

```text
V379_NAND_TIME_CENSUS rc=0 kind=zero size_band=0 sample_complete=0 entries=13 trials=13 entry_any=1 trial_any=1 guest_time_verified=1
V378_NAND_DISPATCH_CENSUS rc=0 kind=zero size_band=0 sample_complete=0 entries=13 trials=13 entry_any=1 trial_any=1 dispatch_verified=1
V377_NAND_HANDLER_CENSUS rc=0 kind=zero size_band=0 sample_complete=0 vectors=13 handlers=13 trials=13 vector_any=1 handler_any=1 trial_any=1 chain_verified=1
```

`sample_complete=0` means these are verified pairs **within the bounded
retained public log sample**, not proof of exhaustive execution across the
original game. The original game has not booted, reached its frontend or
completed the NAND callback. Overall workflows can still fail on inherited
full-startup obligations despite a successful bounded checkpoint.

## Hardware and execution invariants

V374 advances one native completion only at the authenticated original
OSRestoreInterrupts entry, with no pending X1, both previous Broadway Y
flags clear and the previous Hollywood IPC flag acknowledged. A published
Y1 is delivered through the genuine native IPC/PI mask chain, preserving
the original IOS response including negative errors.

V376 uses the already-tested `native_external_irq.h` PowerPC exception
bridge and `wii_nand_y1_exception.h`. The helper requires a real Y1
(without Y2), a latched Hollywood flag, no unacknowledged X1 intake, guest
MSR.EE enabled, a preemptible call boundary, and exact installed
`0x80000500` vector bytes. It saves the interrupted PC in SRR0 and
masked MSR in SRR1 without rewriting guest GPR/LR/CTR/XER. Other queued IOS
completions are allowed to remain waiting because they do **not** invalidate
a Y1 that is already on the wire. The harness stops after entering the
vector to avoid accidentally executing the preempted function with a
different PC.

V376 has now been authenticated in the owner run. V377, V378 and V379
executed progressively larger portions of the installed original Wii vector,
OS exception handler, dispatcher and `OSGetTime` entry.

The next verified frontier is V380: execute the original `OSGetTime`
instructions and observe the genuine `OSDisableScheduler` call at
`0x805293F8`. After that, V381 will execute the original scheduler and
check dispatch to the guest-registered IPC handler at `0x80519318` with IRQ
slot 27 and the original saved exception frame. These NAND-specific tests
must not borrow the SC-only previous IOS reply values or force a successful
IOS response. Completion of the actual NAND callback and full native Wii
boot remain unverified.

## Windows original-free regression

From a Windows checkout on `research/wii-native-recomp-preflight`, with
Visual Studio C++ build tools or MinGW-w64 on PATH:

```bat
research\native_recomp\windows_nand_reply_selftest.bat
```

This tests V374 and V376 native IPC/exception behavior without any game
image. It is useful for Windows portability, but it is not a substitute
for the private authenticated game-code execution workflow.
