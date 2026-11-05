# Phase 36: Read-only PS2 steering memory-access census

**Status:** Research tooling committed to the Code/AI/Gameplay branch. No handling hook, ASI or in-game result. No original binaries are distributed.

## Purpose

Undercover PS2 (`0x004082B0`) and Carbon PS2 (`0x003D58D8`) both have identifiable `DoHumanSteering` routines. Phase 35 found matching PS2 angle tables, but we still do **not** know the complete meaning of the chassis and racer state that feeds the angle calculation.

This phase provides a narrow reproducible tool to inventory **static MIPS load/store instructions** in both steering routines, rather than transplant guessed object offsets into Carbon PC. It uses Phase 33's exact SHA-256 gating, signatures, direct-call checks and verified routine bounds. It fails closed before reading any candidate instructions if either supplied ELF differs from the supported original.

The scanner reports effective displacements, base/target registers, direction, instruction address, and relative routine address. A small set of instruction addresses already verified by Phase 33 is explicitly labeled as evidence anchors. Other accesses using the same displacement are **not** granted that label.

## Run with your own originals

From the repository root:

```sh
python physics/phase36/steering_memory_audit.py --uc /path/to/SLUS_218.01 --carbon /path/to/SLUS_214.93 --json phase36_steering.json --csv phase36_steering.csv
python -m unittest discover -s physics/phase36 -p 'test_*.py' -v
```

Output overwrites are rejected unless `--overwrite` is passed. Without report flags, the script prints a local JSON report to standard output. There is no game memory access, executable patching, or file modification apart from requested reports.

## Interpretation limits

- This is **not** a dynamic trace, decompiler, alias analysis, control-flow proof, object-type inference, or complete physics port.
- Equivalent signed displacements in PS2 builds are not automatically equivalent fields, nor necessarily from the same object.
- Register provenance and actual execution paths are not reconstructed here.
- MIPS register-relative memory instructions that do not use the enumerated primary opcodes are omitted.
- Output counts are static instruction counts, not rates or observations during play.
- Do not infer Carbon PC structure offsets from PS2 offset numbers. Carbon PC steering code is at `0x006EF540`, but it needs independent x86 evidence.
- This tool relies on the verified Phase 33 signatures. Its source-only synthetic unit tests exercise its decoding, anchoring and rejection logic; they do not replace original-executable verification.

## Next step

Run the auditor on the **exact original two PS2 executables** and examine per-base-register grouping and where dynamic state may feed the 55-degree cap. Then investigate corresponding Carbon PC variables under a read-only, version-gated observer. Only after source-backed mappings exist should a separate opt-in steering-only experiment be contemplated.

**Keep Phase 30 tire-force experiment disabled:** the user reported heavier CCX handling. No changes here affect grip or steering.

## Verification

The 22 synthetic unit-test methods were added to the branch, but original-binary verification and a GitHub CI run are **not claimed** by this phase. Run tests as shown above in a local Python environment; the actual original-file scan still requires the owner's binaries.
