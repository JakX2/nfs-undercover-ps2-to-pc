# Phase 34: Original PS2 state-dependent steering angle

**Status: read-only, structural binary research. Not an installed ASI or a complete steering port.**

## Source verification

We reexamined original SHA-matched Undercover PS2 SLUS_218.01 and Carbon PS2 SLUS_214.93, including the Undercover PS2 **DoHumanSteering** function at 0x004082B0 and its direct **angle helper at 0x00172CB8**.

Original Undercover PS2 SHA-256: 6c53252622348ee5981685420a27e6914e02757e739945f583940b8c35814646

The original full-size local Phase34 verifier (distributed separately in the research ZIP, not yet copied to GitHub) passed **39 Undercover steering instruction checks, 4 helper instruction checks, one exact call target, and 4 Carbon PS2 comparator checks**. **14 offline regression tests passed** using the original supplied binaries, including deliberate SHA rejection. This GitHub directory contains the smaller, pure-Python **reference model** and its independent synthetic tests, not the full original-binary verifier.

## What is reconstructed

In a specific PS2 player-steering input branch, Chassis::State +0x8C is transformed using signed-square input and checked against a threshold near 0.12. The later angle calculation instead reads a DIFFERENT chassis field at +0x48:

| Chassis +0x48 | Intermediate angle calculation |
| --- | --- |
| Greater than +0.1 | Original angle helper takes (state48, 3.8) |
| Less than -0.1 | Original angle helper takes (-state48, 11.0) |
| Between -0.1 and +0.1 | Literal 55-degree value |

The table-based helper returns a fixed-point 16-bit angle. The caller sign-extends it and computes approximately angle16 * 360 / 65536.

Next, at original PS2 addresses 0x00408544–0x00408570, the routine derives an upper-capped intermediate angle:

    min(55, base_degrees * (1 + 0.5 * racer_plus_0x160))

This is **not the final wheel angle**. Later mode, sign, motion and steering-state branches combine this with the transformed input. Neither the exact meaning of chassis +0x48 nor racer +0x160 is verified. Those PS2 fields are NOT interchangeable with Carbon PC offsets.

The supplied script intentionally requires the original helper's **16-bit output** for either active lookup branch. Replacing the fixed-point lookup with ordinary atan2 would introduce an unverified behavioral approximation.

## Reproduction

- No PS2 binaries required for the GitHub reference-model tests: from this folder run: python -m unittest -v test_angle_branch_reference.py
- For read-only original executable signature checks, use the complete locally distributed Phase34 research ZIP with your own original PS2 executables.
- No original ELF/EXE, assets, disassembly dump, in-game memory captures, or compiled ASI in this public repo.

## Direction

The next step is mapping this **state-dependent steering path** onto Carbon PC by observing corresponding PC state fields, **not** lowering tire grip again. Keep Phase 30's tire-force alpha disabled; the user confirmed it made the upgraded Koenigsegg CCX heavier.
