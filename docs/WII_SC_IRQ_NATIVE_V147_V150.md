# Wii SC IPC native execution: V147–V160

Owner-original progress log, 2026-11-20. All game executable bytes, assets,
generated translations and native test fixtures remain private. These checkpoints
run original Wii PowerPC logic through NWiiRecomp-generated C++ in the existing
continuous `__start` owner test, not through Dolphin or a general PPC interpreter.

## Verified execution

| Checkpoint | Authenticated original behavior | Private Actions proof |
| --- | --- | --- |
| V146 prerequisite | Original registered IPC handler `0x80519318` reaches first helper `0x8051905C` | [V146](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44662664035) |
| V147 | Executed first helper and reached another `0x8051905C` call, LR `0x8051935C` | [V147](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44666026642) |
| V148 | One further native read-helper invocation; next distinct helper `0x8051906C`, LR `0x80519380` | [V148](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44666572933) |
| V149 | Original IPC PPCCTRL write-one-to-clear removes Y2; IOS reply still queued and Hollywood IRQ still asserted | [V149](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44667819372) |
| V150 | Original IPC Hollywood PPC_FLAG write-one-to-clear removes the IPC latch; Broadway external IRQ level falls while IOS reply stays queued | [V150](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44668304691) |
| V151 | After authentic MMIO acknowledgments, original handler advances to helper `0x8051B060`, LR `0x805193A4`; Y2 and IPC flag remain clear, IRQ level low and IOS reply still queued | [V151](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44668844111) |
| V152 | Original helper `0x8051B060` runs; first next call is `0x80529434` from `0x80526CB0`. Original hardware ACK remains cleared, IRQ low, IOS reply queued | [V152](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44669548950) |
| V153 | At original post-IRQ call `0x80529434`, deterministic native IOS publishes queued SYSCONF `IOS_Open` reply; valid file descriptor, Y1 and fresh Broadway IRQ asserted, queue drained; stops before helper body | [V153](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44672900601) |
| V154 | Executed original post-IRQ scheduler helper `0x80529434` and entered original interrupt-disable helper `0x805265AC` from `0x80529448`; published Y1, IRQ, and SYSCONF reply preserved | [V154](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44673444700) |
| V155 | Executed original interrupt-disable helper `0x805265AC`; entered original interrupt-restore helper `0x805265D4` at LR `0x80529458` with Y1 IRQ and file reply preserved | [V155](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44674518348) |
| V156 | Executed original interrupt restore `0x805265D4`; reached rescheduler `0x80529940` from `0x80526CB4`; reply IRQ asserted but MSR EE=0, interrupt not yet deliverable | [V156](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44674990548) |
| V157 | Original rescheduler at `0x80529940` ran into context load at `0x805229B4` (LR `0x80526CBC`); SYSCONF reply and Y1 IRQ preserved, MSR EE still 0 | [V157](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44675438829) |
| V158 | Original `OSLoadContext` restored the game-selected running thread via RFI: saved PC, MSR, GPRs, LR, CTR and XER matched; MSR EE=1 and Y1 interrupt deliverable | [V159 suite verifies V158](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44678053006) |
| V159 | Existing native Broadway external-IRQ bridge accepted the pending SYSCONF Y1 reply: SRR0/SRR1 saved, general registers preserved, PC entered installed vector `0x80000500`, and MSR interrupts masked | [V159](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44678053006) |
| V160 | Original installed guest vector instructions ran from `0x80000500` to handler `0x80526CE0` with exception index 4, `THREAD` context, and Y1 IRQ preserved. SRRs verified at vector entry, not assumed invariant through guest prologue | [V160](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44679151214) |

Each milestone uses **16 owner-original native trials** and retains the previous
original-path regression gates. V147–V160 introduce no replacement guest
instructions or forced SC status bytes. The host MMIO bus does implement the
explicit documented hardware W1C semantics.

Representative bounded public markers:

~~~text
V147_SC_IPC_NEXT first=1 caller=1 progressed=1 masked=1 queued=1 irq=1 target=8051905c lr=8051935c
V148_SC_IPC_DISTINCT first=1 caller=1 advanced=1 masked=1 queued=1 irq=1 reads=1 target=8051906c lr=80519380
V149_SC_IPC_ACK write=1 w1c=1 queued=1 irq=1 guest=1
V150_SC_IRQ_CLEAR write=1 w1c=1 ctrl=1 irq_down=1 queued=1 guest=1
V151_SC_AFTER_FLAG cleared=1 irq_down=1 queued=1 masked=1 progressed=1 text=1 target=8051b060 lr=805193a4
V152_SC_POST_HELPER clean=1 idle=1 queued=1 guest=1 text=1 target=80529434 lr=80526cb0
V153_SC_REPLY route=1 cleared=1 service=1 wire=1 fd=1 signal=1
V153_SC_REPLY_STATE bridge=1 wire=1 mail=1 drained=1 irq=1
V154_SC_SCHED_NEXT signal=1 reply=1 guest=1 target=1 pc=805265ac lr=80529448
V155_SC_AFTER_DISABLE y1=1 reply=1 progressed=1 call=1 pc=805265d4 lr=80529458
V156_SC_AFTER_RESTORE irq=1 reply=1 progress=1 text=1 coherent=1 ee=0 ready=0 pc=80529940 lr=80526cb4
V157_SC_RESCHED_NEXT y1=1 reply=1 progressed=1 target=1 coherent=1 ee=0 ready=0 pc=805229b4 lr=80526cbc
V158_SC_RFI pc=1 msr=1 regs=1 waiting=0 running=1 ready_thread=0 linked=0 lifecycle=1 irq=1 reply=1 coherent=1 ee=1 ready=1 old_pc=0
V159_SC_Y1_VECTOR pending=1 safe=1 entered=1 vector=1 regs=1 masked=1
V160_SC_VECTOR_ENTRY saved=1 regs=1 bytes=1 masked=1
V160_SC_VECTOR_ABI index=1 thread=1 idle=0 sr0=0 sr1=0
V160_SC_VECTOR_HANDLER vector=1 masked=1 irq=1 advanced=1 pc=80526ce0 lr=80520970
~~~

