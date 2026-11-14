# V7: Undercover Wii SPR audit bridge

**2026-11-13. Original-free research. Not a playable port.**

## Source-backed classification

The V6 Undercover Wii PowerPC-to-C++ output contained **183 silently discarded `mtspr` writes**, spanning 60 distinct SPR numbers. Measured from the 112 private generated C++ shards:

| Family | Writes |
|---|---:|
| BAT translation (528–543, 560–575) | 127 |
| HID/cache-related (920–923, 1008–1023) | 28 |
| Performance monitoring (952–958) | 13 |
| Exception status/address (18/19) | 10 |
| Timebase (284/285) | 2 |
| SDR1 translation (25) | 1 |
| Other | 2 |
| **Total** | **183** |

The relevant hardware families are documented by [WiiBrew Broadway registers](https://wiibrew.org/wiki/Broadway/Registers) and [Wii memory map](https://wiibrew.org/wiki/Memory_map).

## V7 implementation

- The experimental `apply_spr_audit_v7.py` patch changes previously ignored `mtspr` code generation to `ctx.write_unmodeled_spr` and replaces 59 formerly zero-stubbed `mfspr` sites with `ctx.read_unmodeled_spr`.
- The CPU context stores shadow values, written markers and a write counter. First writes warn that **hardware effects remain unimplemented**. `NWII_SPR_TRACE=1` emits detailed guest-PC diagnostics.
- `NWII_SPR_STRICT=1` rejects known hardware-critical writes before mutation, instead of silently accepting incorrect MMU/cache behavior.
- SPRG0–3 now initialize to zero in the host CPU context.
- `audit_spr_emission_v7.py` checks aggregate coverage in private generated C++ and rejects unhandled write markers and unsupported instruction traps.

## Actual tests and generated output

- **49/49** synthetic emitter assertions passed.
- **64/64** synthetic CPU context assertions passed, plus a separate strict-environment smoke test.
- **4/4** Python aggregate coverage tests passed.
- Applied to an independent V6 source-tree copy, repeated idempotently. Patched recompiler source and CPU context files matched the tested work tree SHA-256 exactly.
- Original Undercover Wii DOL retranslated with V6 code-span gates: **112** numbered C++ shards, **183** explicit diagnostic SPR writes across 60 SPR numbers, **59** shadow reads, **0** ignored `mtspr` markers and **0** explicit unsupported-opcode traps.
- GCC 14.2 successfully syntax-checked **113/113 generated C++ units**, in four bounded batches. One generated shard compiled into a **4.4 MiB x86-64 ELF relocatable object**.

## Limits and next gate

Shadowing values is **not** Wii MMU translation, cache/HID emulation, exception handling, or timer correctness. No complete link, Windows native boot or gameplay has been established. Genuine BAT/HID side effects still require source-backed implementation and differential testing in Dolphin. Original DOL/ELF, private symbol maps, game resources and generated translated game code were not committed.

Next: connect the complete runtime dependencies and capture the first actually executed hardware-register operations, then implement those hardware services with bounded, independently verifiable tests.
