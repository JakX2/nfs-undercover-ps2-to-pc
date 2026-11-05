# Phase 37: Anchor-guided steering-access alignment

**Status:** source-only, offline, read-only research. No live game patch, no tested gameplay/handling change, and no source ELF files distributed.

## Why this phase exists

Phase 36 inventories memory-access instructions inside the verified Undercover PS2 and Carbon PS2 DoHumanSteering functions, but a naive comparison by displacement would produce false matches: +0x8C need not refer to the same C++ object when accessed through unrelated registers. Phase 37 performs a **strict static-shape alignment** while preserving the prior uncertainty and four verified input/output access anchors.

Input consists of the **locally owned original** Undercover PS2 and Carbon PS2 executables already supported by Phases 33 and 36. Each is validated against the exact SHA-256, instruction signatures, helper calls and direct callers before any comparison.

## Method

1. Run Phase 36's audit_original on both original files, which fails closed on unsupported or modified builds.
2. Identify, in order, two chassis_input reads (+0x8C) and two racer output writes (+0x19C and +0x188) at previously authenticated instruction addresses.
3. Partition the remaining memory-access sequences into **five intervals**, avoiding arbitrary matches across established anchors.
4. Within each interval, run a deterministic longest common subsequence comparison of **exact (mnemonic, signed_displacement) pairs** only.
5. Export paired instruction-shape matches, unmatched accesses on each side and flags for ambiguous repeated shapes. Records include the instruction addresses.

This intentionally ignores base-register numbers for matching, then retains them in the report to support later manual register-provenance work. It does not equate base registers, object types or game behavior.

## Usage

From the repository root with Python 3 (standard library only):

    python physics/phase37/steering_access_alignment.py --uc /local/SLUS_218.01 --carbon /local/SLUS_214.93 --output phase37_alignment.json
    python -m unittest discover -s physics/phase37 -p 'test_*.py' -v

The JSON report contains a SHA metadata field, four anchor pairs, five aligned intervals, repeated-shape ambiguity flags and unilateral candidates. Output reports are created **exclusively** by default; pass --overwrite explicitly to replace an earlier output. With no output path, the report prints to standard output.

## Test results

- **22/22 Phase 37 synthetic tests passed locally** using the committed source and tests.
- **24/24 Phase 36 synthetic tests passed locally** in the development worktree; the GitHub Phase 36 test file is a slightly different 22-test version.
- GitHub Actions validation is not claimed.
- Original source executables were **not available in this session**. There is no newly verified real PS2 access-alignment report.

## Boundaries and next action

A static shape match is only a hypothesis-generating clue. It does **not** prove that both routines access the same object or field; an unmatched access also does not demonstrate a changed handling parameter. The algorithm does **not** recover branch conditions, pointer provenance, actual runtime access frequency, or PC variable addresses. The repeated-shape flag warns that the LCS choice can be nonunique.

Next: run the original-file comparison privately, prioritize unmatched regions adjacent to known steering output stores, and trace their base-register origin manually. Then verify Carbon PC's state layout **independently**, with a version-gated read-only observer, before any steering-only modification.

**Keep Phase 30's tire-force experiment disabled** because the CCX felt heavier when that experiment was active. No original ELF data, memory dumps, extracted assets or playable ASI are included.
