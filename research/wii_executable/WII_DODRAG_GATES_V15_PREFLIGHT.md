# Wii V15 preflight: DoDrag branch gates and virtual-call dependencies

**2026-11-11. Analysis-only research.** This is not a C++ implementation of the drag equations. The owner-original Wii ELF was examined read-only with llvm-objdump; no original binaries, disassembly dumps, or proprietary resource bytes are committed.

## Source anchor

DoDrag__9RigidBodyFv starts at Wii address **0x8030ED34**, ending with a return at **0x8030F1B0**. It follows the same body+0x70 -> wrapper+0x00 -> state pointer chain used by the reconstructed integration and frame phases. Initial state flags are loaded as an unsigned halfword at state+0x1C.

The original PPC rlwinm. tests establish these three branch controls:

| Instruction | Flag / branch effect |
|---|---|
| 0x8030ED58 (rlwinm. bit 30), 0x8030ED5C | If flags & **0x0002** is nonzero, branch directly to function epilogue; both drag paths skipped |
| 0x8030ED60 (rlwinm. bit 20), 0x8030ED64 | If flags & **0x0800** is zero, skip the first drag calculation to 0x8030EFF0 |
| 0x8030EFF4 (rlwinm. bit 26), 0x8030EFF8 | If flags & **0x0020** is zero, skip second drag calculation to epilogue |

Thus both optional subpaths may run in a single call, but the 0x0002 bit inhibits both. The English names of the flag fields are not established by this control-flow analysis.

## Opaque dependencies and floating-point anchors

- First subpath 0x8030ED68..0x8030EFEC uses virtual slots **+0x388**, **+0x384**, **+0x364**; multiple original frsqrte/rsqrt operations; body float fields around +0xD4/+0xD8/+0xDC, state vectors and environment-related float fields.
- Second subpath 0x8030EFFC..0x8030F198 uses virtual slots **+0x388**, **+0x384**, **+0x360** and a call to original rsqrt at 0x80232544.
- The Wii r2-relative original float constants used here include: displacement -24544 = 0.0f, -24540 = 1.0f, -24520 = 0.5f, -24516 = approximately 5e-11f, -24512 = 4.0f, -24508 = -0.5f, -24504 = approximately 1.225f.
- The vtable slot names and signatures are not yet recovered; no assumption is made that they map directly to AddForce/SetForce or torque methods. No validated vehicle-drag coefficients or full force/torque vector formulas are claimed.

## Next implementation gate

1. Inspect callers and vtable-slot targets for +0x388/+0x384/+0x364/+0x360, identify the actual interfaces and side effects.
2. Split each gated PPC subpath into source-backed intermediate vector calculations, preserving PowerPC FMA order and conditional branches.
3. Write original-free numerical tests, then compare the candidate outputs to a private Dolphin emulation trace of identical pre-/post-DoDrag state. Validate both flags independently and both enabled together.
4. Keep the V14 OnEndFrame callback opaque until such testing supports replacing it with a real native drag implementation.

This preliminary gate report supports future reconstruction work without representing speculative code as finished gameplay physics.
