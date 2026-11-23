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
| V380 | Original `OSGetTime` returned through IRQ dispatcher to `OSDisableScheduler` at `0x805293F8`; 13 bounded positive observations | Stops at scheduler entry |
| V381 | Original `OSDisableScheduler` body called the guest-registered IRQ slot-27 handler at `0x80519318`; saved frame and live Y1 verified | Stops at IPC handler entry, no NAND callback |
| V382 | Original IPCInterruptHandler executed to a naturally linked translated guest helper; live Y1 and known helper classification observed | Does not identify which specific IPC helper or reply callback |
| V383 | Original `IPCInterruptHandler` register read at `0x8051905C` executed and called `IpcReplyHandler` at `0x805190C0` | Stops at reply handler entry, no ACK or callback |
| V384 | Original `IpcReplyHandler` executed its first IPC register-read callee `0x8051905C`, LR `0x805190E8`; 12 positive owner observations | Stops at first register-reader entry |
| V385 | Original `IpcReplyHandler` performed a second `IPCReadReg` at `0x8051905C` (LR `0x805190FC`); live NAND ARMMSG coherency checked in the native bus | Stops at second reader entry; no Y1 acknowledgment |
| V386 | Second reader executed into the next genuine translated guest callee; retained 12 valid pairs, hardware Y1 still asserted | Historical SC writer/callsite and cache classification absent, actual callee unresolved |
| V387 | Original post-reply callee executed into another genuine guest function with Y1 still pending; 12 bounded positive pairs | No original Y1 ACK and no historical IPC writer match in sampled frontier |
| V388 | Original Wii reply-handler guest call chain reached the PPC register writer and issued genuine Broadway `PPCCTRL.Y1` W1C; retained 12 verified pairs | Hollywood `PPC_FLAG` still asserted, no NAND callback or boot |
| V389 | Original Wii PowerPC subsequently issued a distinct Hollywood `PPC_FLAG.IPC_PPC` W1C, lowering the native IRQ level; 12 bounded verified pairs | No return to NAND callback yet |
| V390 | Original translated NAND IPC reply handler executed past both hardware ACKs to its post-ACK cache-invalidation helper; 12 retained authentic pairs | Cache-helper entry only; NAND callback not reached |
| V391 | Second authentic post-ACK, reply-handler-owned call identified as another cache-related guest callee; 12 retained positive owner pairs | No context or callback call observed in retained V391 boundary |
| V392 | First reply-handler-owned non-cache guest callee after repeated cache work classified as Wii OS context management, 12 retained original observations | No callback observed; exact context target not exported by sanitized census |
| V393 | Original Wii context-management code proceeded to guest `OSSetCurrentContext` at `0x805228CC` from the reply handler; 12 verified pairs | No ISFS callback entry; original setter body unverified |
| V394 | Continue genuine `OSSetCurrentContext` into original `_isfsFuncCb` at `0x804F0E04`, classifying live IOS header/ABI | Owner-original test pending; not proof of NAND completion |

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

Owner run [45121381861](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45121381861)
confirmed the authentic Wii IRQ dispatcher executed the original `OSGetTime`
body and reached `OSDisableScheduler` at `0x805293F8`. All earlier
V377–V379 checkpoint censuses remained positive:

```text
V380_NAND_SCHED_CENSUS rc=0 kind=zero size_band=0 sample_complete=0 entries=13 trials=13 entry_any=1 trial_any=1 scheduler_verified=1
```

Owner run [45122081279](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45122081279)
authenticated the original guest-registered IPC handler call from Wii IRQ
slot 27, including saved SRRs and interrupted LR/CTR/XER, with the original
Y1/Hollywood IRQ still latched. The bounded log retained 12 complete
positive pairs:

```text
V381_NAND_IPC_CENSUS rc=0 kind=zero size_band=0 sample_complete=0 entries=12 trials=12 entry_any=1 trial_any=1 ipc_verified=1
```

The IPC handler was *entered* but not yet executed through its first
nested call. The exact NAND callback result remains unverified.

Owner run [45122546234](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45122546234)
authenticated the original registered guest IPC handler's first nested
translated function call. At least one retained observation matched the
known Wii IPC read/write/cache helper set and had live Y1 hardware, but
the bounded census does not expose a specific helper address:

```text
V382_NAND_IPC_NEXT_CENSUS rc=0 kind=zero size_band=0 sample_complete=0 entries=12 trials=12 known_any=1 signal_any=1 next_verified=1
```

Owner run [45123298165](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45123298165)
confirmed the NAND Y1-specific original `IPCReadReg` guest function at
`0x8051905C` returned to its registered IPC owner, which then called the
real `IpcReplyHandler` at `0x805190C0`. Its bounded public result was:

```text
V383_NAND_REPLY_CENSUS rc=0 kind=zero size_band=0 sample_complete=0 entries=12 trials=12 entry_any=1 trial_any=1 reply_handler_verified=1
```

The reply-handler *entry* does not imply it has read the reply message,
acknowledged Y1, called any completion callback or returned to NAND.

