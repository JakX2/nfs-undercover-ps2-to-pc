# Boot-first execution priority, November 28, 2026

**Primary objective:** execute the original Wii `__start` path continuously in
the complete AOT-translated Windows executable until the original game
`main` is entered. Do not equate any source-only, synthetic, isolated AOT
or stopped-callback run with original-game boot.

## Current genuine Windows frontier

The verified full-image Windows original run
[46096246382](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/46096246382)
links and launches the original private executable, enters the original
fourth SI `__SITransfer`, completes original save/interrupt-disable, and
stops before device MMIO. The earlier post-time handler guard is verified.
No fourth transfer return, full SI IRQ return, OSInit return, `main`, frame
or gameplay is yet authenticated in the complete Windows image.

## Single-build continuous integration gate

The preferred owner-original Windows regression is
[`wii-windows-si-continuous.yml`](../../.github/workflows/wii-windows-si-continuous.yml).
It runs existing original-free transfer/handler/callback regression tests,
then **one** original DOL/ELF private full-image Windows build with the deepest
currently installed authenticated route, `--owner-callback-prefix`.

The configured chain attempts: original startup -> native SI IRQ handler ->
fourth SI transfer/device completion and original ABI restore -> fifth alarm
cancellation -> original callback prologue/compiler save. Each original
instruction must run in the same full-image native CPU context and
authenticated Wii device state. Unexpected operation, timeout, malformed
marker, partial stage and nonzero exit fail closed. Success only proves the
bounded callback-prefix stop, **not** IRQ return, full boot or graphics.

### Immediate execution work

1. **V752 owner-original Windows return**: if the full-image process fails
   after the V751 prefix, diagnose the first `V777_TRANSFER_INVALID` or
   MMIO-failure marker and fix the actual native device/scheduler, emitted
   CPU state, or original return dispatch. Keep the existing source-only
   tests as regression controls rather than inventing more count targets.
2. **Handler continuity**: after the original fourth return passes, allow
   the authenticated fifth alarm call and callback to execute in the same
   full-image Windows process. Use existing V753-V756 witness/observer
   implementations; do not treat their original-free passes as runtime
   evidence.
3. **Real interrupt return to OSInit**: reuse already developed V920
   original handler BLR/dispatcher continuation, V922 native `rfi` context
   return, and V928 IRQ-enable leaf return-to-OSInit as *candidate*
   integration seams. Validate their prior original/private proofs before
   adapting them to Windows. Do not claim these joined on Windows yet.
4. **Resume original startup**: validate re-entry to `OSInit` at
   `0x80520670`, return to the original `__start` caller, then advance
   original `__init_user` and the direct main call at `0x800041A0`
   to original game `main` at `0x802D3F40`. Addresses come from the
   project's private matching DOL/ELF *static* audit. They are not
   runtime-achieved milestones.
5. **Graphics and resources**: only after the actual game's `main` and
   subsequent native initialization are entered, repair demanded IOS/DVD,
   memory, threading, VI/GX, audio and input services; then validate a
   first native frame and frontend before changing game behavior.

If the runtime fails during original code execution, report its **first
observed** failing stage and last authenticated event, fix that dependency,
and repeat the full-image run. Preserve exact owner DOL/ELF identity, native
AOT execution, zero interpreter fallback, and redacted private CI cleanup.

## Explicit non-goals

Do not advance isolated formatter instruction-count milestones solely to
increase the number. Do not switch to Dolphin, PCSX2 or a Carbon-based
remake as the native recompilation implementation. Do not mark `main`,
frontend, a frame or gameplay as reached merely because NWiiRecomp emitted
or linked the corresponding C++ functions. Keep the owner original assets,
generated translated game code, binaries and raw traces out of public Git.
