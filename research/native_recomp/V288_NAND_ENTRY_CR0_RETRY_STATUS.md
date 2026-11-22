# V285–V288: original NAND child first guard and missing service entries

Date: 2026-11-22. Development branch:
`research/wii-native-recomp-preflight`.

This is a continuation of the authenticated original Wii
NWiiRecomp native NAND/IPC callback research. It is **not**
evidence of game `main`, a first Windows frame, or gameplay.

## V284 root context

V284 statically verified the NAND child `0x8052FA60` calls
`0x8051D20C` at offset `+0x50`, compares the return `r3`
against zero at `+0x54`, and conditionally skips to `+0xBC`
at `+0x58`. V280 previously established a later call to
`0x8051E150` at `+0xAC`, whose return is similarly compared
before calling original SC writer `0x8052FCA4` at `+0xB8`.
V281 owner-native 16-trial trace saw neither later service nor
writer entry. V269 read-only MMU watch observed no SC status-byte
writes during the same bounded original guest window.

## V285: owner-native early service function-entry census

**Corrected public + owner-original green:**
https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44976006151

```text
V285_NAND_SERVICE trials=16 frontier=64 stable=1 distinct=1 entries=0 min_trial=0 max_trial=0 pre=0 post=0 child=0 sc1=0 sc3=0
V278_FCA4_CENSUS trials=16 frontier=64 stable=1 distinct=1 entries=0 min_trial=0 max_trial=0 pre=0 post=0 child=0 sc1=0 sc3=0 callback=0 nand=0
```

The genuine original helper `0x8051D20C` does **not** appear
in either the pre-V259 or post-V259 part of the restored NAND trial.
This does not prove that the preceding branch was taken: the guest
could remain in an earlier nested function and never reach this
callsite before the bounded V260 64-call stop.

V285 has a read-only private guest-entry observer at original
`0x8051D20C` and checks exact child LR `0x8052FAB4`;
it retains V278 and V269 independent owner-native gates.

## V286: original entry-guard result function shape

**SHA-pinned owner Wii ELF + public green:**
https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44976049748

```text
V286_SOURCE original=8051d20c instructions=30 direct_calls=5 target_count=5 cond_branches=1 bclr=1 literal_return0=0 literal_return1=0 literal_return2=0 literal_return3=0 literal_return_other=0 sc_read=0 sc_write=0 field188_read=0 field188_write=0
```

The original function has five direct calls:
`0x804F2064`, `0x8051E5A4`, `0x8051E5BC`,
`0x80545104`, `0x80545150`. It has no direct read or
write of the known SC byte or field `+0x188`.
Static presence does not establish any of these calls were
actually executed in V285.

## V287: inspect original NAND child's first 80 bytes

**SHA-pinned owner ELF and synthetic green:**
https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44976156940

```text
V287_NAND_PREFIX child=8052fa60 bytes=80 calls=0 conditional=1 forward_beyond_early=1
V287_PREFIX_BRANCH rank=1 offset=24 dest_offset=92 bo=4 bi=2 cr_expected=0 prev_cmp_kind=0 cmp_field=-1 cmp_ra=-1 imm_class=-1
```

Before the first service BL at `+0x50`, there is **no
direct BL in the entry prefix**, but there is a conditional
branch at `+0x18` that can skip forward to `+0x5C`,
past the first guarded call. Its original BO=4, BI=2
branches when `CR0.EQ == 0` (not equal). V287's
immediate-predecessor decoder did not identify the CR
producer, which was located further back.

## V288: earlier original condition producer

**Original Wii ELF and synthetic green:**
https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44976282175

```text
V288_EARLY_CR child=8052fa60 branch_offset=24 skip_target=92 bo=4 bi=2 cr_expected=0 producer=cmpimm producer_offset=8 cr_field=0 ra=3 rb=-1 imm_class=0
```

The original instruction at `+0x08` is a signed
`cmpwi r3,0`. The branch at `+0x18` skips to `+0x5C`
when that comparison is **not equal**.

This is the earliest directly verified static branch capable of
bypassing `0x8051D20C`, `0x8051E150` and
`0x8052FCA4` together.

It is not yet proven whether either of the first two original
instructions modify r3 or whether the branch actually executes
on the observed native path. **Do not** infer the entry callback
return value from this static scan alone.

## V289 native probe and the next decision

V289 is a candidate-only, read-only original guest observer for
function entry `0x8052FA60`, collecting **only a zero/nonzero
classification** of incoming r3 plus the original status byte,
pre/post IPC phase and bounded event count. It never sets guest
registers, PC, LR, SC memory, interrupts or IOS replies.
The owner-original run and corrected public source-only regression
must **both** be green before its input classification is claimed.

If the incoming original r3 is nonzero, verify the two instructions
between function entry and `cmpwi r3,0` preserve r3 and correlate
the actual guard path. If incoming r3 is zero or the original
entry is not observed, inspect where the guest stopped in the
earlier authentic IPC/NAND call chain before modifying runtime
semantics.

All owner game DOL/ELF, AOT-generated PowerPC game source and raw
guest execution logs remain owner-private and ephemeral.

No second SYSCONF IOS request, full original main, native first
frame, frontend or gameplay has been verified. The pre-existing
hourly development task is not duplicated.
