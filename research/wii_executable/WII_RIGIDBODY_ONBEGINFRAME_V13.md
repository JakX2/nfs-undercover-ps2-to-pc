# Wii V13: RigidBody OnBeginFrame dispatch and gravity pipeline

**2026-11-11.** Read-only original Wii PowerPC ELF analysis. The new host implementation contains independently written C++17 and synthetic tests only. No original compiled code, game asset bytes, or retail files are committed.

## Direct integration caller

Named Wii symbol OnBeginFrame__9RigidBodyFf begins at **0x8030EC44** and spans **240 bytes**. At **0x8030ECB8** it directly calls DoIntegration__9RigidBodyFf at 0x8030F9C4, forwarding its float timestep.

Original PowerPC control flow:

| Address | Confirmed behavior |
|---|---|
| 0x8030EC6C–0x8030EC7C | Follow body +0x70 -> wrapper +0x00 -> state, OR 0x0400 into state +0x1C flags (big-endian u16) |
| 0x8030EC80–0x8030EC88 | State byte +0x5D == 2 skips primitive preparation and DoIntegration |
| 0x8030EC8C–0x8030ECAC | Otherwise follow the primitive intrusive list sentinel at body +0x104, call Prepare__Q29RigidBody9PrimitiveFRCQ29RigidBody5State at 0x8030BCB4 for each, then read the next pointer from the node +0x00 |
| 0x8030ECB0–0x8030ECB8 | Call DoIntegration with same timestep |
| 0x8030ECBC–0x8030ECD4 | Clear three force f32 slots state +0x50..+0x58 and three torque f32 slots +0x60..+0x68 for all statuses |
| 0x8030ECD8–0x8030ECE8 | Re-read state +0x5D; if zero, copy state u16 flags +0x1C to previous-flags slot +0x1E |
| 0x8030ECEC–0x8030ED0C | If flags bit 0x0002 is set, multiply mass (state +0x2C) by gravity (body +0x78 -> object +0xF0), and accumulate into force-Y state +0x54 with PPC fmadds |

### Critical frame timing

Gravity enters the force accumulator **after** the current integration and force reset. It is therefore available for a future step, rather than applied immediately to the already integrated velocity. A naive port that adds gravity directly to velocity in OnBeginFrame will break the observed update ordering.

The original status handling distinguishes 0 (active), 1 (the inactive DoIntegration zeroing path), and 2 (skip preparation/integration). The full lifecycle of statuses is not yet recovered.

## Original-free C++ adapter

New wii_rigidbody_frame.hpp/.cpp exposes ApplyRigidBodyOnBeginFrame using private, bounded Wii memory snapshots. It calls the V12 post-orientation integration stage, clears original force/torque fields, handles history flags and conditionally seeds gravity for the next step.

Original Primitive::Prepare is **not** yet reconstructed. The host wrapper requires an explicit WiiPrimitivePrepare callback for nonempty lists. It rejects missing callbacks, list cycles, bad Wii addresses and more than 4096 nodes; the original game's corrupt-memory behavior need not match. The complete stage uses copy-on-commit to prevent caller-visible partial writes on exceptions.

## Synthetic verification

The new test_wii_rigidbody_frame.cpp covers:
- Two consecutive active frames with mass=1000, inverse mass=.001 and gravity=-9.8, showing pending -9800 force is consumed in integration and then restored to force-Y for the next step.
- Status=2 retaining velocity and position while clearing accumulators; flags are set but history is not updated.
- Status=1 entering inactive integration and zeroing velocities.
- Two-node primitive list invoking two synthetic preparation callbacks before integration.
- Cyclic list and missing callback rejection with atomic rollback.

The GitHub Actions research workflow compiles this test with Clang C++17 AddressSanitizer and UBSan alongside the V12 matrix/center-of-gravity test, other physics/Attrib regressions and 37 original-free Python tests. Check the latest CI status before merging; the original ELF is not used by CI.

## Unrecovered dependencies

The original OnEndFrame__9RigidBodyFfb at **0x8030EA74** delegates to UpdateCollider (0x803151F4), possible DoWorldCollisions (0x80315538), DoDrag (0x8030ED34), and virtual callbacks. The primitive Prepare implementation and scheduler remain open. This is not a verified full car simulation, PS2-to-Wii function match, or playable native PC build.
