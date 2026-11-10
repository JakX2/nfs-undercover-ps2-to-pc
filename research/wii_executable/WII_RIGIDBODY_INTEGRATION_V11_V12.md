# Wii RigidBody integration V11–V12: orientation and body matrix research

Status: **experimental, source-only, synthetic tests; no runtime equivalence claim**.

## Original Wii reference

The owner-local, symbol-rich PowerPC ELF identifies `DoIntegration__9RigidBodyFf` at
`0x8030F9C4`, length `0x744`. The established V8–V10 contiguous prefix
ends at `0x8030FCF0` (linear and angular clamps).

The independent host implementation now separates two subsequent phases:

* **V11** `wii_rigidbody_orientation.cpp`: `0x8030FCF4..0x8030FE70`.
  Reads angular velocity from state `+0x30`; zero squared magnitude
  skips the orientation update. Otherwise integrates state quaternion
  `+0x00` (XYZW), normalizes it and rebuilds the state `+0x70`
  orientation matrix via `VU0_quattom4` at `0x8023480C`.
  The original uses floating-point operations whose exact Wii FPSCR
  behavior has not been reproduced.
* **V12** `wii_rigidbody_final_transform.cpp`: experimental reconstruction
  of the remaining matrix/center adjustment, with a 4x4 body matrix at
  `+0x84` and a three-float body center offset at `+0xE4`.
  State `+0x40,+0x44,+0x48` supply the diagonal values. The
  comparison threshold is approximately `1e-6` (original f32 bits
  `0x358637BD`). The portable implementation uses
  `transpose(R) * (D * R)` and adjusts position at state `+0x10`
  by the difference between old and new rotated center offsets.

## What is established versus tentative

* **Source-backed memory locations:** state quaternion `+0x00`,
  position `+0x10`, angular velocity `+0x30`, diagonal scalars
  `+0x40/+0x44/+0x48`, orientation matrix `+0x70`, body matrix
  `+0x84`, and body center offset `+0xE4`.
* **Source-backed helpers:** `VU0_quattom4` at `0x8023480C`,
  `VU0_MATRIX4_mult` at `0x802348FC`.
* **Host approximations:** C++17 `std::fma`, reciprocal and sqrt
  semantics, exception-based rejection of invalid quaternions,
  and copy-on-commit snapshots. None of these guarantee bit-exact
  PowerPC results or preserve the original instruction-side effects.
* **Not yet established:** complete physics runtime behavior,
  engine scheduling, Wii-versus-PS2 object-layout equivalence,
  collision coupling, game input/output traces, or a playable PC port.

## Synthetic checks

`test_wii_rigidbody_final_transform.cpp` covers identity orientation,
a nonzero angular velocity with center-of-gravity correction, the
reciprocal threshold including negative scalars, inactive-state
short-circuit, and rollback when the output matrix cannot be written.
`test_wii_rigidbody_controls.cpp` also covers V10 zero timestep,
an asymmetric body matrix, and noncanonical inactive status 255.

These are synthetic host-memory fixtures, **not** Wii emulator
differential traces. A passing test demonstrates only agreement with
the encoded host expectations. Run the repository's dedicated
Wii executable research workflow and review sanitizer output after
each change; never label unexecuted tests as passed.

## Next validation gate

1. Confirm V12 C++ targets are included in the CI workflow, then run
   Clang C++17 ASan/UBSan and all existing synthetic tests.
2. Inspect the private ELF's matrix multiplication and reciprocal
   branch instruction order again, especially nonidentity orientations,
   near-threshold floats, NaNs and nonzero center offsets.
3. Obtain an owner-local Wii emulator state trace at the entry/exit of
   `DoIntegration`, compare numerical outputs, and record tolerances.
4. Validate PS2 Emotion Engine independently. Do not transfer Wii
   structure offsets to PS2 without separate evidence.

No proprietary binaries, disassembly dumps or extracted assets are
included in this repository document.
