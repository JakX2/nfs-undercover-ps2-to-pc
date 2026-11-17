# V52 continuous Wii __start -> original EXIInit polling

**Status: verified owner-original native AOT checkpoint. Not a complete Wii OS boot.**

The native execution path starts at the Wii game's authentic `__start` entry
`0x8000403C`, follows the original `OSInit` initialization sequence and
returns from its second `__OSCacheInit` call. At `0x805208C4`, the original
PowerPC `bl` dispatches to `EXIInit` at `0x804EF9BC`. Original game
instructions execute continuously through the first 22-instruction
three-channel EXI transfer-control polling prefix. A **synthetic** `sc; blr`
stops precisely at `0x804EFA14`, before the as-yet-unintegrated
`__OSMaskInterrupts` call.

## Verified evidence

- [Successful V52 focused owner-native CI](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44194868244)
  confirmed `continuous-start`, original entry `0x8000403C`,
  observed stop `0x804EFA14`, and stage 52. The runner also required
  its original-free C++ semantic test to pass all **16 owner trials**
  before printing the checkpoint marker.
- Previously verified V51 continuous startup remains an independent regression
  checkpoint at `0x805208C4`.
- The EXI prefix reads control status registers at `0x0D00680C`,
  `0x0D006820`, and `0x0D006834`. Tests inject explicit ready/busy
  schedules and verify the precise sequence and values of the guest MMIO
  reads, including loopback when any channel reports a busy status.
- The original EXI 32-byte nested stack frame, `OSInit` caller LR
  `0x805208C8`, preserved previous startup state, and existing
  interrupt-mask MMIO sequence are asserted.
- No PowerPC interpreter fallback is permitted in the exercised path.
  The private source remains SHA-256-pinned to
  `16a09adcf1987c1f3617d10f3a1cb830f32886afb583f9f8f88e0963ae5fe1f4`.

## Implementation

The owner-private fixture builder is
`make_start_to_exi_poll_v52.py` and its independent no-overwrite oracle is
`test_v52_continuous_exi_geometry.py`. The native AOT generator and runtime
semantic harness are `generate_start_to_exi_poll_v52.cpp` and
`test_start_to_exi_poll_v52.cpp`. The private runner is
`run_v52_continuous_exi_poll.sh`.

All seven DOL text slots were already in use. The final text segment
starts at the original `DBInit` entry `0x804E5020` and already
contains the original `DBInit` body and a synthetic `DBPrintf` callback
at `0x804E50B8`. V52 preserves those bytes, fills the gap after that
callback with explicit **synthetic NOP padding**, and places only the
owner-extracted, source-checked EXI prefix at its actual guest address.
This design introduces no additional DOL text section and does not
relocate the guest executable. The no-overwrite test compares all old
sections, both data sections, and the precise allowed `OSInit`
call/stop replacement.

New CI workflow `.github/workflows/wii-v52-fast-check.yml` stages the
owner's exact SHA-pinned source privately, applies previously verified
original-free NWiiRuntime patches to pinned NWiiRecomp
`595f176f1d24cc54ff2e8389feed12d7fb553cc2`, runs only the V52
private fixture, generator, native test and checkpoint assertion, and
removes original executables and generated native output on completion.
It avoids recompiling each V38-V51 milestone just to test a local V52
edit. The larger `wii-continuous-startup.yml` still runs the complete
sequential regression chain for cross-version coverage.

To rerun the focused owner-private verification, use
**Actions -> Wii V52 Focused Owner Test -> Run workflow** on
`research/wii-native-recomp-preflight`, with the existing
`WII_GHIDRA_PRIVATE_ENABLED` variable and owner-private staging secrets.
No user re-upload, external release of the DOL, or new scheduled task is
required.

## Limitations and next target

The polled EXI register statuses are a deterministic test oracle, not
an implementation of a Wii EXI device, its transfer timing, IOS, or
interrupt completion. The `sc; blr` at `0x804EFA14` is a test boundary,
not original game code. The next milestone should integrate the
authentic `__OSMaskInterrupts` routine and subsequent EXI initialization
instructions with bounded, explicit interrupt and peripheral callbacks,
reusing the separately tested direct-`OSInit` research when possible.

The native game has **not** reached original `main`, produced a first
frame, loaded the frontend, or entered gameplay. Keep PR #36 a draft
until a genuinely bootable native build exists. Original DOL/ELF,
original PowerPC slices, game assets, and generated game-derived C++
must remain owner-private.