## Corrected test-phase ownership

The initial V149 owner test failed on the inherited public assertion
`V118 original IPC X1 submission differs`. The existing early-startup
observer treated the later SC handler's PPCCTRL Y2 acknowledgment as if it
were a second outgoing X1 submission. The V149 derivation now only allows
that V118 observer while `post118_x1 == 0`; the original V118 submission
is still tested, and the later authentic MMIO path reaches the older
interrupt-controller native handler. The corrected owner-native V149 run passed.

V150 similarly scopes V146's first-IPC-helper assertion to
`v146_leaf_seen == 0`, so subsequent genuine calls do not trigger a
one-time test observer.

V153 exposed a second phase-ownership hazard: the inherited V79 reply
harness repoints `POST_OWNER` to `0x805190C0` for the older STM reply
processor, whereas the later genuine SC post-IRQ scheduler call is at
`0x80529434` (LR `0x80526CB0`). V153 now validates this authentic SC
callsite explicitly. Its result is the original SYSCONF `IOS_Open` file
descriptor, **not** the earlier STM `IOS_Open` zero-result assumption.
V155 must likewise limit any inherited IRQ-disable observer to its
original phase while preserving the actual SC request and Y1 signaling.


V158 corrected a stale STM assumption: the original scheduler selected
`THREAD`, not `IDLE_CONTEXT`, and the selected thread was RUNNING (`2`),
not WAITING (`4`). RFI verification now compares against the actual
OSContext selected by original Wii code and validates thread lifecycle,
without changing guest registers or readiness. V159 corrected the inherited
V153 trial gate so the authenticated external vector `0x80000500` is
accepted as a legitimate end-state alongside translated game text.

## Hardware and runtime boundaries

The native `IosBus` models Broadway IPC registers and Hollywood IPC flags.
After authentic W1C of PPCCTRL Y2, the separate Hollywood interrupt latch
remains asserted until the original PPC_FLAG write clears it. That ordering
is now verified in the *same* owner-original execution chain.

A queued IOS reply is deliberately **not** published by V149–V152. V153
publishes it through exactly one deterministic native `IosYieldScheduler`
step at the authenticated guest yield boundary, after PPCCTRL Y2 and
Hollywood flag W1C. Its successful reply raises a fresh Y1 interrupt;
this is **not** Starlet ARM execution, IOS timing emulation or proof
of delivery to the game's async SC completion callback.

The reduced private fixture still includes explicitly synthesized device
services and a test-created SYSCONF file. Neither is proof of complete Wii
hardware emulation.

## Next execution gates

1. V152 **verified** that the original post-flag helper returns into the
   dispatcher and reaches `0x80529434` with LR `0x80526CB0`. Complete the
   original IRQ dispatcher return and saved-context restoration. A helper
   entry is not proof that the entire interrupt has returned.
2. V153 **verified** the queued SYSCONF `IOS_Open` reply publication at
   the original guest's `0x80529434` callsite. V154 **verified** the original
   scheduler's next helper `0x805265AC` at LR `0x80529448` with Y1 and the
   file reply intact. V155 **verified** the original interrupt-disable helper
   reaches interrupt-restore `0x805265D4` with LR `0x80529458`. V156
   **verified** original execution to the rescheduler `0x80529940`
   (LR `0x80526CB4`), with the reply asserted but MSR EE=0 and no
   deliverable external IRQ. V157 **verified** rescheduler execution to
   original context loader `0x805229B4` (LR `0x80526CBC`). V158
   **verified** the selected RUNNING thread's original RFI restoration,
   including PC, MSR EE=1, registers, and pending Y1 IRQ readiness. V159
   **verified** the existing native PowerPC exception bridge entered the
   installed vector with original saved SRR0/SRR1. V160 **verified** the
   translated original exception-vector instructions reached the Wii OS
   handler `0x80526CE0` with index 4 and the RUNNING thread's context.
   V161 should execute the handler into the original IRQ dispatcher. A
   complete second IPC reply handler and SC callback are not yet verified.
3. Resume the original SC async callback and verify any actual guest write
   to SDA status byte at `r13 - 3176`, including value changes.
4. Allow original OSInit's `0x8052096C` retry to leave its loop only through
   authentic status, and verify the next call at `0x8052BE14`.

No game `main`, graphics frame, frontend, world loading or gameplay is
verified. PR #36 remains a draft pending a genuine runnable startup.
