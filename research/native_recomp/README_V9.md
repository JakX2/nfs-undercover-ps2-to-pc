# V9: Validated GameCube/Wii disc FST for NWiiRecomp

**Original-free runtime engineering. No native Undercover boot has been achieved.**

The stock NWiiRuntime has two resource paths: high-level `DVDOpen` (addressed by V8) and low-level `VirtualDisc`, which uses `sys/boot.bin`, `sys/fst.bin`, and `files/`. The original low-level parser constructed strings from unbounded FST pointers, trusted directory fields without validation, and did not resolve host filename case differences.

## What changed

- A 12-byte-entry, big-endian, bounds-checked FST parser validates root, parent/end indices, NUL-terminated name ranges, and safe relative path components.
- Supports Wii file offsets shifted left two bits and GameCube file offsets as written.
- `VirtualDisc::parse_fst` now rejects malformed FST input, resolves files through V8's confined guest-path resolver, refuses host files shorter than the FST-listed length and records mapped/missing file counts.
- Original disk file offsets are preserved. The patch does not fabricate a `boot.bin` or `fst.bin`.

## Reproduce with the original-free toolkit

Apply the existing V8 disc-path patch to a private NWiiRecomp source tree first. Then from that tree's root:

```bash
git apply --check /path/to/nwiirecomp_validated_fst_v9.patch
git apply /path/to/nwiirecomp_validated_fst_v9.patch
g++ -std=c++20 -O2 -Wall -Wextra -Werror \
  -I nWiiRuntime/include /path/to/test_fst_virtual_disc_v9.cpp \
  nWiiRuntime/src/hle/virtual_disc.cpp -o /tmp/fst_v9_test
for mode in wii gc missing invalid; do
  /tmp/fst_v9_test /tmp/synthetic_disc_$mode "$mode"
done
```

Measured: **49 Wii, 49 GameCube, 48 missing-resource and 38 invalid-FST assertions passed** (184 total). All four also passed GCC AddressSanitizer + UndefinedBehaviorSanitizer runs. Synthetic fixtures contain no original-game bytes.

## Remaining blocker

The checked Drive folders contain Undercover's ELF/DOL and extracted categories, but not the original `sys/boot.bin`, `sys/fst.bin`, or `NFS/ZDIR.BIN`. The latter appears in the Wii executable's static strings but is distinct from the Wii FST. Extracted filenames alone cannot establish the original Wii DVD file offsets. The V9 tests therefore validate the parser and mapping behavior, **not real-disc compatibility or executable startup**.

Source references: [WiiBrew Wii disc](https://www.wiibrew.org/wiki/Wii_disc) and the inspected `nWiiRuntime/src/hle/virtual_disc.cpp` from the uploaded NWiiRecomp source.
