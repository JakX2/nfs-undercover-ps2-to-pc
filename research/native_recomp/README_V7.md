# V7: Wii SPR audit layer

This research module continues the owner-private Undercover Wii decompilation/recompilation work in PR #36. It is a **diagnostic compatibility layer**, not a full Wii MMU implementation or a playable PC game.

## Apply to the V6-patched NWiiRecomp source

```bash
python3 apply_spr_audit_v7.py /path/to/NWiiRecomp-master
```

The patch is idempotent and fails closed when required upstream code anchors change. It modifies NWiiRecomp's PowerPC instruction emitter and the CPUContext header. The V4, V5 and V6 source modifications are still prerequisites.

Previously ignored `mtspr` instructions now generate `ctx.write_unmodeled_spr(...)`; previously zero-stubbed `mfspr` instructions read a corresponding shadow value. The shadow is **for audit and readback only**. It does **not** implement BAT/MMU mapping, cache invalidation, exception effects or timing.

On a future linked runtime:

- `NWII_SPR_TRACE=1`: log each such write with the guest PC and value.
- `NWII_SPR_STRICT=1`: reject known hardware-critical unmodeled writes instead of treating the shadow as hardware parity.

These environment variables affect execution, not code generation. On default settings the first write to each previously unsupported SPR warns explicitly.

## Reproduce coverage

Use the owner's matching Undercover Wii DOL/ELF, private sized-symbol map, and V6 code-span whitelist. Keep generated game C++ private. Then run:

```bash
python3 audit_spr_emission_v7.py /private/generated-v7 --expected-writes 183
```

The tool prints aggregate counts, checks for ignored `mtspr` markers and explicit unsupported-opcode traps, and does not publish game bytes.

Two original-free C++ regression sources are committed here: `test_v7_spr_emission.cpp` and `test_v7_spr_runtime.cpp`. The full source-only V7 ZIP delivered in the project conversation includes their build runner, a Python regression, an environment-variable smoke test, and a detailed report.

**Measured V7:** 112 numbered C++ shards, 183 diagnostic writes across 60 SPRs, 59 reads, zero ignored `mtspr` markers, zero emitted opcode traps. All 113 generated translation units pass GCC 14.2 C++20 syntax checking. One translated unit compiles into a 4.4 MiB x86-64 object. The complete program has not been linked or booted.

Next: build the full Wii runtime with external dependencies, obtain a headless trace, identify the first executed BAT/HID writes, and reproduce their effects with Dolphin-backed tests. WiiBrew reference: https://wiibrew.org/wiki/Broadway/Registers .
