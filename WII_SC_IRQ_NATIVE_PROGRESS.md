# Wii SC IRQ native continuation: V141-V223

Status: **V223 original third-negative-Y1 `IpcReplyHandler` first hardware read verified (16/16 owner-original trials); V214–V222 negative reply transport, vector, scheduler and registered IPC handler verified**.
V200-V213 independently confirm the genuine second-Y2 dispatcher, registered IPC
handler, control-register read and write helpers, PPCCTRL Y2 write-one-to-clear,
Hollywood PPC_FLAG W1C, post-ACK IPC handling, genuine scheduler/interrupt-control functions, guest-selected CPU context restoration, and the original resumed game-thread call after RFI.
**Second IOS reply transport is verified for the authentic −4 result, including Y1 exception entry, original IRQ dispatcher and first real IpcReplyHandler register read. A successful SYSCONF file open, completed asynchronous callback, and SC retry-loop exit are not verified.**
Earlier V141-V145 checkpoints remain historical first-interrupt evidence.

## Latest verified Wii PowerPC execution (2026-11-21)

The second original Wii `IOS_Open` request reached the native host IOS
scheduler after Broadway submitted it through the real guest IPC path.
The native IOS transport now distinguishes a *captured request intake*
from the writable live `X1` MMIO bit, retains the submitted physical pointer
until Starlet ACK, and defers completion delivery until the guest acknowledges
`Y2` and clears the Hollywood IPC interrupt cause.

