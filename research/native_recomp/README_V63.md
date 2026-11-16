# V63: Full original Wii OSSetErrorHandler translated; ordinary registration executes natively

**Status: independent original-PowerPC native execution, not integrated OSInit, game boot, or a complete runtime.**

V63 analyzes and emits the complete original **0x288-byte `OSSetErrorHandler` function at `0x805230B8`** from the user's SHA-256-pinned Undercover Wii DOL. Its 162 original instructions are emitted as native C++ by the unchanged NWiiRecomp translating pipeline (aside from existing V15/V26 source fixes). Two genuine original interrupt helper bodies execute with it: `__RAS_OSDisableInterrupts_begin` at `0x805265AC` and `OSRestoreInterrupts` at `0x805265D4`. A synthetic `sc; blr` at `0x80523340` is the only test return boundary. No proprietary PowerPC body or generated game C++ is distributed.

## Verified guest behavior

- **42 original-PPC-native tests**: error indices `0, 1, 2, 7, 15, 17, 31` crossed with six different guest MSR states. Each original call disables interrupts, reads and replaces the selected error-handler table entry, restores the prior interrupt-enable state, returns the original handler pointer, restores LR/stack and r28-r31, and leaves adjacent guest-memory canaries unchanged.
- **423 / 423 semantic assertions** passed using NWiiRecomp-generated native C++; **zero interpreter fallback** on all exercised paths.
- The complete original `OSSetErrorHandler` body, plus the original guest MSR and floating-point helpers referenced by the *unexecuted* index-16 path, is translated. The exception-index-16 floating-point context updates, floating-point helper behavior, and crash/error-handling callback dispatch are **not verified**. No synthetic FPU services are asserted as working.
- **255 / 255 fail-closed guards** mutate every original function instruction and every bundled original helper instruction (plus the explicit terminal), verify section layout, owner SHA, trailing/truncated bytes, and prevent overwriting existing output. Every mutation test passes an **empty** output directory, so rejection cannot be attributed merely to an already populated destination.
- **Optimized C++20**, **ASan/UBSan** and a **fresh extraction of the original unmodified NWiiRecomp ZIP** all passed. The fresh run installs the V15 non-split dispatcher and V26 syscall-PC fixes; no additional runtime-patch behavior is necessary to test ordinary error registrations.
- Private test image contains three text sections. Analyzer reports **eight entries**: the complete error handler, four helper entries (MSR and FPU), the two original interrupt helpers, and the synthetic stop. Some function entries are translated but not executed by these tests.

## Reproducing

Supply your own legitimately obtained Undercover Wii DOL and a matching isolated NWiiRecomp checkout. The runner deletes temporary owner-code DOL fragments, native-generated original-code C++, and binaries on exit:

```bash
bash run_errorhandler_v63.sh /private/NWiiRecomp-master /private/NfsMWRelease.dol.bin
V63_SANITIZE=1 bash run_errorhandler_v63.sh /private/NWiiRecomp-master /private/NfsMWRelease.dol.bin
```

Owner-original DOL SHA-256 must equal `16a09adcf1987c1f3617d10f3a1cb830f32886afb583f9f8f88e0963ae5fe1f4`. The builder extracts genuine instructions from the original DOL only after validating that hash. The original source DOL, ELF, private slice and translated guest C++ must remain private.

## Next verified integration target

V62 separately executes direct `OSInit` through both `__OSCacheInit` L2CR polling loops up to `0x80522644`. V63 establishes the ordinary-index `OSSetErrorHandler` semantics required by the next call at `0x80522650` (error index 1, handler pointer `0x805223F8`). **V63 does not yet join these paths**, and must not be presented as reaching `OSInit` return or `EXIInit`. The remaining original `__OSCacheInit` epilogue and the direct `OSInit` continuation to `0x805208C4` are still to be verified. The continuous original `__start` path is separately verified only through V26's `0x805206B4`, with five missing source-only V26 harness files not yet committed.

Long-term unimplemented: Wii hardware-accurate caches and IOS, original `main`, first Windows frame, frontend, gameplay. Preserve draft PR #36, retain original-free sources only.
