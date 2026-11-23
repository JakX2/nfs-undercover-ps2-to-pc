# V361–V366: authentic NAND IPC intake and first native IOS ACK

Date: 2026-11-23. Branch: `research/wii-native-recomp-preflight`. PR #36.

**Milestone classification: partial original-game native startup and one real Starlet
ACK of the restored Wii NAND request. Not an IOS reply, completed NAND/SYSCONF
initialization, `main`, frontend, first frame, or playable port.**

Original Wii executables, AOT-translated game code, request bytes, and raw owner
logs remain private. Public commits contain independently authored runtime,
diagnostic tooling, and original-free regression fixtures only.

## Confirmed predecessor: real original Wii request submission

V352–V355 preserved the original PowerPC `PPCMSG` and `PPCCTRL.X1` calls,
forwarding their unmodified MMIO values through the existing native Wii
`IosBus`. The V353 privacy-safe census of the authenticated NAND run
confirmed message validation and submission:

```text
V353_NAND_MAILBOX rc=134 kind=signal sample_complete=1 msg=1 ctrl=1 queued=1 invalid=0 chain=2
```

The request was in Starlet's intake queue; no ACK or reply had yet been proven.

## V361: verified native Starlet ACK

[Owner-original V361 run](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/45102142557)
executed the restored original Wii AOT code. Its bounded source-private log was
classified without publishing guest data:

```text
V361_IOS_YIELD rc=134 kind=signal size_band=0 sample_complete=1 steps=1 first_pump=1 last_pump=1 pending_first=0 pending_last=0 irq_any=1 eligible_any=0 replies_any=1
V310_PUBLIC_FAILURE id=1339 label=V98 NAND registration did not preserve existing callback and IOS state callback=1 nand=1 trials=0
```

`StmIos::Pump::Ack` is enumeration value 1 in
`wii_stm_ios.h`. One genuine native `IosYieldScheduler::service_one`
ran at the authenticated original `OSRestoreInterrupts` callsite
`0x805265D4`, after the guest queued `PPCCTRL.X1`. The original request
pointer passed 32-byte alignment and 64-byte physical-RAM-span checks.

After service, the native IOS intake queue was drained, the hardware IRQ line
was asserted, and a native IOS completion was queued. Exception delivery was
not yet eligible at the sampled call, because guest MSR.EE was disabled.
No guest register, memory byte, original PowerPC branch, forced status-3,
successful descriptor, or fabricated IOS reply was introduced.

V361's *initial* public test included an insufficient candidate-mode source
guard. Corrected independently in
[commit d7589875](https://github.com/JakX2/nfs-undercover-ps2-to-pc/commit/d75898756fe8758d59f8992ada4e69b299d57ddb).
The source-only regression, full generated public C++20 harness syntax,
and separate runtime/boot regressions passed. The authenticated owner run
used the same IOS-yield implementation; the corrected source guard affected
the original-free test's failure behavior only.

## Follow-on fixes and diagnostics

- V362 distinguishes the exact bounded 16-trial owner harness PASS marker from
  `rc=0` alone. This prevents describing V360's normal process exit as a full
  original Wii boot. No game boot is inferred from a bounded harness PASS.
- V363 conditions V98's *old idle-IOS-state assertion* on the pre-ACK phase.
  Its original linked shutdown-callback list integrity check remains active
  for the authenticated NAND phase. This is an observer change only.
- V364 keeps the read-only original guest call census visible after native
  IOS drains X1 and creates a queued completion.
- V365 adds read-only checks of external-IRQ eligibility, safe PowerPC
  dispatch state, and bytewise equality of the installed Wii IRQ vector.
  It does **not** enter the exception vector.
- V366 fixes a full-field-order expectation in a V362 synthetic sparse-log
  regression fixture; it does not affect the game or IOS behavior.

The V363/V365 follow-on owner-original outcomes must be reviewed separately.
Do not infer that the native guest has ACKed Y2, returned from its exception
handler, received a Y1 reply, transitioned SYSCONF status to 3, or left the
retry loop until the corresponding original-game traces show it.

## Next authentic execution boundary

1. Verify V363 preserves the genuine NAND shutdown callback list and
   allows the original PowerPC return from `OSRestoreInterrupts`.
2. Observe the native pending Y2 IRQ after EE restoration. Require original
   installed-vector bytes and safe dispatch state, rather than forcing an IRQ
   from a historical SC test observer.
3. Advance the real PowerPC exception handler and verify the guest's Y2 and
   Hollywood W1C acknowledgment.
4. Service the *same* native IOS request's queued completion only at a
   legitimate later Starlet yield; preserve actual IOS status/error codes,
   then deliver Y1 through the original handler and callback.

There is no completed native game boot, rendered frame, frontend, or
playable gameplay in V361–V366. The pre-existing hourly Undercover development
automation remains in place.
