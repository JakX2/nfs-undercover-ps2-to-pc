# Wii V19: two-frame rigid-body motion/drag integration test

**2026-11-11.** This milestone combines original-free C++ reconstructions
from earlier Wii PowerPC ELF analysis into an end-to-end **synthetic**
physics frame. The owner's original Wii executable is read-only evidence,
not an input to this test or a distributed artifact.

## Confirmed original scheduling and restored dependencies

- `RigidBody::OnBeginFrame` at Wii **0x8030EC44** calls
  `RigidBody::DoIntegration` at **0x8030F9C4**, then clears force and
  torque and optionally queues gravity for a future step.
- `RigidBody::OnEndFrame` at **0x8030EA74** calls `DoDrag` at
  **0x8030ED34** for an active body, then invokes a virtual
  `ShouldSleep` implementation.
- `DoDrag` uses both angular and linear drag branches, passes the
  calculated vectors through world/local conversion, and calls
  `ResolveTorque` and `ResolveForce`.
- The original base implementations of `ResolveTorque` and
  `ResolveForce` wake eligible rigid bodies and call `Detach`,
  whose behavior remains **injected and unresolved**.

## New original-free test

`test_wii_rigidbody_pipeline.cpp` creates a private, bounded,
big-endian Wii address-space fixture containing an active body,
original field offsets, identity body/orientation matrices, a unit
quaternion, a primitive-list sentinel, original body axis dimensions
(1,2,3), speed (3,4,0), angular velocity (0,3,4), inverse mass 0.01,
and synthetic environment drag coefficients.

It then executes:

1. **Frame one begin**: original source-backed state integration with
   zero pending force, proving the initial velocity is unchanged.
2. **Frame one end**: call V14 OnEndFrame with its DoDrag callback set
   to the new V18 reconstruction and the ShouldSleep callback set to
   the previously recovered Wii base predicate. With collision pass
   disabled, drag accumulates source-backed negative force and torque,
   but does **not** retroactively change already integrated velocity.
3. **Frame two begin**: original source-backed integration consumes the
   queued force and torque, updating velocity and orientation before
   zeroing the accumulators. Assertions check the prior-frame force
   contribution to velocity and that accumulator clearing occurred.
4. **Frame two end**: computes the next aerodynamic force based on
   the newly integrated motion and verifies drag invocation and
   additional Detach callbacks.
5. **Global inhibit control**: original bit 0x0002 suppresses both
   drag paths, while the end-frame dispatcher still invokes `DoDrag`.
   The begin-frame gravity code is also invoked independently.

All vehicle state is synthetic and private. Original-free tests
intentionally use a **no-op injected Detach** solely to isolate the
frame timing. This does not mean real game Detach or downstream
vehicle suspension behavior is proven unnecessary. Similarly,
the original primitive list is empty, and world collisions,
WWorldPos updates and derived-class overrides are not run.

The GitHub Actions Wii research workflow compiles this integration
test under **Clang C++17, AddressSanitizer and UBSan** alongside
the standalone V18 drag and earlier native/synthetic controls.
Confirm the newest workflow conclusion before treating the
integration target as validated.

## Boundaries and future work

This proves the combined **host-side synthetic pipeline**, not that
the original Wii body produces numerically identical results for
all states. Original Dolphin memory traces, PPC FPSCR behavior,
derived vehicle vtable targets, Detach, tire forces, collision solver,
suspension, player controls and the game-level update scheduler
remain outside current coverage.

The PS2 Emotion Engine executable is a separate stripped MIPS code
reference; the Wii PowerPC field offsets must **not** be assumed to
match it. No playable PC port is claimed.
