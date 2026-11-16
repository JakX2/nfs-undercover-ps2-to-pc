# Undercover Wii native recomp V17: real `__init_hardware` entry and OS boundaries

## Verified milestone (2026-11-13)

V17 uses the **real upstream NWiiRecomp analyzer, C++ generator and generated `run_game(nwii::runtime::CPUContext&)` dispatcher**. It privately extracts from the original, SHA-pinned Undercover Wii DOL the first two original `__start` calls (8 bytes), the complete original `__init_registers` function (144 bytes), and the complete nine-instruction, **36-byte original `__init_hardware`** at `0x800042E0`. Its three `bl` instructions reach the exact original Wii OS addresses, in order:

| Call at | Target | Meaning | V17 implementation |
|---|---|---|---|
| `0x800042F0` | `0x80520FB4` | `__OSPSInit` | Explicit synthetic `sc; blr` callback, **not implemented OS service** |
| `0x800042F4` | `0x8051FBB0` | `__OSFPRInit` | Explicit synthetic `sc; blr` callback, **not implemented OS service** |
| `0x800042F8` | `0x80522540` | `__OSCacheInit` | Explicit synthetic `sc; blr` callback, **not implemented OS service** |

A synthetic `sc; blr` stop immediately after the two original `__start` calls ensures control halts at original address `0x80004044`. **The original CPU-service bodies and the rest of `__start` are not executed.** Original game-derived C++ output and sliced DOLs are generated only under a temporary private directory and deleted at script exit. None of the original game bytes, the original ELF/DOL, or generated proprietary functions are included or committed.

## Tests

Run with an existing upstream `NWiiRecomp-master` source checkout:

```bash
bash run_v17_tests.sh /path/to/NWiiRecomp-master
bash run_v17_tests.sh /path/to/NWiiRecomp-master /private/path/NfsMWRelease.dol.bin
V17_SANITIZE=1 bash run_v17_tests.sh /path/to/NWiiRecomp-master /private/path/NfsMWRelease.dol.bin
```

The runner applies the previously committed, **idempotent V15 non-split dispatcher fix** to the supplied local recompiler checkout, compiles the actual analyzer and recompiler, builds a wholly synthetic six-function Wii DOL, and then optionally uses the user's original DOL. The second mode refuses input unless its SHA-256 is `16a09adcf1987c1f3617d10f3a1cb830f32886afb583f9f8f88e0963ae5fe1f4`.

**Recorded local test results:**

- Source-only **synthetic** six-function generated dispatcher: **10,754/10,754 assertions** over 512 startups.
- **Original-game startup + original `__init_hardware`**, privately generated through NWiiRecomp: **26,114/26,114 assertions** over 512 startups.
- Test-only service boundaries: **3 per startup, 1,536 calls total**, in the original order, verifying expected LR values `0x800042F4`, `0x800042F8`, `0x800042FC` and restoration to original startup `0x80004044`.
- Source-backed MSR behavior verified: `__init_hardware` executes `mfmsr`, ORs the FP-enable bit `0x2000`, and writes it back via `mtmsr`; `r31` saves the incoming link register. The original register init also produces known `r1`, `r2`, and `r13` values, while the other cleared GPRs remain correct apart from documented MSR/LR temporaries.
- **26/26** original-free safety rejection checks, including incomplete sections, incorrect BL edges, wrong MSR/LR instruction forms, missing syscalls/returns, invalid mode, wrong SHA and nonempty output.
- Complete release and `-fsanitize=address,undefined` runner **both passed**, including all 512 synthetic and 512 owner-original startup trials. `interpret_step` throws if invoked and was not reached.

The C++ test works against actual `CPUContext`, not a handwritten register mock. No PowerPC interpreter fallback is used. This is an authentic *hardware-init function execution*, but the Wii OS hardware service effects remain unimplemented. It does not demonstrate any graphical game boot.

## Original Wii OS dependency census

Run on the owner's private SHA-verified DOL:

```bash
python3 audit_hardware_v17.py /private/path/NfsMWRelease.dol.bin
```

The scan reports only original symbol addresses, direct call edges, and instruction-family **counts**, not copyrighted instruction bytes. Verified results:

- `__OSPSInit` (84 bytes) contains **3 direct calls** to `PPCMfhid2`, `PPCMthid2` and `ICFlashInvalidate`. It also uses multiple special-purpose register writes and a synchronization instruction.
- `__OSFPRInit` (296 bytes) has **31 paired-single opcodes, 32 floating-point opcodes, one conditional branch,** and MSR/HID instructions. It contains no direct `bl`. Accurate paired-single/HID2 semantics are not yet supplied.
- `__OSCacheInit` (312 bytes) contains **26 direct `bl` instructions**, **five conditional branches, six sync instructions**, and dependencies including HID0, L2CR, `ICEnable`, `DCEnable`, `DBPrintf`, and `OSSetErrorHandler`. These are substantial native compatibility tasks, not safe no-ops without more validation.

## Current limitation and next engineering gate

V17 is a **bounded six-function native dispatcher test** with synthetic service stubs. **It does not execute the three original Wii OS service functions, return into unmodified `__start` after the hardware-init call, execute `__init_data`, run `OSInit` or `main`, link full translated game code, initialize hardware, or render graphics.** The next phase should validate the actual guest-visible state changes required by `__OSPSInit`, `__OSFPRInit`, and `__OSCacheInit`, including HID0/HID2/L2CR state, paired-single and floating-point register initialization, and cache operations. Only then should the service stubs be replaced with tested native/HLE implementations.
