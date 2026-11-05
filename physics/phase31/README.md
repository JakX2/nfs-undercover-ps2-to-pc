# Phase 31: Carbon PC steering function mapping

**Status:** research and read-only binary verification. No ASI or patch in this phase.

The supported retail Carbon PC executable was identified by SHA-256:

\`baaaaec33873d4ba7e4dbae6a5212049ffdcf9679a35d865d7625b4189952fd3\`

Its PE32 image base is \`0x00400000\`. The Carbon PC function believed to correspond to the *named* \`SuspensionRacer::DoHumanSteering\` routine in Carbon Wii is at **\`0x006EF540\`** (729 bytes including the \`ret 4\` ending at \`0x006EF816\`).

### Key cross-platform matches

| Build | Routine | Address | Function size |
| --- | --- | --- | ---: |
| Carbon PC | \`SuspensionRacer::DoHumanSteering\` (inferred name) | \`0x006EF540\` | 729 |
| Carbon Wii | \`SuspensionRacer::DoHumanSteering\` (ELF symbol) | \`0x802EDB88\` | 664 |
| Undercover Wii | \`SuspensionRacer::DoHumanSteering\` (ELF symbol) | \`0x80324B48\` | 1,288 |
| Undercover PS2 | Unmatched in stripped executable | unknown | unknown |

Supporting PC calls inside the Carbon steering routine:

- \`0x006EF5E9\` and \`0x006EF63E\` → \`0x006DFDE0\` (max steering).
- \`0x006EF74E\` → \`0x006A1900\` (table lookup).
- \`0x006EF75A\` → \`0x006E0090\` (steering speed).
- \`0x006EF7EC\` → \`0x0075CF60\` (scalar timing getter).
- \`0x006EF802\` → \`0x006A2250\` (rolling-window recorder).
- \`0x006EF841\` → \`0x006EF540\` (a directly identified caller).

These names for Carbon PC are inferred from the *named* Wii call-graph correspondence. This is not a claim that retail Carbon PC exports these names.

Undercover Wii's routine contains two \`pow\` calls and two \`bATan\` calls absent from the mapped Carbon PC routine. This shows a different code path, **not** by itself a proven explanation of lighter steering.

### Offline verifier

Requires Python 3, standard library only, plus a user-owned copy of the exact supported \`NFSC.exe\`:

\`\`\`sh
python physics/phase31/verify_carbon_pc_steering.py /path/to/NFSC.exe --json steering_checks.json
python -m unittest discover -s physics/phase31 -p 'test_*.py' -v
\`\`\`

Set \`CARBON_NFSC_EXE\` to your local executable path to enable binary-backed regression tests. Without that file, those tests will **skip**, not claim a pass.

The verifier performs 17 instruction/call-site checks. It does not modify or run the game. Some numeric constants found in the code include ±45 and ±70; their specific gameplay meaning is still unverified.

### Source and provenance

Derived by comparative analysis of user-supplied Carbon PC \`NFSC.exe\` and named Wii symbols. No raw executable/disassembly has been uploaded. The experimental Phase 30 tire-force patch should remain disabled: the user reported it made the upgraded CCX heavier.
