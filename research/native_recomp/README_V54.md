# V54: Original Wii `SetInterruptMask` executes natively, including all MMIO banks

**Verified scope: isolated original PowerPC function execution through NWiiRecomp-generated native C++, not an integrated original `OSInit` chain, hardware interrupt-controller model, game boot, or gameplay.**

## Real original function tested

`SetInterruptMask` at **`0x805266E0`** is **604 bytes / 151 original PowerPC instructions** through the last original `blr` at `0x80526938`. The test builder reads those exact instructions only from an owner-provided, **SHA-256-pinned** Undercover Wii DOL. It appends a **test-only `sc; blr`** at `0x8052693C` so direct-return tests can terminate. The generator validates the complete private section's FNV hash, DOL section geometry, entry point, synthetic boundary, and the complete analyzed function. The bounded analyzer has two entrypoints: the original function and the synthetic stop. No original PowerPC bytes or game-derived generated C++ are checked into source control.

The real original function selects Wii interrupt-mask register banks with `cntlzw`, PowerPC conditional branches and bit-mask instructions. Real guest `lhz`, `stw`, `sth` and `lwz` operations invoke the NWiiRuntime MMIO callback hooks; the callbacks **record or return deterministic test-register values**, without claiming a real Wii hardware interrupt-controller implementation:

| PPC leading-zero group | Register transaction | Width |
| --- | --- | --- |
| 0–4 | `0x0C00401C` write | 16-bit |
| 5–7 | `0x0C00500A` read then write | 16-bit |
| 8 | `0x0D006C00` read then write | 32-bit |
| 9–11 | `0x0D006800` read then write | 32-bit |
| 12–14 | `0x0D006814` read then write | 32-bit |
| 15–16 | `0x0D006828` read then write | 32-bit |
| 17–27 | `0x0C003004` write | 32-bit |
| 28–32 | early return, no MMIO | none |

These MMIO addresses are the **physical** addresses observed by NWiiRuntime after guest address normalization. The native suite checks the original helper's returned remaining mask, exact register read/write order, register widths, endian-independent numeric values, preserved stack/LR and untouched nonvolatile registers. A separate seven-step direct-call chain starts with the same `r3 = 0xFFFFFFF0` state established by V53's interrupt initializer and verifies each native return mask through zero. Three r4 mask patterns are tested at every step. That chain intentionally enters `SetInterruptMask` directly each time, and does not claim the original `__OSInterruptInit` loop itself has run.

## Reproducible original-code tests

- **366/366 native semantic assertions** across **54 direct branch/call cases**, including the seven-bank mask progression, five MMIO register groups with readback, the first and last write-only banks, and no-MMIO return cases; **zero PowerPC interpreter fallback** in tested branches.
- **214/214 original SHA, 151 original-instruction + two synthetic-instruction corruption, section metadata, truncated/appended DOL and no-output-overwrite safety checks**. Every mutation must fail closed before emitting output C++.
- Full **optimized**, **ASan/UBSan**, and **fresh unmodified upstream NWiiRecomp ZIP** native test runs passed. The last reproduction applies the existing original-free V15 non-split-dispatch and V26 syscall-PC patches to the fresh checkout.
- Owner DOL SHA-256: `16a09adcf1987c1f3617d10f3a1cb830f32886afb583f9f8f88e0963ae5fe1f4`.

Run against a dedicated NWiiRecomp checkout and your own legitimate game DOL, **not** against the GitHub repository's shared worktree:

```bash
bash run_setmask_v54.sh /private/NWiiRecomp-master /private/NfsMWRelease.dol.bin
V54_SANITIZE=1 bash run_setmask_v54.sh /private/NWiiRecomp-master /private/NfsMWRelease.dol.bin
```

The runner uses a temporary directory for the owner-private instruction slice, generator output and native executable, and removes them at exit. The source-only archive includes V15 and V26 patch prerequisites. Do not upload proprietary DOL/ELF/ISO, assets, original instruction slices or game-derived translated C++.

## Follow-up

1. **V55:** Bridge this genuine `SetInterruptMask` function into V53's original `__OSInterruptInit` conditional `0x80526698`–`0x805266AC` loop, verifying every real MMIO call, the loop's seven passes and its return through original `OSRestoreInterrupts` and handler setup. Ensure all guest device reads are deterministic and traceable; do not invent interrupt-controller hardware delivery.
2. Resume the original direct `OSInit` beyond interrupt initialization once the integrated test passes, then integrate it with the single original `__start` chain still bounded at V26's `0x805206B4` (including the five missing V26 source-only harness files).
3. Continue original Wii OS/IOS, filesystem, graphics, audio and input runtime work toward game `main` and genuine first frame. These have **not** been reached.

Keep development PR #36 a draft. Preserve existing Carbon adaptation and other independent project work.
