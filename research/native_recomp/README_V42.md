# V42: Original Wii exception-vector handler is copied natively

**Verified scope:** Bounded original Undercover Wii `OSInit` entry to original `OSExceptionInit` with authentic handler copy. This is **not** full exception-vector installation, correct cache coherency, continuous `__start`, or a bootable PC game.

## Native milestone

From the owner's original Wii DOL with pinned SHA-256 `16a09adcf1987c1f3617d10f3a1cb830f32886afb583f9f8f88e0963ae5fe1f4`, V42 restores **nine genuine PPC instructions** at `0x80520D80`–`0x80520DA0`, previously stopped in V41. The native C++ dispatcher performs vector address computation, invokes the **original `memcpy`** at `0x80004338`, and copies the **0x98-byte original exception handler template** into guest memory at `0x80000100` for exception index zero. V42 stops at **`0x80520DA4`**, replacing the original call to `DCFlushRangeNoSync` with an explicit terminal test syscall; data-cache flush, `sync`, `ICInvalidateRange`, and subsequent vector installation **have not executed**.

The owner-original handler-template bytes are extracted *privately* and stored in the private generated test DOL as a non-executable DOL data section at fixture-only MEM2 address `0x90050000`. The test seeds guest MMU memory from these bytes at their original text address `0x80520EC0`. This is necessary because V39's conservative analyzer safety guards overwrite otherwise unexecuted private text entries, and the prior native test did not load the entire original DOL into the MMU. These private bytes, the private test DOL, and generated game-derived C++ never enter the source ZIP or GitHub.

For the unmarked path, the original `OSExceptionInit` template-clear loop first overwrites one template instruction with `nop` and the original native `memcpy` then copies that resulting template. The test oracle takes these runtime changes and independently seeded adjacent-word canaries into account. For marked exceptions, the code stops at the existing synthetic debug-service boundary and does not perform a vector copy.

## Verification

- **2,844 / 2,844 native guest assertions**, six original `OSInit` configurations plus direct helpers; **32 analyzed function entries** including four pre-existing synthetic analyzer safety guards, with **zero PPC interpreter fallback** on the verified paths.
- **335 / 335** original-owner SHA, mutated PPC instruction, template-byte, section-geometry, output-safety and overwrite guards.
- Existing original-free patch checks: **14 / 14** V30, plus **13 / 13** V29 on a fresh upstream checkout.
- **Optimized GCC C++20**, **ASan/UBSan** native tests, and **fresh unmodified upstream NWiiRecomp ZIP** builds all passed against the SHA-pinned original owner DOL.
- The memory checks cover every one of the **152 output bytes**, every corresponding source byte, target canaries, source handler patching and the original vector offset table, in addition to the earlier startup state and dispatch counts.

Run from the source-only package with an isolated NWiiRecomp source checkout and an owner-provided original Wii DOL:

```bash
bash run_osinit_vectorcopy_v42.sh /private/NWiiRecomp-master /private/NfsMWRelease.dol.bin
V42_SANITIZE=1 bash run_osinit_vectorcopy_v42.sh /private/NWiiRecomp-master /private/NfsMWRelease.dol.bin
```

The runner creates the private DOL and original-game translation in a temporary directory and deletes these outputs on exit. The six V42 additions are `make_osinit_vectorcopy_v42.py`, `generate_osinit_vectorcopy_v42.cpp`, `test_osinit_vectorcopy_v42.cpp`, `test_osinit_guards_v42.py`, `run_osinit_vectorcopy_v42.sh`, and `README_V42.md`; the complete source-only archive also contains all V41 prerequisite sources.

## Remaining work

1. Implement/verify original `DCFlushRangeNoSync` at `0x80522320`, the subsequent `sync` and `ICInvalidateRange` at `0x80522378`, with correct guest-visible ordering, followed by additional exception vectors. Do not silently treat cache operations as implemented.
2. Integrate the now-verified directly entered `OSInit` path into continuous original `__start` execution; the last verified end-to-end startup fixture is V26 through `0x805206B4`, and five source-only V26 harness files are still missing from the PR.
3. Continue through `__OSInitSystemCall`, Wii OS/IOS dependencies, original game `main` (`0x802D3F40`), the first frame, frontend and ultimately gameplay.

All original DOL/ELF binaries, assets, owner-private generated image and translated game source remain private. PR #36 stays draft until native boot and reproduction requirements are met.
