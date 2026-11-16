# Undercover Wii native recomp V10: verified JDLZ 0x02 decoding

Original-free reference implementation. **No Undercover game files are included.** This component is not a playable native port and does not emulate the Wii DVD drive.

## Compile and test

```bash
c++ -std=c++20 -O2 -Wall -Wextra -Werror test_jdlz_v10.cpp -o test_jdlz_v10
./test_jdlz_v10
c++ -std=c++20 -O2 -Wall -Wextra -Werror jdlz_cli_v10.cpp -o jdlz_cli_v10
c++ -std=c++20 -O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer \
    test_jdlz_fuzz_v10.cpp -o test_jdlz_fuzz_v10
./test_jdlz_fuzz_v10
```

Optionally install the header into the existing NWiiRecomp runtime checkout:

```bash
python3 install_jdlz_v10.py /path/to/NWiiRecomp-master
```

This installs `nWiiRuntime/include/runtime/jdlz_decoder_v10.h`, **not a game-specific hook**. Never automatically replace a disc file read with its decompressed counterpart: original Wii code and resource loaders may need the original compressed bytes.

## Verify using your own extracted disc files

```bash
./jdlz_cli_v10 GLOBAL/GAMEPLAY.LZC /tmp/gameplay-decoded.bin GLOBAL/GAMEPLAY.BIN
./jdlz_cli_v10 FRONTEND/FRONTB1.LZC /tmp/frontb1-decoded.bun FRONTEND/FRONTB1.BUN
```

CLI verifies exact bytes against the optional reference file and refuses to write on mismatch. A decompressed output larger than 256 MiB is rejected by default, as are truncated blocks, invalid references and inconsistent block lengths. The core decoder supports a JDLZ block embedded within a larger buffer through `input_consumed`.

## Verified on the owner's original Undercover Wii files

5 JDLZ pairs, **25,815,288** uncompressed bytes, all five matched byte-for-byte. 91 synthetic decoder assertions and 20,000 deterministic malformed-input variants passed; AddressSanitizer and UndefinedBehaviorSanitizer clean.

`GLOBAL/GLOBALA.LZC` uses `HUFF` rather than `JDLZ`. It is intentionally unsupported by this decoder. Its separate original-game entry point has been identified for future research.

See `WII_NATIVE_JDLZ_V10.md` for hashes, matched sizes and the original symbol addresses. The full native C++ program has not been linked or booted.
