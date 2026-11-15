# V41: Original Wii exception-template clearing loop runs through native NWiiRecomp

**Status: owner-original bounded execution, not complete exception-handler initialization or a bootable Windows game.**

The private SHA-256-pinned Wii DOL (`16a09adcf1987c1f3617d10f3a1cb830f32886afb583f9f8f88e0963ae5fe1f4`) now drives NWiiRecomp-generated native C++ through additional genuine `OSExceptionInit` PowerPC code after the previously verified `__DBIsExceptionMarked` calls.

## Source-grounded V41 extension

- Restores the original exception-mark comparisons and branches at `0x80520CC8` / `0x80520CF4`, previously overwritten by V40's test stops.
- With exception index zero **unmarked**, follows the original `0x80520D20` through `0x80520D7C` template-clearing instructions. The native loop uses PowerPC `mtctr`, `bdnz` and `stw`, writing **one guest 32-bit `0x60000000` instruction** into the independently seeded template buffer at `0x80520F18`. Tests assert exact 4-byte changes, both neighboring canaries and exhausted guest CTR.
- With exception index zero **marked**, rejects the original `DBPrintf` call through an **explicit synthetic syscall at `0x80520CDC`**, before any unimplemented debug service can return. A separately entered original `OSExceptionInit` scenario exercises the second marking call and stops at the other real debug callsite, `0x80520D08`.
- The unmarked path stops at **`0x80520D80`**, *before* the original vector target computation, `memcpy` to low-memory exception vectors, data-cache flush and instruction-cache invalidation. These operations are **not** claimed as executed. Earlier `0x80520C44` debug and other test-only service stops remain fail-closed.
- Uses the original `OSInit` entry `0x80520670`, not the continuous original executable `__start`. The latest fully integrated `__start` fixture remains V26 through `0x805206B4`. Four of the 32 analyzer entries are synthetic protection roots, not original-game functions.

The owner-private builder copies the newly executed PPC words from the original DOL into a synthetic test image; it does not redistribute those words. The native generator verifies a fixed hash of the original PPC exception continuation with only the documented test stops substituted, plus all V40 source checks. Output safety rejects changed bytes and unknown DOL geometry before writing generated C++. No original PowerPC function body or game-derived compiled C++ is published.

## Verified tests

| Test | Result |
| --- | ---: |
| Native guest semantic checks (six original `OSInit` paths, direct second debug path, original marker and prior services) | **994 / 994** |
| SHA-pinned malformed-image, instruction mutations, guest branch and output-safety checks | **318 / 318** |
| Existing V30 state/emitter patch checks | **14 / 14** |
| V29 prerequisite patch checks on fresh upstream | **13 / 13** |
| Optimized C++20 native runner | **Pass** |
| ASan/UBSan native runner | **Pass** |
| Fresh, unmodified NWiiRecomp archive | **Pass** |
| Original functions discovered including test-only analyzer guards | **32** |
| Interpreter fallback on tested paths | **0** |

Verified with the SHA-pinned owner Wii DOL and NWiiRecomp-master archive, using GCC C++20 and Python 3. The script deletes private sliced DOL and generated translated C++ on exit. Do not commit temporary outputs.

```bash
bash run_osinit_vectorclear_v41.sh /private/NWiiRecomp-master /private/NfsMWRelease.dol.bin
V41_SANITIZE=1 bash run_osinit_vectorclear_v41.sh /private/NWiiRecomp-master /private/NfsMWRelease.dol.bin
```

The complete source-only V41 ZIP includes previous required test and runtime patches plus the six new V41 files: `make_osinit_vectorclear_v41.py`, `generate_osinit_vectorclear_v41.cpp`, `test_osinit_vectorclear_v41.cpp`, `test_osinit_guards_v41.py`, `run_osinit_vectorclear_v41.sh`, and this README. No proprietary Wii game executable, assets, function body, generated original-game C++ or original-game test slice belongs in GitHub or the distributed ZIP.

## Next milestone

The next authentic function continuation is the vector-target address computation and original `memcpy`/cache-service sequence. It needs validated guest RAM and accurate cache semantics; do not bypass the missing operations with an unconditional success stub. Independently, the later direct-entry `OSInit` milestones still need to be integrated with the original `__start` dispatcher; five source-only V26 harness files remain unpublished, preventing full GitHub-only reproduction of that older milestone.

Original `main` at `0x802D3F40`, the first native frame, frontend, and playable gameplay remain unreached. PR #36 must remain **draft**.
