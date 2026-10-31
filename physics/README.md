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
