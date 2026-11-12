# Wii V23: Primitive::SetCollision geometry-call argument reconstruction

Date: 2026-11-12. This is source-backed analysis from the owner's original **Undercover Wii** big-endian PowerPC ELF and original-free C++17 regression code. Original retail binaries, asset bytes and model identities remain private.

## Source evidence

The original, unstripped symbol `SetCollision__Q29RigidBody9PrimitiveCFRCQ29RigidBody5StateRQ38Dynamics9Collision8Geometry` begins at **0x8030BD5C** and has symbol size **0x1EC (492 bytes)**. The original ELF reports a call to `Set__Q38Dynamics9Collision8GeometryFRCQ25UMath7Matrix4RCQ25UMath7Vector3RCQ25UMath7Vector3Q48Dynamics9Collision8Geometry5ShapeRCQ25UMath7Vector3` at **0x800E9440**. The SetCollision wrapper itself does **not** resolve contacts; it constructs arguments and calls this separate geometry method.

| Original primitive/state field | Original offset | Verified role |
|---|---|---|
| Primitive local quaternion XYZW | primitive +0x08/+0x0C/+0x10/+0x14 | Combined with state quaternion when shape != 2 |
| Primitive geometry parameters | primitive +0x18/+0x1C/+0x20 | Passed by reference to Geometry::Set |
| Primitive shape enum | primitive +0x24 | Branch on integer 2; forwarded to Geometry::Set |
| Primitive local XYZ | primitive +0x28/+0x2C/+0x30 | Recomputed current world point |
| Prepared earlier world XYZ | primitive +0x38/+0x3C/+0x40 | Subtracted from current world point |
| State quaternion XYZW | state +0x00/+0x04/+0x08/+0x0C | Left factor of local quaternion product |
| State world position | state +0x10/+0x14/+0x18 | Added to rotated local point |
| State orientation three rows | state +0x70/+0x80/+0x90 | 3x3 transform of local point |

The original `0x8030BD5C..0x8030BE4C` computes world position using multiply/add/rounding operations matching the earlier `Primitive::Prepare` transform, then constructs **delta = new world position minus earlier prepared world position**. The earlier prepared value is not overwritten in this function. The call passes the world point, delta, the original primitive geometry parameters and shape.

At **0x8030BE50**, shape `2` branches to the identity orientation constant at **0x80569AD0** (all 16 floats independently inspected in the original ELF), and calls Geometry::Set at **0x8030BE6C**. Other shapes execute the quaternion path: original PPC combines **state quaternion * primitive local quaternion**, calls `VU0_quattom4` at **0x8030BF0C**, then calls Geometry::Set at **0x8030BF28**. The existing host implementation of `WiiQuaternionToMatrix4` supplies the established Wii layout and signs.

## Implemented V23 code and tests

- `wii_rigidbody_collision_args.hpp`: header-only `BuildWiiPrimitiveCollisionCall` with the six output values, bounded 32-bit Wii snapshot address arithmetic, independently validated shape read and optional quaternion path. It **returns values only** and **does not mutate the geometry or Wii snapshot**.
- `test_wii_rigidbody_collision_args.cpp`: synthetic shape-2 identity orientation, source-ordered translation/delta, noncommuting state/local quaternion multiplication, and unmapped/invalid memory rejection.
- Native CMake/CTest integration and the existing Clang ASan/UBSan GitHub source-only test workflow.

The reconstructed 3x3 arithmetic uses host `std::fma(float)` and is not claimed bit-identical to Wii floating point (including `frsp`, denormals, FPSCR rounding, or original VU0 emulation). Shape `2` is a **source-observed numeric discriminator** only; it is not asserted to represent any named geometry primitive without further evidence.

## Explicit remaining gaps

This source-backed wrapper is **not** full collision handling. Next: decompile/characterize `Dynamics::Collision::Geometry::Set` at Wii **0x800E9440** (540 original bytes), determine its actual writes and shape-specific branches, then connect with `RigidBody::UpdateCollider`, `DoWorldCollisions` and independent original emulator traces. Vehicle tire, steering, suspension, contact resolution, native game rendering and Carbon PC engine integration remain separate tasks. No original game files were modified, and this is **not yet a playable port**.
