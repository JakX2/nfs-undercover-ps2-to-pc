# V4: Real Undercover Wii DOL translated by NWiiRecomp

Date: 2026-11-13. This is aggregate original-free research, not a game port.

## Verified first translation

- The actual NWiiRecomp C++ analyzer and recompiler compiled offline with GCC 14.2 using a separate C++20 command-line driver (no SDL/TOML/GUI).
- Owner-original DOL entry 0x8000403C; 27,941 privately derived ELF symbol roots supplied.
- NWiiRecomp discovered 32,420 candidate functions and visited 1,806,810 instruction slots. Additional inferred starts need code/data validation.
- Generated 112 numbered C++ shards plus a dispatcher unit. **113/113 generated C++ units passed GCC 14.2 C++20 syntax-only checks.**
- All generated game code (hundreds of MB) and the owner's executable files remain private.

## Translator compatibility finding

- The unmodified translator emitted **489 hard unsupported-opcode traps**.
- An experimental indexed paired-single instruction patch maps psq_lx, psq_stx, psq_lux, and psq_stux to the runtime's existing quantized load/store helpers.
- Six synthetic emitter tests passed. Pristine-source application and idempotence passed.
- Recompiling the complete original DOL after the patch produced **71 hard traps**, 418 fewer.
- The remaining cases include 70 paired-single estimate operations and one apparent code/data false-positive.
- Separately **193 mtspr instructions for 64 distinct special-purpose register numbers are silently unhandled** in emitted code.

## Boundary and next work

Passing syntax does **not** establish native object linking, hardware compatibility, startup or playable graphics. Wii-exact quantization and FPSCR behavior remain unverified. The full NWiiRuntime needs SDL2/toml++/GLAD dependencies not locally available, and compatibility needs testing against Dolphin. The source-only reproducibility kit (offline driver, patch, tests, scripts) is provided separately without copyrighted game data.

References: https://wiibrew.org/wiki/Paired_single and https://wiibrew.org/wiki/Memory_map

Next: classify inferred function boundaries, handle missing SPR and paired-single operations, then build a complete headless runtime.