| Milestone | Authenticated owner-native evidence | Result |
|---|---|---|
| V183 | [16-trial run 44844951023](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44844951023) | A second IPC request was submitted through the genuine original guest path, enabling eight additional translated PPC call entries without a synthetic IOS reply. |
| V184 | [16-trial run 44845800535](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44845800535) | Six more translated PPC calls; the second IOS request remained an authentic `IOS_Open`. |
| V185 | [16-trial run 44846147043](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44846147043) | Original guest execution reached `PC=0x80529434 / LR=0x80526CB0`, the native IOS yield boundary, with no reply yet queued. |
| V186 | Native second-request owner-original trial; see `wii-v186-second-ios-ack.yml` | One genuine second-request Starlet `Y2` ACK, Hollywood IRQ, one queued completion, no guest CPU mutation or fabricated reply. |
| V187-V188 | Original PPC scheduling / OSDI trials; see dedicated versioned workflows | Genuine original handler calls after the second IOS ACK, preserving the pending reply and masked IRQ state. |
| V189 | [16-trial run 44851180151](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44851180151) | Original interrupt-restore helper reached `PC=0x80529940 / LR=0x80526CB4` with SC readiness still 1. |
| V190 | [16-trial run 44852816608](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44852816608) | Authentic rescheduler entered `PC=0x805229B4 / LR=0x80526CBC`; `Y2=1`, IRQ flag=1, one genuine second IOS completion queued, guest state coherent, SC=1, MSR.EE=0. |
| V191 | [16-trial run 44856455287](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44856455287) | Original PPC resumed from `0x805229B4` and reached the authentic OSInit retry helper entry `PC=0x8052F830 / LR=0x80520970`. `SC=1`, `MSR.EE=1`, external exception ready=1, second IOS completion remains queued, and all 16 owner-native/source-only checks passed. |
| V192 | [16-trial run 44856826905](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44856826905) | Executed the original helper at `0x8052F830`; next translated PPC entry was the original interrupt-disable helper at `PC=0x805265AC / LR=0x8052F84C`. Guest `r3=1`, CR0.EQ=1, `SC=1`, `MSR.EE=1`, `Y2=1`, Hollywood IRQ=1, one second IOS completion still queued, 16/16 original-game and public guards passed. |
| V193 | [16-trial run 44857365572](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44857365572) | Executed original `OSDisableInterrupts` at `0x805265AC`, reaching authentic `OSRestoreInterrupts` at `PC=0x805265D4 / LR=0x8052F92C`. `MSR.EE=0`, IRQ-ready=0, `SC=1`, queued second IOS completion=1, Y2/flag=1, `r3=1`, CR0.EQ=0. Both owner original and original-free CI passed. |
| V194 | [16-trial run 44857645514](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44857645514) | Executed original `OSRestoreInterrupts` and returned to **exactly** `PC=0x8052F830 / LR=0x80520970`, the same OSInit retry helper reached in V191. `r3=1`, CR0.EQ=1, SC=1, MSR.EE=1 and IRQ-ready=1. The Y2 Hollywood interrupt and one second IOS completion remained pending, demonstrating a repeatable native OSInit retry cycle. Owner-original 16/16 and public source guards passed. |
| V195 | [16-trial run 44862789293](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44862789293) | Native hardware IRQ entry admitted the **second genuine IOS Y2** at authenticated V194 instruction boundary. Original installed exception vector checked; `SRR0=0x8052F830`, SRR1/MSR saved/masked, GPR/LR/CTR/XER preserved, guest PC moved to `0x80000500`. The queued second IOS completion was not delivered or fabricated. Owner-original and original-free suites passed. |
| V196 | [16-trial owner run 44863075636](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44863075636) | Resumed the **original compiled PowerPC exception vector** at `0x80000500`, reached original OS exception handler `PC=0x80526CE0`; saved SRR0/1 and LR/CTR/XER/GPR frame verified; second IOS completion remains pending. Owner-original execution passed 16/16. |
| V197 | [16-trial run 44863349099](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44863349099) | Executed authentic original second Y2 handler and entered IRQ dispatcher at `PC=0x80526A3C`; saved nonvolatile GPRs, SRR0/SRR1, LR/CTR/XER and unconsumed second IOS reply all verified. Owner-original and source-only CI passed 16/16. |
| V198 | [16-trial run 44864067516](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44864067516) | Original second IRQ dispatcher called genuine timebase helper `PC=0x8052A824 / LR=0x80526C84`; EE masked, queued IOS completion intact, instruction count advanced. Corrected instrumentation validates prior V197 saved exception frame rather than incorrectly assuming live SRR0 is preserved. Owner-original and public CI passed. |
| V199 | [16-trial run 44864292383](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44864292383) | Original second Y2 timebase helper executed into native scheduler-disable helper `PC=0x805293F8 / LR=0x80526C98`; EE masked, real IOS completion still pending, authentic guest execution progress, 16/16 owner and source-only checks passed. |
| V200 | [16-trial run 44866053683](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44866053683) | Executed original scheduler-disable and IRQ slot 27 dispatch to installed IPC handler `PC=0x80519318 / LR=0x80526CAC`. Verified second interrupt frame, masked MSR.EE and queued native IOS completion. Earlier V98 NAND idle-queue observer was narrowly phase-scoped rather than bypassing original code. Owner-original and public tests passed. |
| V201 | [16-trial run 44866283734](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44866283734) | Original second-Y2 IPC handler body executed to its first original read helper at `PC=0x8051905C / LR=0x8051933C`, with one IOS completion still queued and no synthetic hardware ACK. Owner-original and public tests passed. |
| V202 | [16-trial run 44866481776](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44866481776) | Original read helper executed and returned to the IPC handler, which called `0x8051905C` again with `LR=0x8051935C`. Original second-Y2 reply remains pending. Owner-original and public tests passed. |
| V203 | [16-trial run 44866697625](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44866697625) | Following one more original IPC read, the second IRQ entered distinct control-write helper `PC=0x8051906C / LR=0x80519380`. All 16 owner-original trials and public tests passed. **The helper has not yet executed its Y2 MMIO acknowledgment.** |
| V204 | [16-trial run 44866938035](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44866938035) | The original translated Wii control-write helper executed a genuine guest PPCCTRL Y2 W1C. `V204_Y2_ACK write=1 w1c=1 flag=1 queued=1 guest=1 progressed=1 sc=1`. Y2 cleared, but Hollywood IRQ flag remained asserted, external IRQ remained high and the IOS completion remained queued. No synthetic acknowledgment was injected. |
| V205 | [16-trial run 44867139348](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44867139348) | Original translated Wii code performed genuine Hollywood PPC_FLAG W1C after PPCCTRL Y2 clear. `V205_Y2_FLAG write=1 cleared=1 ctrl=1 irq_down=1 queued=1 guest=1 progressed=1 sc=1`. The external IRQ signal dropped; one second IOS completion stayed queued. Original owner and public tests passed. |
| V206 | [16-trial run 44868741846](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44868741846) | After both genuine guest ACK stores, the translated original IRQ handler executed into `PC=0x8051B060 / LR=0x805193A4`. `V206_Y2_POST ack=1 irq_down=1 queued=1 open=1 guest=1 masked=1 coherent=1 sc=1 pc=8051b060 lr=805193a4`. Guest MSR.EE remains masked, the Hollywood IRQ is down, the second original `IOS_Open` is still awaiting reply publication, and the SC readiness byte remains 1. All 16 owner-original trials and original-free tests passed; this is not a second IOS reply delivery. |
| V207 | [16-trial run 44868991286](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44868991286) | Executed the authenticated original guest function at `0x8051B060`, reaching the scheduler-related `PC=0x80529434 / LR=0x80526CB0` from genuine guest control flow. `V207_Y2_NEXT ack=1 irq_down=1 queued=1 open=1 replied=0 guest=1 caller=1 coherent=1 irqflag=1 mapped=1 sc=1 ee=0 pc=80529434 lr=80526cb0`. Guest MSR.EE remains masked, IRQ remains low, SC byte still 1 and the second IOS reply is **not yet published**. Owner-original 16/16 and public tests passed. |
| V208 (scheduler lane) | [16-trial run 44869261710](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44869261710) | The original scheduler function at `PC=0x80529434` called original `OSDisableInterrupts` at `PC=0x805265AC / LR=0x80529448`. `V208_Y2_SCHED y2=1 irq_down=1 queue=1 open=1 replied=0 guest=1 caller=1 coherent=1 mapped=1 sc=1 ee=0 pc=805265ac lr=80529448`. The queued second IOS reply is not yet published, SC remains 1, and both public and owner-original tests passed. |
| V209 | [16-trial run 44869502917](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44869502917) | Executed the original `0x805265AC` interrupt-disable function and reached original `OSRestoreInterrupts` `PC=0x805265D4 / LR=0x80529458`. `V209_Y2_OSDI y2=1 irq_down=1 queue=1 open=1 replied=0 guest=1 caller=1 coherent=1 mapped=1 sc=1 ee=0 pc=805265d4 lr=80529458`. All 16 owner-original trials and public tests passed. |
| V210 (two native lanes) | [16-trial post-OSDI run 44869977280](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44869977280), [16-trial OSRestore run 44870048669](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44870048669) | Both independently derived original-game tests executed the second-cycle interrupt-restore successor and agreed on `PC=0x80529940 / LR=0x80526CB4`. The guest retained Y2 cleared, Hollywood IRQ down, one pending second IOS completion, original IOS_Open request, MSR.EE masked and SC byte 1. Their owner-original and public test jobs passed. This is still original guest control-flow tracing, **not** second IOS reply consumption. |
| V211 | [16-trial run 44870855923](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44870855923) | The original second-interrupt rescheduler at `0x80529940` executed into original `OSLoadContext` at `PC=0x805229B4 / LR=0x80526CBC`. `V211_Y2_RESCHED y2=1 irq_down=1 queue=1 open=1 replied=0 guest=1 caller=1 coherent=1 mapped=1 sc=1 ee=0 pc=805229b4 lr=80526cbc`. Guest execution and original-free tests both passed. |
| V212 | [16-trial run 44871142986](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44871142986) | Executed the original second-interrupt `OSLoadContext` and genuine PowerPC `rfi`. The game-selected thread (`thread=1 idle=0`) restored exactly its saved PC, MSR, 32 GPRs, LR, CTR and XER; EE returned to 1 while the IRQ remained low and second IOS completion queued. `V212_Y2_RFI pc=1 msr=1 regs=1 irq_down=1 queue=1 open=1 coherent=1 sc=1 ee=1 idle=0 thread=1`. Both owner-original 16/16 and public tests passed. |
| V213 | [16-trial run 44871880274](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44871880274) | Executed the original game-selected thread **after** second-Y2 PowerPC `rfi` and reached the original SC/OSInit retry path `PC=0x8052F830 / LR=0x80520970`. `V213_Y2_THREAD guest=1 caller=1 coherent=1 mapped=1 irq_down=1 queued=1 open=1 sc=1 ee=1 pc=8052f830 lr=80520970`. All 16 owner-original and public tests passed. This demonstrates the second interrupt's return to game logic, **not** exit from the SC retry loop. |
| V214 (parallel IPC lane) | [16-trial run 44874813700](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44874813700) | At the original guest-selected yield after the second Y2 ACK, one native `IosYieldScheduler::service_one` publishes the **actual** `IOS_Open=-4 (Invalid)` reply without fabricating a descriptor, drains the queued completion, asserts Hollywood Y1/IRQ and preserves the guest CPU/SC status. `V214_Y2_NEGATIVE invalid=1 mode=1 path=1 published=1 irq=1 drained=1 cpu=1 sc=1`. Owner 16/16 and public tests passed. This verifies **transport of a negative response**, not a successful IOS Open or execution of the original Y1 handler. |
| V215 (negative Y1 lane) | [16-trial run 44874980129](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44874980129) | The authentic game-selected thread was restored through the original V212 PowerPC `rfi` with MSR.EE=1; a native IOS scheduler step published the real `-4 Invalid` reply, drained its queue and asserted Y1/IRQ. The Broadway hardware exception bridge entered the installed original `0x80000500` vector with the interrupted PC/MSR/GPRs/LR/CTR/XER preserved. `V215_Y1_VECTOR pump=1 published=1 signal=1 empty=1 cpu=1 entered=1 saved=1 regs=1 masked=1 sc=1`. Owner 16/16 and public passed. |
| V216 (negative Y1 lane) | [16-trial run 44875351209](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44875351209) | Executed the actual installed original Wii external-vector instructions from `0x80000500` into original exception handler `PC=0x80526CE0 / LR=0x80520970`, retaining the **negative** second IOS reply, Y1 IRQ, saved CPU ABI and masked MSR.EE. `V216_Y1_ENTRY saved=1 regs=1 bytes=1 masked=1 y1=1 negative=1`; `V216_Y1_HANDLER vector=1 irq=1 reply=1 index=1 context=1 masked=1 progressed=1 pc=80526ce0 lr=80520970`. Owner 16/16 and public passed. |
| V217 (negative Y1 lane) | [16-trial run 44875869747](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44875869747) | Original game PowerPC code executed from exception handler `0x80526CE0` into original IRQ dispatcher `PC=0x80526A3C / LR=0x80520970`. The hardware Y1/IRQ is asserted, the genuine `IOS_Open=-4` reply remains in the second request, original context and masked MSR state are coherent. `V217_NEG_DISPATCH index=1 context=1 masked=1 irq=1 reply=1 guest=1 saved=1 pc=80526a3c lr=80520970`. Owner 16/16 and public tests passed. This does not demonstrate registered IPC callback execution. |
| V218 (negative Y1 lane) | [16-trial run 44876238673](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44876238673) | Original `__OSDispatchInterrupt` advanced from `0x80526A3C` into its genuine `OSGetTime` helper at `PC=0x8052A824 / LR=0x80526C84`. `V218_NEG_NEXT irq=1 reply=1 guest=1 caller=1 masked=1 sc=1 pc=8052a824 lr=80526c84`. The actual negative IOS_Open response, pending Y1 interrupt and SC status 1 remained intact. Owner 16/16 and public source-only tests passed; **this is OSGetTime, not the registered IPC handler**. |
| V219 (negative Y1 lane) | [16-trial run 44876483964](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44876483964) | Executed original `OSGetTime` through its return to the IRQ dispatcher, then reached original `OSDisableScheduler` at `PC=0x805293F8 / LR=0x80526C98`. `V219_NEG_OSDI guest=1 caller=1 masked=1 irq=1 reply=1 sc=1 pc=805293f8 lr=80526c98`. All 16 owner-original and public tests passed. The registered IPC handler entry is the next unverified guest-code checkpoint. |
| V220 (negative Y1 lane) | [16-trial run 44877456875](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44877456875) | The third original Y1 interrupt passed `OSDisableScheduler` and entered the genuine `IPCInterruptHandler` at `PC=0x80519318 / LR=0x80526CAC` with registered IRQ slot 27 and the saved CPU frame. `V220_NEG_IPC irq=1 reply=1 context=1 caller=1 guest=1 masked=1 sc=1 pc=80519318 lr=80526cac`. All 16 owner-native and public tests passed. The probe initially used dispatcher index 4 where the callback expects slot 27; this **test-harness assertion defect** was corrected without modifying guest instructions. |
| V221 (negative Y1 lane) | [16-trial run 44877842764](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44877842764) | The original registered third-Y1 IPC callback executed its PowerPC body and called hardware read helper `PC=0x8051905C / LR=0x8051933C`. `V221_NEG_LEAF call=1 masked=1 signal=1 reply=1 stepped=1 sc=1 pc=8051905c lr=8051933c`. Original `IOS_Open=-4`, Y1 asserted and SC status 1 remain intact. All 16 owner-original trials and public tests passed; no successful SYSCONF open or callback completion is claimed. |
| V222 (negative Y1 lane) | [16-trial run 44878093738](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44878093738) | The original registered third-Y1 handler executed through its first PPC read helper and entered genuine `IpcReplyHandler` at `PC=0x805190C0 / LR=0x80519354`. The actual `IOS_Open=-4`, IRQ and SC=1 remain unchanged. Owner-original 16/16 and public tests passed. |
| V223 (negative Y1 lane) | [16-trial run 44878570758](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44878570758) | The genuine `IpcReplyHandler` executed into its first PPC register read helper at `PC=0x8051905C / LR=0x805190E8`. `V223_NEG_REPLY_READ irq=1 wire=1 caller=1 guest=1 masked=1 sc=1`. Owner-original 16/16 and public tests passed. |

