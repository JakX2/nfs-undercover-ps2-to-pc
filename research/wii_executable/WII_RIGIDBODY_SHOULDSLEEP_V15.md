# Wii V15: RigidBody::ShouldSleep recovered from original vtable and PPC code

**2026-11-11.** Read-only original Wii NfsMWRelease.elf inspection.
New C++17 source and original-free tests only; original Wii executable bytes
and assets remain private.

## Proven virtual method identities

The original ELF symbol __vt__9RigidBody is at **0x805A8438**, length
**0x3C8** bytes. Its actual 32-bit big-endian function-pointer entries
establish both target identities:

| Vtable byte offset | Pointer value | Named function |
|---|---|---|
| +0x3AC | 0x80315D18 | ShouldSleep__9RigidBodyCFv (196 bytes) |
| +0x298 | 0x8030100C | GetNumContactPoints__9RigidBodyCFv |

V14 OnEndFrame invokes virtual +0x3AC and sets state byte +0x5D to 1
if the return value is nonzero. Thus the base-class implementation
is **definitively RigidBody::ShouldSleep**, not an anonymous heuristic.
The body may have a derived-class vtable at runtime: the base entry
does not prove that every dynamic rigid-body instance uses this exact
implementation.

## Original Wii ShouldSleep control flow

The original implementation at **0x80315D18..0x80315DD8**:

1. Follow body +0x70 -> wrapper +0x00 -> state.
2. Compute the Euclidean magnitude of angular velocity from state
   +0x30/+0x34/+0x38, calling rsqrt at 0x80232544 (despite its name,
   this helper returns an **approximate square root**).
3. Compute the Euclidean magnitude of linear velocity from state
   +0x20/+0x24/+0x28 with the same helper.
4. Read f32 body radius at state +0x6C and environment pointer
   body +0x78 -> environment f32 sleep-motion threshold at +0xE0.
5. At 0x80315D84 use fmadds to compute:

   motion = linear_speed + radius * angular_speed

6. Use fcmpo to check **motion strictly less than threshold**.
   Equality, greater-than or unordered returns false without calling
   the contact accessor.
7. If the threshold comparison passes, invoke virtual +0x298 and
   compare its return against **2 using UNSIGNED cmplwi**. True
   only if the comparison is greater-than.

GetNumContactPoints originally reads a byte at state +0x5C and
sign-extends it. The unsigned follow-up comparison means even an
anomalous signed value -1 is interpreted as 0xFFFFFFFF (>2) in the
base Wii implementation. This subtle behavior is preserved by the
host reconstruction rather than silently replacing it with a signed
comparison.

### Mathematically

~~~text
angular_speed = approximate_sqrt(wx*wx + wy*wy + wz*wz)
linear_speed  = approximate_sqrt(vx*vx + vy*vy + vz*vz)
motion = linear_speed + (body_radius * angular_speed)
return motion < env_sleep_threshold
    && uint32(sign_extended_contact_count) > 2
~~~

The original rsqrt helper tests against f32 bits 0x2E5BE6FF,
about 5e-11, and returns zero for nonpositive/tiny/unordered
squared inputs. The PC implementation uses std::sqrt above the
same threshold but cannot claim bit-accurate Wii reciprocal-square-
root refinement or FPSCR behavior.

## Portable reconstruction

- wii_rigidbody_sleep.hpp/.cpp: WiiRigidBodyBaseShouldSleep reads only
  bounded, big-endian 32-bit Wii memory snapshots. It reuses previous
  V5/V6 velocity, radius and signed contact accessors.
- test_wii_rigidbody_sleep.cpp: synthetic tests cover a known angular
  magnitude 5 and linear magnitude 10, radius=2 and motion=20;
  strict inequality at threshold 20; contact counts 0..8;
  unsigned handling of signed contact bytes 0xFF and 0x80;
  zero/tiny motions; threshold NaN/infinity; Wii rsqrt unordered
  input fallback; and missing environment pointer.
- Dedicated Clang C++17 ASan/UBSan CI target runs with the earlier
  original-free Python and C++ tests. No original executable loaded.

Do NOT automatically substitute this base implementation for the
V14 injected callback when the actual dynamic rigid-body vtable is
unknown. It is now available as a source-backed callback for base
instances and as a reference for identifying derived overrides.

## Next gate

Decode the concrete dynamic class/vtable assignment for common
vehicle rigid bodies and inspect derived overrides. Continue
the gated DoDrag numerical paths from the V15 preflight. A true
Wii emulator state trace remains necessary to test floating-point
and gameplay equivalence; this is not yet a complete native PC
collision/drag/vehicle engine.
