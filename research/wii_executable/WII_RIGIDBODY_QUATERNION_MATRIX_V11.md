# Wii V11: Quaternion normalization and orientation matrix

**2026-11-11.** Read-only original-source inspection of owner Wii NfsMWRelease.elf. All new C++ and tests are independently written. No original game binary, compiled function bodies, game archives or resource payloads are committed.

## Original PowerPC evidence

In DoIntegration__9RigidBodyFf (Wii address 0x8030F9C4, size 0x744), V10 ends at 0x8030FCF0 after the final linear/angular clamp. The contiguous next original block is:

- **0x8030FCF4–0x8030FD14:** compute the square sum of clamped angular velocity at state +0x30, +0x34, +0x38. The fcmpu zero-equality branch skips quaternion and orientation-matrix updates if this sum is zero, transferring control to 0x8030FE74.
- **0x8030FD18–0x8030FE24:** multiply the angular vector by timestep, then update the state quaternion (x,y,z,w) at +0x00, +0x04, +0x08, +0x0C. Cross terms prove omega-times-quaternion orientation, not the reverse operand order. The leading scalar is exactly 0.5f (original r2-24520, IEEE-754 0x3F000000).
- **0x8030FE28–0x8030FE6C:** sqrt-based quaternion normalization, then writes of all four normalized float32 components. Constant 1.0f (r2-24540) is used as reciprocal numerator.
- **0x8030FE70:** invokes VU0_quattom4__FRCQ25UMath7Vector4RQ25UMath7Matrix4 at Wii 0x8023480C (0xF0 bytes), generating the 16-float matrix at state +0x70. Despite the legacy VU0 function name, this Wii helper is plain PowerPC float instructions. The original 4x4 layout was checked through its direct stfs output offsets.

Original per-component orientation update with omega already multiplied by timestep:

~~~text
dx = omega.x*q.w + omega.y*q.z - omega.z*q.y
dy = omega.y*q.w + omega.z*q.x - omega.x*q.z
dz = omega.z*q.w + omega.x*q.y - omega.y*q.x
dw = -(omega.x*q.x + omega.y*q.y + omega.z*q.z)
q += 0.5 * (dx,dy,dz,dw)
q /= sqrt(q.x*q.x + q.y*q.y + q.z*q.z + q.w*q.w)
~~~

The original matrix output in 4x4 row-style memory order:

~~~text
1-2(y*y+z*z)      2(x*y+z*w)       2(x*z-y*w)       0
2(x*y-z*w)        1-2(x*x+z*z)     2(y*z+x*w)       0
2(x*z+y*w)        2(y*z-x*w)       1-2(x*x+y*y)     0
0                 0                0                1
~~~

The original helper uses 0.0f, 1.0f and 2.0f constants verified in Wii .sdata2.

## New original-free host implementation

- wii_rigidbody_orientation.hpp/.cpp: read the Wii state XYZW quaternion, read its 4x4 matrix, rebuild the orientation matrix, and apply the source-backed quaternion update after the V10 phase.
- WiiMutableSnapshot now has atomic 4-float and 16-float big-endian snapshot writers. They reject unaligned, incomplete or unmapped Wii-address spans. All V11 stages use copy-on-commit to avoid exposing partial host writes if later validation fails.
- test_wii_rigidbody_orientation.cpp: original-free identity and z-rotation sign controls, nonzero angular step for dt=0.5 and omega=(0,0,2), expected normalized quaternion and 4x4 matrix, zero-angular skip, inactive-state skip, rejected zero quaternion, missing matrix rollback.

### Qualification

Host std::fma and std::sqrt approximate, but do not prove exact Wii PPC FPSCR or rounding behavior; the adapter explicitly rejects zero/nonfinite quaternion norm rather than producing a nonfinite stored matrix. The original game's complete runtime has not been executed or differentially tested. The V11 slice stops immediately after original 0x8030FE70. Subsequent matrix and body-state handling from 0x8030FE74 onward is not reconstructed. This is NOT a complete vehicle simulation, nor a native PC game.

The branch's GitHub Actions workflow compiles and sanitizer-tests this code alongside the existing V10 controls and 37 source-free Python ELF/call-graph checks. The owner ELF is not needed in CI.

**Next:** recover the post-quaternion matrix combination and verify it with owner-local Wii emulator traces before claiming full engine-frame integration.
