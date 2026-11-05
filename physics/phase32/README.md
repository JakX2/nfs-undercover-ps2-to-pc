# Phase 32: Undercover Wii human-steering input shaping

**Status:** Read-only code/constant analysis. Not a patch or complete handling replacement.

## Source and findings

Original Undercover Wii ELF SHA256: 1de2533575414a989e240db5cc99b528b7bf99f048f3d79022d9e1c8725d1653

The symbol-named SuspensionRacer::DoHumanSteering begins at 0x80324B48 (1,288 bytes). It reads Chassis::State +0x8C and uses one of two input transforms:

| Path | Equivalent computation | Location |
| --- | --- | --- |
| Power | sign(x) * pow(abs(x), 1.15) | 0x80324CD8–0x80324CFC |
| Square | x * abs(x) | 0x80324D04–0x80324D08 |

The power/square choice depends on an IO-module/vtable-derived flag. It is **not yet established** which controller, keyboard or wheel configurations use each path.

The exponent was decoded from the original SDA2 double (approximately 1.149999976) and a subsequent magnitude threshold was decoded from a float (approximately 0.119999997).

**Important distinction:** if the transformed magnitude is below the threshold, one branch zeros a **steering output accumulator**. It does **not** zero the underlying transformed input, which is still recorded at racer +0x11C. There are also enum-specific paths that bypass this transformation.

The approximate original-input magnitudes that exceed the threshold are 0.1582 (power path) and 0.3464 (square path), **in this branch only**.

| Input magnitude | Power transform | Square transform |
| ---: | ---: | ---: |
| 0.20 | 0.15710 | 0.04000 |
| 0.50 | 0.45063 | 0.25000 |
| 0.75 | 0.71832 | 0.56250 |
| 1.00 | 1.00000 | 1.00000 |

The routine also calls CalculateMaxSteering, two bATan branches, Sim::GetTime and AverageWindow::Record. The code contains constants 3.8, 11.0, a branch-specific 55.0, and about 1/360. These have not all been assigned reliable gameplay meanings. The routine stores a steering state at racer +0x108, an input-state value at +0x11C, and records history using +0x120. Do not copy these Wii racer offsets into Carbon PC.

Carbon PC's independently mapped steering routine at 0x006EF540 also consumes Chassis::State +0x8C but uses different racer object offsets and processing paths.

## Reproduce

1. Provide your **own** original NfsMWEuropeEnDuRelease.elf, with the exact SHA above.
2. Run: python physics/phase32/undercover_wii_steering_curve.py /path/to/NfsMWEuropeEnDuRelease.elf
3. Run: python -m unittest discover -s physics/phase32 -p "test_*.py" -v
4. To enable the original-binary test, set UC_WII_ELF to your locally owned ELF path.

The script exports 41-point illustrative curves and a local verification JSON. In the local research environment it passed **15 instruction signatures, 7 direct-call checks, 6 constants and 9 tests**.

The exported post-deadzone columns are deliberately *illustrations of this branch's zero-output gate*, **not** reconstructed game-state values or complete wheel-angle predictions.

## Next technical steps

- Identify and cross-validate the PS2 steering counterpart independently.
- Resolve IO device selection and the arctangent/state-dependent steering paths.
- Build read-only PC state observation before a reversible steering-only experiment.
- Keep Phase 30's heavier-feeling tire-force alpha disabled.