**Current authenticated instruction boundary:** the V194 original guest stopped
at `0x8052F830` (LR `0x80520970`), and V195 subsequently admitted the
hardware exception, yielding `PC=0x80000500`, `SRR0=0x8052F830` and
masked guest MSR. The V191-V194 owner-original trace proves a closed SC
initialization retry cycle; V195 entered the second Y2 exception without
consuming the queued IOS reply. The retry is not resolved.

**Current verified PowerPC frontier:** the original second-Y2 exception
acknowledged PPCCTRL.Y2 and Hollywood PPC_FLAG (V204-V205), executed
registered IPC handling and the scheduler (V206-V211), entered original
`OSLoadContext` at `0x805229B4` and performed genuine PowerPC `rfi`
(V212). The original selected thread resumed and made its next authentic
PowerPC call at `PC=0x8052F830 / LR=0x80520970` (V213), back on the
SC/OSInit retry path. The second completion remains queued in this
guest-only lane, MSR.EE is enabled, IRQ is down and SC status remains 1.
This proves a complete *second interrupt round-trip back to game logic*,
**not** `OSInit` exit or `main`.

**New original Wii IPC argument provenance (owner-negative diagnostic,
not an additional successful boot milestone):** The
[owner-original V208 prologue run 44877363825](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44877363825)
observed the original ISFS function's `_savegpr_26` prologue at
`PC=0x80545100 / LR=0x804F1E40` *before* ISFS copies its incoming
r3/r4 arguments to preserved registers:
`V208_Y2_PROLOGUE seen=1 mapped=1 slash=0 mode_valid=0 mode_mem2=1 mode_slash=1`.
The incoming r3 is mapped but not a slash-prefixed path; r4 is
already a MEM2 virtual pointer to slash-prefixed text rather than
a valid scalar IOS open mode. This directly rules out the later
IOS_OpenAsync request serializer as the **first** corruption point.

