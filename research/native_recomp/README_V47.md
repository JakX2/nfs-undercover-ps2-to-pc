# V47: Original Wii `__OSInitAlarm` and shutdown registration execute natively

**Scope:** a **direct-entry, owner-original Wii PowerPC execution test**, not an end-to-end original `OSInit` or `__start` run and not a native Windows game boot. The full 88-byte original `__OSInitAlarm` at `0x805210CC` executes through NWiiRecomp's non-split generated native C++ dispatcher. Its three original dependencies execute natively as well:

| Wii entry | Length | Behavior exercised |
| --- | ---: | --- |
| `__OSInitAlarm` `0x805210CC` | 88 bytes | Compare current exception 8 handler; initialize alarm list and register shutdown callback if needed |
| `__OSGetExceptionHandler` `0x80520EB0` | 16 bytes | Read the actual guest exception handler table |
| `__OSSetExceptionHandler` `0x80520E9C` | 20 bytes | Replace exception handler 8 and return its previous value |
| `OSRegisterShutdownFunction` `0x80527B4C` | 136 bytes | Insert the original alarm shutdown node in priority order, maintaining head/tail and previous/next links |

The original alarm handler address `0x805217BC` is **stored**, not called or translated in this fixture. The original alarm shutdown node lives at `0x8060BCB8`. The initial implementation of the V47 test accidentally seeded a different node address; the corrected test now checks all four pointer links explicitly for empty-list insertion, head insertion, tail insertion and equal-priority append. Already-installed paths must neither reset alarm state nor register the shutdown node.

The function returns through the original PPC `blr` into one **synthetic terminal `sc; blr`** placed at `0x80004900` in the private test image. No OS service callbacks or HLE behavior are used in this native path. The address-local original guest code is copied only from the SHA-pinned owner Wii DOL, while the fixture's exception table and shutdown-list memory are independently authored synthetic data.

## Reproduction

Requirements: isolated unmodified or previously safely patched NWiiRecomp source checkout, Python 3, C++20 GCC, and an owner-provided Wii DOL with SHA-256:

`16a09adcf1987c1f3617d10f3a1cb830f32886afb583f9f8f88e0963ae5fe1f4`

Run from this source package directory:

```bash
bash run_alarm_v47.sh /private/NWiiRecomp-master /private/NfsMWRelease.dol.bin
V47_SANITIZE=1 bash run_alarm_v47.sh /private/NWiiRecomp-master /private/NfsMWRelease.dol.bin
```

The test runner verifies the owner DOL digest **before modifying** the isolated NWiiRecomp checkout, then applies existing fail-closed V15 non-split dispatch and V26 guest syscall-PC fixes. Original PPC snippets and all generated game-derived C++ are created under a `mktemp` directory and deleted on exit. Do not run source patchers on an unrelated checkout.

## Verified results, 2026-11-15

- **338/338 native semantic assertions** across six alarm startup cases and four additional direct getter/setter pairs. Original entry, helper call counts, return PC, saved LR, nonvolatile register and stack behavior verified.
- **87/87 mutation/negative/output-safety checks:** every original PPC word in the three private sections is modified in turn and rejected by the generator, along with section metadata errors, truncated or appended DOL bytes, synthetic terminal mutations, wrong owner SHA, nonempty output and missing output directory.
- Full optimized C++20 and **ASan/UBSan** native builds passed. A freshly extracted **unmodified upstream NWiiRecomp ZIP** passed the optimized native and safety tests with the required V15/V26 patches applied.
- Native analyzer found **five** entries including the explicit synthetic stop. No interpreter fallback occurred on the tested paths.

Only independently authored Python/C++/shell source, this README and existing source-only prerequisite patches are distributed. Do not publish the original DOL, ELF, extracted function bytes, private test slice or generated original-game C++.

## Next work

Integrate these genuine original alarm functions into the verified V46 `OSInit` chain, after the original `__OSInitSystemCall` returns to call `__OSInitAlarm` at `0x805208B0`. Then expand the later original OS/IOS service dependencies. **The continuous original `__start` path remains separately bounded at V26's `0x805206B4`**; its five unpublished harness files are still a reproducibility gap. The game's original `main`, native first frame and playable PC port have not been reached. Keep PR #36 draft and preserve existing Carbon adaptation work.
