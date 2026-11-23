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
| V376 | Native original-boundary PowerPC exception entry implemented and under owner CI validation | Do not claim original handler or frontend has executed |

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

Both authenticated jobs still reported an incomplete original bounded-harness
outcome. A native process exit code of zero is **not** a successful harness
or proof of full Wii boot.

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

The next owner-private checkpoint must confirm V376 actually entered
the original vector and persisted its saved CPU state. Only then should
the bounded native runner resume translated instructions from
`0x80000500`, verify the original OS exception handler, and progress
toward `0x80519318` registered IPC handling, callback execution and
NAND startup completion.

## Windows original-free regression

From a Windows checkout on `research/wii-native-recomp-preflight`, with
Visual Studio C++ build tools or MinGW-w64 on PATH:

```bat
research\native_recomp\windows_nand_reply_selftest.bat
```

This tests V374 and V376 native IPC/exception behavior without any game
image. It is useful for Windows portability, but it is not a substitute
for the private authenticated game-code execution workflow.
