# V11: Undercover Wii EA HUFF + JDLZ resource codecs

Source-only C++20 research toolkit for the owner's original Wii resource archives. No executable, disc image, game assets, ELF code, private symbols, or game-derived payload bytes are included.

## Test without original game data

```bash
cd research/native_recomp
g++ -std=c++20 -O2 -Wall -Wextra -Werror test_huff_v11.cpp -o test_huff_v11
./test_huff_v11
g++ -std=c++20 -O2 -Wall -Wextra -Werror test_dispatch_v11.cpp -o test_dispatch_v11
./test_dispatch_v11
g++ -std=c++20 -O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer test_huff_mutations_v11.cpp -o test_huff_mutations_v11
./test_huff_mutations_v11
g++ -std=c++20 -O2 -Wall -Wextra -Werror ea_resource_cli_v11.cpp -o ea_resource_cli_v11
python3 test_install_v11.py
```

Dependencies: headers in this directory from **V10** (`jdlz_decoder_v10.h`) and **V11** (`huff_decoder_v11.h`, `ea_resource_decoder_v11.h`). GCC or Clang C++20; Python 3 for install test. `ea_resource_decoder_v11.h` recognizes JDLZ and HUFF headers and returns an explicit failure for unknown signatures. `HUFF` supports EA 30FB/32FB/34FB, plus 31FB extended header in the same decoder.

## Optional exact-byte verification (owner's own files)

```bash
./ea_resource_cli_v11 GLOBAL/GLOBALA.LZC /tmp/GLOBALA.bin GLOBAL/GLOBALA.BUN
./ea_resource_cli_v11 GLOBAL/GAMEPLAY.LZC /tmp/GAMEPLAY.bin GLOBAL/GAMEPLAY.BIN
```

The `ea_resource_cli_v11` command verifies all decoded bytes against the optional original reference before writing the decoded output. It **never downloads or bundles game files**. The original `GLOBALA.LZC` HUFF input yields 265,564 bytes, byte-for-byte equal to `GLOBALA.BUN`. With V10's five JDLZ pairs, six real Undercover Wii compressed resources have now been verified, 26,080,852 decoded bytes total.

## Runtime staging, not automatic interception

```bash
python3 install_jdlz_v10.py /path/to/NWiiRecomp-master
python3 install_ea_codecs_v11.py /path/to/NWiiRecomp-master
```

The V11 installer refuses conflicting headers and is idempotent. **Neither script replaces `DVDOpen`, the low-level virtual disc reader, or the original PowerPC `JLZDecompress`/`HUFF_decompress` calls.** Original Wii game code may need compressed `.LZC` bytes, and replacing disc reads with decoded bytes would be unsafe without first identifying each call site's contract.

## Proven limitations

These decoders are native C++ functions, but the **complete Undercover executable has not been linked or booted**. Codec correctness on six files does not demonstrate total resource coverage, frame rendering, a loaded world, or working gameplay. The upcoming objective is to trace the game-side decompress call paths and link the native runtime, preserving original compressed file semantics.
