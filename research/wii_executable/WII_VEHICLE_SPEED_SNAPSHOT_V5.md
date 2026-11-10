# Wii Undercover V5: first real vehicle / rigid-body speed accessors

**2026-11-10.** Read-only disassembly of owner-original Wii NfsMWRelease.elf plus an original-free C++17 host-side snapshot implementation. This is a narrowly verified physics-data interface, **not a recovered simulation loop or working PC car controller**.

## Identified Wii symbols and accessed fields

| Function from original ELF | Wii virtual address | Assembly-backed behavior |
|---|---|---|
| GetSpeedXZ__9RigidBodyCFv | 0x80300ED0 (28 bytes) | Load rigid-body +0x70 pointer, then dereference wrapper +0x00; use state f32 velocity X +0x20, Z +0x28, square and accumulate, tail-branch to rsqrt |
| GetSpeed__9RigidBodyCFv | 0x80300EEC (36 bytes) | Same pointer chain; load state f32 X +0x20, Y +0x24, Z +0x28; sum three squares and tail-branch to rsqrt |
| GetOOMass__9RigidBodyCFv | 0x80300F10 (16 bytes) | Return state +0x3C f32, apparently reciprocal mass based on name |
| GetRadius__9RigidBodyCFv | 0x80300F20 (16 bytes) | Return state +0x6C f32 |
| GetIndex__9RigidBodyCFv | 0x80300F38 (16 bytes) | Return unsigned state +0x5E byte |
| GetSimableType__9RigidBodyCFv | 0x80300F30 (8 bytes) | Return rigid body +0xFC u32 |
| GetSpeed__8PVehicleCFv | 0x802EE2CC (8 bytes) | Return vehicle +0x120 f32 |
| Game_GetSimableSpeedKmh__FP8ISimable | 0x8028CD4C (100 bytes) | If simable null, return 0; call virtual slot +0x58 for another interface, return 0 if absent; call virtual slot +0x34 for raw speed; multiply float32 by 3600.0 and then by 0.001 |
| rsqrt | 0x80232544 (76 bytes) | Original function is **misleadingly named**: uses frsqrte and two Newton-like refinements, then multiplies the reciprocal result by its input. Therefore its returned value approximates sqrt(input), not reciprocal sqrt. Nonpositive/tiny values below its comparison threshold return zero. |

The Wii sdata2 base is 0x80715EE0. Original float constants in the km/h path are at base -25380 (3600.0) and base -25384 (0.001), and the zero fallback at base -25440. rsqrt's positive threshold has original float bits 0x2E5BE6FF (about 5.00000006675716e-11). These are control facts extracted privately, not original asset payloads.

## Portable PC side

- wii_vehicle_snapshot.hpp/.cpp decodes a bounded synthetic/owner-local Wii big-endian memory view through the already validated WiiAddressSpace interface from V4.
- RigidBodyVelocity and RigidBodySpeed / RigidBodySpeedXZ traverse the double indirection, read IEEE-754 f32 components, and compute a Euclidean length. The host uses std::sqrt plus the Wii threshold, not the **exact** original frsqrte-based PPC floating-point rounding sequence. Expect small bitwise output differences.
- RigidBodyInverseMass, RigidBodyRadius, RigidBodyIndex, RigidBodySimableType and PVehicleSpeed reproduce observed field loads on valid snapshots.
- SimableSpeedKmh takes explicit simulated presence flags instead of faking Wii virtual tables. It preserves the **two** float32 arithmetic steps, raw_speed * 3600.0f * 0.001f, which are semantically about 3.6 times speed. No source unit for raw_speed is proven simply by the factor.

## Tests

The new synthetic test_wii_vehicle_snapshot.cpp covers a deliberately constructed pointer chain, (3,4,12) velocity, 13-unit 3D speed, XZ speed sqrt(153), big-endian f32 fields, radius, inverse mass, index, simable type, vehicle stored speed, zero/tiny/nonfinite cases and null/misaligned/unmapped pointers. The test compiled and passed locally with Clang C++17 + ASan + UBSan.

The dedicated Wii research GitHub Actions workflow has been extended to compile and run the vehicle test against the same original-free C++ memory decoder, alongside the previous 37 synthetic Python and Attrib test controls. Verify the final CI run before merging.

## Important boundaries

A Wii member function using a virtual slot does not establish the virtual-interface class identity, underlying physics update, full car handling, acceleration, tire forces, collision, steering, AI or a PC-compatible memory layout. Float arithmetic is only behaviorally approximate, not a matching decomp. No live Wii or PS2 runtime differential tests, resource edits, original binaries or model assets are committed.

**Next target:** named motion integration/vehicle update functions, with an explicit source-backed state-transition test; only after that, start reconstructing a PC physics step with a benchmark against actual Wii/PS2 behavior.
