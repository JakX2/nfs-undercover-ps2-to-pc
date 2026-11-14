# V27: Original Wii `__OSGetExecParams` executes natively

**Verified bounded original-game helper execution, not a full native Wii boot.**

This owner-private test extracts the *complete original* Wii `__OSGetExecParams`
function at guest `0x80523B1C` (36 bytes) and `memcpy` at `0x80004338`
(80 bytes), from the SHA-256-pinned original Undercover Wii DOL. The original
PowerPC instructions are translated by NWiiRecomp's analyzer and native C++
emitter, then run through its non-split `run_game(CPUContext&)` dispatcher.
No PowerPC interpreter fallback or replacement implementation is used on the
executed path.

The original `OSInit` calls `__RAS_OSDisableInterrupts_begin` at
`0x805206B4`, sets `r3=r30`, then calls `__OSGetExecParams` from
`0x805206BC`. Original `r30` is `0x806F4F00`, the destination buffer. This
milestone executes the genuine *callee*, **not yet its original OSInit caller**.
The V26 continuous original startup still ends at its synthetic syscall stop
at `0x805206B4`.

## Native execution semantics

The original helper reads the guest low-memory exec-params pointer at
`0x800030F0`. When its unsigned value is below `0x80000000`, it writes a
single zero word to the `r3` destination and returns. Otherwise it transfers
control to original `memcpy`, copying **28 bytes** from that pointer to `r3`.
The cross-function transfer is an unconditional PPC tail branch, preserving
caller LR. These semantics are verified by execution, not just disassembly.

Four test configurations exercise a zero pointer, the high invalid sentinel
`0x7FFFFFFF`, a regular MEM1 source buffer, and the exact lower valid boundary
`0x80000000`. Tests check all 28 destination bytes, two overflow guards and an
underflow guard, source preservation, guest SP/LR, nonvolatile GPR state,
execution count, dispatch counts, precise V26 syscall-stop PC, and zero PPC
interpreter fallback. There are three native analyzer function entries
(original helper, original memcpy and a test-only stop). Only the stop uses
synthetic `sc; blr`, at guest `0x80004900`.

## How to reproduce

Use a local, **separate** pristine NWiiRecomp checkout and an owner-provided
`NfsMWRelease.dol.bin` with SHA-256
`16a09adcf1987c1f3617d10f3a1cb830f32886afb583f9f8f88e0963ae5fe1f4`.
From `research/native_recomp`:

```bash
bash run_execparams_v27.sh /private/NWiiRecomp-master /private/NfsMWRelease.dol.bin
V27_SANITIZE=1 bash run_execparams_v27.sh /private/NWiiRecomp-master /private/NfsMWRelease.dol.bin
```

The runner reuses the existing idempotent original-free V15 dispatcher and
V26 syscall-PC patches. It creates the sliced original DOL, generated C++ and
binaries **only inside an automatically deleted temporary directory**. It
refuses to overwrite owner inputs and runs negative fixture checks before
executing the native binary. The supplied NWiiRecomp checkout is modified by
patches; use an isolated copy. C++20 GCC, Python 3 and bash are required.

## Verified local results (2026-11-14)

| Test | Result |
| --- | --- |
| Owner DOL SHA-256 | Match |
| Native original PowerPC helper and memcpy | 3 analyzed entries; 4 trials |
| Optimized original-native semantic checks | 99/99 passed |
| Owner SHA, mutated PPC fixture, output safety negatives | 15/15 passed |
| GCC AddressSanitizer and UndefinedBehaviorSanitizer | 99/99 passed; 15/15 guard checks |
| Interpreter fallback | 0 |

The source-only scripts contain no original game executable, game assets,
extracted PowerPC function bodies or generated translated game C++. This
milestone does **not** increase the V26 continuous-startup function count or
assertion count: it is a separate original-game native dependency proof.

## Next

Integrate both original exec-params branches into the continuous V26 `OSInit`
run, preserving the original preceding interrupt-disable call. Then continue
through performance-counter register setup, IOS and remaining OS initialization
with verified, guest-visible state and no silent HLE substitutions. The five
unpublished V26 generator/test files are still a GitHub reproducibility gap;
commit them separately when recovered, without pretending V27 replaces them.
No original game `main`, first frame, frontend or gameplay has run.
