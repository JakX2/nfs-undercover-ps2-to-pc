# Wii V14: RigidBody OnEndFrame lifecycle and collision dispatch

**2026-11-11.** Owner-original Wii PowerPC NfsMWRelease.elf was examined read-only by llvm-objdump. Only independently authored C++17 and original-free synthetic tests are committed. The original binary, resource data and extracted function bytes remain private.

## Source-backed PowerPC observations

The original OnEndFrame__9RigidBodyFfb is at **0x8030EA74**, size **0xF8** bytes. It receives a float timestep and a collision-pass boolean and follows body+0x70 -> wrapper+0x00 -> state.

| Wii instruction range | Verified control flow |
|---|---|
| 0x8030EA98–0x8030EAAC | State+0x5D == 0 takes active collision/drag branch; all other values take world-position synchronization |
| 0x8030EAB0–0x8030EAB4 | Only if caller boolean true, call UpdateCollider at 0x803151F4 |
| 0x8030EAB8–0x8030EAC0 | Clear state flags+0x1C bit 0x0004 AFTER collider update |
| 0x8030EAC4–0x8030EAD0 | Read body+0xE0 collider and call WCollider::IsEmpty at 0x80406778 |
| 0x8030EAD4–0x8030EAE0 | If collider nonempty, call DoWorldCollisions at 0x80315538 with 2.0f multiplied by timestep |
| 0x8030EAE4–0x8030EAE8 | Call DoDrag at 0x8030ED34 regardless of collision-pass boolean on the active path |
| 0x8030EAEC–0x8030EB10 | Call virtual +0x3AC, resolved in RigidBody base vtable to ShouldSleep at 0x80315D18; if true set state+0x5D to 1. Derived override still possible. |
| 0x8030EB14–0x8030EB24 | For nonzero state: body+0x2C object, virtual slot +0x50 resolves world-position object |
| 0x8030EB28–0x8030EB3C | Call WWorldPos::Update at 0x80425B8C with state+0x10, body+0xC4, boolean true, null collider, boolean true |
| 0x8030EB40–0x8030EB48 | Both paths clear processing flag 0x0400 from state flags+0x1C |

The r2-relative original float at displacement -24524 is exactly 2.0f (IEEE bits 0x40000000). The original PPC rlwinm instruction masks at 0x8030EABC and 0x8030EB44 establish that the cleared flag bits are respectively 0x0004 and 0x0400.

## New portable code

- wii_rigidbody_endframe.hpp/.cpp: ApplyRigidBodyOnEndFrame with an explicit WiiEndFrameCallbacks interface. All unknown original methods are represented as caller-supplied callbacks; they are **not reimplementations** of collision, drag or position synchronization.
- WiiMutableSnapshot::WriteU8: a bounded host-owned synthetic Wii state-byte write, never an emulator/process patch.
- One private copy-on-commit transaction: callback failure, invalid Wii address, or a missing callback on an invoked branch leaves the caller snapshot unchanged.
- WiiEndFrameResult exposes original branch decisions and final status/flags to tests. The base Wii RigidBody vtable resolves callback should_sleep to the named ShouldSleep method; see WII_RIGIDBODY_SHOULDSLEEP_V15.md. Host injection remains necessary when derived-class overrides are unknown.

## Original-free tests

test_wii_rigidbody_endframe.cpp verifies full active call order and 2x timestep; the collision boolean false and empty-collider paths; status values 1/2/255 using world-position synchronization; original flag clearing order; virtual status transition to 1; null interfaces and missing callbacks; exception-safe rollback; and bounded byte writes.

The dedicated GitHub Actions workflow builds/tests under Clang C++17 ASan/UBSan along with the earlier V13 controls and 37 synthetic Python PowerPC/ELF tests. No original game data is used by CI. A passing synthetic test proves the host control-flow contract, NOT exact in-game runtime equivalence.

## What remains

Original DoDrag at Wii 0x8030ED34 is longer, involving multiple flag gates, rsqrt calculations and virtual calls. Its behavior is deliberately not guessed by V14. UpdateCollider, DoWorldCollisions and world-position update remain opaque. The base virtual +0x3AC ShouldSleep is now separately reconstructed in V15, but runtime derived overrides remain open. Next step: isolate drag subpaths with verifiable force/torque behavior, then compare owner-private Wii emulator memory traces with host results. The complete physics engine, PS2 MIPS reconciliation and playable native PC port remain unfinished.
