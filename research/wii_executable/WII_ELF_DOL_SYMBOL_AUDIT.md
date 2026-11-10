# Wii Undercover ELF symbols and exact DOL source-alignment audit

**2026-11-10.** An owner-supplied Wii `NfsMWRelease.elf` and corresponding `NfsMWRelease.dol` from the Undercover Wii Drive archive were examined locally, read-only. Both are **PowerPC Wii builds**, unlike the original MIPS PS2 executable. Neither original executable, proprietary code, asset bytes nor full symbol inventories are published in this repository.

## Main finding: unusually complete Wii function labels

The Wii ELF32 big-endian PPC executable is **not stripped**, retains a complete `.symtab` and `.strtab`, and contains relocations. Its original function metadata provides a high-quality reference for game engine C++ recovery. It does **not** contain decompiled C++ source.

| Checked original-image fact | Result |
|---|---:|
| Wii ELF file bytes | **11,151,296** |
| Wii DOL file bytes | **6,433,280** |
| Wii entrypoint, ELF and DOL | **`0x8000403C`** |
| ELF section headers | **26** |
| ELF program headers | **14** |
| Total ELF symbol entries | **51,490** |
| STT_FUNC function symbol entries | **27,941** |
| Sized, inside executable section | **27,941/27,941** |
| Unique STT_FILE source filename strings | **774** |
| Source FILE symbol entries | **779** |
| Relocation entries | **178,846** |
| Executable section byte sum | **5,652,004** |
| Non-overlapping union of named function spans | **5,642,144** |
| Named function span coverage of executable sections | **99.8256%** |

Function symbol counts by executable ELF section: `.init` **14**, `.text` **27,793**, `.kpadtext` **134**. Representative actual source-file labels include `zAI.cpp`, `zPhysics.cpp`, `zRender.cpp`, `zGameplay.cpp`, `zWorld.cpp`, `zTrack.cpp`, `zCamera.cpp`, and `zLua.cpp`. These confirm that Wii function naming can guide system-by-system analysis; no architecture-independent identity is inferred merely from matching source terminology.

**Coverage qualification:** the 99.8256% is a union of the ELF's function-symbol `value/size` ranges, not a count of correctly decompiled instructions and not PS2 coverage. Inline code, non-function words and unlabeled spans need separate treatment.

## Independent byte-level Wii ELF ↔ DOL check

The source-only checker matches every nonempty DOL code/data section to a unique allocatable ELF section with the exact same virtual address and original bytes. It requires all extra DOL section-alignment bytes to be zero and each ELF BSS subsection to fall inside the DOL BSS range.

- **3/3** nonempty DOL text sections match the ELF exactly.
- **8/8** nonempty DOL data sections match the ELF exactly.
- **6,432,900** original nonpadding bytes compared, **0 mismatches**.
- **124** verified zero padding bytes in the DOL.
- **3** ELF NOBITS BSS sections contained within DOL BSS.
- Entry points match: `0x8000403C`.

This establishes the ELF as an exact code-and-data reference for the supplied Wii DOL's loaded section bytes, rather than an unverified sibling build. **No equivalence with the PS2 MIPS executable or Carbon PC program has been shown.** The ELF may contain legacy game-name labels; use section-byte proof rather than filename assumptions.

## Reproducible no-asset tools

- `research/wii_executable/wii_elf_dol_audit.py`: fail-closed, bounded, source-only ELF parsing, aggregate symbol measurements, and optional DOL section equality checks.
- `research/wii_executable/test_wii_elf_dol_audit.py`: **13/13** locally passing original-free synthetic unit tests. Includes corrupted DOL code, alignment filler, entry mismatch, bad ELF architecture/link and malformed bounds.
- Owner-local invocation:

```sh
python research/wii_executable/wii_elf_dol_audit.py \
  --wii-elf NfsMWRelease.elf \
  --wii-dol NfsMWRelease.dol
```

The script emits only JSON aggregate counts and section identifiers, not function bodies, proprietary byte ranges or entire symbol lists. It never modifies its inputs. The original-supplied audit was completed locally and passed.

## Recommended reconstruction direction

1. **Lead with Wii:** import the symbol-rich `NfsMWRelease.elf` into a PPC-aware reverse engineering tool. Preserve named symbol values/sizes and compilation-unit anchors.
2. **Define subsystems:** recover typed interfaces and call relationships for world streaming, vehicles, AI, physics, graphics and gameplay, with selected functions rather than attempting 27,941 manual rewrites at once.
3. **Cross-check the PS2 version:** compare invariant game resource formats, strings, imported gameplay logic and data structure semantics. **Do not reuse Wii addresses, pointer layout, instruction sequences or ABI as PS2 evidence.**
4. **Port to PC in a separately authored engine:** platform abstraction for files, rendering, audio, input, physics and threading. Existing Carbon PC format work in draft PR #33 may provide practical interim resource/runtime controls, but is not a proof of Wii code portability.
5. Next original-source gate: generate a *private* indexed, per-subsystem Wii symbol and call-reference catalog; select a small concrete engine module and reconstruct/test a function family using independent runtime behavior.

**Scope:** read-only research, no executable modification, no recovered full source code and no working PC port yet. Keep draft until reviewed.
