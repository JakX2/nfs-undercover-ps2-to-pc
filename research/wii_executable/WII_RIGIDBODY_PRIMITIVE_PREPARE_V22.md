# Wii V22: original RigidBody::Primitive::Prepare reconstruction

Date: 2026-11-11. Source-backed reverse engineering of the owner-original Wii PowerPC NfsMWRelease.elf; only independently authored C++17 and original-free tests are committed.

## Original PowerPC instruction evidence

- Prepare__Q29RigidBody9PrimitiveFRCQ29RigidBody5State begins at 0x8030BCB4 and is exactly 0xA8 (168 bytes). It has no function calls and no conditional branches.
- OnBeginFrame__9RigidBodyFf at 0x8030EC44 directly calls Prepare at 0x8030EC9C while iterating the intrusive primitive list at body +0x104. DoIntegration follows at 0x8030ECB8. Thus the original prepares primitive world positions BEFORE integration updates the body.
- Function args: r3 is the original primitive Wii pointer; r4 is the original state Wii pointer. No need to follow a RigidBody pointer inside this helper.

## Source-backed Wii 32-bit object layout

| Field | Original Wii offsets | Direct behavior |
|---|---|---|
| Primitive local vector | +0x28, +0x2C, +0x30 | Three f32 words loaded via lwz to stack, then lfs |
| State rotation row 0 | +0x70, +0x74, +0x78 | Local X multiply-add terms |
| State rotation row 1 | +0x80, +0x84, +0x88 | Initial local Y multiplications |
| State rotation row 2 | +0x90, +0x94, +0x98 | Final local Z multiply-add terms |
| State world position | +0x10, +0x14, +0x18 | Final fadds translation |
| Primitive prepared world vector | +0x38, +0x3C, +0x40 | Three terminal stfs writes |

For source local vector (x,y,z), state orientation rows M0/M1/M2, and state translation T:

    transformed.x = fma(z,M2.x, fma(x,M0.x, y*M1.x))
    transformed.y = fma(z,M2.y, fma(x,M0.y, y*M1.y))
    transformed.z = fma(z,M2.z, fma(x,M0.z, y*M1.z))
    primitive.world = f32(transformed) + T

The original uses frsp on transformed components before the final translation, so host std::fma(float) approximates mathematical behavior but is not verified bit-identical under Wii FPSCR, denormals or rounding.

## New source-only implementation and tests

- wii_rigidbody_primitive.hpp/.cpp: WiiRigidBodyPrimitivePrepare, WiiPrimitiveLocalPosition, WiiPrimitivePreparedWorldPosition, and MakeWiiPrimitivePrepareCallback for the preexisting begin-frame API. Reads the explicit State argument, not an inferred RigidBody address. WriteVec3BE checks and atomically commits all three output floats.
- test_wii_rigidbody_primitive.cpp: synthetic tests for nonorthogonal matrix vs transpose errors; two local input vectors with distinct expected outputs; alternative explicit state address; two-node OnBeginFrame iteration BEFORE body displacement; status-2 inactive skip; direct failed output-span rejection; and rollback of an earlier node if a later node is unmapped.
- CMakeLists.txt now compiles the primitive helper into the host-native Windows/Linux physics library and creates a dedicated primitive regression CTest executable.
- pc_physics_smoke.cpp now uses a real synthetic primitive-list node instead of the previous empty sentinel and explicitly invokes MakeWiiPrimitivePrepareCallback. Every frame checks world position against the PRE-INTEGRATION state and emits prepared_primitive_x/y/z in the CSV output.
- The Wii research GitHub Actions workflow compiles the standalone primitive regression under Clang C++17 ASan/UBSan. The separate native host GitHub Actions builds and CTests on both Windows/MSVC and Ubuntu.

## Scope boundaries

This closes the previously unresolved Primitive::Prepare callback for the **base, directly named function**, but does NOT implement Primitive::SetCollision, UpdateCollider, DoWorldCollisions, vehicle steering, suspension, broadphase/contact forces, actual original-game geometry assets, or the PS2-specific layout. A prepared primitive world position is NOT by itself a complete collision system. No real Wii emulator trace comparison or bit-identical PPC floating-point result has been demonstrated.

All retail Wii/PS2 game executables and assets remain private. Check the head CI run before claiming the new Windows build or primitive tests are green.

Next: inspect SetCollision__Q29RigidBody9PrimitiveCFRCQ29RigidBody5StateRQ38Dynamics9Collision8Geometry at Wii 0x8030BD5C and isolate its source-backed geometry writes, then test collision-primitives against original owner-local emulator traces.
