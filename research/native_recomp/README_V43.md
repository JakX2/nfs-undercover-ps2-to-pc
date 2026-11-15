# V43: Original Wii exception-vector cache loops execute natively

**Scope:** Bounded original Wii game-code execution in a directly entered `OSInit` native test. This is **not** full Wii cache emulation, complete exception-vector installation, continuous `__start`, native boot or a playable Windows game.

## Original PPC progression

This milestone extends owner-original `OSExceptionInit` execution beyond V42's first authentic exception-vector copy. At original guest PCs `0x80520DA4`–`0x80520DB4`, the game now calls the complete original `DCFlushRangeNoSync` function at `0x80522320` (44 bytes) and `ICInvalidateRange` at `0x80522378` (52 bytes), including the original `dcbf`, `icbi`, `sync`, `isync`, CTR loops and return paths. An explicit synthetic stop at **`0x80520DB8`** prevents unverified subsequent exception-vector installation.

The first exception handler is the original **152-byte** template copied by the original `memcpy` from V42, placed at `0x80000100`. Both original cache routines perform **five operations on 32-byte cache-line addresses** (`0x80000100`, `0x80000120`, `0x80000140`, `0x80000160`, `0x80000180`) for the unmarked index-zero exception. The marked debug branch remains a strict synthetic stop before its unresolved `DBPrintf` service. The original guest cache and memory ordering instructions were AOT translated with zero interpreter fallback.

## Guest cache runtime adaptation and limitations

`apply_cache_events_v43.py` patches NWiiRecomp's CPUContext and PowerPC C++ emitter to retain **guest cache-operation observability**, rather than silently discarding these opcodes. The runtime now records the first 32 aligned `dcbf` and `icbi` addresses and maintains their total counts, last touched line, `sync` and `isync` counts. The emitted C++ also uses host sequentially consistent memory fences to preserve ordering on tested paths. PPC RA=0 semantics are respected for cache effective addresses.

**This is not an accurate model of Wii D-cache dirty/valid state, hardware write-back, exception-visible cache effects, or instruction-cache invalidation of statically recompiled host code.** The current AOT dispatcher has no retranslation/invalidation mechanism. Pending runtime work includes suitable memory-coherence behavior and handling self-modifying guest code. Other unsupported PowerPC cache instructions remain visibly unimplemented. This is a trace-and-ordering baseline, not a full cache service.

The patch is idempotent and rejects unknown/ambiguous or **partially patched** source states before any write. An independent original-free negative suite verifies atomic source editing behavior.

## Verification

Using the pinned owner-original Wii DOL SHA-256 `16a09adcf1987c1f3617d10f3a1cb830f32886afb583f9f8f88e0963ae5fe1f4` and the owner's original NWiiRecomp archive:

| Check | Result |
| --- | ---: |
| Native guest semantic assertions, six `OSInit` variants plus earlier direct helper tests | **2,913 / 2,913** |
| Original DOL instruction mutations, SHA, helper-call graph, data oracle, section bounds and overwrite safety checks | **364 / 364** |
| Original-free V43 runtime/emitter patch guards | **14 / 14** |
| V30 HID0/HID4/FPSCR guards (fresh source) | **14 / 14** |
| V29 performance-SPR patch guards (fresh source) | **13 / 13** |
| Optimized GCC C++20 native execution | Pass |
| ASan/UBSan native execution | Pass |
| Fresh, unmodified NWiiRecomp checkout reproduction | Pass |
| Analyzed native function entries including four prior synthetic analyzer guards | **34** |
| PowerPC interpreter fallback in tested paths | **0** |

The native assertions verify the exact original handler bytes, guest-memory canaries, source preservation, 32-byte aligned cache operation sequence, loop counts, full native helper dispatch and earlier system-time/interrupt/arena/IPC/exception setup effects. The private fixture uses a separate owner-derived DOL data section as an oracle for the handler source because the synthetic analyzer guard at the original text PC is non-executable.

Reproduce with an isolated NWiiRecomp source tree and your own unmodified game DOL:

```bash
bash run_osinit_cache_v43.sh /private/NWiiRecomp-master /private/NfsMWRelease.dol.bin
V43_SANITIZE=1 bash run_osinit_cache_v43.sh /private/NWiiRecomp-master /private/NfsMWRelease.dol.bin
```

The runner applies original-free V15, V26, V29, V30 and V43 emitter/runtime adaptations to an isolated local checkout; all generated original-game C++ and owner-private DOL slices are created in a temporary directory and deleted on exit.

## Distribution and next work

Eight new original-free V43 sources are distributed and committed: `apply_cache_events_v43.py`, `make_osinit_cache_v43.py`, `generate_osinit_cache_v43.cpp`, `test_osinit_cache_v43.cpp`, `test_osinit_guards_v43.py`, `test_cache_patch_guards_v43.py`, `run_osinit_cache_v43.sh`, and this README. The source-only archive includes the previous 52-file V42 dependencies. It contains **no proprietary original Wii executable, game assets, original PPC function bodies, private slices, or generated game-derived C++**.

Priorities: verify continuation into the next exception vector and later `__OSInitSystemCall`; extend the runtime toward genuine cache and exception semantics; restore continuous original `__start` execution after V26's `0x805206B4` test boundary and publish the five missing original-free V26 harness sources. **Original game `main` (`0x802D3F40`), first native frame, frontend and gameplay have not yet been reached.** Keep PR #36 a draft.
