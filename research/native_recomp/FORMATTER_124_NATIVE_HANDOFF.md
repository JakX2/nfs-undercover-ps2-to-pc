# Formatter instructions 123–125: native verification handoff

Updated 2026-11-27. Source-only documentation. No original-game bytes or
translated game code are stored here.

## Verified baseline

- Last **owner-original native** result independently confirmed: **122 original
  instruction visits per trial, 8 trials, 976 visits overall, 0 interpreter
  fallbacks** in the bounded formatter continuation lane.
- The owner-original **123-instruction** workflow
  [46020094169](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/46020094169)
  **failed** after translating the original code and completing the formatter
  continuation. Trial 0 emitted `V1256_OPEN_FAILURE kind=witness ... stage=8
  reason=0 line=0`, without a nested-refusal marker or 984-visit total.
  **Stage 8 is not a reliable failing-location identifier:** the shared
  `last_stage` field may be inherited from an earlier witness. A later source
  change logs `V1256_WITNESS_SOURCE source_line=...` for generic witness throws,
  without logging guest addresses or original values. This requires a new
  private owner run. **Do not advance the verified native frontier above 122.**
- The **124th original word** was authenticated as non-record,
  zero-base PowerPC `addi` with one volatile GPR destination. The private
  source-only fixture passed in
  [46021379576](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/46021379576).
- The **125th original word** was authenticated and classified in the private
  **read-only** provenance audit
  [46022052003](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/46022052003)
  as another zero-base `addi`, no condition-register/XER side effects.
  **125 has not been executed.**

## What the 124 implementation now does

The opt-in `--formatter-nested-caller-report-third-immediate` lane extends
the 123 fixture by one original word and a separate test-only stop guard.
`prepare_formatter_nested_fixture.py` maintains the predecessor contracts
for 118–123, installs the authenticated 124 word, updates private native
analyzer scope to 36 bytes, and refuses overlapping roots and altered guards.

The independent `FormatterThirdImmediateWitness` validates the original
word, PPC zero-base semantics, destination register, all live GPRs, CR/XER,
FPSCR-adjacent GQR state, guest MSR/LR/CTR/SRR0/SRR1, instruction count,
and guard bytes. The harness arms it at authenticated stage 41, **allows the
AOT-generated instruction to execute**, and validates the transition at
stage 42/43 before stopping ahead of 125. The witness does not interpret or
execute the original instruction itself.

The parent nested-frame lease, the report-byte observer, and the
immediate-compare observer now recognize an optional seventh successor. The
older 120–123 modes remain separate and must still refuse malformed
predecessor/guard sequences.

The opt-in `FORMATTER_CALLER_REPORT_THIRD_IMMEDIATE` log verifier requires
**8 × 124 = 992** exact total visits, 8 trial markers, 8 successful 124
observations, no interpreter fallback, and no claimed boot. A 976- or
984-visit log cannot satisfy the 124 validator.

## Source-only tests, not original execution

- [124 integrated native source gate, 46023569789](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/46023569789):
  success. Includes strict runner syntax, 124 fixture/nesting/wiring,
  121–123 regressions, and optimized plus ASan/UBSan C++ byte/compare
  guard witnesses. Each C++ mode passed 20 seventh-successor guard cases.
- [124 exact log contract, 46022650458](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/46022650458):
  success. Includes altered-visit, altered-marker, older-mode, and fallback
  refusal tests.
- [124 isolated native observer, 46021801340](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/46021801340):
  success in optimized and sanitized builds; **327,680 synthetic outcomes**,
  **29 arm** and **24 observation** negative mutations.

Source-only synthetic execution demonstrates invariants but cannot be
substituted for owner-original code execution.

## Private owner gate

`.github/workflows/wii-formatter-caller-report-third-immediate-native-owner.yml`
has a narrow push trigger, an original-free regression job and a distinct
read-only prerequisite job. The latter requires **both** pinned,
successful upstream owner jobs:

1. Original 123 native continuation: run `46020094169`, commit
   `0b036a779d9bfd0913642c3a1926ef2bd34f3a1d`,
   job `owner-second-immediate`.
