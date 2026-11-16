# V6: Wii ELF-aware function discovery, false instruction trap eliminated

Date: 2026-11-13. This is original-free source research, not a playable PC port.

## Source-backed root cause

The remaining V5 opcode trap at `0x800044C0` was due to the ELF `.init` section's `gTRKInterruptVectorTable` string `Metrowerks Target Resident Kernel`, which NWiiRecomp treated as PowerPC code. Two other false function candidates `0x80006420` (`_rom_copy_info`) and `0x800064B0` (`_bss_init_info`) are ELF OBJECT entries.

Four *genuine* 8-byte `STT_NOTYPE` MetroTRK service stubs at `0x80555530`, `0x80555538`, `0x80555540` and `0x80555548` must remain. They are labeled `TRKAccessFile`, `TRKOpenFile`, `TRKCloseFile`, `TRKPositionFile` and contain a trap/return sequence; a simple STT_FUNC-only mask incorrectly drops them.

## Implemented V6 approach

The experimental analyzer patch supports an optional whitelist of verified half-open ELF code spans. Its default behavior is unchanged. A revised offline translator driver reads original sized STT_FUNC ranges from the existing private `Name,Location,Size` CSV with `--strict-symbol-spans`, and can extend the whitelist with separately verified NOTYPE stubs using `--trusted-extra-spans PATH` and a private `Start,Size` CSV. Never trust all NOTYPE entries because some are clearly data.

With 27,941 original sized functions and four verified NOTYPE stubs, retranslation yielded **32,417 function candidates (down from 32,420)**. Dispatch-table diff shows exactly three removed false functions and no added entries. Original `__TRK_reset` and four MetroTRK stubs remain. **Explicit unsupported opcode traps: 1 → 0.** The **183 ignored `mtspr` instructions remain unresolved**.

## Verification

- Ran patched NWiiRecomp against the owner-private, DOL/ELF-matched Undercover Wii executable, regenerated all 112 C++ shards and the dispatcher.
- Verified no `UNIMPLEMENTED Opcode` or `UNIMPLEMENTED OPCODE` emissions across the 112 generated shards.
- GCC 14.2 C++20 syntax checks passed on generated `output_0.cpp`, `output_110.cpp` (includes the MetroTRK stubs) and `main_output.cpp`.
- Ten synthetic analyzer trust-boundary assertions passed, including original-free embedded text, real roots after the text, an interior helper entry, interval merging and fail-closed malformed spans.
- Applied analyzer patch twice to pristine upstream source and confirmed idempotence and exact SHA-256 match against the tested local implementation.

## Limitations

This is an analyzer/code-generation correction, not native execution, code linking, graphics or gameplay. Symbol-free legitimate assembly and dynamic vectors may still need source-verified exceptions; the strict whitelist is **experimental and opt-in**. The retained MetroTRK trap stubs require runtime-specific HLE/interpreter correctness. No private executable, game data, generated game C++ or private symbol map is included. Full source-only V6 toolkit is available as a separate ZIP in this research conversation.
