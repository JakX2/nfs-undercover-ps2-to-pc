# V28: Original Undercover Wii `OSInit` executes through `__OSGetExecParams`

**Verified bounded native integration test, not an uninterrupted `__start` boot or a playable port.**

V28 independently starts at the owner's original Wii `OSInit` address
`0x80520670` and executes the first **80 original PowerPC bytes** through the
real second interrupt-disable call and the original `__OSGetExecParams` call at
`0x805206BC`. The next original `OSInit` instruction, `li r3,0` at
`0x805206C0`, is replaced with an **explicit synthetic `sc; blr` stop** in a
private test-only DOL. No original instructions after `0x805206BC` run.

Nine function entries are analyzed and translated to host C++20 by the actual
NWiiRecomp analyzer and non-split `run_game(CPUContext&)` emitter. These are:

| Guest address | Original function | Test status |
| --- | --- | --- |
| `0x80520670` | `OSInit` | Authentic prefix through the exec-params call |
| `0x805450E8` | `_savegpr_20` | Complete original body |
| `0x8052A844` | `__OSGetSystemTime` | Complete original body |
| `0x8052A824` | `OSGetTime` | Complete original body |
| `0x805265AC` | `__RAS_OSDisableInterrupts_begin` | Complete original body, twice called |
| `0x805265D4` | `OSRestoreInterrupts` | Complete original body |
| `0x80523B1C` | `__OSGetExecParams` | Complete original body |
| `0x80004338` | `memcpy` | Complete original body, only on valid pointer path |
| `0x80520BDC` | Already-initialized branch | Explicit synthetic `sc; blr` rejection boundary; not taken |

The actual test stops at `0x805206C0`, inside the first `OSInit` function,
without adding a tenth analyzer function root.

## Genuine state changes covered

Four isolated native starts cover two MSR.EE initial states and four
low-memory `0x800030F0` exec-params source-pointer values: zero,
`0x7FFFFFFF`, a valid MEM1 pointer, and the boundary `0x80000000`.

The original `OSInit` creates its 80-byte frame, calls the complete original
nonvolatile register-save helper, sets its one-time initialization flag,
executes the complete system-time path and its high/low/high timebase read,
writes the original high/low timestamp globals, disables interrupts again, and
calls the authentic exec-params helper. For low pointers, the helper clears
only the first destination word; for valid addresses, it tail-branches into
the original `memcpy` to transfer exactly 28 bytes.

Native assertions verify the exact synthetic stop PC, guest stack/LR save,
all 12 saved nonvolatile GPR words, one-time init flag, low-memory/timebase
offset arithmetic (including carry and rollover cases), MSR.EE masking,
preservation of other MSR bits, native dispatch-call counts, destination
underflow/overflow canaries and every expected exec-params destination byte.
**No interpreter fallback** or unexpected synthetic syscall occurred.

The timebase source is still NWiiRuntime's existing **virtual instruction
counter**. `trace_call(OSGetTime)` seeds that virtual timebase in the test only
so the observed timestamp is reproducible. This is **not** evidence of real
hardware timing accuracy, IOS initialization, or clock fidelity.

## Reproduce locally

Requires Python 3, GCC with C++20, the owner-original Wii DOL matching SHA-256
`16a09adcf1987c1f3617d10f3a1cb830f32886afb583f9f8f88e0963ae5fe1f4`,
and a separate NWiiRecomp checkout.

```bash
bash run_osinit_execparams_v28.sh /private/NWiiRecomp-master /private/NfsMWRelease.dol.bin
V28_SANITIZE=1 bash run_osinit_execparams_v28.sh /private/NWiiRecomp-master /private/NfsMWRelease.dol.bin
```

The runner idempotently applies the original-free V15 non-split dispatcher
and V26 exact syscall-PC patches. It creates the SHA-validated private test
DOL and all emitted game-derived C++ under a temporary directory and deletes
them when the runner exits. It refuses nonempty generated-output directories.
The C++ test uses controlled stubbed hardware callbacks where needed, not a
production Wii service implementation.

## Verified results (2026-11-14)

| Check | Result |
| --- | --- |
| Original Wii `OSInit` through exec-params, four scenarios | **239/239 native assertions passed** |
| Private DOL SHA, malformed/altered instructions, bounds, output safety | **42/42 passed** |
| Native original/analyzer entries | **9** |
| Optimized native C++20 / emitter test runner | **Passed** |
| AddressSanitizer + UndefinedBehaviorSanitizer native runner | **Passed** |
| Freshly extracted pristine upstream NWiiRecomp + V15/V26 patches | **Passed** |
| Unplanned interpreter fallback / syscall sites | **Zero** |

The owner DOL/ELF, extracted function bodies, synthetic/private test DOL and
NWiiRecomp-generated game-derived C++ **are never shipped or committed**.
The distributed source is independent test infrastructure, structural
verification, documentation and existing original-free emitter patches.

## Scope and next work

V26 separately demonstrated continuous original Wii `__start` from
`0x8000403C` to the explicit earlier `OSInit` stop at `0x805206B4`.
**V28 does not yet combine that whole start chain with the V28 continuation.**
The complete five-file V26 runner/fixture package also remains missing from
GitHub and should be recovered/published from its earlier verified source-only
archive. After the source gap is closed, merge these proven functions into one
continuous `__start` dispatcher and validate on the original owner DOL.

From `0x805206C0`, the next genuine Wii `OSInit` dependencies are
`PPCMtmmcr0` (`0x804B7964`) and the other performance-counter setup helpers,
followed by more OS, IOS and hardware initializers. Graphics, frontend, world,
`main` (`0x802D3F40`), first frame, and gameplay are not reached.