Owner run [45123975844](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45123975844)
authenticated the original `IpcReplyHandler` body executing far enough
to invoke `IPCReadReg` at `0x8051905C` from LR `0x805190E8`. Twelve
bounded samples passed:

```text
V384_NAND_REPLY_READ_CENSUS rc=0 kind=zero size_band=0 sample_complete=0 entries=12 trials=12 entry_any=1 trial_any=1 ipc_read_verified=1
```

Owner run [45124715246](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45124715246)
then tried to execute the first register-reader function toward the
second original call. It hit V80's **first-SYSCONF** ARMMSG request-pointer
oracle before V385 could observe a second read:

```text
V310_PUBLIC_FAILURE id=1183 label=V80 original ARMMSG read selected a different request callback=1 nand=1 trials=0
V385_NAND_SECOND_READ_CENSUS rc=134 kind=signal size_band=0 sample_complete=1 entries=0 trials=0 entry_any=0 trial_any=0 second_read_verified=0
```

The corrected V385 lane retains that V80 original-SC assertion verbatim
outside authenticated NAND. On the NAND path only, it checks that the
original ARMMSG read result equals the native hardware mailbox and that
Y1 remains asserted. This is a **host observer correction**, not a guest
IPC reply or an acknowledgement.

Owner run [45125571086](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45125571086)
then authenticated the *second* original reply-handler IPC register read,
and independent ARMMSG coherency against the live native IOS mailbox:

```text
V385_NAND_SECOND_READ_CENSUS rc=0 kind=zero size_band=0 sample_complete=0 entries=12 trials=12 entry_any=1 trial_any=1 second_read_verified=1
V385_NAND_ARMMSG_CENSUS rc=0 kind=zero size_band=0 sample_complete=0 samples=12 coherent_any=1 y1_any=1 mailbox_verified=1
```

Owner run [45126202626](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45126202626)
executed the second original reader and stopped at another genuine
translated guest callee, while live Y1 remained asserted:

```text
V386_NAND_NEXT_CENSUS rc=0 kind=zero size_band=0 sample_complete=0 entries=12 trials=12 signal_any=1 writer_any=0 cache_any=0 next_verified=1
```

The absence of the historical SC writer/callsite pair and known cache
helper in this sample is material. It does **not** establish the actual
next function's identity or imply that the original NAND handler never
uses the PPC register writer; it only rules out those exact classifications
at V386's first retained successor. V387 therefore accepts either a
genuine Y1 W1C or a further original guest function call.

Owner run [45127532251](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45127532251)
executed V386's authentic NAND IPC callee further. It produced a second
real translated guest call with Y1 still asserted, but neither a guest
Y1 acknowledgement nor a match to the earlier SC-specific writer pair:

```text
V387_NAND_ROUTE_CENSUS rc=0 kind=zero size_band=0 sample_complete=0 entries=12 trials=12 ack_any=0 next_any=1 writer_any=0 route_verified=1
```

This result prompted V388's bounded 16-call original guest trace. Its
authenticated owner run [45128739995](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45128739995)
confirmed that the unchanged original NAND reply-handler call chain
reached a real guest Broadway `PPCCTRL.Y1` write-one-to-clear before the
16-call budget. Hardware Y1 was asserted before the write, then cleared,
while Hollywood's independent IRQ flag and IRQ level remained asserted:

```text
V388_NAND_BOUNDED_CENSUS rc=0 kind=zero size_band=0 sample_complete=0 entries=12 trials=12 ack_any=1 bounded_any=0 writer_any=1 read_any=1 cache_any=0 bounded_verified=1
```

The owner checkpoint exited normally, but its inherited full-startup
harness was still incomplete. The first public-original-free V388 test
had one missing source-shape guard (a V386 marker mutation was not
rejected); its correction and two-request MMIO regression are staged
separately from the authenticated game-code evidence.

Owner run [45130565691](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45130565691)
continued the authentic original guest call chain beyond Broadway's
`PPCCTRL.Y1` acknowledgement and observed a **second distinct original**
Hollywood `PPC_FLAG.IPC_PPC` write-one-to-clear. After that write the
Hollywood bit cleared and the native IRQ line was no longer asserted.
This occurred through the translated original Wii code, not a fabricated
host acknowledgement:

```text
V389_NAND_FLAG_CENSUS rc=0 kind=zero size_band=0 sample_complete=0 entries=12 trials=12 flag_ack_verified=1
V388_NAND_BOUNDED_CENSUS rc=0 kind=zero size_band=0 sample_complete=0 entries=12 trials=12 ack_any=1 bounded_any=0 writer_any=1 read_any=1 cache_any=0 bounded_verified=1
```

V389 deliberately stopped immediately after the actual Hollywood MMIO
write, before the original PPC handler continued to its next call. V390
removes only this instrumentation stop, preserving both guest-owned ACKs
and stopping at the first naturally linked original post-ACK callee.