2. Original 124 private fixture: run `46021379576`, commit
   `4292e39f7084d845f92272c7cd9707ce991a7ff3`,
   job `owner-provenance`.

Until both jobs have passed, the private 124 execution job **skips** rather
than attempting unverified code. The owner stage additionally repeats its
pin checks before accessing the SHA-verified private DOL/ELF and executing
the NWiiRecomp-generated native code. Files and generated translated code
are removed with an unconditional cleanup step.

If 123 fails or times out, fix and reverify 123 first, then update the exact
pinned requirement for a new successful 123 run before authorizing 124.
Do not lower the guard, reinterpret fixture success as original execution,
or publish original DOL/ELF instructions in GitHub.

## Current owner execution blocker

The failed original 123 run is a **hard stop** for the gated 124 original-code
execution. The 124 owner workflow requires that exact successful 123 owner job
and currently skips execution. Do not edit the prerequisite to accept a failed
job, remove the condition, or claim 124 original execution from source tests.

The inherited source-only 120/121/122 assertions also needed to recognize the
optional 124 nested guard. Their amendments preserve the original modes and
are verified by the relevant original-free regressions, not by guessing a
new original checkpoint. The 123 execution diagnostic patch was committed
after the failed run; its source-line result has not yet been observed
on original game code.

The separate instruction-125 private read-only audit already succeeded,
and the instruction-125 zero-input fixture is independently gated by it.
125 source-only preparation does not unblock native 123 or 124.

**Unchanged larger limit:** no continuous game `__start` to `main`, native
frontend, rendered first frame, or playable game is claimed by this bounded
formatter lane. Keep pull request #36 draft.

## Predecessor guard repair (2026-11-27)

The subsequent 123 owner attempt [46025030157](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/46025030157) failed with the same generic witness marker. Two independent issues were identified by source inspection:

1. The native runner suppressed the new source-line marker and nested refusal stages above 35. Commit `7839814` preserves only the fixed, redacted diagnostic shapes through stage 43, separates the 123 observer and parent-lease failure sites, and tests the actual grep filter.
2. The independent 122 sign-extension witness still required a fixed syscall guard at its second successor. The 123 and 124 fixtures intentionally replace that slot with an authenticated word. The 123 immediate witness had the analogous problem in the 124 lane. Commit `b696b97` binds explicit optional successor words at arm time, verifies the moved guard at arm and observation, and refuses gaps, mutated words, or return aliases. Legacy short modes keep their fixed guard.

The 123 isolated witness tests [46058494734](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/46058494734) and the inherited 124 source integration [46058494576](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/46058494576) passed. The new synthetic three-lane successor-chain regression exercises the 122, 123 and 124 layouts using shared CPU state and independently mutates each remaining word and terminal/return guard before and after each witness. Its results are source-only.

The repaired original 123 owner attempt is [46058494707](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/46058494707). It was pending when this update was authored. The original 124 owner pins remain unchanged until a successful original 123 execution is verified. **The execution frontier remains 122.** No original bytes are included in these changes.

## Instruction-125 observer preparation (source-only)

The authenticated read-only 125 provenance remains
[46024552413](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/46024552413).
A separate independently authored `FormatterFourthImmediateWitness` now
models the **observation contract** for a future 125 AOT step, not execution
of original code. It enforces PPC zero-base `addi` semantics; a single
volatile-GPR write; unchanged CR, XER, GQR, LR, CTR, MSR and SRR registers;
an exact instruction-count delta; and both immutable guest guard slots.

- [125 independent source-only witness 46059195465](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/46059195465):
  optimized and ASan/UBSan builds passed, covering **327,680 synthetic
  results**, **29 arm** and **24 observation** refusal mutations.
- [124 predecessor witness 46059344119](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/46059344119)
  and [125 paired successor witness 46059344178](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/46059344178)
  passed. The 124 witness preserves its existing short-mode guard, while an
  optional explicitly supplied authenticated lookahead relocates the terminal
  guard for a possible 125 test. The additional paired test manually applies
  synthetic GPR changes and mutates predecessor words, successor words, the
  terminal guard and return guard at arm and observation boundaries.

