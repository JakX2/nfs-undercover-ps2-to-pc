# V747: observe the first actual post-system-time dependency

V744/V746 owner run 45548036089 confirms the third handler call is the exact previously executed nested system-time root. The remaining static handler graph includes ordinal 4 __SITransfer, 5 OSCancelAlarm, 6 indirect, 7 SITransfer, 8 unnamed, 9/10 interrupt disable/restore, 11 indirect, 12 GPR restore. These are hypothetical branches, not dynamic execution.

V747 adds an opt-in continuation after V742's verified return. All subsequent handler instructions still pass the existing exact label, tick, ABI, device and branch checks. Any newly linked call is refused before executing it, with a strict bounded ordinal/kind/count event. A separate audit accepts only a valid V742 prefix followed by that exact refusal (or actual verified handler return). No new MMIO writes, callbacks, transfer completion or helper calls are authorized. Prior V742 default stop remains unchanged. Owner execution pending.
