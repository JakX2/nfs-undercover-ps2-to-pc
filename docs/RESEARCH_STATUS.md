# Scenery research status through V46

This document records **offline** observations, not an installable PC mod.

## Verified Wii fixture observations
- Undercover Wii RedBuilding scenery scene: 8,488 bytes; SHA-256 `cb08ca728a9b76992aaaefe32b450565ef53246f090cfe296f77d96c5d272e7f`.
- 31 original scene instances, each 96 bytes, and 31 32-byte `0x3410D` auxiliary records.
- RedBuilding 1B instance 26 at approximately (2631.938721, 3261.404541, 199.968338).
- In this **Wii fixture**, child `0x34105` has eight 48-byte candidate spatial nodes. Nonnegative references address instance indices; negative `-k` references resolve to node `k`. All original scene instances are covered exactly once, with exact descendant AABB unions.
- `0x34107` (3,072 bytes) has a candidate 24 × 128-byte cadence: the first block is zero; 23 populated blocks each end in two 32-bit values (384, 384). Semantics remain **unknown**. Its length fits both `(31+1) × 96` and `8 × 384`.

## Reported V42 Carbon experiment (not independently retested here)
- Original Carbon scene root at stream offset `0x27BAF0C0`, master row 406, section ID `0x343447`; corresponding Wii section also uses numerical ID `0x343447`, **not** proof of geographic equivalence.
- Experimental standalone Carbon ROOT inserted one UC RedBuilding info, instance and corresponding 32-byte auxiliary record, moving counts 25→26, increasing root size 8616→8816 bytes.
- Carbon `0x34105` and `0x34107` remained byte-identical; index ownership, relocations, shaders, collision and streaming unresolved.

## V45/V46 validation
- Offline Wii-only failure-case checks show a virtual 32nd instance is not covered by an unchanged verified 31-instance spatial hierarchy.
- `0x34107` evidence remains observational; no safe writer schema is proven.
- Earlier fixture-backed package reported 164/164 selected tests passing, **not** an in-game test or a fresh CI result for this repository.

## Immediate research goals
1. Read original Carbon PC scene roots from an authorized local stream, including candidate offset `0x27BAF0C0`, after fingerprint validation.
2. Derive Carbon-specific `0x34105`/`0x34107` schemas from independent samples rather than assuming Wii compatibility.
3. Disambiguate `0x34107` size relations with multiple original scenes having different instance and node counts.
4. Trace symbol-rich Wii `LoaderScenery` and Carbon's runtime for table consumption, relocation and ownership.
5. Do not create an installable game patch until dependencies and registration are verified.
