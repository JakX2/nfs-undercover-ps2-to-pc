# Wii V18: two numerical DoDrag branches and source-backed virtual dispatch

**2026-11-11.** Independently written portable C++17 under
`research/wii_executable/`, derived by **read-only disassembly** of
the owner's original Wii PowerPC `NfsMWRelease.elf`. No retail
executable bytes, original function body, resource archives or game assets
are committed. This is a research reconstruction, **not** a proven
bit-identical Wii port or a playable native Windows game.

## Source symbol and early flags

`DoDrag__9RigidBodyFv` begins at **0x8030ED34** (1152 bytes) and
returns at 0x8030F1B0. It dereferences body +0x70 -> wrapper +0x00
to obtain the state pointer in r30. The flags at state+0x1C are
loaded as an unsigned 16-bit halfword.

| Original PowerPC address | Control flow |
|---|---|
| 0x8030ED58 | If bit **0x0002** set, return before both paths |
| 0x8030ED60 | If bit **0x0800** set, compute and dispatch angular drag |
| 0x8030EFF0 | **Re-read** state+0x1C after angular virtual callbacks |
| 0x8030EFF4 | If new flags have bit **0x0020**, compute linear drag |

A subtlety: the original does **not** test bit 0x0002 again after
the first path. If the torque-resolution callback sets bit 0x0002
and 0x0020, the linear path is still reached. The new host
implementation explicitly re-reads the original retained state
address, not an entry-time copy, before selecting that second path.

## Original source fields and constants

- **Angular input:** state+0x30/+0x34/+0x38, copied into a stack
  vector before the first virtual `ConvertWorldToLocal(...,false)`.
- **Linear input:** state+0x20/+0x24/+0x28, read immediately before
  the second virtual `ConvertWorldToLocal(...,false)`.
- **Three body dimensions:** float32 body+0xD4,+0xD8,+0xDC.
- **Angular coefficients:** body+0x78 -> environment object, float32
  environment+0x60,+0x64,+0x68.
- **Linear coefficients:** same environment, float32 +0x70,+0x74,+0x78.
- **Original .sdata2 constants:** 4.0f, -0.5f, approximately
  1.225f (exact f32 bits 0x3F9CCCCD), and the positive
  squared-length cutoff 0x2E5BE6FF (approximately 5e-11).
- **Vector magnitude helper:** the original `rsqrt` at
  0x80232544 returns an approximate **square root**, not
  the reciprocal. For nonpositive, tiny or unordered squared
  input it returns zero.

The original code's four virtual slots in the RigidBody base
vtable were identified in V16:

- `+0x388` -> `ConvertWorldToLocal` (0x8030F27C)
- `+0x384` -> `ConvertLocalToWorld` (0x8030F1B4)
- `+0x364` -> `ResolveTorque` (0x8030F4E4)
- `+0x360` -> `ResolveForce` (0x8030F570)

**Derived Wii rigid-body classes can override these slots**. The
new host code therefore injects all four, and includes a separate
`MakeWiiBaseDragCallbacks` adapter using the previously
reconstructed base functions. Active base-class ResolveForce/
ResolveTorque still require the original `Detach` effects as
an explicit host callback.

## Source-inferred drag calculations

With body axis lengths `d=(dx,dy,dz)`, angular-local vector
`a`, linear-local vector `v`, and environment coefficients
`c_angular` and `c_linear`:

~~~text
angular_area = (
    4*dx*sqrt(dy*dy + dz*dz),
    4*dy*sqrt(dx*dx + dz*dz),
    4*dz*sqrt(dx*dx + dy*dy)
)

local_angular_drag[i] =
    a[i] * angular_area[i] * c_angular[i] * (-0.5 * |a| * 1.225)

linear_area = (4*dx*dx, 4*dy*dy, 4*dz*dz)

local_linear_drag[i] =
    v[i] * linear_area[i] * c_linear[i] * (-0.5 * |v| * 1.225)
~~~

These expressions paraphrase the **observed PowerPC floating-point
data flow**, not recovered source language. The original uses
PowerPC `frsqrte`, `fnmsubs`, `fmadds`, `frsp` and
single-precision stores at various points. The C++17 host uses
`float`, `std::fma` and `std::sqrt` and therefore does **not**
claim bit-for-bit PPC FPSCR, subnormal, or rounding identity.
Pair magnitude computations also use the original tiny-value
zero fallback.

After computing each local drag vector, the original calls
`ConvertLocalToWorld(...,false)` and then the matching
`ResolveTorque` or `ResolveForce` virtual. Those side effects
may update flags, force/torque accumulators and sleep status.

## Committed, original-free implementation

- `wii_rigidbody_drag.hpp/.cpp`:
  `ApplyRigidBodyDoDrag`, `WiiDragCallbacks`,
  `WiiDragResult` and `MakeWiiBaseDragCallbacks`.
  All processing uses **host-owned private, bounded Wii
  big-endian memory snapshots**, and stages mutations through
  copy-on-commit. Missing callbacks on taken branches throw.
- `test_wii_rigidbody_drag.cpp`: checks both paths with
  nonzero angular and linear velocity, dimensions (1,2,3),
  original coefficient fields and known expected drag results.
  It checks callback order, initial no-drag/one-path/both-path
  gate combinations, **changed second flag following a torque
  callback**, base-class force/torque accumulation, zero coefficients,
  missing virtual dependencies, invalid environment and atomic
  rollback after a callback exception.
- The dedicated Wii research GitHub Actions workflow now compiles
  and runs this target with Clang C++17
  `-fsanitize=address,undefined`, alongside the prior synthetic
  and C++ tests. Always inspect the current commit's actual CI
  conclusion before claiming green status.

## Remaining dependencies and validation

This is a **testable numerical behavioral reconstruction** of
DoDrag's two currently identified paths, not a direct execution
of original Wii code. It has not yet undergone original-vs-host
Dolphin memory trace comparison. Derived vehicle vtable dispatch,
`Detach` internals, precise PPC reciprocal-square-root iteration
and floating-point rounding, contact/collider forces, tire and
steering behavior remain open. The PS2 Emotion Engine port
has not been matched at these function addresses or memory offsets.

**Next:** capture original Wii pre/post-DoDrag state in a controlled
Dolphin run, verify callback order and values, resolve Detach,
and integrate the validated host DoDrag into the V14
OnEndFrame callback without assuming all derived classes are base.
