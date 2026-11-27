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
