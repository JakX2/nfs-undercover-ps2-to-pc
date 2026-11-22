# V265–V268: authenticated Wii SYSCONF retry condition and state writers

Date: 2026-11-22. Branch: `research/wii-native-recomp-preflight`.

## Owner-verified results

This series investigates the **same** V263 post-NAND original Wii
guest-loop, which repeats a 32-instruction call sequence 19 times
inside V260's 64-call observation limit. It does not claim the
original game reached `main` or made a second IOS submission.

**V265**: [owner-original and synthetic CI](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44972107467)

```text
RETRY_EDGE_AUDIT verified=1
RETRY_EDGE backedge_count=1 back_span=8 bo=12 bi=2 cr_field=0 cr_bit=2 ctr_decrement=0 ctr_zero=-1 cr_expected=1
```

The sole backward branch uses PPC BO=12, BI=2: branch while
`CR0.EQ == 1`, without decrementing or comparing `CTR`.

**V266**: [corrected owner-original and synthetic CI](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44972316352)

```text
V266_CONDITION_AUDIT verified=1
V266_CONDITION backedge_from=8 backedge_to=0 prev_distance=4 producer_kind=2 producer_cr_field=0 producer_ra=3 producer_rb=-1 producer_imm_zero=0 producer_imm_class=1 compares_helper_r3=1
```

The instruction between the linked helper call at `0x8052096C`
and the backward conditional branch is **`cmplwi r3,1`**.
Thus the observed *retry condition* is equivalent to:

```cpp
do {
    result = original_function_8052F830();
} while (result == 1);
```

This is an independent semantic summary, **not** a copy of or
replacement for proprietary translated PowerPC game code.

An initial V266 summary incorrectly set `compares_helper_r3=0`
because the original-free classifier recognized only comparison
against zero. The corrected source and synthetic test now recognize
all direct compare-immediate operands, including the owner-verified
value `1`. Both CI jobs passed after the correction.

**V267**: [owner original / source-only CI](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44972433066)

```text
V267_HELPER_AUDIT verified=1
V267_HELPER_STATE size_ins=71 direct_calls=12 disable=3 restore=4 gettime=0 mftb=0 sda_loads=1 sc_direct=1 sc_byte=1 sda_other=0 lr_branch=1 blr_unconditional=1 r3_li_one=0 r3_li_zero=0 r3_li_other=0 r3_load=1 r3_or_copy=6 cmp_r3_one=0
```

The authentic helper `0x8052F830` is **71 original PowerPC
instructions long** and directly loads the known byte at
`r13-3176` (the SYSCONF status). Its static control flow also has
one `blr` form and several copies into `r3`, although a full
dynamic proof of the load-to-return path is still required.
No direct `OSGetTime` call or `mftb` was found in the helper.

**V268**: [owner-original and synthetic CI](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44972566424)

```text
V268_SC_AUDIT verified=1
V268_SC_DIRECT sections=3 read=2 write=11 byte_read=2 byte_write=11 helper_read=1 helper_write=2 writer_owners=6 unmapped=0
V268_SC_WRITER rank=1 owner=80530ba0 writes=3
V268_SC_WRITER rank=2 owner=8052f790 writes=2
V268_SC_WRITER rank=3 owner=8052f830 writes=2
V268_SC_WRITER rank=4 owner=80530dbc writes=2
V268_SC_WRITER rank=5 owner=8052f94c writes=1
V268_SC_WRITER rank=6 owner=8052fca4 writes=1
```

This is a full original-ELF scan for **direct byte loads/stores**
using r13-relative displacement `-3176`. Six original functions
contain 11 direct status-byte stores. The repeated helper itself
contains **two direct stores**, alongside the confirmed status load.
It is not yet known whether either store executes during the
64-call loop. Indirect or indexed accesses are not covered.

## Mechanism and outstanding dependency

Combined with V262's 16-trial native observation of a constant
SYSCONF byte value **1**, no new native IOS request, no new queued
IOS reply, and no external interrupt, these findings narrow the
startup wait to the original SYSCONF status and its genuine update
path. The exact original return-value dataflow and the reasons the
status stays at 1 are **not yet established**.

The immediate next gate (V269) uses the pinned NWiiRecomp
`MMU::write8` pre-store `watch_hit` hook, armed only after the
authenticated V259 IPC reentry, to count actual guest status-byte
writes before the verified V260 64th-call stop. No status byte,
guest register, PowerPC instruction, IOS result or callback is
modified by that observer.

Only independently written audit scripts, synthetic regressions,
aggregated address/count results and technical documentation are
public. SHA-pinned Wii DOL/ELF inputs, game-derived translated code
and raw private execution traces remain ephemeral in owner CI.

## Correctness boundaries

Static existence of a store does **not** establish that its control
flow was reached. No synthetic IOS descriptor or forced SYSCONF
completion may be used to claim native boot.

A full Windows port still requires authentic completion of the
NAND/SYSCONF path, execution of game `main`, graphics/audio/input
runtime integration, frontend and first frame, and gameplay.
None of those later milestones has been verified here.
