# V22: Native execution of Undercover Wii `__init_data` and memory helpers

**Status: Verified isolated original-code execution. Not a complete Wii startup or a playable PC build.**

V22 tests the original 168-byte / 42-instruction Wii `__init_data` at guest address
`0x80004238` through **NWiiRecomp's actual generated native C++20 `run_game(CPUContext&)` dispatcher**.
It also executes four complete original game helper routines:

| Helper | Guest address | Size | Tested effect |
| --- | --- | --- | --- |
| `memcpy` | `0x80004338` | 80 bytes / 20 PPC instructions | 65-byte synthetic guest-memory relocation |
| `__flush_cache` | `0x80004304` | 52 bytes / 13 PPC instructions | Correct native dispatch and return; cache instructions remain host no-ops |
| `memset` | `0x8000443C` | 48 bytes / 12 PPC instructions | Original zero-fill wrapper invoked |
| `__fill_mem` | `0x80004388` | 180 bytes / 45 PPC instructions | Clears BSS ranges with PPC byte/word loops |

Only a **synthetic test-only `sc; blr` endpoint** at `0x80004900` stops the run. The owner-private DOL source is
SHA-256 pinned to `16a09adcf1987c1f3617d10f3a1cb830f32886afb583f9f8f88e0963ae5fe1f4`.
The owner's original DOL, private test DOL, generated game-derived C++, and actual resources **are not bundled or committed**.

## Original Wii data table findings

The original initialization tables reside at `0x80006420` (copy/relocation) and `0x800064B0` (BSS zero-fill),
and are loaded into the actual NWiiRuntime guest MMU for the isolated test.
The original copy table has **11 nonzero entries**, all with `source == destination`, and a terminating zero entry.
Therefore `__init_data` *correctly skips* its `memcpy` and cache-flush paths with the original table because the
Wii DOL loader is expected to have already mapped initialized data.

The BSS table has **three nonzero entries**, clearing **950,236 + 13,164 + 56 = 963,456 bytes** in total.
The test pre-fills those ranges, checks every byte is cleared, and protects the bytes immediately before and after
all three ranges. A second, **independently authored small test table** deliberately adds a 65-byte source-to-destination
relocation plus 96- and 7-byte BSS entries. That forces the original `memcpy`, `__flush_cache`, `memset`, and
`__fill_mem` call chain to run and verifies copied data, source preservation, BSS clearing and canaries.

Both modes count entry into each translated helper to ensure the observed effect is produced by the original
PowerPC control flow rather than by test-side memory modification after dispatch.

## Reproduce with a private owner-local copy

Requirements: Python 3, GCC/Clang with C++20, and NWiiRecomp sources. An isolated checkout is preferred;
`run_v22_tests.sh` applies the **existing source-only V15 non-split dispatcher fix** to the local checkout
(idempotently). Other startup patches from V18-V21 are not needed for this isolated data-initialization test.

```bash
cd research/native_recomp
bash run_v22_tests.sh /path/to/NWiiRecomp-master /private/path/NfsMWRelease.dol.bin
V22_SANITIZE=1 bash run_v22_tests.sh /path/to/NWiiRecomp-master /private/path/NfsMWRelease.dol.bin
```

For original-free guard tests alone, no game file is needed:

```bash
bash run_v22_tests.sh /path/to/NWiiRecomp-master
```

The runner creates a new private `mktemp -d` working directory and deletes it on exit. The full original-game
binaries and generated C++ are never published. The original table data is read from the owner's verified DOL
rather than embedded in a public fixture. All generated tests use the real upstream `CPUContext` / guest MMU.

## Verified results (2026-11-13)

| Test | Result |
| --- | ---: |
| Original `__init_data` and all genuine memory routines, original table, three runs | **2,890,458 assertions passed** |
| Same genuine original PPC functions, synthetic relocation/zero table, 12 runs | **3,069 assertions passed** |
| Invalid table, truncated PPC functions, hash, overwrite and generator safety | **41 checks passed with owner DOL**, 36 original-free |
| Original PPC functions discovered and generated | **6**, counting the synthetic stopping endpoint |
| Release build, original+synthetic data tables | **Passed** |
| GCC AddressSanitizer/UndefinedBehaviorSanitizer, original+synthetic data tables | **Passed** |
| Fresh upstream NWiiRecomp checkout, original+synthetic data tables | **Passed** |
| Interpreter fallback and unexpected syscall | **None** |

## Remaining limitations and next steps

- **Isolated `__init_data` entry, not seamless `__start` continuation.** Test seeds a valid guest stack and
  makes its own controlled return. The real `__start` reaches this function only after preceding Wii hardware
  initialization, whose error-handler registration and diagnostic routines are not fully connected.
- The recompiler currently emits **no-op host behavior for cache maintenance** inside `__flush_cache`, so actual
  I-cache/D-cache coherence has not been proven. The helper's original control flow and return are tested.
- The original copy table is intentionally in-place. The game-wide loader and MMU mapping still need end-to-end
  validation when executing `__start` in sequence.
- `OSSetErrorHandler` is a **648-byte original routine** with Wii OS service dependencies. It remains a test-only
  boundary in V21. Do not claim it is faithfully implemented merely because `__init_data` can run separately.
- `OSInit`, the original `main`, GX/audio input services, and the frontend have not been reached; native boot and
  playable gameplay remain unverified.

**Next:** bridge the original `__start` third call at `0x80004054` into this verified data-initialization path,
using a source-grounded OS error-handler state model or faithfully translated OS routines. Then continue toward
Wii `DBInit`, `OSInit`, and `main` with bounded guest-PC traces.
