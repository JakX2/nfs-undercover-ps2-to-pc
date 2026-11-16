# V57: Original Wii interrupt initializer returns to original OSInit natively

**Scope: bounded original Wii native execution, not continuous `__start`, complete `OSInit`, Wii hardware emulation, game `main`, a displayed frame, or gameplay.**

## Genuine original execution

V57 builds on the SHA-256-pinned original Wii `OSInit` chain from V56. The owner-private builder replaces **only** the prior synthetic interrupt-loop stop at `0x805266AC` with the unmodified original PowerPC instructions from `0x805266AC` through `0x805266DC`. This executes the complete original `__OSInterruptInit` epilogue:

1. Branch to genuine **`OSRestoreInterrupts`** at `0x805265D4` (nine unmodified PPC instructions, already carried by the private test image); its original `mfmsr` / `mtmsr` logic restores the saved interrupt-enable state and returns the previous state.
2. Invoke original **`__OSSetExceptionHandler`** at `0x80520E9C` to install handler 4 at `0x80526CE0` into the guest exception-handler dispatch table.
3. Execute the original stack/register/LR restoration and `blr` in `__OSInterruptInit`, returning to the original caller `OSInit`. A deliberate **test-only syscall at `0x805208BC`** prevents entering the unimplemented `__OSContextInit`.

The complete original exception-vector copy, cache-line maintenance, system-call initialization, alarm registration, module clearing, and seven-bank interrupt-mask MMIO loop remain in the *same* directly entered `OSInit` sequence. The old final `DBPrintf` remains a **single explicit test-only return callback**; it is not a native reimplementation. MMIO callbacks supply deterministic register values and record transactions; they do **not** model live Wii interrupt-controller side effects.

The non-split NWiiRecomp analyzer discovers **50 entries**, including synthetic and conservative guards. The tested paths use **zero PowerPC interpreter fallback**. The private image's original code is extracted only from the owner's SHA-256-pinned DOL, not embedded in the six published source/test files or in generated native C++ distributions.

## Reproducible verification

- **17,785/17,785 original-native assertions**: six original `OSInit` configurations, complete vector/system-call/alarm/module/mask-loop regression, exact exception handler 4 installation, restored `r29`/`r30`/`r31`/stack/LR and 12 direct original `OSRestoreInterrupts` cases across both previous and requested EE states, including preservation of unrelated MSR bits.
- **532/532 source/DOL/mutation and safe-output checks**: every original interrupt-initializer word through `blr`, entire original interrupt-mask routine, interrupt-restore helper, original owner SHA, test-DOL geometry, handler-template data and no-overwrite guarantees.
- **Optimized C++20 and ASan/UBSan runs passed.** A freshly extracted, unmodified NWiiRecomp ZIP checkout reproduced the same 17,785 native assertions and 532 guards after applying the original-free prerequisite source patches (the initial clean run was split after compilation timeout); prerequisites V29 13/13, V30 14/14, V43 14/14 and V44 16/16 guards also passed.
- Private owner Wii DOL SHA-256: `16a09adcf1987c1f3617d10f3a1cb830f32886afb583f9f8f88e0963ae5fe1f4`.

From the extracted source-only ZIP, supply your own legitimate original Wii DOL and a dedicated NWiiRecomp checkout:

```sh
bash run_osinit_interrupt_return_v57.sh /private/NWiiRecomp-master /private/NfsMWRelease.dol.bin
V57_SANITIZE=1 bash run_osinit_interrupt_return_v57.sh /private/NWiiRecomp-master /private/NfsMWRelease.dol.bin
```

The runner patches only its isolated NWiiRecomp checkout, runs the prerequisite source-patch guards, then deletes all temporary private game-derived DOL slices, translated C++, generated binaries and output data. The ZIP is source/test/documentation only.

## Next work

1. Recompile the original `__OSContextInit` after `0x805208BC`, preserving the complete original execution chain within `OSInit`.
2. Restore all test-only debug callbacks via genuine, independently authored runtime services; implement verified Wii hardware/IOS/MMIO behavior rather than assuming deterministic MMIO test observations equal full hardware emulation.
3. Connect the later directly entered `OSInit` sequence to continuous execution from the original `__start`. The last verified `__start` test remains V26 through `0x805206B4`, with five unpublished V26 harness sources still a reproducibility gap.
4. Retain PR #36 as draft until real native boot and eventually game `main`, first frame and gameplay are demonstrated.

Never publish copyrighted Wii executable data, owner-private function bodies, game assets or emitted translated game C++.
