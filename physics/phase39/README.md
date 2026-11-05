# Phase 39: Steering-state dependency triage

**Research-only. No installed handling patch, inferred Carbon PC field addresses, live steering measurements, or newly verified original-binary comparison.**

## What changed

Phase 38 introduced within-block GPR ancestry for original PS2 steering access instructions. Phase 39 produces a **review queue** instead of requiring a researcher to read every nested trace by hand.

The public CLI uses Phase 38's audited source loader, which first verifies both exact original PS2 executable SHA-256 values, the Phase 33 steering instruction signatures, and call-site evidence before inspecting either function.

The Phase 39 report:

- Partitions candidate memory accesses into five intervals between four **previously verified** steering read/write anchors.
- Compares exact (mnemonic, signed displacement, direction) **static instruction shapes** separately in each interval.
- Flags differences in instruction-shape counts and, where counts match, differences in the **local GPR-provenance shape**. These are **only research leads**.
- Tracks unresolved GPR ancestry: block_live_in_unknown, opaque_barrier, unknown_definition, depth_limit, and merged partial_load_unknown.
- Marks repeated-shape ambiguity. It never assumes matching register numbers, displacements or local ancestry trees prove the same underlying object or field.

The four anchor events in each PS2 routine, in source instruction order: two reads from steering-input offset +0x8C, a shaped-input write to +0x19C, and a steering-output write to +0x188. These are **console-side** observations; the Carbon PC object layout is not established.

## Phase 38 correctness fix

The original Phase 38 instruction decoder treated MIPS LWL/LWR (partial-word merge loads) as ordinary GPR loads. These instructions merge source bytes with an existing destination register, so their result is not a clean, independently attributable pointer load.

The decoder now terminates such chains with partial_load_unknown. Two new regression tests cover the byte-merge opcode recognition and a preceding-pointer-load false-positive case. Phase 39 carries the new uncertainty marker into its reports.

## Reproduce locally with your exact original PS2 executables

Run from the repository root with Python 3 and its standard library only:

    python physics/phase39/steering_state_triage.py --uc /path/to/SLUS_218.01 --carbon /path/to/SLUS_214.93 --output phase39_steering_review.json
    python -m unittest discover -s physics/phase39 -p 'test_*.py' -v

Outputs are created exclusively by default. Replacing a report requires --overwrite. Without --output, JSON is sent to standard output. Original binaries are never written to, and the script never reads a live game process.

## Tests and limits

- **30 Phase 39 synthetic tests** exercised locally before commit.
- **40 Phase 38 synthetic tests** exercised locally after the partial-load correction.
- GitHub CI runs source-only tests for phases 36–39; any green CI result proves regression tests, **not** executable/source equivalence.
- No authenticated original PS2 binaries were available during this Phase 39 session. The report against the original files has **not** been generated.

Static instruction-order regions are not necessarily control-flow regions. Identical shapes can involve different base objects, and shape differences may have no effect on gameplay. The provenance signature intentionally ignores address relocation and arithmetic immediates; it is a **coarse triage tool**, not a proof of physics behavior.

## Next evidence required

1. Run this tool privately against the exact SHA-matched original PS2 executables.
2. Inspect review entries between the second input read and the two output stores, noting unknown register roots and branch paths.
3. Independently identify Carbon PC steering-state equivalents using version-gated, read-only observation.
4. Only then attempt a separate **opt-in, reversible steering-only** prototype. Do not revive the Phase 30 lateral tire-force hook: it made the upgraded CCX feel heavier.

Do not commit copyrighted executable files, extracted assets, game memory dumps, or experimental installable binaries.