The 125 observer is **not wired to the private native harness**. It is not
proof that 125, 124 or 123 original instructions execute. The earlier
verified original 122-instruction frontier must advance through distinct
owner-original CI gates before any 125 execution claim. Neither original
instruction bytes nor generated game translation code appear in these files.


## Instruction 125 source-only handoff (2026-11-27)

Instruction 125 is **provenance-authenticated but not natively executed**.
The separate private 125 fixture only verifies the original word and its
successor. The native execution frontier remains **122 instructions per trial
(976 visits)** until a successful original-owner 123 run is confirmed.

Source-only development added:

- `FormatterFourthImmediateWitness` observes an authenticated zero-base PPC
  `addi` with an exact one-instruction register/state delta. The standalone
  optimized and sanitized 125 witness passed in
  [46059195465](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/46059195465).
- The earlier 122 sign-extension witness accepts one more *explicit,
  authenticated* lookahead word, moves its test-only guard by exactly four
  bytes and rejects successor gaps, mutated words and in-block return aliases.
  The four-stage 122–125 synthetic chain covers **100 negative mutations**
  across all predecessor observation boundaries. Its initial optimized and
  sanitized regression passed in
  [46059526289](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/46059526289).
- The optional `--caller-report-fourth-immediate` fixture mode is now
  connected to private image construction, a 40-byte analyzer scope,
  translated-code installation checks and sibling-root preservation. This is
  source-only preparation. No runner mode, owner-original execution gate or
  125 execution claim follows from it.
- `validate_formatter_nested_log.py` now supports a distinct future
  `--caller-report-fourth-immediate` contract requiring exactly
  **8 × 125 = 1,000** visits, eight successful fourth-immediate trial markers,
  zero interpreter fallback, and no known native refusal. Synthetic contract
  tests do not substitute for actual owner-original logs.

The first combined nested source gate
[46059738963](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/46059738963)
found an inherited 124 test which assumed the old maximum extent was 36
bytes. That test was updated to check its own optional 124 branch underneath
the new 40-byte mode. A subsequent combined regression run must complete
before the entire 125 nested/log integration can be called verified.

**Execution order remains mandatory:** diagnose and pass original 123
execution (984 visits), then authorize and pass original 124 (992 visits)
using freshly pinned successful prerequisites, then and only then author and
enable a gated original 125 native execution attempt. Keep PR #36 draft.

## Verified original instruction 123 (2026-11-27)

**Owner-original native execution is now confirmed for instruction 123.**
[Workflow 46061883183](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/46061883183)
completed successfully at `fc4abad8332c81218abee036b2e797595f155fb0`.
The private `owner-second-immediate` job authenticated the earlier original
122 run and the private original 123 fixture, then emitted eight genuine
`FORMATTER_CALLER_REPORT_SECOND_IMMEDIATE` trials and its aggregate marker:

- `owner=1 trials=8`; `second_immediates_verified=8`.
- `total_visits=984` (eight trials of 123 original AOT instructions);
  `fallback=0 complete_image=0 boot_verified=0`.
- No `V1256_WITNESS_SOURCE`, `V1256_OPEN_FAILURE` or nested refusal was
  present in the successful owner log.

This proof supersedes the older *pending/failed 123* remarks elsewhere in
this chronological handoff. The prior 122-instruction verification remains
a historical predecessor, **not** the current execution frontier.

The 124 owner workflow now pins that exact successful 123 run and SHA at
both the eligibility stage and the private owner gate. Its source-only job
and eligibility check passed in
[workflow 46063770019](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/46063770019);
the 124 owner-original step still requires a successful native run and
`total_visits=992` before the frontier advances again.

The newly prepared `wii-formatter-caller-report-fourth-immediate-native-owner.yml`
has a separate original-free 125 source gate, reuses the authenticated
private 125 fixture
[46024552413](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/46024552413),
and intentionally pins a **failed** historical original-124 run as the
native prerequisite. Both gate checks must be updated to one *actually
successful* 124 owner run before original 125 can execute. A source-only
125 success is never proof of 125 execution. Proprietary bytes and
game-derived generated C++ remain private.

Do not claim complete boot, frontend execution or gameplay from these
isolated native startup checkpoints. Keep PR #36 draft.