Owner run [45226222054](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45226222054)
authenticated execution of original translated Wii code beyond the
Hollywood IRQ W1C, into a real post-acknowledgement cache helper.
The original guest remained in a masked interrupt context; both
Broadway Y bits and Hollywood IPC_PPC were clear, and the native
IRQ line stayed low. Twelve retained owner-private pairs passed:

```text
V390_NAND_POST_ACK_CENSUS rc=0 kind=zero size_band=0 sample_complete=0 entries=12 trials=12 cache_any=1 context_any=0 next_verified=1
```

The positive `cache_any` classification refers to the original
`DCInvalidateRange` callsite; it does not by itself show the cache
helper's body finished or the original NAND callback ran.

Owner run [45227656547](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45227656547)
continued the unchanged original NAND reply-handler call chain beyond
V390's cache helper. Its next reply-handler-owned guest function entry
was again classified as the original cache helper, not as the original
context setter or callback. Twelve retained owner-private pairs passed:

```text
V391_NAND_POST_ACK_CENSUS rc=0 kind=zero size_band=0 sample_complete=0 entries=12 trials=12 owner_any=1 cap_any=0 cache_any=1 context_any=0 callback_any=0 next_verified=1
```

These `*_any` fields are OR-aggregated classifications over the bounded
sample. They do **not** claim that every call was a cache helper or that
the original callback will follow immediately. V392 therefore advances
beyond the repeated cache step with a 24-call cap and accepts whichever
real non-cache guest callee appears.

Owner run [45230601180](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45230601180)
authenticated original NAND guest execution after two distinct
PowerPC-owned hardware interrupt acknowledgements and repeated cache
calls, reaching the first non-cache function whose LR belonged to
`IpcReplyHandler`. The guest target matched a Wii OS context-management
helper. It is not yet clear from the public census whether that target
was `OSClearContext` or `OSSetCurrentContext`:

```text
V392_NAND_POST_CACHE_CENSUS rc=0 kind=zero size_band=0 sample_complete=0 entries=12 trials=12 owner_any=1 bounded_any=0 cache_any=0 context_any=1 callback_any=0 next_verified=1
```

The public original-free tests initially passed after fixing a mistaken
fixture stop assertion; the original-private V392 harness then exposed
a compiler `-Wparentheses` failure in a widened completion predicate.
The corrected V392 source added an independent g++ `-Wall -Wextra
-Werror` original-free compile check. Its public test lane passed and
the owner-original run reached the context-management checkpoint
without changing original PPC or IOS result data.

Owner run [45232203761](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45232203761)
continued the unchanged original PowerPC context-management path and
authenticated the next actual reply-handler-owned call to
`OSSetCurrentContext` at `0x805228CC`. It retained twelve valid
original guest trials, all with both hardware interrupt ACKs complete:

```text
V393_NAND_GUEST_NEXT_CENSUS rc=0 kind=zero size_band=0 sample_complete=0 entries=12 trials=12 reply_any=1 clearctx_any=0 setctx_any=1 cache_any=0 isfs_any=0 next_verified=1
```

The older SC-only observations had identified this OS setter and an
indirect `_isfsFuncCb` call as separate stages. The V393 NAND census
confirms the setter call **but not** execution of its body, the later
ISFS callback, or the original NAND completion callback. V394 tests
that next original indirect call without substituting a specific IOS
reply result or guest request pointer.

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

V385 authenticated the second original `IPCReadReg` and live
NAND ARMMSG coherency. V386 and V387 each advanced to genuine guest
successors, but neither observed a Broadway Y1 W1C nor the expected
historical SC writer/callsite pair. V388 executed a bounded original guest call chain and reached the
genuine `PPCCTRL.Y1` W1C before exhausting the call budget.
V389 independently verified the subsequent genuine Hollywood
`PPC_FLAG.IPC_PPC` W1C and native IRQ deassertion. V390 subsequently
authenticated original guest execution through both W1Cs to its
`DCInvalidateRange` entry, matching the historical cache-helper
classification without forcing it.

V391 advanced the authentic reply-handler-owned call chain
through an additional cache-related callee. V392 then executed
unchanged original PowerPC until a genuine reply-handler-owned OS
context-management function entry, with both hardware ACKs complete
and the native IRQ line down. The exact context target is not
disclosed in the bounded public record.

V393 authenticated the next reply-handler-owned guest call as
`OSSetCurrentContext` from the original NAND context-management path.
V394 is the next unverified frontier: execute the original setter
and verify the genuine indirect `_isfsFuncCb` entry, checking
guest-visible request fields, return status and user data without
assuming the historical SC error code.

That ISFS callback entry, if reached, is still distinct from
execution of the NAND completion callback. The latter and full
native Wii startup remain unverified.

## Windows original-free regression

From a Windows checkout on `research/wii-native-recomp-preflight`, with
Visual Studio C++ build tools or MinGW-w64 on PATH:

```bat
research\native_recomp\windows_nand_reply_selftest.bat
```

This tests V374 and V376 native IPC/exception behavior without any game
image. It is useful for Windows portability, but it is not a substitute
for the private authenticated game-code execution workflow.
