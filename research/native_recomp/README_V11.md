# Undercover Wii native recomp V11: EA HUFF and JDLZ decoding

All implementation and tests in this toolkit are original-free. **No game data or game-derived source is bundled.** This does not boot a game or intercept Wii DVD reads.

## Build & run tests

```bash
c++ -std=c++20 -O2 -Wall -Wextra -Werror test_huff_v11.cpp -o test_huff_v11
./test_huff_v11
c++ -std=c++20 -O2 -Wall -Wextra -Werror test_dispatch_v11.cpp -o test_dispatch_v11
./test_dispatch_v11
c++ -std=c++20 -O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer test_huff_mutations_v11.cpp -o test_huff_mutations_v11
ASAN_OPTIONS=detect_leaks=0 ./test_huff_mutations_v11
c++ -std=c++20 -O2 -Wall -Wextra -Werror ea_resource_cli_v11.cpp -o ea_resource_cli_v11
```

`HUFF` and `JDLZ` are distinct compression families. `ea_resource_decoder_v11.h` routes their original wrapped inputs to their independent, bounds-checked C++ decoders. The HUFF implementation handles the EA `30FB`, `32FB` and `34FB` methods and the optional extended header bit; only the `30FB` path has been validated against actual Undercover Wii game assets.

## Optional verification on your own original Undercover Wii extraction

```bash
./ea_resource_cli_v11 GLOBAL/GLOBALA.LZC /tmp/GLOBALA.bun GLOBAL/GLOBALA.BUN
./ea_resource_cli_v11 GLOBAL/GAMEPLAY.LZC /tmp/GAMEPLAY.bin GLOBAL/GAMEPLAY.BIN
```

The third command argument enables exact-byte verification and refuses to write output if it differs from the original extracted file.

On the owner's own Wii assets, **all six pairs match exactly**: five JDLZ pairs from V10 plus one HUFF pair, totaling 26,080,852 uncompressed bytes. Original HUFF `GLOBALA.LZC` size: 90,453 bytes; decoded `GLOBALA.BUN`: 265,564 bytes; SHA-256 of decoded data: `04d3f350a47dd6623e31a31aee8ff7e3e91ec7f9f1e3c64a9cd565dfef2859a7`.

## Optional NWiiRuntime source-only install

```bash
python3 install_ea_resource_v11.py /path/to/NWiiRecomp-master
```

Installs the three codec headers under `nWiiRuntime/include/runtime`, without modifying DVD HLE behavior. Repeated invocation is idempotent; conflicting files cause an error before writes.

## Boundaries

We have **not** substituted these decoding routines for the original PowerPC game calls. The original compressed resource must still be read by the Wii emulation layer. Only once the guest decompression call sites are traced and validated could these be hooked to the native implementations safely. Full Windows game linking, native boot, graphics and gameplay are not yet achieved.

See `WII_NATIVE_EA_COMPRESSION_V11.md` for opcode-level connection to the original Wii ELF. The algorithm follows the public EA Huffman format description in [psx-spx](https://psx-spx.consoledev.net/dev/ps1/cdr/cdromfileformats/compression/), implemented independently as a bounded native C++ codec.
