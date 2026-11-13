# V18: Original Undercover Wii `__OSPSInit` executes through native NWiiRecomp dispatch

**Scope:** A bounded, source-grounded proof of native execution, not a playable
Windows port. In addition to original `__start`, `__init_registers`, and
`__init_hardware`, V18 now directly translates and executes four **unmodified
original game functions** in a private owner-DOL slice:

| Original ELF symbol | Wii guest PC | Original length | Role |
| --- | --- | --- | --- |
| `__OSPSInit` | `0x80520FB4` | 84 bytes | Enables paired-single use and clears GQR0..7 |
| `PPCMfhid2` | `0x804B79DC` | 8 bytes | Reads guest HID2 |
| `PPCMthid2` | `0x804B79E4` | 8 bytes | Writes guest HID2 |
| `ICFlashInvalidate` | `0x805223AC` | 16 bytes | Writes HID0 instruction-cache invalidation command |

The original `__init_hardware` calls `__OSPSInit` as the **first** of three Wii
OS services. That call now executes the original 21-instruction function and
its three original directly called helpers, not an HLE stub. The two **other**
service bodies, `__OSFPRInit` and `__OSCacheInit`, remain explicit synthetic
`sc; blr` test stops. A third synthetic stop ends the prefix of original
`__start` at `0x80004044`. This test does **not** execute the complete original
`__start`, the game's `main`, any graphics or missions.

## Change in native runtime

`apply_hid_state_v18.py` adds two `uint32_t` fields to the real upstream
`CPUContext`: `hid0` and `hid2`. It also amends the actual PowerPC C++ emitter
for the narrowly defined `mfspr` and `mtspr` instructions on SPR 1008 (HID0)
and 920 (HID2) to read/write those fields. It does **not** add generic SPR
handling or silently implement the remaining HID, L2CR, cache, FPR or IOS
services. The patch refuses unknown upstream versions and applies idempotently.

**Hardware fidelity limitation:** The current HID0 model records a write with
bit `0x00000800` set; it does **not** model the instruction cache's actual
invalidate, any self-clearing/clearing of the ICFI command bit, or host code
cache invalidation. HID2 is stored as a register word, but paired-single
hardware instruction behavior remains a separate runtime task. Therefore this
is a **validated original instruction/control-flow execution and register-write
model**, not full Wii hardware emulation.

## Reproduce with independent synthetic functions

Requires a local NWiiRecomp source checkout (previously validated against the
owner's NWiiRecomp-master). An isolated copy is recommended because the patch
modifies that checkout's recompiler and CPUContext headers. C++20 GCC/Clang
and Python 3 are needed.

```bash
bash run_v18_tests.sh /private/path/NWiiRecomp-master
```

This builds a completely **independent synthetic PPC DOL** with a deliberately
different PSInit stack frame/register usage and synthetic HID0 helper. The
PowerPC program is assembled from generic ISA instructions, not copied out of
a game resource. The actual analyzer recovers **nine functions** and the real
non-split NWiiRecomp generator emits `run_game(CPUContext&)`.

## Verify with your own original Undercover Wii DOL

```bash
bash run_v18_tests.sh /private/path/NWiiRecomp-master /private/path/NfsMWRelease.dol.bin
V18_SANITIZE=1 bash run_v18_tests.sh /private/path/NWiiRecomp-master /private/path/NfsMWRelease.dol.bin
```

Owner-original SHA-256, checked before reading function bytes:
`16a09adcf1987c1f3617d10f3a1cb830f32886afb583f9f8f88e0963ae5fe1f4`.

The 6-section private test DOL includes only the first two original `__start`
calls, the complete original `__init_registers`, `__init_hardware`,
`__OSPSInit`, `PPCMfhid2`, `PPCMthid2`, and `ICFlashInvalidate` bodies. Gaps
in the startup text section are independently synthesized NOPs. No original
proprietary executable bytes, original game-derived C++ output, ELF, DOL or
assets are included in this repository or source-only distribution. The
script uses a private temporary directory and removes generated content at
exit. It refuses to overwrite pre-existing files.

## Recorded test results

| Native test | Pass count | Attempts |
| --- | ---: | ---: |
| Original Undercover startup/PSInit path | **30,723 / 30,723** | 512 |
| Independent synthetic nine-function startup | **29,699 / 29,699** | 512 |
| Original-free safety/idempotence/invalid-input checks | **28 / 28** | N/A |

Both complete reproduction runners passed in GCC release and
AddressSanitizer + UndefinedBehaviorSanitizer configurations. Each 512-run
test dispatches nine native PPC-derived functions, including three nested
PSInit helpers; the real-game test confirms 4,608 function entries, correct
MSR `0x2000` enablement, preservation plus OR of HID2 `0xA0000000`, HID0
`0x00000800`, GQR0..7 zeroing, 16-byte guest PSInit stack frame, guest LR
save/restore, return to `__start`, remaining FPR/cache stop ordering and no
PowerPC interpreter fallback. Tests include initial HID bits both set and
cleared plus randomized unrelated register bits.

The 28 rejection cases cover malformed startup/PSInit/HID/helper opcodes,
wrong call destinations, truncated/oversized DOL sections, invalid generator
mode, output overwrite prevention, owner SHA mismatch, HID patch conflict,
and repeated patch installation. All failed generation leaves its output
folder empty.

## Files

- `apply_hid_state_v18.py`: targeted HID0/HID2 CPUContext and emitter patch.
- `make_psinit_slice_v18.py`: synthetic or owner-private DOL slice builder.
- `generate_psinit_dispatch_v18.cpp`: source-only original PPC control-flow
  and instruction-form checks plus real analyzer/dispatcher generation.
- `test_psinit_dispatch_v18.cpp`: actual guest `CPUContext` behavioral oracle.
- `test_psinit_guards_v18.py`: 28 negative and patch-safety checks.
- `run_v18_tests.sh`: reproducible release/sanitizer runner.
- `apply_nonsplit_dispatch_v15.py` and `make_hardware_boundary_v17.py`:
  unmodified original-free dependencies copied into standalone source ZIP.

**Next gate:** inspect `__OSFPRInit` and its HID2/PSE and 32 floating-point +
paired-single register operations, then implement the guest-visible register
initialization with hardware-faithful semantics. Later address the much
larger `__OSCacheInit` dependency graph (HID0, L2CR, cache and error handlers).
Do not claim an original Wii boot or working PC rendering until those
runtime dependencies are resolved and independently verified.
