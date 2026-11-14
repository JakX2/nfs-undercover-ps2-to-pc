# V19: Original Undercover Wii `__OSFPRInit` executes through the native dispatcher

**Status: validated isolated native startup slice, NOT a playable Windows port.** This release builds an owner-private `NfsMWRelease.dol.bin` slice containing the genuine Wii `__start`, `__init_registers`, `__init_hardware`, `__OSPSInit` and its HID0/HID2/instruction-cache helper trio, plus **the complete 296-byte original `__OSFPRInit` (74 PowerPC instructions)**. The remaining `__OSCacheInit` is an explicit synthetic `sc; blr` boundary. After hardware init, `__start` also reaches a controlled synthetic stop at `0x80004044`; no subsequent game startup code executes.

The **actual upstream NWiiRecomp Analyzer and non-split `Recompiler::generate_cpp`** generate and compile `run_game(nwii::runtime::CPUContext&)` for **nine discovered functions**. The test invokes that generated dispatcher on the host CPU without interpreter fallback. Original Wii DOL, ELF, decoded assets, sliced DOL and generated game-derived C++ remain in a private temporary directory and are never packaged or published.

## New guest-state behavior

`apply_fpscr_v19.py` applies an idempotent, fail-closed patch to the existing NWiiRecomp source checkout, following V15's dispatcher fix and V18's HID0/HID2 mappings:

- The C++ emitter no longer silently discards `mtfsf`. It emits a call to `CPUContext::mtfsf(FM, frB)`.
- That helper copies the **selected four-bit FPSCR fields** from the low 32 bits of the source FPR's 64-bit representation. The original initializer uses **FM = `0xFF`**, selecting all eight nibbles.
- The existing `fpr[32]`, `ps1[32]` and paired-single `psq_load` / `ps_mr` runtime implementations are exercised directly. With HID2's paired-single-enabled bit, original code loads both paired-single elements and propagates them to all 32 registers, then loads scalar FPR0 and copies its scalar half to all 32 FPRs.
- With that HID2 bit disabled in a separate owner-private direct-entry test, the original branch **skips** paired-single copies; the scalar FPR bank and FPSCR still initialize, and the prior `ps1` halves remain unchanged.

**Fidelity limit:** FPSCR writes model field selection, not all real PowerPC FPSCR exception/status semantics, rounding-mode effects, W/L variation or exceptional floating-point values. HID0's cache invalidate command, paired-single FPSCR exception effects, and Wii GPU/OS services are still incomplete. The tests use independently seeded, ordinary finite floating-point values as a behavioral oracle; this does not validate the game's real `.bss` seed constants or complete hardware semantics.

## Reproduce without any game files

```bash
bash run_v19_tests.sh /private/path/NWiiRecomp-master
```

The synthetic builder creates a deliberately different 70-instruction FPR initialization routine in its own tiny PowerPC DOL, as well as the previous original-free startup, PSInit and HID helpers. No Undercover PPC bytes appear in the source toolkit.

## Verify privately against your own Wii DOL

```bash
bash run_v19_tests.sh /private/path/NWiiRecomp-master /private/path/NfsMWRelease.dol.bin
V19_SANITIZE=1 bash run_v19_tests.sh /private/path/NWiiRecomp-master /private/path/NfsMWRelease.dol.bin
```

Owner DOL SHA-256 pinned by prior work: `16a09adcf1987c1f3617d10f3a1cb830f32886afb583f9f8f88e0963ae5fe1f4`. The builder rejects any other file, refuses an existing destination, and verifies the original FPR function's branch, `psq_l`, `lfd`, 31 `ps_mr`, 31 `fmr`, full-field `mtfsf` and `blr` before producing its temporary executable slice.

The runner updates the **local** NWiiRecomp checkout with V15/V18/V19 source-only patches; use a separate checkout if you need to preserve upstream. It compiles with C++20, runs independent synthetic and owner-private tests, and removes all generated private game code on exit. GCC is tested; Clang may require additional compatibility work.

### Results, 2026-11-13

| Executed test | Passed assertions | Scope |
| --- | ---: | --- |
| Original Undercover Wii startup / FPR initializer | **95,748** | 512 complete bounded native dispatch starts |
| Original-free synthetic FPR initializer | **94,724** | 512 complete bounded native dispatch starts |
| Original Undercover Wii HID2 enabled/disabled branch | **4,501** | 256 direct FPR entries, paired-single lanes and scalar bank |
| Independent FPSCR selected-nibble behavior | **6,144** | 1,024 register images × 6 field masks |
| Original-free patch and malformed-input guards | **22** | Idempotence, conflicting versions, section/instruction/overwrite/SHA rejection |

Both **complete release and AddressSanitizer/UndefinedBehaviorSanitizer** runners pass, including owner-original privately generated native code, with no sanitizer violations reported.

**Next milestone:** native translation and faithful guest-state implementation of the original `__OSCacheInit` path (312 bytes) and its HID0/L2 cache helper call graph. That is a substantial additional hardware project. Do not claim Wii OS services, full native startup, renderer, main-menu boot or gameplay from V19 alone.
