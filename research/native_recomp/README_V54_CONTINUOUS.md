# V54: Eight authentic Wii EXI interrupt handlers register in continuous native startup

**Status: verified owner-original focused native AOT execution**, from Wii
`__start 0x8000403C` through `OSInit`, original `EXIInit`, and
eight uninterrupted `__OSSetInterruptHandler` calls to the synthetic
stop **`0x804EFAA0`**.

[Successful V54 original-game focused CI](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44198340642)
confirmed the instrumented stage **54**, correct original entry/stop
addresses, all 16 owner-native semantic trials and no PowerPC
interpreter fallback on exercised paths.

## Source-backed Wii behavior

The owner DOL remains SHA-256-pinned to
`16a09adcf1987c1f3617d10f3a1cb830f32886afb583f9f8f88e0963ae5fe1f4`.

At guest PCs `0x804EFA40`, `0x804EFA50`, `0x804EFA60`,
`0x804EFA6C`, `0x804EFA78`, `0x804EFA84`,
`0x804EFA90`, and `0x804EFA9C`, original PowerPC dispatches to
`__OSSetInterruptHandler` at **`0x805265F8`**. Its 5-instruction
original routine indexes the interrupt table via the original global
`r13-3408`, reads the former entry and stores the new callback.
The original `__OSInterruptInit` previously initialized this
table at guest `0x80003040`. V54 verifies original vector indices
**9 through 16**, eight owner-original handler addresses, the previous
zero handler results, and byte-accurate table contents and canaries.

The 16 trial oracle checks original BL return addresses and GPR
arguments, EXI temporary register usage, preserved guest stack and
previous native startup invariants. Earlier EXI busy-loop,
`__OSMaskInterrupts`, and thirteen MMIO writes continue to execute
in the same original `__start` chain. Hardware register status is
still provided by an explicit deterministic test callback.

## Owner-private fixture construction

- `make_start_to_exi_handlers_v54.py` extracts original PowerPC
  exclusively from the SHA-locked owner DOL. It writes exactly
  `0x805265F8-0x8052660C` into previously synthetic NOPs and
  extends the original EXI routine to the next synthetic `sc;blr`
  boundary at `0x804EFAA0`.
- `test_v54_continuous_exi_handlers_geometry.py` reconstructs V53
  independently and rejects any unrelated original/synthetic
  instruction or DOL segment changes.
- `generate_start_to_exi_handlers_v54.cpp` checks the original
  five-instruction handler setter, all eight BL targets and the
  inherited EXI mask call graph before generating native C++.
- `test_start_to_exi_handlers_v54.cpp` verifies all eight handler
  registrations over the 16-case continuous native startup suite.
- `run_v54_continuous_exi_handlers.sh` keeps private executable
  slices, original PowerPC-to-C++ output, binaries and native test
  logs in a cleanup-trapped temporary directory.
- `.github/workflows/wii-v54-fast-check.yml` runs the owner's
  focused test without recompiling each older milestone.
  `.github/workflows/wii-continuous-startup.yml` adds the new
  V54 checkpoint after V53 for the complete sequential regression.
  These are separate CI results, and the full sequential suite
  must be checked independently.

## Next boundary

The original EXI routine resumes at `0x804EFAA0` and soon calls
additional EXI device identification/probing functions. Original
hardware device behavior, complete EXI initialization, IOS, OS,
rendering, game `main`, frontend and gameplay remain unimplemented.
Keep PR #36 in **draft**. No proprietary DOL, ELF, original instruction
bodies, assets or generated game-derived C++ are committed.
