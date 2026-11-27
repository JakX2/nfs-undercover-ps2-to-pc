# Wii formatter: verified instruction 121, guarded instruction 122

Recorded: 2026-11-27 (UTC). This handoff describes a bounded original
Wii AOT native continuation, not a complete executable boot or frontend.

## Verified native frontier

- [Owner workflow 46012175547](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/46012175547) succeeded.
- Eight trials x 121 original instruction visits = **968 aggregate visits**.
- Its log reports immediate_verified for all eight trials, fallback=0,
  complete_image=0 and boot_verified=0.
- The previous 120-instruction path and all earlier guards remain
  mandatory predecessors.

## Instruction 122 provenance, not native execution

- The [read-only 122 audit](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/46013062762)
  passed. The original word is a non-record PPC extsb, with one proven
  constant register input, source/destination aliasing, and no CR/XER
  modification.
- The first private 122 fixture attempt failed because it incorrectly
  assumed this source register was the one written by instruction 121.
  The amended fixture replays original 118 byte load, 119 compare,
  120 stack copy, and 121 zero-input immediate symbolically, then
  selects the authentic 122 source by its own encoding. An unknown
  input is rejected; no original word or register value is printed.
- The private signext fixture and nested-fixture builder now support
  an opt-in 122 word and guarded original 123 successor. Scope and
  translated-code installation use a 28-byte callee extent in this
  mode, versus 24 bytes for instruction 121.
- The new source-only C++ FormatterSignextWitness verifies a decoded
  non-record extsb, authenticated input, a one-instruction native tick,
  unchanged other GPRs/CR/XER/GQR/PC-related state, and the next
  original word and synthetic guard. This witness cannot substitute
  or emulate original Wii code.

## New regression coverage

- test_formatter_report_signext_fixture.py: 256 byte outcomes,
  provenance from different earlier constants, alias restrictions,
  tampered predecessors, original-word match, and extent.
- test_formatter_report_signext_nested.py: guarded merge, sibling
  preservation, source independence, mode/scope/install wiring.
- test_formatter_report_signext.cpp: 1,280 positive combinations
  plus arm, observation, duplicate and cross-CPU negative tests.
  The 122 source-only workflow builds with address and undefined
  behavior sanitizers.
- The owner fixture is pinned to successful original 122 read-only
  audit and stages proprietary DOL/ELF only on the private runner.
  No original word, address, asset or translated game code is public.

## Remaining verification

1. Confirm the corrected original-122 owner fixture workflow passes.
2. Connect the 122 witness with the complete original-code native
   runner while preserving 120/121 modes and stopping before 123.
3. Validate exactly eight trials x 122 visits = 976, with negative
   regressions rejecting old 121 outputs and changed CPU snapshots.
4. Gate original 122 native execution on BOTH successful 121 native
   execution and successful corrected 122 owner fixture.
5. Native game boot, frontend and gameplay remain future milestones.

The existing hourly Undercover task continues; no duplicate is needed.
