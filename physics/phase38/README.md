# Phase 38: Conservative steering register-provenance tracing

**Status:** source-only, read-only handling research. No installed patch, ASI, changed physics values, real-source scan in this session, or in-game handling result.

## Motivation

Phases 36 and 37 showed how to inventory and compare memory-access instruction shapes in the original PS2 steering code. Phase 38 follows the **general-purpose register that supplies a selected memory access's base address** backward through the current conservative straight-line region. This avoids treating matching numeric displacements as evidence of identical objects.

The tool annotates accesses to previously investigated displacements (+0x48, +0x64, +0x8C, +0x9C, +0xC0, +0xD8, +0x160, +0x188 and +0x19C), plus previously verified anchors.

## What the tracer recognizes

- Local GPR definitions by `lui`, `addiu`, `ori`, `addu` and `or` where supported.
- Pointer loads and their base-register origins within the same region.
- Direct branch targets, calls, jumps, and delay-slot boundaries. These **break** tracing rather than guessing predecessor values.
- Unknown opcodes and unmodeled register writes terminate a provenance chain.
- Missing earlier definitions become `block_live_in_unknown`; they are **not** assigned guessed chassis or racer object types.

The output is a JSON tree of local definition PCs with explicit uncertainty markers (`block_live_in_unknown`, `opaque_barrier`, `unknown_definition`, `depth_limit`). It is **not** complete SSA, control-flow dataflow, pointer alias analysis, or evidence that a value has a particular dynamic meaning.

## Run with user-owned original files

From the repository root:

```sh
python physics/phase38/register_provenance.py --uc /local/SLUS_218.01 --carbon /local/SLUS_214.93 --output phase38_pointer_origins.json
python -m unittest discover -s physics/phase38 -p 'test_*.py' -v
```

The program calls Phase 36's `audit_original` for each source file, which in turn uses Phase 33's exact SHA and instruction/call verification. The analyzer refuses unsupported binaries before reporting, reads but never modifies them, and rejects overwriting an existing report unless `--overwrite` is supplied. Without `--output`, it prints JSON to stdout. Source files and raw instruction words are **not** included in the output.

## Tests and interpretation

**38/38 synthetic Phase 38 tests passed locally** with the development source. They cover MIPS register decoding, branch and delay-slot barriers, pointer-load chains, unmodeled clobbers, candidate reporting, and safe rejection of invalid input at the CLI boundary. This does not establish real PS2 results.

The source-only GitHub CI also runs Phases 36 and 37. No original PS2 executables or extracted game assets belong in GitHub Actions or public commits.

## Next milestone

Run Phase 38 with the original supported executables privately. Inspect anchors for both games and group access trees by local GPR load origins. If the source-backed results support it, trace the unexplained console motion-state values further, then independently map their counterparts in Carbon PC using **version-gated read-only evidence**. Do not copy PS2 offsets into Carbon PC.

**Phase 30's lateral tire-force experiment remains disabled.** It made the user's CCX feel heavier; this work does not edit grip or wheel-angle values.
