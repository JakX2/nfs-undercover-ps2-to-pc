# V55: Original Wii EXIGetID cached-ID return executes in continuous native startup

**Status: verified bounded owner-original AOT execution, not full EXI device detection or boot.**

[Successful owner-private V55 focused CI](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44199674182)
verified the original `__start` guest entry `0x8000403C`, original
`EXIGetID` function entry `0x804EFD7C`, and synthetic checkpoint
**`0x804EFAB0`** with stage **55**. The test requires 16
owner-original native semantic trials and forbids PowerPC interpreter
fallback.

## Explicit test-only cached-device premise

The normal Wii first-boot EXI device identification path is not yet
implemented. To isolate a legitimate original PowerPC fast branch,
the test-only native entry callback supplies a nonzero cached ID at
guest `r13-3824`, after the authentic `__init_data` startup has
cleared BSS. That injection is **not** original game logic, a real
detected device, or Wii EXI hardware emulation.

The original `EXIInit` callsite at `0x804EFAAC` then enters the real
PowerPC prologue of `EXIGetID` at `0x804EFD7C`. The genuine original
instructions verify channel zero and request type two, read the
injected cached ID, store it via the original guest output pointer,
return success (r3=1), and follow the original branch to the
epilogue at `0x804F0110`. Original register-save and restore
thunks at `0x805450F4` and `0x80545140` execute natively.

The alternative uncached/device-probe path at `0x804EFDD4` is
deliberately terminated by a synthetic test-only `sc;blr`. No
claim is made that the original full `EXIGetID` body or peripheral
polling works. The final `sc;blr` at `0x804EFAB0` stops the
continuous original `EXIInit` immediately following the first
`EXIGetID` call.

## Implementation and privacy

- `make_start_to_exi_idcache_v55.py` extracts only the SHA-256-pinned
  owner's original EXI callsite, cached-ID function prologue, and
  authentic return epilogue. Other unexecuted code is conspicuous
  synthetic NOP padding and explicit stop instructions.
- `test_v55_continuous_exi_idcache_geometry.py` rebuilds V54
  independently, verifies original function/callsite geometry,
  and rejects changes outside the exact new test ranges.
- `generate_start_to_exi_idcache_v55.cpp` verifies the native AOT
  callgraph, original restore helper, original cached-ID store and
  test-only slow-path boundary.
- `test_start_to_exi_idcache_v55.cpp` validates the original
  16-trial continuous startup state, original EXI IRQ registration,
  mask and MMIO behavior, synthetic cached-ID injection,
  original return register and guest memory values.
- `run_v55_continuous_exi_idcache.sh` and
  `.github/workflows/wii-v55-fast-check.yml` reproduce the owner
  test privately without recompiling every earlier version.
  `.github/workflows/wii-continuous-startup.yml` also adds a
  V55 stage after V54, to be regarded as passed only once its full
  sequential run succeeds.

The private original DOL digest remains
`16a09adcf1987c1f3617d10f3a1cb830f32886afb583f9f8f88e0963ae5fe1f4`.
Generated original-game C++, private test DOLs and all executable
fixtures remain owner-private in temporary directories and are
removed on exit. No original Wii game bytes or assets are committed.

## Next: genuine uncached EXI detection

Research the original `EXIGetID` uncached/device-status branch,
its transaction dependencies and MMIO/interrupt semantics. That
path cannot be credited to the cached-ID V55 shortcut. Later
milestones still require EXIInit completion, OS/IOS and game
startup, original `main`, first frame and gameplay. Keep PR #36
draft and preserve the existing hourly development task.
