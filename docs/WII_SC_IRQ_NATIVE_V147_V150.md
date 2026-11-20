# Wii SC IPC native execution: V147–V153

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

Each milestone uses **16 owner-original native trials** and retains the previous
original-path regression gates. V147–V153 introduce no replacement guest
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

## Hardware and runtime boundaries

The native `IosBus` models Broadway IPC registers and Hollywood IPC flags.
After authentic W1C of PPCCTRL Y2, the separate Hollywood interrupt latch
remains asserted until the original PPC_FLAG write clears it. That ordering
is now verified in the *same* owner-original execution chain.

A queued IOS reply is deliberately **not** published by V149–V152. V153
publishes it through exactly one native IOS scheduler step after authentic
PPCCTRL Y2 and Hollywood flag W1C at the verified post-interrupt guest
call boundary. The
separate deterministic `IosYieldScheduler` may service it at a valid guest
yield boundary once the preceding interrupt is fully acknowledged. This
is not Starlet ARM execution or an accurate timing/coherency model.

The reduced private fixture still includes explicitly synthesized device
services and a test-created SYSCONF file. Neither is proof of complete Wii
hardware emulation.

## Next execution gates

1. V152 **verified** that the original post-flag helper returns into the
   dispatcher and reaches `0x80529434` with LR `0x80526CB0`. Complete the
   original IRQ dispatcher return and saved-context restoration. A helper
   entry is not proof that the entire interrupt has returned.
2. V153 **verified** the queued SYSCONF `IOS_Open` reply publication at
   the original guest's `0x80529434` callsite. V154 should execute that
   scheduler helper's original code and reach a genuine successor without
   test-owned state writes. The newly asserted Y1 IRQ still needs authentic
   interrupt handling and eventual original SC callback execution.
3. Resume the original SC async callback and verify any actual guest write
   to SDA status byte at `r13 - 3176`, including value changes.
4. Allow original OSInit's `0x8052096C` retry to leave its loop only through
   authentic status, and verify the next call at `0x8052BE14`.

No game `main`, graphics frame, frontend, world loading or gameplay is
verified. PR #36 remains a draft pending a genuine runnable startup.