The original ELF's symbol table identifies the intended call chain:
`SCReloadConfFileAsync -> NANDPrivateOpenAsync -> nandOpen ->
ISFS_OpenAsync -> IOS_OpenAsync`. The original NAND wrapper maps
its open mode to an IOS-compatible scalar before calling ISFS.
The read-only successor probe compares ISFS's saved caller LR with
the NAND callsite and the incoming r4 with caller-preserved r31,
plus an expected stack pathname, to determine if corruption is
present before the NAND-to-ISFS call or occurs during its native
execution. Preserve public boolean-only results; do not publish
translated game instructions or the original binary. Do not
modify the standard IOS ABI or fabricate a successful response.

**Latest verified third-Y1 negative-response execution:** the authentic `-4`
second IOS_Open response was published to Y1 (V214), entered the installed
external exception vector (V215), executed that original PowerPC vector
to `ExternalInterruptHandler` (V216), reached `__OSDispatchInterrupt`
(V217), called original `OSGetTime` (V218), and returned through the
dispatcher into original `OSDisableScheduler` (V219). The pending IRQ
and negative reply remain intact. This is a **native execution milestone**,
not an SC-ready transition or successful file open. V220 and V221 now **verify** the original registered IRQ callback entry and its first hardware read with this reply. Further callback execution and delivery to the SC reader are not yet verified.

