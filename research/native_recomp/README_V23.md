# V23: Continuous native `__start` through original `__init_data`

**Status:** A bounded, **actual-game-code native startup integration test**, not a complete native Windows boot or gameplay build.

V22 proved that the original Undercover Wii `__init_data` and its memory-copy/zero helpers worked when entered **in isolation**. V23 now combines the verified V21 hardware-initialization dispatcher and V22 data-initialization functions in **one NWiiRecomp-generated `run_game(CPUContext&)`**. A private test image is assembled only from the owner's SHA-pinned Wii DOL, with explicit synthetic diagnostic/error callback bodies and an explicit stop immediately after the third original `__start` call.

## Original Wii executable findings and actual execution boundary

- Original owner DOL SHA-256: `16a09adcf1987c1f3617d10f3a1cb830f32886afb583f9f8f88e0963ae5fe1f4`.
- The original `__start` at `0x8000403C` calls `__init_registers` (`0x800041A8`), `__init_hardware` (`0x800042E0`), then `__init_data` (`0x80004238`) via a BL at **`0x80004054`**.
- All **three** calls are executed through the original NWiiRecomp-generated native function dispatcher, including the original PowerPC stack prologue between the second and third calls.
- The original `__init_data` invokes the original translated `memset` and `__fill_mem` for three zero-fill entries; the original 11 in-place relocation entries cause no `memcpy` or `__flush_cache` calls. Those helper bodies are included and the call counts are asserted.
- Three original BSS ranges, totaling **963,456 bytes**, are verified **byte-by-byte** after the combined startup run. Neighboring bytes are checked for overwrites. The native run also validates MSR, HID0, HID2, FPSCR, FPR and paired-single register state, GQR clearing, guest stack pointer and caller LR.
- **Original PowerPC ABI detail:** The third-call prologue stores two `0xFFFFFFFF` stack words after decrementing `r1` by 8. `__init_data` saves its own return address into the caller's *linkage area* at `SP_before-4`. The resulting upper word is therefore `0x80004058`, not `0xFFFFFFFF`, while the lower word remains the original sentinel. V23 explicitly verifies this authentic behavior.
- **Synthetic test stop at `0x80004058`:** Only code up through the original third BL is used from `__start`; this address in the privately synthesized test DOL contains **`sc; blr`**, not the original fourth startup instruction. Thus **`DBInit`, `OSInit`, `__init_user`, and `main` have NOT run**.

## Native code versus deliberate boundaries

The test runs the real owner-original `__init_registers`, `__init_hardware`, `__OSPSInit`, its HID helpers, `__OSFPRInit`, `__OSCacheInit`, native cache-enable helpers, `__init_data`, `memcpy`, `__flush_cache`, `memset`, and `__fill_mem`. The complete *selected* original functions, up to 23 entries including two synthetic service callbacks, are fed to the actual upstream Analyzer and Recompiler, which produce native C++ compiled for the host CPU. No PowerPC interpreter fallback is allowed.

The original `DBPrintf` and `OSSetErrorHandler` functions have **not** been executed; their bodies in this *test-only* DOL are unmistakably synthetic `sc; blr` callbacks. This is not a Wii OS implementation. L2CR busy-poll completion remains bounded and deterministic rather than cycle-accurate, and cache line maintenance and HID0 ICFI self-clearing semantics remain unverified. The original complete `__start` was not executed past `0x80004058`.

## Reproducible tests

Dependencies: GCC 14 (or compatible C++20 compiler), Python 3, local source-only NWiiRecomp checkout. Use an **isolated** upstream checkout because the test runner will apply existing original-free V15/V18/V19/V20 runtime patches locally.

Without game files, an independently authored synthetic Wii DOL is generated and tested:

```bash
bash run_v23_tests.sh /private/NWiiRecomp-master
```

With the **user's original SHA-pinned DOL**, the private full startup slice is also tested:

```bash
bash run_v23_tests.sh /private/NWiiRecomp-master /private/NfsMWRelease.dol.bin
V23_SANITIZE=1 bash run_v23_tests.sh /private/NWiiRecomp-master /private/NfsMWRelease.dol.bin
```

The runner uses a temporary directory and deletes owner-derived DOL slices and NWiiRecomp-generated game C++ on exit. **Never commit or share those files.**

### Verified outcomes

| Execution | Checked result |
|---|---:|
| Actual original Undercover continuous startup, 16 trials | **15,417,324 assertions passed** |
| Independent synthetic startup, 16 trials | **1,832 assertions passed** |
| Original-free source, malformed-section, wrong-hash and output guards | **33/33 passed** |
| Original function roots in private native dispatcher | **23** |
| Fully original-free synthetic function roots | **19** |
| Original BSS cleared per run | **963,456 bytes** |
| Complete optimized local runner | **Passed** |
| Complete AddressSanitizer + UndefinedBehaviorSanitizer runner | **Passed** |
| Fresh NWiiRecomp ZIP checkout, owner+synthetic runner | **Passed** |

An additional **source-only range-validator in the V23 generator** rejects truncated data sections, invalid file/guest ranges and overlapping on-disk sections *before* the older NWiiRecomp loader sees them. Earlier loader versions did not consistently reject a truncated trailing section; the test now rejects it. The validation tests also reject mutated BL targets, missing stop/return instructions, corrupted synthetic data-initialization code, incompatible base-section layouts and nonempty code-output destinations.

## Source-only public files

New V23 files:

- `make_start_to_data_v23.py`: builds a tiny owner-private Wii startup image or an entirely synthetic fixture; stores the relocation/zero table as a real DOL data section.
- `generate_start_to_data_v23.cpp`: validates section ranges and original/synthetic guest call contract, then calls the **real** NWiiRecomp non-split `generate_cpp`.
- `test_start_to_data_v23.cpp`: semantic native execution and original guest MMU regression, without proprietary PPC bytes.
- `test_start_guards_v23.py`: invalid-input, SHA pin, source-layout and overwrite checks.
- `run_v23_tests.sh`: clean rebuild, temporary private output and release/sanitizer runner.
- `README_V23.md`: these notes and reproduction instructions.

Existing original-free V15/V17–V22 support scripts are required for the local standalone ZIP and remain unchanged in GitHub.

## Next milestone

Replace the `OSSetErrorHandler` test callback with a **source-verified** original guest implementation or a faithful bounded native bridge that preserves its interrupt masking, OS handler table and error-handler return semantics. `DBPrintf` can remain a carefully scoped diagnostic shim while early initialization progresses. Then extend the original `__start` dispatcher beyond `0x80004058` into the real `DBInit` and `OSInit` callgraph, resolving missing Wii services incrementally. Do **not** treat this verified bounded prefix as a complete game boot, frontend rendering or gameplay.
