# NFS Undercover PS2/Wii physics → Carbon PC

Research-only branch for native Carbon PC handling experiments. This work is **not a full physics port**, and this directory is independent of the scenery/map-conversion project.

## Verified milestones

- **Phase 24:** 32-bit opt-in observer ran in the user's Carbon PC test installation and captured tire-force inputs. Does not change handling.
- **Phases 27b–28:** read-only coefficient probe collected 227 successful memory snapshots for an **upgraded Koenigsegg CCX**; two coefficient values were observed (about 1.06 and 1.10). These are *Carbon* measurements, not stock Undercover parameters.
- **Phase 29:** decoded three pointer-linked numeric arrays (18 float entries) from each of the Undercover PS2 and Wii CCX tire records. Four of 18 values differ between these builds; exact semantic field names are not established.
- **Phase 30:** opt-in experimental Undercover-derived lateral tire-force calculation ran in Carbon PC. The user reported **heavier** handling, contrary to the project's goal. Log reports 19,971 replaced calls and 0 fallbacks. **Keep this experiment disabled.**
- **Phase 31:** high-confidence identification of the Carbon PC \`SuspensionRacer::DoHumanSteering\` implementation at \`0x006EF540\`; cross-checks against symbol-rich Carbon Wii / Undercover Wii executables. See [Phase 31](phase31/README.md).

## Boundaries

- Only the supported, version-matched **Carbon PC** executable is addressed. Version-sensitive tools must fail closed on an unexpected executable SHA.
- No original game executables, archives, full game-code disassembly, extracted model/texture/audio assets, runtime memory dumps, or unlicensed binaries belong in this public repository.
- Source files and structured findings are for studying independently acquired local game copies. A successful offline structural match is not a live behavioral port.
- Incompatible tire-call-site hook ASIs **must not** be loaded simultaneously. Perform live tests only in a disposable game copy.

## Current Phase 32 findings

- [Phase 32: Undercover Wii steering-input shaping](phase32/README.md): confirmed signed-power (exponent about 1.15) and signed-square input paths, plus a 0.12 branch threshold, with original-ELF verification and 9 tests.
- [Police AI research](../gameplay/police/README.md): five-platform function map, verified Undercover pursuit probability branch and attribute-owner migration cautions.

## Phase 33: PS2 steering functions mapped

- [Phase 33 PS2 verification and five-build map](phase33/README.md): independently identified stripped Undercover PS2 at **0x004082B0** (1,216 bytes) and Carbon PS2 at **0x003D58D8** (688 bytes) using exact original executables. Undercover PS2's signed-square input path and mode-specific 55-versus-45 comparison are directly observed in the code.
- No Phase 33 handling patch exists. Phase 30's tire-force alpha remains disabled after the heavier-feeling CCX test.

## Phase 34: original PS2 angle-helper path

- [Phase 34 state-dependent steering-angle reference](phase34/README.md) identifies original Undercover PS2 angle helper at 0x00172CB8; selects arguments using chassis state +0x48 and applies a dynamic, upper-capped intermediate steering limit. This is separate from the input at chassis +0x8C.
- Exact PS2 binary checks and 14 tests passed in the local full research package. The GitHub directory presently contains a smaller source-only Python reference and synthetic tests. The original 16-bit lookup table and subsequent steering state dynamics remain unported.

## Phase 35: shared PS2 fixed-angle lookup confirmed

- [Phase 35 research](phase35/README.md) verifies **identical 257-entry angle LUTs** and **91/94 identical helper instructions** across original Undercover PS2 and Carbon PS2. The remaining three words relocate the table address.
- The table itself is not the cause of the PS2 handling difference. Work now focuses on the caller's state-dependent logic, console motion fields and their Carbon PC equivalents.
- The complete local-source verifier and **21 passing tests** are included in the downloadable Phase35 research package. GitHub includes a smaller source-only reference model and synthetic tests.

## Immediate next work

1. Derive the mathematical transformation in Undercover Wii's steering routine and independently match Undercover PS2's routine.
2. Compare PC steering state offsets/units with Undercover calculations using read-only observation.
3. Build a separate opt-in **steering-only** prototype with a Carbon fallback; keep Phase 30 disabled.
4. Validate the CCX driving feel with repeatable A/B tests. Do not equate lighter steering with simply reduced tire grip.

The full phase archives and the proprietary inputs remain outside GitHub.

## Phase 36: SHA-gated steering-access census

- [Read-only Phase 36 memory-access audit](phase36/README.md): inventories static MIPS loads/stores in original Undercover PS2 and Carbon PS2 steering routines after Phase 33 exact-build checks. Anchors known instructions but never infers PC offsets from console numbers. Includes source-only synthetic tests. No new live game patch or real-binary Phase 36 result is claimed.

## Phase 37: Anchor-guided static steering-access comparison

- [Phase 37 source, tests and evidence limits](phase37/README.md): after Phase 33/36 SHA and signature verification, anchor-partitions the Undercover PS2 and Carbon PS2 steering access streams and aligns exact mnemonic/displacement pairs, marking unilateral and repeated-pattern cases. **22 local synthetic tests passed**, but no original-file Phase 37 result or gameplay patch is claimed. Carbon PC field equivalence remains unknown.

## Phase 38: Steering register-provenance research

- [Phase 38 source, synthetic tests and limitations](phase38/README.md): SHA-gated read-only local MIPS GPR ancestry for candidate steering memory-access bases; conservative branch/delay-slot/opaque barriers. 38 local synthetic tests passed, with no new real-PS2 scan or Carbon PC gameplay patch claimed. Keep Phase 30 tire-force experiment disabled.

## Phase 39: Handling steering-state review queue

- [Phase 39 source, tests and research limits](phase39/README.md): source-backed MIPS steering access/provenance triage organized by known steering input/output anchors. Also fixes the Phase38 false-clean-pointer treatment of MIPS LWL/LWR partial loads. No original-file Phase39 results or live gameplay patch. Phase30 tire-force hook remains disabled.

## Phase 40: Carbon PC steering write anchors

- [Read-only Carbon PC store decoder](phase40/README.md): decodes two previously verified x86 instructions in the Carbon PC steering function, `mov [esi+0x104], eax` and `mov [esi+0x118], edx`, after exact Phase31 executable validation. Their semantic field names and relationship to PS2 offsets remain **unverified**. Includes 25 synthetic tests, no game hook or modified handling.

## Phase 41: Carbon PC x86 steering-store source registers

- [Read-only Phase 41 register tracer](phase41/README.md): validates the exact Carbon PC executable against Phase 31/40 before using GNU objdump to disassemble the bounded steering function. Recovers independently checked instruction boundaries and conservatively traces EAX/EDX before two verified stores, stopping on unknown definitions and branch/control boundaries. Synthetic tests only, no source-backed run in this session and **no gameplay patch**. Phase 30 tire-force hook stays disabled.

## Phase 42: Carbon PC ESI-relative steering access inventory

- [Phase 42 source, synthetic tests and limitations](phase42/README.md): exact-version-gated, bounded x86 disassembly inventories explicit PC steering routine memory accesses through ESI, groups simple constant displacements and separates complex/indexed and unknown operation forms. Phase 40's two verified ESI-relative writes must be recovered at their exact instruction boundaries. No user-original executable analyzed in this phase, no PS2 field equivalence claimed, and no handling patch. Phase 30 tire-force test remains disabled.

## Phase 43: Carbon PC +0x104/+0x118 candidate access review

- [Phase 43 source, tests and research constraints](phase43/README.md): SHA-gated, read-only focused review of static ESI-relative reads and writes to two known Carbon PC steering-function displacements. Checks branch boundaries and ESI register changes, including the first memory-access instruction, before reporting possible lexical relationships. **Does not establish runtime object identity, field names, PS2 equivalence or an in-game handling change.** Phase 30's tire-force hook remains disabled.

## Phase 44: Carbon PC steering ESI control-flow path audit

- [Phase 44 source, tests and research limits](phase44/README.md): version-gated read-only x86 CFG over the Carbon PC steering routine, tracking paths between candidate ESI-relative +0x104 / +0x118 accesses. Distinguishes modeled routes with no detected ESI writes, register definitions and unknown effects (calls, indirect transfers, unmodeled instructions), while explicitly declining to infer source-level object identity or PC/PS2 field equivalence. No real original-file result or gameplay patch; Phase 30 tire-force hook stays disabled.
