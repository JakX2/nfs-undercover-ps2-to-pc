# V12: Validated DOL loader and real NWiiRuntime CPU image

Original-free C++20 test toolkit. The patch applies to a local upstream NWiiRecomp source checkout. **This does not yet execute translated Undercover code or boot the game.**

## Apply

    python3 apply_validated_dol_v12.py /path/to/NWiiRecomp-master

Run twice to check idempotence: the second call reports False. The script installs a header at nWiiRuntime/include/loader/validated_dol_v12.h and patches only Executable::load_dol in nWiiRuntime/src/core/loader.cpp. It validates section offsets, file ranges, guest RAM ranges, entry-point coverage, loaded-section overlaps, BSS size/alignment and catches partial reads. A failed load does not overwrite a previously valid entry point or section list.

Crucially, **BSS may legally overlap initialized data**. Original Undercover Wii exhibits this. Its BSS is zeroed before initialized sections are loaded, so initialized bytes are restored by the subsequent copies. V12 permits this ordering; falsely rejecting overlapping BSS would prevent loading the real game.

## Build tests (no game files needed)

    UP=/path/to/NWiiRecomp-master
    INC="$UP/nWiiRuntime/include"
    SRC="$UP/nWiiRuntime/src/core/loader.cpp"
    g++ -std=c++20 -O2 -Wall -Wextra -Werror -I "$INC" test_validated_dol_v12.cpp "$SRC" -o /tmp/test_dol_v12
    /tmp/test_dol_v12 /tmp/synthetic_test.dol
    python3 make_fixture_v12.py /tmp/synthetic_image.dol
    g++ -std=c++20 -O2 -Wall -Wextra -Werror -I "$INC" test_dol_cpu_image_v12.cpp translated_fixture_v12.cpp "$SRC" -o /tmp/test_dol_image_v12
    /tmp/test_dol_image_v12 /tmp/synthetic_image.dol

The tests use the original upstream NWiiRuntime loader and CPUContext/MMU types, not a substitute memory object. A separately compiled synthetic run_game(CPUContext&) fixture verifies the same function signature that generated code must supply. It is not game code.

Observed: 69 synthetic DOL validation and actual loader assertions passed. Both binaries also compiled and passed under GCC AddressSanitizer/UndefinedBehaviorSanitizer.

## Owner-local original Wii DOL test

    /tmp/test_dol_image_v12 /path/to/your/NfsMWRelease.dol

The test was run against the user's original DOL (SHA-256 16a09adcf1987c1f3617d10f3a1cb830f32886afb583f9f8f88e0963ae5fe1f4) without committing any game bytes:

- Entry PC 0x8000403C; entry instruction word 0x4800016D.
- 12 sections, including 3 text, 8 initialized data and 1 BSS.
- 6,433,024 initialized bytes loaded into actual guest RAM and byte-compared.
- 996,280 BSS bytes verified after zeroing and initialized-data restoration.
- 32,800 initialized bytes genuinely overlap the declared BSS span and remain preserved.
- The separately linked synthetic function verified 32-bit arithmetic wraparound, guest MMU writes, link-register return, and stop flag.

## Next gate

Link the actual game-derived translated C++ function shards with the complete NWiiRuntime and resolve missing external service symbols. This test proves the loader/CPU-state/ABI boundary and private DOL memory image, **not native boot, rendering, missions or gameplay**. Keep copyrighted DOL/ELF, generated game code and assets private.
