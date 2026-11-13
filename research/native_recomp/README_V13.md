# Undercover Wii native recomp V13: actual translated PPC leaf execution

**Scope:** reproducible source-only harness for extracting a tightly audited leaf
function from an **owner-provided Wii DOL**, using the real NWiiRecomp
`Recompiler::generate_function_cpp` and linking it into a native C++20 program
with the actual NWiiRuntime `CPUContext` / guest MMU.

**This is not a complete game build or first gameplay boot.** V13 executes two
selected original *leaf functions*, with only test-local service stubs. The
original DOL, ELF, generated game-function C++, game textures, audio and assets
are **never included** in this toolkit or GitHub commits.

## Files

- `recompile_leaf_v13.cpp`: generic, source-only driver. It loads a privately
  supplied DOL via `Executable`, selects PPC instructions from a validated text
  span, calls the upstream NWiiRecomp emitter, and writes generated C++ **only
  to a user-selected private output path**. It rejects missing `blr`, guest calls,
  out-of-range branches, unaligned spans and invalid output symbols.
- `make_synthetic_dol_v13.py`: builds a fresh, entirely synthetic 2-function
  PPC DOL. No original Undercover instruction data is contained.
- `test_leaf_driver_v13.py`: eight extraction/rejection tests.
- `test_synthetic_leaf_v13.cpp`: tests 1,024 assertions on two independently
  authored PowerPC functions after **actual NWiiRecomp translation**, using
  native `CPUContext`, registers, MMU read/write and LR return.
- `test_real_leaf_v13.cpp`: source-only contract checks for two owner-local
  game functions, using their addresses supplied at runtime.
- `run_v13_tests.sh`: builds translator from an existing NWiiRecomp source
  checkout and tests in a temporary directory. Private generated files are
  automatically destroyed when the script exits.

## Synthetic tests, no game data needed

```bash
bash run_v13_tests.sh /path/to/NWiiRecomp-master
```

The NWiiRecomp checkout should first have the V12 validated-DOL patch applied,
although the synthetic DOL also works on the stock loader. The upstream
analyzer/recompiler has existing `-Wunused-variable` and `-Wsign-compare`
compiler warnings. Those remain visible during building the generator;
compiled generated leaf functions are built with `-Werror -Wno-unused-label`
to accommodate labels emitted by upstream that are not always jump targets.

## Optional: verify on your own original Undercover Wii DOL

```bash
bash run_v13_tests.sh /path/to/NWiiRecomp-master \
    /private/path/NfsMWRelease.dol 8007ADAC 8007AE38
```

These are two owner-verified local ELF symbol addresses, not a published symbol
map. The first is the 28-byte attribute nibble-to-character helper, the second
the 44-byte attribute string-copy helper. Both end in `blr` and have no external
function calls. The harness generates their full C++ bodies **locally**;
neither source translation is checked in.

Test result with owner-original DOL SHA-256
`16a09adcf1987c1f3617d10f3a1cb830f32886afb583f9f8f88e0963ae5fe1f4`:

- 18 original PowerPC instructions, directly emitted to C++.
- C++20 compiler **linked both actual game-derived functions** with real
  NWiiRuntime `CPUContext` and host code, no JIT/interpreter execution.
- 1,197 semantic assertions passed: 261 nibble input values, five varying
  string-copy payloads, byte-for-byte memory writes, sentinel preservation,
  PowerPC LR return, and guest original opcode readback.
- Same 1,197 assertions also passed with GCC AddressSanitizer +
  UndefinedBehaviorSanitizer. No sanitizer violations observed.
- Original-free synthetic fixture: **1,024 assertions** passed under both
  native release GCC and ASan/UBSan, plus **8 rejection checks**.

This successfully executes **two isolated genuine Undercover Wii functions**
on the host CPU, but cannot yet link the complete generated function table,
call real OS/HW services, render a frame or load a playable mission.

**Next engineering gate:** link a larger real translated call graph into the
actual generated NWiiRecomp dispatcher, preserving guest state and identifying
unresolved Wii OS, graphics and exception service symbols. Do not claim the
native PC port is playable without a full startup trace and actual rendering.
