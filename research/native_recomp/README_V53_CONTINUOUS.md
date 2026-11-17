# V53 continuous native Wii startup reaches original EXI interrupt masking

**Verified original-code milestone:** from Wii `__start 0x8000403C`
through `OSInit` and the authentic `EXIInit` mask/MMIO path to the
explicit synthetic stop `0x804EFA34`.

## Evidence and behavior

[Focused owner-private original Wii V53 CI passed](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/44196632310).
The run requires 16 successful owner-original native semantic trials,
the exact start and stop guest PCs, and no interpreter fallback. The
original DOL remains SHA-256 pinned to
`16a09adcf1987c1f3617d10f3a1cb830f32886afb583f9f8f88e0963ae5fe1f4`.

The original `EXIInit 0x804EF9BC` enters `__OSMaskInterrupts
0x8052693C` through its original PowerPC `bl` at `0x804EFA14`.
The complete original 0x80-byte mask helper runs natively, including
nested interrupt-disable/restore. Its masked-bank short path preserves
`0x800000C4 == 0xFFFFFFF0` and `0x800000C8 == 0`. The direct-entry
V67 suite independently tests the longer `SetInterruptMask` paths.

The EXI initializer then executes the original four MMIO writes at
`0x804EFA20`, `0x804EFA24`, `0x804EFA28`, `0x804EFA30`. These clear
the three channel control registers and program channel zero's control
value `0x2000`. The test verifies all **13** prior and current MMIO
writes in order, the original EXI polling reads, the mask helper's
guest return address `0x804EFA18`, stack frames, preserved state,
previous startup regressions and the exact test-only stop PC.

## Native AOT source and reproduction

The independently written source-only files are:

- `make_start_to_eximask_v53.py`: extends the owner-private V52 fixture
  and installs only owner-extracted PPC instructions at authentic
  `0x8052693C` and `0x804EFA14`.
- `test_v53_continuous_eximask_geometry.py`: checks all original DOL
  sections against reconstructed V52, accepts only the two new verified
  ranges, and rejects unsafe replacements.
- `generate_start_to_eximask_v53.cpp`: verifies original mask call
  targets, MMIO write instructions, and native translation roots.
- `test_start_to_eximask_v53.cpp`: runs 16 continuous native startup
  configurations with a deterministic, independent Wii hardware-status
  test oracle and zero interpreter fallback.
- `run_v53_continuous_eximask.sh`: builds the fixture and generated
  C++ in private scratch directories and deletes them on exit.
- `.github/workflows/wii-v53-fast-check.yml`: owner-private focused
  test that avoids redundant compilation of V38-V52.
- `.github/workflows/wii-continuous-startup.yml`: full previous-to-V53
  sequential regression with a required instrumented guest-PC advance.
  This distinct full run needs its own CI result before declaring it passed.

The source tree and public CI contain no proprietary DOL, ELF, copied
PowerPC bodies, generated game-derived native code, or game assets.
The verified status refers to the focused private run, not a game boot.
All MMIO values are test-input callbacks, not a Wii EXI/IOS model.

## Next frontier

The next original `EXIInit` callsite at `0x804EFA34` begins interrupt
handler installation. The next milestone should recover the authentic
callee and its register/stack semantics, keeping any temporary
hardware callback explicit. Device discovery and EXI transfer support,
complete Wii OS/IOS, original game `main`, graphics, frontend and
gameplay remain unimplemented. **Keep PR #36 draft.**
