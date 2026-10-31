# Police AI and pursuit-code research

This directory belongs to the AI/Code/Gameplay chat. It is separate from the scenery, map and asset pipeline.

## Verified function mapping

The Phase 6 five-build table is included in this directory. Most Carbon PC names are **inferred** from matching call order in symbol-rich Wii binaries, while the addresses themselves are independently extracted from each build.

Notable code locations:

| Function | Carbon PC | Undercover PS2 | Undercover Wii |
| --- | --- | --- | --- |
| AICopManager::OnTask | 0x004463C0 | 0x0010BFB8 | 0x800147F8 |
| AICopManager::UpdatePursuits | 0x00445C70 | 0x0010A0B0 | 0x800129DC |

## Phase 7: Undercover-specific probability gate

Undercover PS2 and Wii both have a conditional pursuit-engagement probability check not present in the corresponding Carbon PS2 and Wii routines.

- Named Wii helper: GetGlobalProbabilityCopsEngagingPursuit
- Named Wii random helper: bRandom(float)
- Wii insertion: 0x80013144 onward
- PS2 counterpart: 0x0010A878 onward
- Carbon PC original UpdatePursuits: 0x00445C70

Verified abstract branch (see deterministic C++ reference):

    if (manager_flag && random_sample > engagement_probability)
        manager_flag = false;

The true source of engagement_probability, its configured non-fallback value and the exact downstream meaning of manager_flag remain **unverified**. The getter's 0.0 fallback does **not** establish a default game probability of zero. The Wii and PS2 builds evaluate their getter/random calls in different orders; the branch comparison matches, but function side effects have not been fully excluded.

Original Phase 7 static verifier previously passed 38 cross-build structural checks. This repository contains only the minimal explanatory reference code, not a live police gameplay plugin.

## Phases 10–15: attribute collection and owner migration

A key trap discovered in Phase 15: five shared instance hashes move from Carbon owner 0x551E22B3 to Undercover owner 0xB803FE69; their presence under a new owner must not be mistaken for deletion.

Phase 15 verified 12 relocated tables and 110 owner/child links across the five supplied builds, with 30 distinct child keys in the selected owner groups. The serialized three-word headers of five moved records differ (Carbon: 7,13,7; Undercover: 0,0,0), but their **semantics are unknown** and they must not be interpreted as probabilities.

The complete owner graph, pointer-relocation parser and asset inputs remain outside this initial public GitHub import. A proper source-only parser import should preserve the five-build SHA guards and rerun fixture-backed corruption tests before being marked validated.

## Safety and scope

This directory does not contain original game assets or executables; it does not modify the game. There is no working Undercover police AI port for Carbon PC yet. Do not use console manager offsets directly on PC.

## Next work

Identify the actual typed attribute read behind the engagement-probability getter and the downstream manager-flag semantics; then consider a version-gated, read-only Carbon observation before any game patch.
