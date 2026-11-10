# Wii Undercover V7: first state-changing prefix of RigidBody::DoIntegration

**2026-11-10.** Reconstructed from the owner-original, symbol-rich Wii PowerPC `NfsMWRelease.elf` through read-only disassembly. No retail program code, binary bytes, games or executable patch is included. This is an **isolated prefix**, not the full 1,856-byte `RigidBody::DoIntegration` implementation.

## Original instruction witness

The original Wii symbol `DoIntegration__9RigidBodyFf` starts at `0x8030F9C4` and has `0x744` bytes. Following the standard prologue, the observed first branch at `0x8030F9F4..0x8030FA24`:

1. Dereferences `RigidBody +0x70 → wrapper +0x00 → state`.
2. Reads unsigned state byte `+0x5D`.
3. **If nonzero:** writes six zero u32 words to the two three-float spans at state `+0x20,+0x24,+0x28` and `+0x30,+0x34,+0x38`, then jumps directly to the function epilogue at `0x803100D8`. The source branch tests *nonzero*, not specifically sleeping state value 1.

**If the byte is zero**, the original beginning at `0x8030FA28` computes a float32 scale from the caller timestep and state inverse mass at `+0x3C`, then updates:

~~~text
scale = timestep * state.inverse_mass
state.vel.x = fma(state.force.x, scale, state.vel.x)
state.vel.y = fma(state.force.y, scale, state.vel.y)
state.vel.z = fma(state.force.z, scale, state.vel.z)
~~~

The observed velocity destination words are `+0x20,+0x24,+0x28`, and previously reconstructed force slots are `+0x50,+0x54,+0x58`. The original uses PPC `fmuls` and `fmadds`. The third velocity store is at `0x8030FAD8`. This is only the start of a much larger routine, which subsequently computes torque/orientation, translation, clamping and other state updates. **We have not reconstructed those later operations.**

## Portable, deliberately limited adapter

`ApplyDoIntegrationVelocityPrefix(WiiMutableSnapshot&, uint32_t, float)` returns a path enum:

- `inactive_cleared`: state byte is nonzero; writes six zero float32 slots.
- `active_velocity_updated`: state byte is zero; performs only the three linear-velocity fused multiply-add operations.

A **copy-on-commit** mechanism ensures that if any snapshot write span is malformed, the caller's original synthetic snapshot stays unchanged. The host uses C++ `std::fma`, but different host/compiler floating-point environments and the lack of PPC FP-mode control prevent any claim of bit-identical behavior. The update deliberately does not simulate an entire frame.

Added original-free regressions:

- The test's state with timestep 0.25, inverse mass 0.5, starting velocity (10,20,30), force (2,4,6) must produce (10.25,20.5,30.75) by the verified prefix.
- State bytes 1 and 2 take the nonzero branch and clear the two spans, preserving the force vector.
- Sparse-region second-write failure rolls the host snapshot back to its original bytes.

The V6 state flag/force/torque tests and earlier `37` synthetic Python ELF/DOL/call graph tests are retained in CI. The new prefix test is added to the existing Clang C++17 AddressSanitizer/UBSan `test_wii_rigidbody_controls.cpp` target.

## Next step toward genuine gameplay

Continue within the same `0x744` byte function to recover the torque/angular integration, translation and clamps. A future Wii emulator trace should compare actual pre- and post-step memory against host outputs, under the same input and floating-point conditions. To construct a native PC physics loop, we will also need the owner-original scheduler, suspension, collision, timing and input paths.

This V7 work demonstrates **a verified first slice of the vehicle integration algorithm**, not a complete physics tick, playable Windows build or PS2 matching decompilation.
