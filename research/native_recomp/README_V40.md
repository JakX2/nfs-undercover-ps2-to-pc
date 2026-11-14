# V40: Original Wii exception-mark helper executes through native NWiiRecomp

**Status: bounded original-game native execution, not complete exception vector initialization or a bootable PC game.**

From an owner-private SHA-pinned Undercover Wii DOL, this milestone extends the original `OSInit` -> `OSExceptionInit` native dispatcher beyond V39's `0x80520CA8` stop and executes the authentic 24-byte **`__DBIsExceptionMarked` at `0x804E50A0`**. The PowerPC body performs the original `r13`-relative debug-info pointer read, left shift of a mark bit by exception index, mask load and bitwise `and` before returning.

Two original exception-control-flow cases are exercised:

- An absent or sub-2 boot-info record takes the original branch at `0x80520CB0` / `0x80520CBC`, writes the original exception template word, calls `__DBIsExceptionMarked` at **`0x80520CF0`**, and stops at synthetic terminal syscall **`0x80520CF4`**.
- A qualifying boot-info record calls that same genuine helper at **`0x80520CC4`** and stops at synthetic terminal syscall **`0x80520CC8`**, before its unimplemented debug print / vector-copy branch. Legacy fallback records also exercise this route.

The original early debug branch at `0x80520C44` is still a separate fail-closed synthetic stop. **Neither of the new stops is in the original executable.** No original vector-copy, cache-synchronization or exception-handler installation is claimed. Further original exception setup, OS/IOS work and native game startup remain necessary.

## Source-backed implementation

The V40 private slice builder extracts the original helper, with exact original address/instruction bytes, and appends it as the seventh DOL executable section. The previous V39 seven-section test image had no spare text section. V40 therefore merges the existing neighboring original OSInit and exec-params sections into one contiguous guest-address span, filling the inter-section gap with **synthetic PPC NOPs for the test image only**. No original game function is relocated or modified except at the documented synthetic guard locations.

The original SHA-256 validation is inherited from the V39/V38/V28 builder chain: `16a09adcf1987c1f3617d10f3a1cb830f32886afb583f9f8f88e0963ae5fe1f4`. The analyzer/emitter guard checks the new original exception-branch spans and the complete helper with source-derived fingerprints, in addition to the earlier call-graph, memory and hardware checks. The four V39 synthetic analyzer-root guards are retained and **are not additional game functions**.

The debug-structure pointer and mark masks in these tests are independently authored guest-memory fixtures, not claims about a real Wii IOS/debug environment. The original PowerPC helper is additionally called directly with exception indices `0`, `1`, `7`, `31`, `32`, `63` and zero, all-ones and sparse mark masks. This checks bit-mask and shift edge behavior, operand preservation, native dispatch and guest ABI.

## Verification

| Check | Result |
| --- | ---: |
| Original-native assertions, six `OSInit` scenarios plus independent direct calls | **977/977** |
| Corrupt original/private images, source opcode mutations, bounds, SHA, output-safety checks | **281/281** |
| Existing V30 source-patch guards | **14/14** |
| Fresh upstream V29 source-patch guards | **13/13** |
| GCC C++20 optimized runner | **Passed** |
| ASan/UBSan native runner | **Passed** |
| Fresh unmodified NWiiRecomp checkout | **Passed** |
| NWiiRecomp analyzed entries / guest interpreter fallbacks | **32 / 0** |

The 32 entries include 28 authentic guest function roots and **four never-executed synthetic analyzer guards**. Test-only syscall stops are separate safety boundaries and are not authentic original service implementations.

## Reproduce privately

The complete source-only package contains the previous V15/V26/V29/V30 and V39 prerequisites along with six new V40 Python, C++, shell and documentation files. Provide an isolated local NWiiRecomp checkout, GCC C++20, Python 3 and your private Wii DOL:

```bash
bash run_osinit_dbmark_v40.sh /private/NWiiRecomp-master /private/NfsMWRelease.dol.bin
V40_SANITIZE=1 bash run_osinit_dbmark_v40.sh /private/NWiiRecomp-master /private/NfsMWRelease.dol.bin
```

The script creates a temporary private sliced Wii DOL and private generated C++, deletes them on exit, and fails closed on unknown upstream, changed guest instructions or output overwrite. Never commit or redistribute those original-derived binaries, original assets or generated game-derived C++.

## Remaining dependencies

The genuine exception-vector installation loop, original `DBPrintf`, cache flush and invalidate operations, and original `__OSInitSystemCall` are not yet executed. The latest full original `__start` chain is still V26 through `0x805206B4`. The V27–V40 direct-entry `OSInit` work needs to be linked into that continuous startup. Five original-free V26 harness files are still absent from PR #36, and the draft branch alone cannot fully reproduce V26. The actual game `main` at `0x802D3F40`, the first native game frame, frontend and gameplay are **not reached**.
