# V62: Native original Wii L2CR completion polling with an explicit test-device status provider

**Scope:** The owner's SHA-256-pinned Wii DOL supplies original PowerPC instructions. The test invokes original `OSInit` directly and executes the authentic disabled-L2 branch of `__OSCacheInit` through both L2IP polls, guest MSR restoration, and L2 reenable. It stops via an intentional synthetic syscall at `0x80522644` **before** `OSSetErrorHandler`. This is **not** a physical or full software model of Gekko L2 cache behavior, nor continuous original `__start`, nor a game boot.

## Original-code extension

- V61 executed `__OSCacheInit` through `0x805225E8`, immediately before the hardware L2 completion poll.
- V62 restores the genuine **0x58-byte original PowerPC range `0x805225EC`–`0x80522640`** from the owner's private DOL. It includes two L2IP polling loops, a second status-check debug path, clearing L2I, restoring the saved MSR, L2 reenabling, and an original final `DBPrintf` call.
- The original `PPCMfl2cr` and `PPCMtl2cr` execute through NWiiRecomp-generated C++, not an interpreter. The original `__OSCacheInit` continues to the **explicit test-only stop at `0x80522644`**, immediately before calling the authentic, still-unimplemented `OSSetErrorHandler` at `0x805230B8`.
- The already-enabled L2 route also reaches the existing explicit test stop at `0x80522644`, without executing the disabled-L2 initialization branch.
- Earlier original exception-vector setup, native `memcpy`, cache maintenance, original syscall and alarm setup, module, interrupt and context initialization, and L1 cache initialization remain in the same bounded test. Prior `DBPrintf` callbacks remain explicitly test-only.

## Guest L2CR register adaptation

`apply_l2cr_device_v62.py` is an independently written, fail-closed and idempotent patch to the matching NWiiRecomp revision. It introduces an **optional** `CPUContext::l2cr_read_provider` callback. Generated `mfspr L2CR` reads the provider only if the owner explicitly registered one. **Without a provider, it returns `CPUContext::l2cr` unchanged**, preserving V60 value-state behavior. Generated `mtspr L2CR` continues to write the guest value normally.

This separation is essential: L2I (bit 21, mask `0x00200000`) is the global invalidate *request*, whereas L2IP (bit 0, mask `0x00000001`) is the *read-only in-progress status*. The test explicitly supplies synthetic busy/ready sequences to exercise original loopbacks; there is **no automatic clearing, timing assumption, true asynchronous completion, cache invalidation, coherency or compiled-code invalidation** in the runtime. A permanently busy external status provider triggers a bounded test exception instead of being silently declared complete. Replacing this test device with verified Gekko behavior remains future work.

Relevant public architecture references:
- IBM Gekko RISC Microprocessor User's Manual 1.2, L2CR bit layout, SPR 1017, `L2I` and `L2IP` descriptions: https://datasheets.chipdb.org/IBM/PowerPC/Gekko/gekko_user_manual.pdf
- Linux PowerPC L2CR constants: https://kernel.googlesource.com/pub/scm/linux/kernel/git/song/linux/+/refs/heads/md-next/arch/powerpc/include/asm/reg.h
- Motorola PowerPC cache invalidation erratum about `L2IP` observing a busy state: https://www.nxp.com/docs/en/errata/MPC7400CE.pdf (related processor family, not a Wii-specific timing guarantee).

## Verified execution

Reproduce with your legitimately owned original Undercover Wii DOL and an isolated matching NWiiRecomp checkout:

```bash
bash run_osinit_l2poll_v62.sh /private/NWiiRecomp-master /private/NfsMWRelease.dol.bin
V62_SANITIZE=1 bash run_osinit_l2poll_v62.sh /private/NWiiRecomp-master /private/NfsMWRelease.dol.bin
```

The runner removes the private sliced DOL, emitted original-code C++, native executable, and temporary generator on completion. Do not publish owner executables, private slices or generated game C++.

- **18,005 / 18,005** native semantic assertions, with no PPC interpreter fallback on tested paths. Six original direct-`OSInit` scenarios, including three normal uninterrupted paths; additional direct L1/L2 cache and L2CR helper tests; positive busy/ready combinations for both original polls; MSR save/restore and L2 enable state; exact original guest dispatch counts; a separate **never-completes negative test**.
- **74 / 74** original-code mutation, expected Wii image SHA, DOL geometry, output overwrite and owner private-image guards.
- **10 / 10** V62 source-patch idempotency/ambiguity/fail-closed guards. The fresh, unmodified upstream checkout also passed V29 **13/13**, V30 **14/14**, V43 **14/14**, V44 **16/16** and V60 **26/26** prerequisite patch tests.
- Optimized C++20, complete ASan/UBSan and freshly extracted untouched NWiiRecomp checkout runners **all passed**.
- **59 analyzer entries**, including synthetic and conservative roots, not 59 independently executed original functions.
- Original DOL SHA-256: `16a09adcf1987c1f3617d10f3a1cb830f32886afb583f9f8f88e0963ae5fe1f4`.

## Next concrete work

1. Replace the test-injected status sequence with a documented Wii/Gekko L2 cache device contract and explicit invalidation-completion event; independently test read-only L2IP and write-time bit semantics.
2. Native-execute original `OSSetErrorHandler`, finish `__OSCacheInit`'s epilogue, return to `OSInit`, and advance into EXI/SI/SRAM and threading initialization.
3. Reconnect the proven direct-`OSInit` initialization to continuous original `__start` (currently separately verified only through V26's `0x805206B4`) and publish the five still-missing V26 harness sources.

**Do not claim** hardware-faithful L2 invalidation, complete game startup, original `main`, first frame, frontend or gameplay. Keep PR #36 draft.
