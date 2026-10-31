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

## Immediate next work

1. Derive the mathematical transformation in Undercover Wii's steering routine and independently match Undercover PS2's routine.
2. Compare PC steering state offsets/units with Undercover calculations using read-only observation.
3. Build a separate opt-in **steering-only** prototype with a Carbon fallback; keep Phase 30 disabled.
4. Validate the CCX driving feel with repeatable A/B tests. Do not equate lighter steering with simply reduced tire grip.

The full phase archives and the proprietary inputs remain outside GitHub.
