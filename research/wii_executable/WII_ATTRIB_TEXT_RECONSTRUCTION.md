# First Wii PowerPC behavioral reconstruction: Attrib text helpers

**2026-11-10.** Three functions were inspected in the owner's **symbol-rich original Wii ELF** at their named PPC symbol addresses, and independently transcribed to **portable, original-free C++17**. Only new code and tests are committed. This does **not** represent a recovered full source file or original ABI-equivalent implementation.

| Wii named symbol | Wii ELF address | Reconstructed behavior |
|---|---|---|
| `NibbleChar__6AttribFUc` | `0x8007ADAC` | Convert low integer values to decimal/hex lowercase ASCII; for values ≥10 adds 87 then truncates to one byte |
| `ValueToText__6AttribFPCvUiPc` | `0x8007ADC8` | Iterate input bytes, emit high hex nibble then low hex nibble, terminate output |
| `IntToString__6AttribFPcUi` | `0x8007AE64` | Emit an unsigned base-10 integer from the 10^9 place down, omitting leading zero digits; return `0` for zero |

The PPC entry offsets above are **Wii-specific** and must not be treated as PS2 or PC addresses. They were decoded with `llvm-objdump` against the original ELF, not copied from third-party pseudo-source.

## Portable implementation

`attrib_text.hpp/.cpp` implements these behaviors in the `undercover::attrib` namespace. It deliberately replaces unchecked caller-buffer writes with `std::string` results and rejects a null pointer with nonzero length. These are safe host-language adaptations, **not** faithful PowerPC calling conventions or exact memory side effects.

Original-free C++17 regression executable `test_attrib_text.cpp` passed locally with:

```sh
g++ -std=c++17 -Wall -Wextra -Wpedantic -Werror \
  research/wii_executable/attrib_text.cpp \
  research/wii_executable/test_attrib_text.cpp \
  -o test_attrib
./test_attrib
```

The tests cover 16 nibble values, five-byte hexadecimal encoding, null-source behavior, unsigned decimal boundaries, and 10,000 deterministic uint32 values compared with `std::to_string`. **No live Wii runtime differential test was conducted.**

## Remaining work

- Recover named call sites and decode enough surrounding `Attrib` behavior to validate preconditions, including signedness and buffer-size assumptions.
- Add tested parsers for source-preserving numeric and attrib serialization paths.
- Match selected routines to stripped PS2 functions through **semantic evidence** (constants, input-output behavior, resource file interactions), not address offsets.
- Do not extrapolate this small helper success to rendering, streaming, game loop or full gameplay recovery.

**Classification:** three small assembly-informed behavioral reconstructions plus host-side tests. No copyrighted program bytes or retail assets are distributed.
