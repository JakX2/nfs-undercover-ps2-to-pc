# V50: Original Wii interrupt initialization prefix and genuine memset execute natively

**Scope:** Original-game native PPC execution in an isolated owner-private test. This does not mean full `__OSInterruptInit`, OS initialization, a native Windows boot, or a playable game.

## Genuine code covered

The original Undercover Wii **`__OSInterruptInit`** begins at **`0x8052661C`**. Its authentic 12-instruction prefix now runs through NWiiRecomp's native non-split C++ dispatcher, including the original direct PowerPC `bl` to **`memset` at `0x8000443C`**. The complete original 48-byte `memset` and original 180-byte **`__fill_mem` at `0x80004388`** execute too, with no PPC interpreter fallback.

The 128-byte interrupt-handler table at **`0x80003040`** is cleared byte-for-byte. The initializer writes the real table address to the original `r13`-relative global (`r13-3408`), saves its stack frame/LR and callee-saved registers, and then reaches an explicit **test-only syscall stop at `0x8052664C`**. The original instructions at `0x8052664C` and later are **not executed** in this slice; this is **before** interrupt-mask and Wii MMIO-register initialization. The private test image is created only from the owner's SHA-256-pinned original Wii DOL; no original game instruction bodies are embedded in the distributed source.

## Verified results

| Check | Result |
| --- | --- |
| Owner-original native assertions, eight nonzero interrupt-table input patterns | **1,155/1,155 passed** |
| Original PPC opcode mutation, original SHA, DOL geometry, and no-output-overwrite guards | **84/84 passed** |
| Analyzed entrypoints | **4** (three original functions and one synthetic stop) |
| Interpreter fallback | **0** |
| Optimized GCC C++20 | **Passed** |
| ASan/UBSan | **Passed** |
| Newly extracted unmodified upstream NWiiRecomp archive, with V15/V26 patches | **Passed** |

The assertions verify all 128 cleared bytes and both neighboring canaries for each run; the exact global-pointer store and adjacent canaries; guest register values, original saved LR, guest stack, helper-call counts and exact controlled termination. The V50 regression includes strict negative tests that mutate **every instruction** of the private test image (including the test-only syscall/return), malformed sections, and replacement of the owner executable. The source generator refuses malformed images without writing generated C++.

## Reproduce privately

Requires the owner-original Wii DOL with SHA-256 `16a09adcf1987c1f3617d10f3a1cb830f32886afb583f9f8f88e0963ae5fe1f4`, Python 3, C++20 compiler (GCC used) and an isolated NWiiRecomp checkout. The test runner **modifies the supplied NWiiRecomp checkout** by applying the existing fail-closed, idempotent V15 and V26 source-only patches. Prefer a disposable copy.

```bash
bash run_interrupt_prefix_v50.sh /private/path/NWiiRecomp-master /private/path/NfsMWRelease.dol.bin
V50_SANITIZE=1 bash run_interrupt_prefix_v50.sh /private/path/NWiiRecomp-master /private/path/NfsMWRelease.dol.bin
```

The runner builds a temporary private DOL containing the genuine owner-original PPC functions, asks NWiiRecomp to generate native C++, runs its assertions and corrupted-image test suite, then removes the private generated outputs on exit. No original game executable, assets, game instruction bodies, or generated C++ should be committed or shared.

## Integration boundaries and follow-up

**V49** separately verified that the original directly entered `OSInit` initializes Wii module globals through `0x805208B4`, with a test-only stop at `0x805208B8`. **V50 is a separate original `__OSInterruptInit` entry test**, **not** a connected continuation of V49. The next integration task is to connect its verified memory-initialization prefix to the V49 `OSInit`-entered chain, then implement interrupt-mask state, `SetInterruptMask`, Wii hardware MMIO behavior and the remainder of original `__OSInterruptInit`.

The last independently tested continuous **`__start`** chain remains V26 to `0x805206B4` with five missing published V26 harness files. Debug printing still uses a test-only callback in the later direct-`OSInit` chain; Wii OS/IOS and hardware-accurate cache/interrupt handling remain incomplete. **No game `main`, first native boot, frame, frontend or gameplay** has been verified. Keep PR #36 a draft.
