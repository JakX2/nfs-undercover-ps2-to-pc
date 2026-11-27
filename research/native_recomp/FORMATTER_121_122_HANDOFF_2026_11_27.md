# Wii formatter: original 122 native verified, original 123 guarded

Recorded 2026-11-27 UTC. This is a bounded original Wii PowerPC AOT
continuation, **not** complete original game startup, frontend, or gameplay.

## Verified native execution (owner original code)

- Original instruction 121, zero-input `addi`:
  [owner run 46012175547](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/46012175547)
  **passed** with 8 x 121 = **968 original visits**, zero interpreter
  fallbacks. The previous 120-instruction path and guard chain passed.
- Original instruction 122, non-record `extsb`:
  [owner run 46016564555](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/46016564555)
  **passed** with 8 x 122 = **976 original visits**, zero interpreter
  fallbacks. Its exact final marker is
  `FORMATTER_CALLER_REPORT_SIGNEXT_NATIVE` with
  `signexts_verified=8`, `immediates_verified=8`,
  `total_visits=976`, `fallback=0`, `complete_image=0`,
  `boot_verified=0`. The original next label remains protected.
- The highest **verified original native frontier is 122 instructions
  per trial**. Do not equate aggregate visits with 976 consecutive
  instructions, or claim a full boot.

## Instruction 123: separate original provenance and fixture

- [Read-only owner audit 46017050592](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/46017050592)
  **passed**: original 123 is another zero-base `addi`, reads zero
  registers, writes one register, has zero CR/carry/XER/overflow effects,
  and has a fully modeled immediate result. This is **classification**,
  not execution.
- [Private owner fixture 46017777084](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/46017777084)
  **passed**. Marker
  `FORMATTER_123_IMMEDIATE_FIXTURE verified=1 previous_122_fixture=1
  instruction_123=add_immediate zero_input=1 volatile_destination=1
  next_guard=1 original_execution=0`.
- The nested builder's opt-in `--caller-report-second-immediate`
  mode carries the authenticated 123 word and guarded original 124
  successor through private image, translation hooks and analyzer
  scope. The callee fixture extent advances from the 122 mode's 28
  bytes to **32 bytes** with the test guard.
- A separate source-only C++ `FormatterSecondImmediateWitness`
  observes the translated 123 zero-input addi. It is not a guest
  instruction interpreter. Its full-range synthetic tests are
  **prerequisites**, not an original 123 native proof.
- An exact **8 x 123 = 984** native result is the next execution target.
  It requires a separate complete owner execution, all eight genuine
  immediate operations, preserved CPU/ancestor state and zero fallback.
  Do not advance the verified frontier to 123 on fixture or synthetic
  results alone.

## Guards, privacy and regressions

- The original 122 private fixture initially refused an incorrect
  assumption that the `extsb` input register was written by 121.
  The accepted implementation replays original 118 byte load,
  119 compare, 120 stack copy and 121 immediate to authenticate the
  actual original 122 source, without exposing operand data.
- Regession tests keep the older 120 and 121 guarded-word chains intact
  while allowing opt-in nested successors. The older 120 test's
  obsolete 121-only regex was independently repaired to include the
  nested 122 and 123 conditions. Never drop the base 120 check.
- Keep proprietary DOL/ELF, original instruction words, private
  register values, game assets and translated game C++ on private
  owner runners. The public repository only contains independent
  tooling, tests, and fixed-class result summaries.
- Continue original Wii native startup/runtime work and verify each
  discrete milestone. Complete executable linking, real main,
  first frame, frontend and gameplay remain **unverified**.

The existing hourly Undercover task is already active. Do not create
a duplicate scheduled task.
