# V278–V284: authentic NAND-to-SYSCONF writer call is bypassed upstream

Date: 2026-11-22. Branch `research/wii-native-recomp-preflight`.
Original Wii game DOL/ELF, NWiiRecomp-generated game C++ and raw guest logs
remain owner-private. These milestones do not achieve game `main`,
native first frame or playable gameplay.

## Context and confirmed prior checkpoint

The restored original NAND callback executes its child `0x8052FA60`
natively, returns and continues into original IPC entry
`0x8051906C` (V250–V259). In a bounded V260–V269 post-IPC window,
the game repeats the helper at `0x8052F830` and its OS interrupt
helpers 19 times at fixed 32-guest-instruction spacing, without
observed new IOS request, queued reply, external IRQ, or guest write
to the known SYSCONF status byte `r13-3176`. This byte remains **1**.

Independent V265–V271 SHA-verified PowerPC audits showed that the
caller retries while the helper returns 1, and the helper itself
skips its direct status-updating stores unless the status byte is 3.
No forced guest memory value, fake IOS reply, or synthetic shortcut
has been used to bypass this original code.

## V278: owner-native direct writer entry census

[Authenticated owner-original and public CI](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44974820318).

V277 identified a direct original PowerPC `bl` from NAND child
`0x8052FA60` to status writer `0x8052FCA4`; V278 instruments its
actual original guest function entry, including whether LR comes from
the original NAND child, before and after V259 IPC reentry.

```text
V278_FCA4_CENSUS trials=16 frontier=64 stable=1 distinct=1 entries=0 min_trial=0 max_trial=0 pre=0 post=0 child=0 sc1=0 sc3=0 callback=0 nand=0
V269_SC_WATCH trials=16 frontier=64 stable=1 distinct=1 events=0 min_trial=0 max_trial=0 changed=0 write_zero=0 write_one=0 write_other=0 one_to_one=0 one_to_zero=0
```

This proves **no writer entry is observed within the bounded
original guest trial**. The static writer callsite could be skipped
by authentic PowerPC branch logic; absence within the sampled window
does not prove the game cannot eventually leave the loop.

## V279: statically guard the status writer call

[SHA-verified owner ELF and synthetic CI](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44974988167).

```text
V279_NAND_SC_CALL child=8052fa60 writer=8052fca4 direct=1 call_offset=184 skip_cond=2 nearest_skip_offset=180 nearest_target_offset=188 bo=12 bi=2 cr_expected=1 cr_field=0 producer_kind=1 producer_ra=3 producer_imm_class=0
```

The original NAND child calls the writer from offset `+0xB8`.
Immediately prior, a `cmpwi r3,0` and `beq` branch from offset
`+0xB4` skips over the call when the tested result is zero.
An earlier conditional branch also jumps over this call.

## V280: origin of the immediately preceding return code

[SHA-verified owner ELF and synthetic CI](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44975131296).

```text
V280_NAND_R3 child=8052fa60 writer=8052fca4 cmp_offset=176 guarded_call=184 guards=2 source=call source_offset=172 source_target=8051e150 tracked=3 copies=0 width=0 base=-1 disp=0
```

Original child `0x8052FA60 + 0xAC` calls `0x8051E150`.
Its `r3` return value controls the nearest conditional skip
over the SC writer. Original linked return address is `0x8052FB10`.

## V281: native execution never enters that later function

[16/16 owner-native and original-free CI](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44975318403).

```text
V281_NAND_SERVICE trials=16 frontier=64 stable=1 distinct=1 entries=0 min_trial=0 max_trial=0 pre=0 post=0 child=0 sc1=0 sc3=0
V278_FCA4_CENSUS trials=16 frontier=64 stable=1 distinct=1 entries=0 min_trial=0 max_trial=0 pre=0 post=0 child=0 sc1=0 sc3=0 callback=0 nand=0
```

The original service `0x8051E150` itself is **not observed**
in the bounded native path. Therefore its zero/nonzero return
cannot be inferred dynamically at this point. The earlier NAND
branch is a stronger candidate for bypassing *both* calls.

## V282: classify the later service statically

[Owner-authenticated ELF and synthetic CI](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44975424440).

```text
V282_SOURCE original=8051e150 instructions=34 direct_calls=3 target_count=3 cond_branches=2 bclr=1 literal_return0=0 literal_return1=0 literal_return2=0 literal_return3=0 literal_return_other=0 sc_read=0 sc_write=0 field188_read=0 field188_write=0
```

The service has direct calls to `0x804F21D0`,
`0x8051E5A4` and `0x8051E5BC`; no direct accesses to the
SYSCONF status byte or field `+0x188` are seen.
This does not establish which calls or branches would execute.

## V283: both original NAND child skip conditions

[Owner-authenticated ELF and public CI](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44975636407).

```text
V283_NAND_GUARD rank=1 child=8052fa60 branch_offset=88 target_offset=188 call_offset=184 bo=12 bi=2 cr_field=0 cr_bit=2 cr_expected=1 ctr_decrement=0 producer=1 cmp_field=0 cmp_ra=3 cmp_rb=-1 imm_class=0 direct_cr=1
V283_NAND_GUARD rank=2 child=8052fa60 branch_offset=180 target_offset=188 call_offset=184 bo=12 bi=2 cr_field=0 cr_bit=2 cr_expected=1 ctr_decrement=0 producer=1 cmp_field=0 cmp_ra=3 cmp_rb=-1 imm_class=0 direct_cr=1
```

There are **two separate `cmpwi r3,0` + conditional equality**
guards leading to original offset `+0xBC`:

- First guard at `+0x58`: when r3 is zero, it skips the entire
  later function `0x8051E150` and writer `0x8052FCA4`.
- Second guard at `+0xB4`: when the later function returns zero,
  it skips the writer only.

This is static control flow, not proof that either branch is taken
in the native V281 window.

## V284: original input to the earlier zero-result guard

[Corrected authenticated owner ELF and public CI](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44975771548).

```text
V284_NAND_EARLY child=8052fa60 compare_offset=84 branch_offset=88 skip_target=188 source=call source_offset=80 target=8051d20c tracked=3 copies=0 width=0 base=-1 disp=0
```

The first skip condition consumes the return value of original
function **`0x8051D20C`**, called from the NAND child at
`+0x50`. Original linked return address is `0x8052FAB4`.
The initial V284 synthetic negative test expected an unknown-opcode
classification after replacing a call with a NOP, but the conservative
analyzer properly reached the function boundary and classified that
as `entry`. The fixture was corrected and both CI jobs then passed.

## Next authentic execution milestone

V285 adds a **read-only native guest function-entry observer**
at `0x8051D20C` with exact return address `0x8052FAB4`,
retaining V278 and V269 status-writer and memory watch gates.
Check this 16-trial result before inferring whether the first
zero-result branch is reached and taken.

If V285 sees the function execute, inspect its original return path
and the precise input to `cmpwi r3,0`. If the function does not
execute, return to earlier NAND child control-flow and callback
scheduler state. In either case, fix a host Wii service only after
an original-code discrepancy is verified.

No fake successful IOS descriptor, SYSCONF value, guest branch,
register override or timebase jump is allowed to stand in for
original behavior. The full native `main`, first frame and
playable game are **not** verified.

The preexisting hourly Undercover development task is unchanged.
