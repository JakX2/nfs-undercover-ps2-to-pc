# V58: Original Wii OS context initialization returns to OSInit natively

**Scope: direct original `OSInit` entry, bounded original Wii PowerPC execution through NWiiRecomp-generated native C++, not continuous `__start`, a bootable Windows game, or a Wii debug-service implementation.**

## Original-code path

The SHA-256-pinned owner-original Wii `OSInit` at `0x80520670` advances past V57's controlled stop at `0x805208BC` and calls the **full authentic 72-byte `__OSContextInit`** at `0x80522EB8`. The genuine function:

1. Saves its guest LR and allocates a 16-byte stack frame.
2. Registers original exception handler 7 at guest address `0x80522E34` via the original `__OSSetExceptionHandler` at `0x80520E9C`.
3. Clears the original low-memory current-context word at `0x800000D8`, leaving adjacent words intact.
4. Calls `DBPrintf` at `0x804E50B8`, handled **only by the existing explicit test-only callback**. This is not an implementation of original game logging or debug transport.
5. Restores original LR and stack, returns to `OSInit`, and stops at **the synthetic terminal syscall `0x805208C0`**, immediately before the next original startup call.

The original exception handler **target** `0x80522E34` is not executed. In the private test DOL it remains synthetic NOP fill and must never be counted as an executed authentic function. NWiiRecomp's analyzer finds **52 roots** in the private image, including this unexecuted synthetic function entry, old conservative analyzer roots and other test-only guards. All verified native execution paths use **zero PowerPC interpreter fallback**.

The full previously verified exception, system-call, alarm, module and interrupt initialization path is executed unchanged before the original context initializer, with the longstanding test-only `DBPrintf` callback and deterministic MMIO read/write callbacks. The MMIO callbacks are not a Wii interrupt controller.

## Verification

- **17,830/17,830 native assertions** over six integrated original `OSInit` cases and direct-helper tests, including four new direct original `__OSContextInit` tests with independently seeded nonzero low-memory context pointers, stack, LR and MSR values. All check the register/save/return sequence, context-pointer zeroing and canaries, handler 7 registration, expected debug callback count and lack of PowerPC interpreter fallback.
- **28/28 new V58 negative/safety checks** mutate the synthetic call/terminal, every original context function word, key private DOL header fields and original-owner SHA; checks also forbid overwriting existing private output files or nonempty generator directories. The complete private image is independently pinned to original/synthetic section FNV-1a hashes by the fail-closed generator; previously published V57 coverage remains in its separate regression suite.
- **Full optimized C++20 and ASan/UBSan runners passed**, with zero interpreter fallback on tested original paths.
- **Freshly extracted, unmodified NWiiRecomp archive reproduced the same 17,830 assertions and 28 guards**, including the V29 **13/13**, V30 **14/14**, V43 **14/14** and V44 **16/16** prerequisite patch guards.
- Original owner DOL SHA-256: `16a09adcf1987c1f3617d10f3a1cb830f32886afb583f9f8f88e0963ae5fe1f4`.

From the source-only ZIP, with an authorized original DOL and a **dedicated writable NWiiRecomp checkout**:

```sh
bash run_osinit_context_v58.sh /private/NWiiRecomp-master /private/NfsMWRelease.dol.bin
V58_SANITIZE=1 bash run_osinit_context_v58.sh /private/NWiiRecomp-master /private/NfsMWRelease.dol.bin
```

The runner uses a temporary directory for owner-original private test DOL, generated translated game C++, native test binary and logs; it removes these on exit. The ZIP contains only independently authored source/test/documentation, not proprietary original function words, original game binaries/assets, a private image or game-derived translated C++.

## Next engineering steps

- Continue original `OSInit` after `0x805208C0`, inspect and verify the next called original function and Wii OS/IOS dependencies.
- Replace the current test-only debug callback with an independently authored validated native service where needed; advance real MMIO/interrupt behavior rather than claiming deterministic test observations equal hardware support.
- Integrate the later direct `OSInit` execution with the continuous original `__start`, which separately remains at V26 through `0x805206B4`. Five old V26 test harness sources still have not been committed and remain a reproducibility gap.
- **Do not claim** game `main`, first frame, frontend, gameplay or native Windows boot before they are independently observed. Preserve draft PR status.
