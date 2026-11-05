# Phase 33: Verified Undercover PS2 steering-function identification

**Research-only. No gameplay patch.** We identify the stripped PS2 counterpart of SuspensionRacer::DoHumanSteering through instruction signatures, call graph, state offsets and function boundaries.

| Build | Address | Size | Basis |
|---|---|---:|---|
| Undercover PS2 (SLUS_218.01) | **0x004082B0** | **1,216 B** | Exact executable SHA, signatures, helper and direct caller |
| Carbon PS2 (SLUS_214.93) | **0x003D58D8** | **688 B** | Exact executable SHA, signatures, helper and direct caller |
| Undercover Wii | 0x80324B48 | 1,288 B | Named original ELF symbol |
| Carbon Wii | 0x802EDB88 | 664 B | Named original ELF symbol |
| Carbon PC | 0x006EF540 | 729 B | Phase 31 call-graph-inferred match |

## Evidence from original PS2 machine code

- **Undercover PS2** reads Chassis::State steering input at +0x8C (0x00408304), calculates **x * abs(x)** at 0x00408400–0x00408404, and uses a post-transform **0.1199999973** threshold in one branch. Not proof of a universal controller deadzone.
- **Undercover Wii** has both a signed-square path and a separate sign(x) * |x|^1.15 path. That Wii-specific input-device branch must not be assumed present on PS2.
- Undercover PS2 uses **55.0** (0x004083A4) where Carbon PS2 uses **45.0** (0x003D59C4) in an analogous **mode-specific** steering path. Not a proven global wheel-angle limit.
- Undercover PS2 uses **3.8** and **11.0** as parameters of state-dependent angle calculations, and calls a table-driven angular helper at 0x00172CB8. Full mathematical reconstruction is still pending.
- Both PS2 functions write the counterpart racer object at +0x19C and +0x188. **Do not transplant console object offsets into Carbon PC.**
- UC PS2 calls a matched steering helper once: 0x004083C4 → 0x00408770. Carbon PS2 calls its helper twice: 0x003D59E0 and 0x003D5A14 → 0x003D5B88.
- Direct callers are UC PS2 0x00408A8C and Carbon PS2 0x003D5FBC, in their respective steering dispatchers.

## Verification and reproduction

Exact original PS2 ELFs were checked locally: **19 Undercover instruction signatures, 4 calls; 9 Carbon instruction signatures, 3 calls**, plus the direct caller and helper-call xrefs per build. **11/11 Python regression tests passed** with both source binaries available. The addresses are high-confidence inferred identities, not symbols present in stripped PS2 builds.

Original file SHA256:
- UC PS2: 6c53252622348ee5981685420a27e6914e02757e739945f583940b8c35814646
- Carbon PS2: 1bcc9ff09b2dce748ab78453338c2733375a55ee4dd9a8ee534db9803a5e5d9b

Run the accompanying Python verifier (stdlib only) with your own original ELFs. It rejects unexpected SHA values, never modifies binaries, and prints verification metadata only. This repository contains no copyrighted executable, disassembly dump, extracted assets or player memory logs.

**No new steering ASI** is part of Phase 33. The CCX felt heavier under Phase 30's active tire-force hook, so keep that experiment disabled.

Next target: reconstruct state-dependent steering angle calculations and map state fields into Carbon PC before an opt-in steering-only experiment.
