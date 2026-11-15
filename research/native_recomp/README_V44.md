# V44: All 15 original Wii OS exception-vector installations execute natively

**Scope: source-grounded, bounded owner-private native execution, not a complete native Wii boot.** V44 extends the original `OSInit` -> `OSExceptionInit` chain beyond the V43 `0x80520DB8` checkpoint and follows the genuine PowerPC exception-vector loop to its final `DBPrintf` dependency at **`0x80520E58`**. The unresolved call is replaced only in the private test image with an explicit synthetic terminal syscall; `DBPrintf` is **not executed**. This test still enters `OSInit` directly at `0x80520670`, not continuously from the original `__start` at `0x8000403C`.

## Genuine original code now executed

The original branch at `0x80520DC0` loops to `0x80520CA8` until the original exception index reaches 15. Every unmarked iteration executes the game program's own `__DBIsExceptionMarked`, template preparation, the original `memcpy`, the original `DCFlushRangeNoSync` and `ICInvalidateRange`, and associated guest PowerPC arithmetic, CTR branches, `sync`/`isync` and cache-line instructions. After the loop, the original code writes the OS exception-handler pointer global, populates all fifteen 32-bit handler-table entries at `0x80003000`–`0x80003038`, and restores the original exception-template instruction word before the final debug-print dependency.

The owner-original PowerPC source bodies are extracted locally from the **SHA-256 pinned owner DOL**. The private test seeds **independently authored exception-vector offsets** of `0x100`, `0x200`, ..., `0xF00` for a discriminating per-index memory oracle. These are **test inputs**, not a claim about the actual Wii OS vector-offset table from the retail game. For the normal branches, original code copies fifteen 152-byte handler bodies and performs **75 dcbf + 75 icbi line events, 30 sync and 15 isync events** per startup. The test checks every copied byte, including the original per-index bitwise-mark modification to the exception template, source preservation, destination guards, total instruction/cache helper dispatch counts, guest stack, original handler-table contents, and template restoration. Marked/debug paths remain strict pre-`DBPrintf` synthetic stops.

NWiiRecomp analyzes **35 guest code entries** for this private slice, including **five conservative synthetic test guard/address roots**; these five are not newly executed original-game functions. No PowerPC interpreter fallback occurred on tested paths.

## Diagnostic cache-trace adaptation

V43's original-free cache-observability patch stored only the first 32 line addresses. V44 adds a **fail-closed, idempotent, standalone source-only** `apply_cache_trace_v44.py` extension that raises both diagnostic trace capacities to 256 entries. The independent `test_cache_trace_guards_v44.py` checks installer atomicity, idempotence, known-old/new compatibility, and malformed/partially patched source rejection. The runtime records every event during the three unmarked 15-vector startup scenarios in one session, including all **225 flushes and 225 invalidations** accumulated across those scenarios. The trace is **not** a Wii hardware cache model, cache-coherence implementation, or AOT code-invalidation mechanism.

## Reproduce privately

Requirements: GCC with C++20, Python 3, an isolated copy of the original unmodified NWiiRecomp archive, and the owner's original Undercover Wii DOL with SHA-256:

`16a09adcf1987c1f3617d10f3a1cb830f32886afb583f9f8f88e0963ae5fe1f4`

```bash
bash run_osinit_vectors_v44.sh /private/NWiiRecomp-master /private/NfsMWRelease.dol.bin
V44_SANITIZE=1 bash run_osinit_vectors_v44.sh /private/NWiiRecomp-master /private/NfsMWRelease.dol.bin
```

The runner applies V15, V26, V29, V30, V43 and V44 original-free runtime/emitter patches as needed, verifies the private test image and source mutation guards, emits original game-derived C++ only in a temporary directory, compiles it, and erases the private files on exit. It also accepts an already V44-patched isolated checkout after verifying the expected cache emitter and context revision. Never run these modifying scripts in an unrelated or dirty NWiiRecomp working tree.

## Verification results

| Verification | Result |
| --- | ---: |
| Original-owner native assertions, six `OSInit` shapes plus direct helpers | **16,383 / 16,383** |
| SHA, malformed DOL, original code mutations, call graph and output-safety checks | **445 / 445** |
| V44 diagnostic cache-trace patch guards | **16 / 16** |
| V43 cache-emitter patch guards on pristine source | **14 / 14** |
| V30 hardware/FPSCR patch guards on pristine source | **14 / 14** |
| V29 performance-SPR patch guards on pristine source | **13 / 13** |
| Optimized native C++20 execution | **Pass** |
| Standalone owner-native ASan/UBSan binary, complete final assertions | **Pass** |
| Full clean original NWiiRecomp checkout optimized owner run | **Pass** |
| Full owner sanitizer script rerun | **Timed out during large compile; not counted as pass** |

Native sanitizer execution was verified separately using the same generated original-code C++ and full V44 test source, compiled with `-O0 -g0 -fsanitize=address,undefined -fno-omit-frame-pointer`. The full sanitizer driver timed out while compiling its last large native target, before test execution, and is not counted as a completed full-script pass.

## Distribution and next dependencies

Eight new independent original-free sources: `make_osinit_vectors_v44.py`, `generate_osinit_vectors_v44.cpp`, `test_osinit_vectors_v44.cpp`, `test_osinit_guards_v44.py`, `apply_cache_trace_v44.py`, `test_cache_trace_guards_v44.py`, `run_osinit_vectors_v44.sh`, and this README. The source-only ZIP includes V43's prerequisites. **Do not publish** original DOL/ELF files, private extracted guest instructions, generated C++ for game functions, or copyrighted game assets.

The genuine full exception-vector loop now reaches the original final `DBPrintf`, but Wii debug/output services and `__OSInitSystemCall` (`0x805290C8`) remain unresolved. Complete hardware cache semantics, Wii IOS/graphics/audio services and the original game `main` (`0x802D3F40`) have not been reached. The *continuous* original `__start` execution milestone is still V26 through `0x805206B4`, with five V26 harness sources unpublished on the branch. The next priority is closing that reproducibility gap, then connecting the validated direct `OSInit` sequence to one continuous original startup dispatch. Keep PR #36 **draft**.
