# Wii Undercover V6: reconstructed RigidBody state flags and bounded setters

**2026-11-10.** The owner's unstripped Wii PowerPC `NfsMWRelease.elf` was examined with `llvm-objdump` and the existing verified named-symbol map. This milestone adds independent, synthetic-only C++17 tests and safe host-memory state transitions. It does **not** alter a Wii executable, patch an emulator, or implement the complete vehicle physics engine.

## Original assembly anchors

These are addresses in the original Wii PowerPC ELF. Read and write locations below are original game-side memory offsets, not portable C++ struct offsets.

| Named function | Wii entry | Observed behavior |
|---|---|---|
| `GetForce__9RigidBodyCFv` | `0x80300FAC` | Returns state pointer +`0x50` via body+`0x70` -> wrapper +`0x00` |
| `SetForce__9RigidBodyFRCQ25UMath7Vector3` | `0x80300FE0` | Stores 3 float32 words to state+`0x50,+0x54,+0x58` |
| `GetTorque__9RigidBodyCFv` | `0x80300F9C` | Returns state pointer +`0x60` |
| `SetTorque__9RigidBodyFRCQ25UMath7Vector3` | `0x80300FBC` | Stores 3 float32 words to state+`0x60,+0x64,+0x68` |
| `SetAnchored__9RigidBodyFb` | `0x80301050` | Sets or clears bit `0x0080` in a big-endian u16 at state+`0x1C`, leaving other flags unchanged |
| `IsAnchored__9RigidBodyCFv` | `0x80301088` | Tests that same `0x0080` bit |
| `HasHadPassiveCollision__9RigidBodyCFv` | `0x803010B0` | Returns the state+`0x1C` flag bit `0x1000` |
| `HasHadWorldCollision__9RigidBodyCFv` | `0x803010C4` | Returns flag bit `0x0004` |
| `HasHadCollision__9RigidBodyCFv` | `0x803010D8` | Tests nonzero `flags & 0x000C` |
| `GetNumContactPoints__9RigidBodyCFv` | `0x8030100C` | Reads state+`0x5C` byte and explicitly sign-extends it |
| `IsInGroundContact__9RigidBodyCFv` | `0x80301020` | Tests the same sign-extended contact byte for nonzero |
| `IsSleeping__9RigidBodyCFv` | `0x80301114` | Returns state byte at `+0x5D == 1` |
| `IsModeling__9RigidBodyCFv` | `0x80301134` | **Returns state byte at `+0x5D != 2`**, despite its counterintuitive name. This follows two subtracts, bitwise OR and high-bit extraction |
| `GetMass__9RigidBodyCFv` | `0x8030117C` | Reads float32 at state+`0x2C` |
| `GetGravity__9RigidBodyCFv` | `0x80300F90` | Dereferences body+`0x78` to a separate object, reads float32 at that object's `+0xF0` |
| `GetCenterOfGravity__9RigidBodyCFv` | `0x80301174` | Returns direct pointer body+`0xE4`, not state+`0xE4` |
| `SetCenterOfGravity__9RigidBodyFRCQ25UMath7Vector3` | `0x803010F8` | Writes three float32 words directly to body+`0xE4,+0xE8,+0xEC` |

The original vector stores use PowerPC `stfs`; the state flags use `lhz/sth`, and the read-only status methods use byte loads. Bit extraction was checked against the PPC `rlwinm` semantics. No behavior not visible in this fragment has been inferred, e.g., whether these fields drive simulation or how the update loop consumes force/torque.

## Original-free implementation and test scope

Files:
- `wii_rigidbody_controls.hpp/.cpp`: read-only decoded flags, contacts, status, mass and gravity plus a `WiiMutableSnapshot` that **copies and owns** synthetic/private Wii memory regions.
- `test_wii_rigidbody_controls.cpp`: synthetic positive/negative states, 32-bit Wii big-endian f32 readback, force/torque and center-of-gravity stores, anchor on/off/idempotence, collision mask distinctions, sign-extended contact values `0xFF=-1` and `0x80=-128`, state values 1 and 2, invalid/null pointers and atomic rejection of split/unmapped writes.

The host implementation uses the existing bounded WiiAddressSpace validator. An attempted vector write must fit wholly inside **one** region before any bytes are changed. Unlike the original PPC stores, the host adapter rejects malformed addresses with C++ exceptions. It does not write files or connect to another process. The `WiiMutableSnapshot` is **not** an emulator-memory modification tool.

The GitHub Actions workflow compiles the test with Clang, C++17, `-Wall -Wextra -Wpedantic -Werror`, and `-fsanitize=address,undefined`. It also runs the earlier **37** source-free Python ELF/DOL/call-graph tests and other C++ tests. Check the latest PR status before merging.

## Next integration gate

The V5 RigidBody velocity/speed read path plus these V6 field setters now provide a bounded interface to selected Wii physics-state data. The next genuine engine-reconstruction task is to locate the **named simulation update/integration function** that consumes stored force/torque, infer its time-step and mass normalization, and verify state changes in an owner-local Wii emulator trace. No car simulation, collision resolver, steering, suspension, road streaming or native PC gameplay implementation has been proven.

No copyright-protected game binary or original function body is committed.
