# Wii V20: RigidBody::Detach flag and owner-event dispatch

**2026-11-11.** Wii ELF original PowerPC disassembly used as read-only evidence.
All committed C++17 code and tests are independently written, source-only,
and operate on private bounded Wii memory snapshots. No original executable,
proprietary assets, binaries or extracted code bodies are committed.

## Identified original Wii functions and control flow

- `Detach__9RigidBodyFv`: **0x8030E46C**, **160 bytes**.
- `GetOwner__9RigidBodyCFv`: **0x802F7A68**, **8 bytes**, identified by
  the original `__vt__9RigidBody` slot **+0x2E4**.
- `Sim::GetTime`: **0x80378E60**, directly called from Detach.

The original `Detach` routine follows RigidBody+0x70 ->
wrapper+0x00 -> state and loads the flags as big-endian u16
from state+0x1C. The exact PowerPC branch at 0x8030E488
tests flag **0x0002**.

| Original Wii instruction range | Verified action |
|---|---|
| 0x8030E488–0x8030E48C | If bit 0x0002 absent, return with no effects |
| 0x8030E490–0x8030E498 | Clear only bit 0x0002 with rlwinm, store new state flags |
| 0x8030E49C–0x8030E4A8 | Invoke body vtable +0x2E4, base method `GetOwner` (reads body+0x2C) |
| 0x8030E4AC–0x8030E4B8 | Invoke owner vtable +0x7C, obtain a linked object pointer |
| 0x8030E4BC–0x8030E4C4 | If returned linked object is null, exit without event |
| 0x8030E4C8–0x8030E4D0 | Write event constant **0xC91B90D9** into stack local |
| 0x8030E4D4 | Call `Sim::GetTime`; return value is not subsequently used in this routine |
| 0x8030E4D8–0x8030E4F4 | Call linked object vtable +0x3C with stack-event pointer and fixed trailing integers **0** and **2** |

The event constant is derived exactly from original PPC `lis` and
signed `addi`, not a guessed tag. We **do not infer** its domain
meaning, which owner method +0x7C represents, or the side effects
of the unknown linked-object virtual +0x3C.

The original routine does **not** guard against a null owner before
dereferencing its vtable. The portable host adapter deliberately rejects
a null owner as an exception instead of emulating a crash.

## Portable reconstruction

- `wii_rigidbody_detach.hpp/.cpp` adds
  `WiiRigidBodyBaseDetach`, `WiiDetachCallbacks`, and `WiiDetachResult`.
- The base-class owner accessor is implemented directly as the verified
  read of body+0x2C. Runtime derived vtable overrides remain unresolved.
- Virtual owner+0x7C, Sim::GetTime and linked+0x3C dispatches are
  **required host callbacks only when those branches execute**. Missing
  callbacks throw, preventing the caller from interpreting missing game
  logic as a legitimate no-op.
- The full operation is performed on a deep-copied
  `WiiMutableSnapshot`; changes are committed only after successful
  completion. This is a deliberate host-side safety adaptation.

## Original-free verification

`test_wii_rigidbody_detach.cpp` tests:

1. Flag 0x0002 absent: strict no-op and no required callbacks.
2. Flag present: clear before owner callback, then owner resolution,
   simulated Sim time and linked-object event in original order,
   with exact constant and trailing event parameters.
3. Linked-object null: return after clearing the flag, without
   Sim::GetTime or event callback.
4. Integration with prior `RigidBody::ResolveForce`: it first ORs
   flag 0x0040 then invokes Detach, which clears 0x0002 before
   the three-float accumulator is updated.
5. Null owner, missing callback and throwing event handler leave the
   original host snapshot unchanged.

The dedicated research CI compiles this test under **Clang C++17
AddressSanitizer/UBSan** in addition to the earlier 37 original-free
Python ELF/call-graph controls, the standalone V18 drag tests, and
the V19 two-frame integration test. The original Wii file is not
loaded in CI. Review the latest commit's CI result before merge.

## What remains unresolved

Derived owner vtable identity, linked-object class and event meaning,
`Sim::GetTime` side effects, the actual game world/suspension
collision system, exact PowerPC numerical mode and real Wii
emulator differential are not yet reconstructed. The V18 drag path
now has a source-backed base Detach behavior available through
a caller-supplied wrapper, but derived classes must still be treated
as distinct until validated.

**This source-only branch is not a native playable PC port.**
