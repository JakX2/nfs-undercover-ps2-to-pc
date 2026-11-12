# Wii Undercover V8–V10: verified linear and angular integration stages

**2026-11-10.** Owner-original Wii PowerPC NfsMWRelease.elf inspected privately with the symbol-rich, exact-DOL-matched ELF reference. The repo contains independently written portable C++17, synthetic tests, and the instruction-level evidence described here, **not** any proprietary executable bytes, original function bodies, or original resource payloads.

## Scope: contiguous prefix within RigidBody::DoIntegration

The original Wii function DoIntegration__9RigidBodyFf begins at 0x8030F9C4 and spans 0x744 bytes. The previous V7 pass recovered only the status branch and the first linear velocity update. These updates reconstruct a longer **contiguous subset of its state-changing path**, still NOT the complete integrator:

| Original address window | Recovered state changes |
|---|---|
| 0x8030F9FC–0x8030FA24 | State byte +0x5D != 0: clear 3-float state vectors at +0x20 and +0x30, then skip to epilogue |
| 0x8030FA28–0x8030FAD8 | Velocity +0x20 += force +0x50 times (timestep × inverse mass +0x3C) |
| 0x8030FADC–0x8030FB04 | Torque workspace state +0x60/+0x64/+0x68 multiplied by timestep |
| 0x8030FB08–0x8030FB2C | Position +0x10/+0x14/+0x18 incremented by the just-updated linear velocity times timestep |
| 0x8030FB2C–0x8030FBAC | Body-side 3x3 matrix transforms torque, stored back into state +0x60/+0x64/+0x68 |
| 0x8030FBB0–0x8030FBD4 | Add transformed torque into angular velocity state +0x30/+0x34/+0x38 |
| 0x8030FBD8–0x8030FC60 | Saturate each linear velocity component into [-300,+300] |
| 0x8030FC64–0x8030FCF0 | Saturate each angular velocity component into [-30,+30] |

All offsets are original **Wii 32-bit object** offsets, not PC struct offsets. The five added functions following the older V7 prefix are deliberately composable, but the host implementation may re-read state and serialize after each phase; it does not claim instruction-by-instruction or timing/ABI identity.

### Source-backed position and angular velocity checks

Independent named Wii accessors corroborate the fields:

- GetPosition__9RigidBodyCFv (0x803012B8) returns state+0x10; SetPosition__9RigidBodyFRCQ25UMath7Vector3 (0x8030E3B4) stores 3 floats there.
- GetLinearVelocity__9RigidBodyCFv (0x80301298) returns state+0x20; SetLinearVelocity at 0x8030E3D8 stores 3 floats there.
- GetAngularVelocity__9RigidBodyCFv (0x803012A8) returns state+0x30; SetAngularVelocity at 0x8030E3FC stores 3 floats there.
- The prior V6 setters independently confirm the torque working vector at state+0x60.

### Body-side angular transform matrix

The original PowerPC load sites use a 3x3 matrix of 32-bit floats from the RigidBody **itself**:

- First row at body +0x84, +0x88, +0x8C.
- Second row at body +0x94, +0x98, +0x9C.
- Third row at body +0xA4, +0xA8, +0xAC.

The transform is applied to torque after it was already multiplied by timestep. The observed sequence uses an initial multiply, then two fused multiply-adds for each output. It writes the resulting three-component delta back to state+0x60 before adding the same values to angular velocity. This is a concrete matrix-vector operation; the **physical meaning** of that matrix is not established without additional evidence. It may represent an inertia-related transform but should not yet be treated as a verified whole-world inertia tensor.

### Original Wii clamp constants

The Wii original ELF places the following big-endian IEEE-754 float constants in .sdata2, using the r2-relative address base 0x80715EE0:

| r2-relative displacement | Original f32 bits | Meaning |
|---|---|---|
| -24500 | 0x43960000 | +300.0 |
| -24496 | 0xC3960000 | -300.0 |
| -24492 | 0x41F00000 | +30.0 |
| -24488 | 0xC1F00000 | -30.0 |

The original clamp compares each value with its upper bound first, selecting the upper bound if the value is not less than it. Then it compares the lower bound with the capped result and selects the lower bound if greater. This means a source NaN selects the **positive** bound under ordered PowerPC comparisons; it does not transparently propagate. No behavioral claim is made for alternate PPC FP exception/trap configurations.

**Important ordering:** the original writes position using the **pre-clamped** newly integrated linear velocity. Only afterwards does it clamp the three velocity components. A test explicitly checks that the position delta can exceed what would be predicted from the post-clamp velocity.

## New safe PC-host entry points

All code lives under research/wii_executable/wii_rigidbody_controls.hpp/.cpp and operates only on independent, owner-local or synthetic Wii memory snapshot copies:

- RigidBodyPosition and RigidBodyAngularVelocity (plus SetPosition, SetLinearVelocity and SetAngularVelocity).
- ApplyDoIntegrationTranslationPrefix (V8): V7 plus timestep-scaled torque and position.
- ApplyDoIntegrationAngularPrefix (V9): V8 plus body 3x3 torque transform and angular velocity accumulation.
- ApplyDoIntegrationClampedAngularPrefix (V10): V9 plus six clamping stores.

These functions **stop at 0x8030FCF0**, before the original routine's remaining orientation, rotational motion, collision-adjustment or other state updates. All stages use copy-on-commit: exceptions arising from missing Wii memory fields never partially mutate the caller's snapshot. This differs deliberately from raw Wii memory faults and the original store-by-store side effects.

The original uses PowerPC floating-point instructions, including fmuls/fmadds, and its host conversion currently uses float and std::fma. It is not verified bit-identical under PPC rounding, fusion, denormals or FPSCR mode.

## Reproducible synthetic tests and evidence status

Extended test_wii_rigidbody_controls.cpp checks:

- The V8 position/torque update using (10,20,30) initial velocity, (2,4,6) force, 0.5 inverse mass, dt=0.25 and position (100,0,-2). Expected velocity (10.25,20.5,30.75), position (102.5625,5.125,5.6875), scaled torque (1,2,-3).
- V9's nonidentity 3x3 matrix and transformed torque (5,-4,-2), accumulated angular velocity (6,-2,1); inactive-state early branch and atomic rejection if matrix memory is missing.
- V10's linear ±300 and angular ±30 clamps; the pre-clamp position ordering, exact boundary values, NaN/infinity handling and inactive-body path.
- The earlier V6/V7 state and control tests remain.
- The dedicated GitHub Actions workflow runs 37 original-free Python parser/call-graph tests plus Clang C++17 ASan/UBSan tests. The owner-original ELF is **not** used by CI. Inspect the latest run for the final pass status.

## What is not yet proven

This milestone does **not** recover the orientation/quaternion update after 0x8030FCF0, full RigidBody scheduling, suspension and steering forces, collisions or player controls. No real Wii emulator input/output differential has been performed. The PS2 Emotion Engine implementation has not been matched at the function level. There is still no demonstrated native playable Undercover PC build.

**Next**: decode the orientation update at and after 0x8030FCF4, isolate its state variables, matrix/quaternion operations and branch conditions; then test a complete state transition against an original game runtime trace, using only private owner data.
