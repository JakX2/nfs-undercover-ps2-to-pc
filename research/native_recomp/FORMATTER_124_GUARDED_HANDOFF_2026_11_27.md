# Original Wii formatter 124: authenticated guarded handoff

Recorded 2026-11-27 UTC. This is a bounded NWiiRecomp AOT startup
continuation, **not** a complete game boot, first frame or gameplay.

## Verified earlier native frontier

- Original 121 native owner [run 46012175547](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/46012175547): 8 x 121 = 968 visits, zero interpreter fallbacks.
- Original 122 native owner [run 46016564555](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/46016564555): 8 x 122 = 976 visits, zero interpreter fallbacks.
- **Verified native frontier at this handoff: 122 instructions per trial.** The 976 counter is an aggregate of eight discrete trials.

## Read-only 124 instruction classification and private fixture

- [Original 124 read-only audit 46020534517](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/46020534517) passed and reports `family=integer operation=add_immediate reads=0 writes=1 condition_write=0 carry_read=0 xer_write=0 overflow_enable=0 gpr_model=1 original_execution=0`.
- [Private owner 124 fixture 46021379576](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/46021379576) passed. Private result: `FORMATTER_124_IMMEDIATE_FIXTURE verified=1 previous_123_fixture=1 instruction_124=add_immediate zero_input=1 volatile_destination=1 next_guard=1 original_execution=0`.
- The first fixture run `46021347790` failed its owner gate due to a mistyped pinned SHA. The full audit commit SHA was corrected and the replacement completed successfully.
- Original-only authentication reproduces the 118–123 predecessor chain. It checks the original 124 word without publishing operands, addresses, register values, executable slices or translation. It preserves original 125 behind a synthetic stop.
- The new source-only fixture is `prepare_formatter_report_third_immediate_fixture.py`; regression tests are `test_formatter_report_third_immediate_fixture.py`. Only original `addi rD,r0,SIMM` for an allowed volatile GPR is admitted. Unknown source inputs, nonvolatile destinations, altered original predecessor, forged guards, bad extents and overlapped blocks fail closed.

## Independent instruction-124 native observer (not game-code execution)

- `wii_formatter_report_third_immediate.h` observes an eventual **original translated native 124 instruction**. It deliberately does not emulate or substitute PowerPC execution.
- It checks the exact original word, successor word, following stop guard, return guard, NWiiRecomp instruction-visit increment, independently authenticated result, all 32 GPRs, CR/XER, GQR, LR/CTR, MSR and exception state. It rejects duplicate or cross-CPU observations.
- [Source-only witness run 46021575838](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/46021575838) passed: 327,680 positive cases (5 destination registers x all 65,536 immediate values), 29 arming refusals, 24 observation refusals. `original_execution=0`.
- An additional optimized plus ASan/UBSan workflow is separately queued. Do not equate any source-only result with native owner proof.
- [Joined 121–124 symbolic-state workflow 46021609289](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/46021609289) passed, including distinctions between the first immediate destination and the 122 sign-extension source.

## Next verified execution gates

1. Obtain a successful **original instruction-123 native owner run** with eight trials, exactly 8 x 123 = 984 visits, zero interpreter fallback and preserved ancestor state. Its source-only checks and guarded fixture are not sufficient.
2. Integrate the authenticated 124 fixture and observer into the nested private native image, scheduler, formatter log validator and separate owner workflow only after the 123 run is proven.
3. Require an exact **8 x 124 = 992** visit result before advancing the verified native frontier beyond 123.
4. Only then classify instruction 125 through a separately gated, read-only audit and its own mutation tests.

Keep owner DOL/ELF, game-derived PPC words, private symbols, assets and generated translated game code off public GitHub. Keep PR #36 draft. No game `main`, frontend, first frame, or playable gameplay is verified.
