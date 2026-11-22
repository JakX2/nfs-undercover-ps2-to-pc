# V264: authenticated Wii OSInit post-IPC retry control flow

Date: 2026-11-22. Development branch:
`research/wii-native-recomp-preflight`.

**Public-original-free plus owner-original CI green (refined audit):**
https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44969899415

## Source-backed reason to inspect this location

V263's owner-original NWiiRecomp native trace established 16/16 identical
64-call windows after the restored NAND/IPC entry. The original Wii
routine at `0x8052F830`, entered from return address `0x80520970`,
and interrupt-disable/restore helpers at `0x805265AC` and
`0x805265D4` repeat at exactly **32 guest instructions** per visit,
19 times each. During that window the virtual IPC request state,
reply queue, IRQ assertion and SYSCONF status do not change.

V264 is a separate **read-only authenticated owner ELF audit**, not
another native startup advancement. It parses the SHA-pinned original
PowerPC ELF privately, uses its validated function symbol table and
executable section mapping, and inspects the original direct branch
at `0x8052096C`, the immediate following original function body
and the original helper at `0x8052F830`.

## Verified sanitized structural evidence

```text
V264_ORIGINAL_ELF verified=1
V264_LOOP_STRUCT owner=1 direct=1 link=1 window=64 cond=6 backward=1 back_to_call=1 back_cond=1 compare=4 loads=14 stores=1 sda_loads=1 sc_sda=0 sc_byte=0 disable=3 restore=4 gettime=0 mftb=0 back_span=8
PASS: V264 private PowerPC control-flow audit
```

The callsite is indeed a **direct PowerPC branch-and-link** to
`0x8052F830`. The following 64-instruction static inspection window
contains **one conditional backward branch** into the callsite area,
four compare instructions, and one load through r13's small-data base.

Crucially, that load **does not target the known small-data
`r13-3176` SYSCONF status byte**; it is not a direct byte load of
this status. This does not rule out an indirect dependency on SYSCONF,
another global, or pending IPC work.

Across the *entire symbol-bounded helper function* (not merely its
dynamically executed 32-instruction loop), the audit finds 3 direct
branches to `OSDisableInterrupts`, 4 to `OSRestoreInterrupts`, no
direct call to the known `OSGetTime` entry `0x8052A824`, and
no local PowerPC `mftb` instruction. These source-level counts must
**not** be treated as dynamic execution counts.

The original routine may be a legitimate system-state retry or
time-sensitive loop. Its **actual conditional-branch operand and
exit condition have not been established**. No patches to
PowerPC registers, callback state, timebase, MMIO or IOS replies were
made to force the loop to exit.

## Source and verification

- `audit_v264_osinit_retry_elf.py`: bounds-checked ELF32 PPC executable
  section reading, verified SHA and function geometry, immediate branch
  decoding, signed SDA displacement category comparison and aggregate-only
  reporting. Reuses vetted `audit_v243_original_callback_branch` and
  `make_private_elf_symbol_map` original-free libraries.
- `test_v264_loop_static.py`: entirely synthetic PPC direct call and
  conditional backward branch fixtures with positive and negative
  geometry/digest tests; no retail executable required.
- `.github/workflows/wii-v264-loop-static.yml`: public synthetic CI,
  SHA-authenticated private owner ELF staging and audit, restricted
  aggregate-only output, no artifact upload, ephemeral original cleanup.
- The first owner-original V264 audit
  https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44969707289
  was also green and established the direct branch and backward edge.
  The refined audit adds the conditional-backedge and exact known SC-offset
  checks, and again passes both CI jobs.

## Next concrete debugging tasks

1. Identify the exact original small-data offset read in the retry
   window, then map it against the original OS/IPC/SYSCONF state
   variables **privately**. Avoid publishing literal instructions or
   original memory bytes.
2. Classify the conditional backward branch's BO/BI control bits and
   preceding CR-producing comparison using original guest trace and
   original Wii PPC semantics, to determine what would let it exit.
3. Cross-check timer reads and any asynchronous callbacks before
   changing virtual timebase progression. Pinned NWiiRecomp normally
   uses guest `inst_count` as its virtual TB, but V264 did not find
   a direct `mftb` inside the inspected helper.
4. Only after identifying a genuine missing service/condition, implement
   the runtime fix with a synthetic regression and SHA-pinned
   owner-original native test. Verify progress beyond the current
   64-call frontier and ultimately the next real PPCMSG write.

**Not verified:** successful second SYSCONF `IOS_Open`,
completion of NAND/OS initialization, original `main`, first
native game frame, frontend or playable gameplay.
The pre-existing hourly development task remains unchanged.
