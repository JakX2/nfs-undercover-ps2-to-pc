# V53: Original Wii interrupt disable and mask arithmetic execute in integrated native OSInit

**Milestone:** original Undercover Wii PowerPC instructions executed through NWiiRecomp-generated C++20, with a bounded test-only stop. **Not** hardware-accurate interrupt delivery, complete `OSInit`, a continuous `__start` run, or native game boot.

## Original code advanced

Starting directly at authentic `OSInit` (`0x80520670`), V53 continues V52's exception-vector, system-call, alarm, module and interrupt-table/MMIO integration. The original `__OSInterruptInit` now runs through its authentic `bl __RAS_OSDisableInterrupts_begin` at `0x80526674` and further original mask setup instructions through `0x80526694`. Only the prior synthetic `sc; blr` stop at `0x80526674` and synthetic padding in the owner-private DOL are replaced. A new, explicitly test-only `sc; blr` stop is at **`0x80526698`**, *before* the original branch into the mask setup loop at that location. The original `SetInterruptMask` at `0x805266E0` is **not executed** by V53.

The genuine `__RAS_OSDisableInterrupts_begin` function at `0x805265AC` uses original `mfmsr`, PowerPC rotate/mask, `mtmsr` and `blr`, preserving non-EE guest MSR bits and returning the prior EE state in `r3`. That authentic helper was already present in the inherited private original-code section; V53 connects the original interrupt-initializer call to it. The initializer saves that result in `r29`, combines the two freshly zeroed low-memory mask words, stores `0xFFFFFFF0` at `0x800000C4` and leaves `0x800000C8` zero. It computes `r3 = 0xFFFFFFF0` at the new stop; no hardware MMIO read or mask-configuration side effect beyond V52's two validated original write callbacks is invented.

Six direct additional tests call the complete original interrupt-disable helper with MSR inputs `0`, `0x8000`, `0x2000`, `0xA000`, `0x12345678` and `0xFFFFFFFF`; they check the returned previous-state bit, new MSR with EE cleared, preserved neighboring GPRs, LR/stack and direct native call counts. All prior integrated exception vectors, cache traces, alarm registration, syscall copy, module clearing, low-memory and MMIO oracle assertions remain enabled.

## Verification recorded in this session

- **17,671/17,671 native assertions**, including six direct interrupt-disable helper calls and the prior six `OSInit` configurations, **zero PowerPC interpreter fallback** on tested paths.
- **356/356 mutation / owner SHA / DOL geometry / output overwrite guards**, covering every original instruction through the new stop.
- **16/16 V44 cache trace source-patch checks**. From a freshly extracted unmodified upstream NWiiRecomp ZIP, additional prerequisite checks pass: **13/13 V29**, **14/14 V30**, **14/14 V43**, **16/16 V44**.
- Finalized runner passes **optimized**, **ASan/UBSan**, and **fresh upstream optimized** reproductions.
- NWiiRecomp analyzes **48 bounded guest entries**, which include conservative/synthetic test roots; these are *not* 48 additional game functions.
- SHA-256-pinned user-owned original Wii DOL: `16a09adcf1987c1f3617d10f3a1cb830f32886afb583f9f8f88e0963ae5fe1f4`.

Run from the V53 source-only archive, with a separate NWiiRecomp checkout because patch scripts alter checkout sources:

```sh
bash run_osinit_irq_disable_v53.sh /private/NWiiRecomp-master /private/NfsMWRelease.dol.bin
V53_SANITIZE=1 bash run_osinit_irq_disable_v53.sh /private/NWiiRecomp-master /private/NfsMWRelease.dol.bin
```

The private owner DOL is extracted, translated and tested only in a temporary folder removed by the runner. Do not commit original DOL/ELF assets, extracted PowerPC bodies, guest section bytes or game-derived generated C++.

## Remaining work

1. Execute the original `__OSInterruptInit` loop at `0x80526698` through original `SetInterruptMask` (`0x805266E0`) with carefully verified and fail-closed 16/32-bit MMIO semantics. Hardware interrupt-controller and IOS behavior remain unimplemented.
2. Finish original `OSRestoreInterrupts` / interrupt-handler installation and return to the remaining original `OSInit` calls.
3. Connect the later directly-entered `OSInit` execution to original continuous `__start`. That chain still stops at V26 `0x805206B4`; five V26 harness files remain unpublished in PR #36.
4. Reach the original game `main`, real first frame, frontend and gameplay. These milestones have **not** been achieved.

Keep PR #36 a draft, preserve Carbon adaptation work, and publish **only original-free test infrastructure**.
