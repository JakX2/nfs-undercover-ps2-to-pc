# Wii SC IRQ native continuation: V141-V206

Status: **V206 owner-original second IOS post-Hollywood-ACK guest continuation verified (16/16 trials)**.
V200-V206 independently confirm the genuine second-Y2 dispatcher, registered IPC
handler, control-register read and write helpers, PPCCTRL Y2 write-one-to-clear,
Hollywood PPC_FLAG W1C, and next original function entry after the ACK.
**V207 successor and delivery of the second IOS reply remain unverified.**
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

**Current authenticated instruction boundary:** the V194 original guest stopped
at `0x8052F830` (LR `0x80520970`), and V195 subsequently admitted the
hardware exception, yielding `PC=0x80000500`, `SRR0=0x8052F830` and
masked guest MSR. The V191-V194 owner-original trace proves a closed SC
initialization retry cycle; V195 entered the second Y2 exception without
consuming the queued IOS reply. The retry is not resolved.

**Current verified PowerPC frontier:** V204 proves PPCCTRL Y2 is cleared by
the *original* guest store, and V205 proves the Hollywood external-IRQ latch
is cleared by a second authentic guest W1C. V206 advanced beyond both stores
to original PowerPC function entry `PC=0x8051B060 / LR=0x805193A4`.
Hollywood IRQ is down, guest MSR.EE masked, SC byte still 1. The second
`IOS_Open` remains in its original request state and exactly one native
completion remains queued. No second reply has yet been delivered to the
original SC initialization callback.

**V207 (unverified):** run original guest code at `0x8051B060`, record
its next native callee and the queue/request/reply state, then locate the
real IOS completion publication boundary. Never inject an extra IOS pump,
override guest registers or force SC readiness.

**Not yet achieved:** delivery/publication of the *second* IOS reply,
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
