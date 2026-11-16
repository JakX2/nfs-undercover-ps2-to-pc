# V64: Original Wii OS cache initializer returns to OSInit through genuine OSSetErrorHandler

**Status: source-grounded, directly entered original `OSInit` path, not continuous original `__start`, not a game boot.**

From an owner-private SHA-256-pinned Wii Undercover DOL, V64 extends V62's authentic L2 cache setup and completion polling at `0x80522644` through the rest of the **original `__OSCacheInit`** (through `0x80522674`), including the original **`OSSetErrorHandler(1, 0x805223F8)`** call at `0x80522650`. Its complete original PowerPC `OSSetErrorHandler` routine (162 instructions) executes the ordinary-index branch through original interrupt disable, pointer replacement, interrupt restore and register/stack epilogue. `__OSCacheInit` restores its caller frame and returns to original `OSInit`. A synthetic test-only syscall at **`0x805208C4`**, before unresolved `EXIInit`, is the terminal boundary.

The error-handler callback pointer registered at `0x805223F8` and the context exception-handler target at `0x80522E34` are *not executed*. They are synthetic/conservative analyzer roots in this fixture, not verified original-code execution. Likewise, the original error-index-16 floating-point branch is translated into native C++ but **not executed** here. The two original floating-point helper bodies referenced by that branch are present as private original-code slices solely to preserve honest callgraph resolution.

## Measured original PPC execution

- **18,019 / 18,019 native semantic assertions**, over six original directly entered `OSInit` configurations and inherited direct-original helper regressions. Three normal uninterrupted original `OSInit` configurations reach the new `0x805208C4` stop. Other explicit test/debug branches stop earlier by design. **Zero interpreter fallback** on all tested paths.
- The genuine `OSSetErrorHandler` installs error handler 1 in the original guest error-handler table at `0x806F4F74`, without altering the adjacent slots, and restores guest MSR, stack, LR and r28–r31. The same registration is verified on both initially enabled and disabled L2 cache branches, including additional directly entered cache-helper cases.
- All earlier original Wii exception-vector, original memcpy/cache-line loops, system-call initializer, alarm, module, interrupt-mask, context and L1/L2 cache invariants remain passing. Original return-address and overlapping nested stack-slot checks were updated to match the **new genuine error-handler frame**; old V62 assumptions were not merely suppressed.
- **214/214** new SHA, original instruction-mutation, private DOL section geometry, truncated/trailing-image, output no-overwrite and external-original-DOL safety guards, including every newly restored `OSSetErrorHandler` instruction, cache tail and original floating-point helper instruction.
- Full **optimized**, **ASan/UBSan** and **fresh unmodified NWiiRecomp ZIP** test runs passed. Fresh run passed prerequisite V29 **13/13**, V30 **14/14**, V43 **14/14**, V44 **16/16**, V60 **26/26** and V62 **10/10** source-patch guards. **63 analyzed native entries** include prior synthetic/conservative analyzer roots and do not mean 63 independent genuine original functions executed.
- `DBPrintf` remains explicitly test-only callback HLE; L2CR L2IP busy-to-ready state is still an injected test-device callback, not automatically implemented Gekko hardware. No actual game exception, new error-handler callback, or L2 hardware timing is verified.

## Reproduce privately

Supply a legitimately obtained original Wii executable whose SHA-256 matches `16a09adcf1987c1f3617d10f3a1cb830f32886afb583f9f8f88e0963ae5fe1f4` and a matching isolated NWiiRecomp checkout:

```bash
bash run_osinit_cache_return_v64.sh /private/NWiiRecomp-master /private/NfsMWRelease.dol.bin
V64_SANITIZE=1 bash run_osinit_cache_return_v64.sh /private/NWiiRecomp-master /private/NfsMWRelease.dol.bin
```

The runner removes private owner-game DOL slices, emitted original game C++, native executables and generated fixtures on completion. The source-only package contains only independently written original-free code and documentation. Never commit original game DOL/ELF, derived PPC code or generated game C++.

## Limits and next work

The next original call at `OSInit 0x805208C4` is **`EXIInit` at `0x804EF9BC`**. Need to inspect and implement the EXI initialization dependencies with verified MMIO and services, then SI, SRAM and thread/audio startup. The test still starts at **direct `OSInit 0x80520670`**, not continuous original `__start`. The last independently verified continuous original `__start` chain remains V26 through `0x805206B4`, with five missing V26 harness sources not yet committed.

Do not claim complete L2 hardware behavior, Wii IOS, the original game's `main`, Windows native boot, first frame, frontend or gameplay. Keep PR #36 draft.
