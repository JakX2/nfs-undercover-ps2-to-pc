# V5: Undercover Wii native translation, paired-single and SPRG research

Date: 2026-11-13. This is source-only research; no native game boot or link is claimed.

## Measured real-DOL result
- Used privately supplied, ELF-verified Undercover Wii DOL, 27,941 original named function roots.
- NWiiRecomp discovered 32,420 candidate functions and translated 1,806,810 PPC instruction slots into 112 numbered generated C++ shards plus a dispatcher.
- V4 unsupported generated opcode traps: **71**. After V5: **1**.
- All 70 formerly unimplemented real paired-single estimate sites now emit `ctx.ps_rsqrte`. Numerical implementation is approximate and not Wii bit-exact.
- Signed six-bit GQR scale handling corrected for paired-single load/store.
- Implemented SPRG0-SPRG3 read/write translation: **10** previously ignored `mtspr` sites and **22** `mfspr` sites now emit explicit CPUContext operations.
- **183 `mtspr` operations spanning 60 SPRs are still ignored**: 28 in 528–543, 99 in 560–575, 22 in 1008–1023, 34 elsewhere. Full BAT/HID/MMU behavior requires research.
- Last explicit trap occurs at 0x800044C0: verified original ELF ASCII `Metrowerks Target Resident Kernel` misread as code. It lies outside the original named-function spans, though within an executable section; do not automatically replace with a no-op.

## Tests and limitation
- 6/6 existing synthetic indexed PSQ instruction-emission checks passed.
- 10/10 new synthetic emitted-instruction tests passed.
- 71/71 new CPU runtime assertions passed, including signed GQR scale, reciprocal estimate lanes and aliasing.
- Patched a fresh upstream NWiiRecomp extraction, verified idempotence and exact SHA-256 equivalence of patched translator/runtime with the work tree.
- Targeted GCC syntax checks passed for generated units 0, 30, 31, 32, 106 and 110. A larger interrupted run produced 41 successes, not a complete 113/113 V5 result.
- GCC 14.2 successfully compiled a private, translated Undercover unit `output_30.cpp` into a 4.4 MB native x86-64 object file. No full game link/startup, audio, graphics or gameplay.
- Full private generated game code, executables, and ELF symbol inventories are not committed.

Apply V4 `apply_psq_indexed_patch.py` first, then the included `apply_psq_estimate_and_gqr_v5.py` to a private NWiiRecomp source checkout. Complete original-free tests and runnable source-only drivers are distributed in the V5 research toolkit.

References: WiiBrew paired singles https://wiibrew.org/wiki/Paired_single and Broadway registers https://wiibrew.org/wiki/Broadway/Registers . Upstream NWiiRecomp has a custom license.

Next gates: prevent false-positive executable-region discovery, correctly model BAT/HID/MMU side effects, compare FPSCR/GQR/estimates against Dolphin, and link/boot with a complete Wii runtime.
