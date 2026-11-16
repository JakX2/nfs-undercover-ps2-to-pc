# V51: Original Wii OSInit reaches the interrupt table initializer in one native chain

**Scope:** Source-grounded original Wii PowerPC ahead-of-time recompilation, **not** a native game boot. This milestone connects the previously separate V49 `OSInit` path and V50 `__OSInterruptInit` prefix using genuine owner-original guest functions. The original `__start` full chain remains separately verified only through the earlier V26 boundary.

## Genuine original execution

Using the owner's locally supplied, SHA-256-pinned `NfsMWRelease.dol.bin`, the original directly entered `OSInit` (`0x80520670`) executes its previously verified time, hardware, exception-vector, system-call, alarm and module startup paths. At its authentic `bl` at `0x805208B8`, it now enters the **original interrupt initializer** at `0x8052661C` and executes its first 12 original PPC instructions. Those call the **complete original `memset`** at `0x8000443C` and the **complete original `__fill_mem`** at `0x80004388` through generated native C++.

The original code clears exactly **128 guest bytes at `0x80003040`** and writes the table address to the original `r13-3408` interrupt-table pointer. It does not modify adjacent canaries. Its original GPR29-GPR31 saves, LR slot and nested stack frame are validated. The deliberate test-only **`sc; blr` stop at `0x8052664C`** occurs before interrupt mask setup and Wii hardware/MMIO operations. A separate fail-closed synthetic guard at `0x805208BC` rejects accidental return into still-unverified `OSInit` code. Neither stop is part of the original game.

This test image has **48 analyzed native function entries** (including synthetic guard roots) and uses **zero interpreter fallbacks** on the exercised paths. The no-debug exception path returns through original `_restgpr_20` and uses a **single test-only `DBPrintf` callback** to bridge a still-unimplemented service; other debug branches terminate at their preexisting test guards. This is **not** a full `OSInit`, game `main`, boot, frame, or playable Windows port.

## Validation

Verified in the private owner-original workspace:

- **17,605/17,605 semantic assertions** over six `OSInit` boot configurations plus inherited direct helper tests. Original 128-byte interrupt-table contents, zero/nonzero seeds, global pointer preservation, canaries, guest return-address and nested-stack slot reuse, native dispatch counts, exception vectors, cache telemetry, syscall and alarm side effects all checked.
- **338/338** negative tests for the original image's SHA-256, PPC instruction mutation (including the interrupt prefix, `memset`, `__fill_mem`, all neighboring helpers, and copy templates), original DOL section geometry, missing/modified calls and output overwrite refusal.
- **16/16** V44 cache telemetry patch guards in the existing patched checkout.
- Full optimized C++20, full standalone **ASan/UBSan**, and fresh unmodified NWiiRecomp archive optimized runs passed. The fresh archive also passed **13/13 V29**, **14/14 V30**, **14/14 V43**, and **16/16 V44** prerequisite source-patch guards.
- Python syntax and shell syntax checks passed. The independent source-only package has no original DOL, ELF, extracted original PowerPC function body, generated game-derived C++, or asset.

The original owner DOL is SHA-256-pinned to `16a09adcf1987c1f3617d10f3a1cb830f32886afb583f9f8f88e0963ae5fe1f4` and is required only at local test time. All original PPC instruction bytes are read from that file into a temporary test DOL, which the runner deletes on exit. The native code generator checks guest section addresses, sizes, exact owner-private source hashes and the authentic call graph before emitting anything. It rejects a nonempty output directory.

## Reproduction

Requires Linux-like shell, Python 3, C++20 GCC, the owner Wii DOL, and an isolated checkout of NWiiRecomp. Run from the extracted source-only package:

```bash
bash run_osinit_interrupt_bridge_v51.sh /private/path/NWiiRecomp-master /private/path/NfsMWRelease.dol.bin
V51_SANITIZE=1 bash run_osinit_interrupt_bridge_v51.sh /private/path/NWiiRecomp-master /private/path/NfsMWRelease.dol.bin
```

The runner installs the existing original-free V15/V26/V29/V30/V43/V44 adaptations into the **isolated** NWiiRecomp tree, not the original game. The generated game-derived output and private image live only in an auto-removed temporary directory. The V51 source-only files depend on the earlier V49 original-free fixture builders and the V50 original-free interrupt-prefix extractor; the accompanying ZIP bundles both dependency sets.

## Integration boundary and next work

- Complete the original interrupt-mask and Wii hardware/MMIO portion of `__OSInterruptInit`, then connect its genuine return into `OSInit`.
- Replace the test-only `DBPrintf` service with a verified native implementation or explicit modeled stub with appropriate semantics.
- Integrate newer verified `OSInit` into the **original continuous `__start` chain**; its last verified owner-native boundary remains V26 at `0x805206B4`. Five V26 harness/runner files are still missing from this PR and remain a reproducibility gap.
- Continue original OS/IOS services, then reach game `main`, a real frame, frontend, and gameplay. **Do not** claim any of these are achieved yet.

No proprietary game executable, assets or game-derived translated function bodies should be committed. Keep PR #36 a draft and preserve Carbon adaptation work.
