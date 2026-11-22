# V271: authenticated Wii SYSCONF status-three guard

Date: 2026-11-22. Branch: `research/wii-native-recomp-preflight`.

**Original Wii ELF and original-free synthetic jobs passed:**
https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44973427481

## Verified source structure

The helper `0x8052F830` (71 PowerPC instructions) is entered from
the original guest startup retry at `0x8052096C`. V265/V266 proved
the caller repeats while the helper returns **1**. V267/V268 mapped
its direct `r13-3176` SYSCONF state-byte load and two guarded byte
stores, with V270 proving their stored constants 1 and 0.

V271 independently decoded the original ELF control flow and then
checked exact `lbz` destination register versus the following
comparison instruction's source register, in the same SHA-verified
owner ELF. Both owner-original and synthetic tests were green.

```text
V271_GUARD_AUDIT verified=1
V271_SC_GUARD rank=1 store_offset=44 branch_offset=36 target_offset=248 bo=4 bi=2 cr_field=0 cr_bit=2 ctr_decrement=0 cr_expected=0 direct_cmp=1 cmp_kind=2 cmp_ra=29 cmp_imm_class=3 read_rt=29 status_cmp=1
V271_SC_GUARD rank=2 store_offset=240 branch_offset=36 target_offset=248 bo=4 bi=2 cr_field=0 cr_bit=2 ctr_decrement=0 cr_expected=0 direct_cmp=1 cmp_kind=2 cmp_ra=29 cmp_imm_class=3 read_rt=29 status_cmp=1
```

The original helper's direct status load at `+0x1C` targets r29.
The very next instruction at `+0x20` compares unsigned r29 to
the immediate value **3**. A `bne`-equivalent conditional edge at
`+0x24` jumps to `+0xF8` when the status is *not* 3, bypassing
the status=1 store at `+0x2C` and the status=0 store at
`+0xF0`.

Therefore the original helper's status-update branch cannot be
entered unless its directly loaded SYSCONF status is **3**.
The V262 native guest loop maintained SYSCONF status **1** and
V269's 16 owner-native trials observed **zero actual stores** to
the status byte through the same 64-call window.

This establishes the **gated status==3 requirement** for the
helper's two store sites. It does **not** prove that taking the
status==3 branch by itself would succeed, what precise asynchronous
callback sets status=3, or that the native port can boot.

## Original-free assets

- `audit_v271_sc_guard_condition.py`: original ELF SHA and symbol
  checks, short PowerPC conditional branch decode, CR0 producer,
  load register match and status-store guard classification.
- `test_v271_sc_guard_condition.py`: synthetic positive and
  fail-closed negative PowerPC branches, compare sources, private
  workflow properties.
- `.github/workflows/wii-v271-sc-guard-condition.yml`: owner
  SHA-verified DOL/ELF staging, private source audit and cleanup,
  original-free CI; no proprietary bytes or generated game source
  checked into GitHub or uploaded as artifacts.

The hourly Undercover development automation remains unchanged.

## Next root-cause gate

Locate the other original Wii functions that can transition
`r13-3176` to **3**. V268 established direct status stores in
`0x80530BA0`, `0x8052F790`, `0x80530DBC`,
`0x8052F94C` and `0x8052FCA4` besides the helper itself.
Classify those stores' source registers and values, then trace the
relevant authentic callback or IOS completion path.

Do **not** patch the guest byte to 3, simulate a successful
IOS descriptor, or claim Wii initialization has completed.
Game `main`, first frame, frontend and gameplay remain unverified.