**Parallel IOS publication: faithful negative reply verified (V214), successful open not achieved:** the
independent `wii-v208-sc-y2-reply-publication.yml` performs a single native
`IosYieldScheduler::service_one` step at the authenticated guest yield.
Owner results confirm `step=1 wire=1 signal=1 drained=1 cpu=1 sc=1`:
the host reply transport works and raises a genuine Y1/IRQ, but the
second `IOS_Open` receives `-4` (`Invalid`), so `opened=0`.
The [bounded error and argument probes](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44870958203)
show `path_zero=0 path_mapped=1 mode_valid=0 mode_hi8=1`;
the invalid mode is a MEM2 *virtual pointer-shaped* value, not a
byte-swapped `1`/`2`/`3`, and the mapped path candidate does not begin
with `/`. The Wii IOS protocol specifies pathname pointer at request
offset `0x0C`, mode at `0x10`. Do not make `IOS_Open` accept arbitrary
pointer values or treat a negative handle as success. Original request fields have now been compared at guest PPCMSG submission
and at reply publication: `V208_Y2_SEND witness=1 ptr=1 slash=0 mode_valid=0
mode_mem2=1` and `V208_Y2_STABLE sent=1 path=1 mode=1`, verifying
the malformed fields **predate** native IOS service and remain unchanged.
[Owner probe 44871366893](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44871366893).
The [pointer-string classification](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44871578250)
found a valid slash-prefixed, bounded pathname at **mode** offset 0x10,
while the expected pathname word is not itself a mode.
A [neighboring-word scan](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44871814369)
found this pathname only at 0x10 and **no valid mode in any slot from 0x0C
through 0x1C**. A first-known-good request control run
[44872093209](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44872093209)
reported `V208_Y2_BASE old_valid=1 old_reply=1 old_path=1
old_mode=1 old_open=1 same_ptr=0`. The earlier SC/SYSCONF request
retains a valid standard IOS Open pathname/mode and opened file handle in
the **same** native runtime. The ABI implementation is therefore backed by
a concrete working control, whereas the second original request is malformed
at submission and remains unchanged until processing. The failure is localized to the second request's preparation/memory
visibility, or the specific request buffer selected by original code.
A later owner-native [producer/provenance run 44873468351](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44873468351)
established the second buffer is in **physical MEM2**, does not overlap the
first request, and was submitted through the original PowerPC MMIO writer at
`PC=0x8051906C / LR=0x80519780`. The surprising virtual MEM2 pointer
at request offset `+0x10` resolves to the actual
`/shared2/sys/SYSCONF` pathname
(`V208_Y2_PATHCLASS valid=1 shared2=1 sysconf=1`), whereas `+0x0C`
contains a mapped, non-path pointer. This narrows the request-builder
investigation to the original sender around `0x80519780` and its
memory/physical-pointer conversion. libogc's original-free
[IOS_Open/IOS_OpenAsync implementation](https://github.com/devkitPro/libogc/blob/master/libogc/ipc.c)
also writes a **physical** pathname pointer at `+0x0C` and a mode at
`+0x10` before issuing PPCMSG. Do not modify the IOS ABI or invent
a successful open.

**V214 owner-original checkpoint verified:** the independent
[owner-native 16-trial run 44874813700](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44874813700)
proves the genuine **negative** `IOS_Open=-4` is put on the Starlet
reply wire as `IOS::Reply`, the pending second-completion queue is
drained, Y1 and the Hollywood external IRQ assert, and the guest CPU and
SC status remain unchanged. The first V214 run failed during public
harness compilation because its source transformation removed the
definition of `done` before retaining a check using that variable. The
final V214 derivation restores V208's actual hardware-state calculation
and replaces only its successful-open assertion, without changing game
code or synthesizing a handle. A direct cached/uncached alias `get_ptr`
probe was also removed after a separate unverified regression.
Neither early harness failure was a legitimate game execution result.

**V215–V217 verified:** native IOS publishes the genuine negative −4
completion, the Wii hardware bridge enters the installed external vector,
and original PowerPC vector/handler instructions reach the original IRQ
dispatcher at `0x80526A3C`. Each owner-original checkpoint passed 16/16
trials with public tests. The registered IPC callback still needs its own
original-code execution proof. This is a negative reply, not a successful
SYSCONF open.

**Next IRQ lane (unverified):** continue from verified V217 original
`0x80526A3C` IRQ dispatcher to its next guest PowerPC function and
eventually the registered IPC callback. The hourly development task has
already authored a V218 source-only test; check owner-original verification
before declaring an additional milestone.

**Request-construction diagnosis:** owner-native
[run 44876070293](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44876070293)
proved the *original IOS_OpenAsync incoming ABI* was already malformed:
`pathslash=0 modevalid=0 modemem2=1 modeslash=1` at the genuine function
entry, LR `0x804F1ECC`. Its physical IPC writer later preserved both
values exactly:
`V208_Y2_ASYNC_LINK witnessed=1 path_same=1 mode_same=1`. The original
`IOS_OpenAsync` stores, IPC mailbox, native Starlet reply and physical
cache forwarding are not the source of these argument values.
Static inspection of the owner ELF identified its direct caller as
`ISFS_OpenAsync` at `0x804F1E2C`; it forwards a pathname buffer and
an opening mode into `IOS_OpenAsync`. The source-only, read-only probe
now compares the original `ISFS_OpenAsync` incoming registers with
the subsequent `IOS_OpenAsync` registers without exporting the private
game's code, registers, pointers or pathname contents. This producer
comparison remains **unverified** until owner CI finishes. Do not patch
guest args, change the IOS ABI, or fabricate a successful file descriptor.


**Callback chain diagnosis (read-only owner evidence):** The saved original
return site at the `ISFS_OpenAsync` prologue is `0x805192AC`, inside
`IpcReplyHandler`, not a normal direct NAND/ISFS call. A fresh owner
[diagnostic run 44878474239](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44878474239)
verifies that the first request's registered callback pointer and CTR
both indicate the expected `_isfsFuncCb` at `0x804F0E04`. Guest r3/r4
also match the **first reply** result and user-data arguments exactly.
The unexpected `ISFS_OpenAsync` prologue nevertheless receives those
callback-shaped values as pathname/mode, reproducing the malformed MEM2
request. This specifically suggests an original callback dispatch,
nested call/return or saved-LR/stack-state problem, **not** a reason to
change the IOS wire ABI. The exact callback-entry order remains under
investigation; no callback corruption or static-recompilation bug is
yet proven.

**Next (unverified):** trace authentic second `IOS_Open` request
buffer construction and physical RAM/cache visibility before the original
PPCMSG write; compare first known-good SYSCONF IPC request memory with the
malformed second request, without disclosing raw owner/game bytes.
Then allow the genuine IOS response to be processed by the original Y1
interrupt handler and verify an actual SC status transition and OSInit retry
exit. Do not patch guest registers, suppress errors or fabricate a successful
request.

**Not yet achieved:** successful second SYSCONF `IOS_Open`, native execution of the registered IPC callback for the second Y1 reply,
SC status transition to ready, exit from OSInit retry into original
`main`, first frame, frontend, gameplay or a complete Windows port.

The public C++ source-only checkout intentionally lacks NWiiRecomp's generated
CPU/loader headers and private translated Wii game functions. Public tests
compile the independent IOS runtime under C++20 `-Werror` and verify harness
derivation; only owner-original CI can compile/link and execute the complete
translated startup harness. A passing public build is **not** native game boot.


The private test image is constructed from the SHA-256-authenticated owner's Wii
DOL. Original PowerPC instructions are emitted to private temporary native C++
and executed using NWiiRecomp. The public branch contains independently written
host code, original-free source patches and tests only. Do not upload original
executables, extracted instruction words, translated game code or game assets.

## Verified path

| Checkpoint | Guest destination | Owner-native evidence | Meaning |
|---|---|---|---|
| V140 | `0x80000500` | [run 44657890154](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44657890154) | Native IOS SYSCONF ACK raises the installed external exception; CPU SRR state and GPRs are preserved. Test stops before vector execution. |
| V141 | `0x80526CE0` | [run 44659015506](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44659015506) | Original installed PowerPC vector executes and saves interrupted guest state before entering original external exception handler. |
| V142 | `0x80526A3C` | [run 44659554589](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44659554589) | Original exception handler continues into IRQ dispatcher with saved nonvolatile registers, LR, CTR, XER, SRR0 and SRR1. |
| V143 | `0x8052A824` | [run 44659969306](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44659969306) | Dispatcher calls original timebase helper with expected LR, masked MSR and pending IOS request; actual translated native instruction count advances. |
| V144 | `0x805293F8` | [run 44660338019](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44660338019) | Original timebase helper returns and dispatcher enters scheduler-disable helper; native instruction count advances. |
| V145 | `0x80519318` | [run 44662161325](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44662161325) | Original scheduler disable completes; IRQ dispatcher selects registered slot 27 and enters the authentic PowerPC IPC handler with the original exception context and SC IOS ACK still pending. |

All five V141-V145 owner-original runs required **16/16** matching trials, in
addition to preserving prior test gates. Their unit-test companions are invoked
by `.github/workflows/native-recomp-source-checks.yml`.

## Historical V145 to V146 frontier (earlier milestone)

V145 **verified** the registered interrupt-handler entry at `0x80519318`,
IRQ slot 27, after the authentic scheduler-disable routine. The original
dispatcher selected the registered function pointer, preserved its exception
context, and kept the IOS SC acknowledgment genuinely pending.

The V145 native path initially encountered two **harness-only** false
assertions from earlier milestones: V136 treated the later IRQ helper call as
part of its second retry, and V98 still expected idle IOS state after NAND
registration. The scoped corrections preserve those original phase checks and
allow only authentically located scheduler IRQ helper calls to proceed.
No original instruction body or guest status is altered.

At the V145 milestone, V146 targeted the first original helper call from inside the registered IPC
handler. See `.github/workflows/wii-v146-sc-ipc-leaf.yml`. Reaching a helper
is not equivalent to acknowledging the interrupt or completing a reply.

Once selected, the original handler must execute its hardware notification
clear and resume IPC processing. A queued IOS ACK is **not** the same as a guest
reply. The service must publish the actual reply, the original PowerPC guest
must process it, and the original SC status must transition through its verified
code/dataflow before OSInit can escape its retry condition. Do not seed
`r3=0`, override the guest CR0, or manually mark the SC initialization byte
complete.

The original OSInit retry comparison at `0x80520970` compares the helper's
`r3` against `1`. The branch loops while equal. The subsequent
`0x8052BE14` call must be reached by authentic guest control flow, not by a
synthetic skip.

## Verification boundaries

- **Verified:** explicitly bounded execution of owner-authenticated PowerPC
  logic translated to native C++, with original vector/handler/dispatcher
  transitions and test-owned stop instrumentation.
- **Synthetic or host-provided:** Wii IOS guest-memory adapter, SYSCONF fixture,
  device-service steps, host scheduling boundary and native MMIO services.
  These are not a faithful ARM Starlet emulator or complete Wii hardware.
- **Not verified at this historical V145 checkpoint:** SC reply consumption, release of the OSInit retry,
  complete Nintendo OS bootstrap, original `main`, Windows game window,
  first rendered frame, frontend, gameplay, audio or feature parity.

Reproduce the relevant stage from GitHub Actions by manually dispatching
`wii-v141-sc-vector.yml`, `wii-v142-sc-dispatch.yml`,
`wii-v143-sc-time.yml`, `wii-v144-sc-disable.yml` or `wii-v145-sc-ipc.yml` on
`research/wii-native-recomp-preflight`. Private owner-staging requires the
preconfigured DOL/ELF ID secrets and the private-enable repository variable.
The workflows erase owner binaries and generated translation after execution;
public logs must remain bounded to summary and original-free checkpoints.
