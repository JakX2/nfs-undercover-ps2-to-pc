# Wii V16: ResolveForce, ResolveTorque and local-to-world vector transform

**2026-11-11.** Independently authored C++17 reconstruction, anchored by
read-only analysis of the owner's original PowerPC Wii ELF.
The original ELF, proprietary instruction bytes and game resources are NOT
published.

## Wii RigidBody base-vtable call target resolution

The original ELF contains \`__vt__9RigidBody\` at **0x805A8438**.
Directly reading its 32-bit big-endian pointer entries produces:

| Base vtable slot | Original function pointer | Name from ELF |
|---|---|---|
| **+0x388** | **0x8030F27C** | \`ConvertWorldToLocal__9RigidBodyCFRQ25UMath7Vector3b\` |
| **+0x384** | **0x8030F1B4** | \`ConvertLocalToWorld__9RigidBodyCFRQ25UMath7Vector3b\` |
| **+0x364** | **0x8030F4E4** | \`ResolveTorque__9RigidBodyFRCQ25UMath7Vector3\` |
| **+0x360** | **0x8030F570** | \`ResolveForce__9RigidBodyFRCQ25UMath7Vector3\` |

These four exact slot offsets are used inside \`DoDrag__9RigidBodyFv\`
(0x8030ED34) in the Wii original. **Derived-class vtables may override
the targets**; this proves the base implementation, not every runtime
instance. The second, 0x8030F5FC ResolveTorque overload has an additional
vector parameter and is not the +0x364 vtable target.

### Reconstructed ResolveForce and ResolveTorque behavior

Source functions:

- \`ResolveForce__9RigidBodyFRCQ25UMath7Vector3\` at **0x8030F570** (140 bytes)
- \`ResolveTorque__9RigidBodyFRCQ25UMath7Vector3\` at **0x8030F4E4** (140 bytes)

Both follow body+0x70 -> wrapper+0x00 -> state and execute:

1. Check state byte+0x5D **equal to 2**. If so, return immediately:
   neither state nor force/torque accumulators are touched.
2. Otherwise write zero to state byte+0x5D and OR **0x0040**
   into the 16-bit flags at state+0x1C.
3. Call \`Detach__9RigidBodyFv\` at **0x8030E46C**, even if state
   was already zero. The original saves the state pointer in r31
   before the call.
4. Add the three incoming floating-point components to the
   **post-Detach** accumulator, at state+0x50..+0x58 for force
   or state+0x60..+0x68 for torque.

The full \`Detach\` behavior includes virtual interactions and a
flag-dependent branch that remain unreconstructed. The portable
functions therefore REQUIRE an explicit \`WiiDetach\` callback only
on their active branch, rather than silently pretending it is a no-op.
They preserve Wii pointer/state ordering, but use safe host owned
snapshots and copy-on-commit. C++ exceptions intentionally differ
from original PPC hardware failures.

### Reconstructed ConvertLocalToWorld

The original \`ConvertLocalToWorld\` at **0x8030F1B4** (200 bytes)
reads the upper-left 3x3 part of the state orientation matrix at
state+0x70. For each output, the source PC order starts with an
input-Y multiply, FMA input-X, then FMA input-Z. With the optional
boolean argument true, it adds state position at +0x10..+0x18.
With the boolean false, it does not read or add position.

The original overwrites the input vector in place. The new portable
\`WiiRigidBodyBaseConvertLocalToWorld\` returns a value, while
preserving the vector formula and conditional translation on valid
synthetic memory. It reads exactly the nine source matrix words,
not unnecessary fourth-row/column words.

Original \`ConvertWorldToLocal\` at **0x8030F27C** has NOT yet been
fully reconstructed. It begins with optional translation removal and
then transforms a vector with a transposed 4x4 matrix. The later loop
and temporary-alias behavior require independent validation.

## Newly committed C++ source and regression controls

- \`wii_rigidbody_resolve.hpp/.cpp\`: base-class wake-state and
  force/torque accumulator operations with explicit Detach callback.
- \`test_wii_rigidbody_resolve.cpp\`: source-order callback and status
  checks, post-callback accumulator arithmetic, repeated active call
  semantics, strict state 2 no-op, missing callback and exception
  rollback tests.
- \`wii_rigidbody_transform.hpp/.cpp\`: nine-word 3x3 local-to-world
  transform with optional position.
- \`test_wii_rigidbody_transform.cpp\`: synthetic identity, original
  quaternion Z-rotation sign convention, translation on/off,
  sparse three-row Wii memory layout, and malformed address checks.

Both new C++ test binaries are included in the existing research
GitHub Actions workflow under Clang C++17 AddressSanitizer and UBSan,
alongside the earlier **37 original-free Python** format/call tests.
Original retail data is never loaded in CI. Only cite the exact
latest workflow conclusion after it completes.

## Next gates

1. Recover \`ConvertWorldToLocal\` precisely, including its inplace
   matrix transpose, optional translation and stack-buffer cases.
2. Recover the pure arithmetic and dispatch sequencing inside both
   \`DoDrag\` flag-gated paths, now that all four virtual slots have
   source-backed base identities. Keep float rounding approximation
   and derived-class dispatch explicit.
3. Recover \`Detach\`, or at least isolate its first branch with
   vtable targets; maintain the callback contract otherwise.
4. Test original emulator input/output states before declaring
   behaviorally exact drag, physics integration or vehicle handling.

This V16 milestone does not provide a complete drag system,
full PC-native car simulation, original Wii ABI or playable port.
