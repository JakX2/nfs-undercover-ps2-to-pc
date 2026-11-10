# Undercover PS2 executable: first ELF/MIPS call-pattern census

**Date:** 2026-11-10. **Source:** owner-supplied original `SLUS_218.01`, examined read-only. No retail executable, extracted code bytes or original assets are committed.

## Verified ELF header

- File length: **6,153,116 bytes**.
- ELF32, little-endian, ET_EXEC, EM_MIPS (machine 8); MIPS-specific flags **0x20924001**.
- Entry point: **`0x00514F30`**, within `.text`.
- `.text` virtual address **`0x00100000`**, size **4,833,424** bytes.
- `.over` virtual address **`0x00600800`**, size **239,592** bytes.
- `.vutext` size **14,096** bytes; **deliberately excluded** from the ordinary MIPS instruction scan.
- 24 ELF section headers, one program header. Source executable is stripped of ordinary named function symbols.

## Read-only linear 32-bit opcode census

| Candidate pattern | .text | .over | total |
|---|---:|---:|---:|
| Direct JAL words | 65,802 | 4,472 | **70,274** |
| Indirect JALR words | 10,581 | 373 | **10,954** |
| Direct J words | 4,963 | 648 | **5,611** |

Across both `.text` and `.over`, **70,036/70,274 JAL candidates** point into one of the two surveyed code-section address intervals; **238** point outside those intervals. The in-range targets comprise **14,546 distinct candidate addresses**, **not 14,546 confirmed functions**. Two direct calls occur in the first 0x200 bytes from entry: candidate destinations `0x005797D8`, `0x00574E60`.

The corresponding self-contained bounded scanner is `research/ps2_executable/ps2_elf_call_index.py` on branch `research/undercover-ps2-elf-call-index`.

## Interpretation and priorities

These are **raw opcode matches on a linear word scan**, not a proven executable control-flow graph. Data words, dead code, branch delay slots, overlays, and PS2 Emotion Engine-specific opcodes may produce false-positive classification. `JALR` destinations require dataflow/register analysis; `J` is not automatically a tail call. The precise meaning of the `.over` region and DVP overlay tables still needs validation.

Next steps:

1. Add deterministic synthetic ELF32 tests and malformed-file negative cases to the scanner.
2. Determine actual loaded executable ranges from ELF program headers; verify `.over` and overlay semantics.
3. Decode entry startup into a trace with instruction bytes kept private; identify BSS initialization and startup calls with control-flow evidence, rather than just JAL patterns.
4. Establish function boundaries with recursive traversal and MIPS branch-delay-slot handling, then cross-reference graphics, streaming, audio and gameplay systems by strings/callers.
5. Keep the executable-decompilation branch separate from asset-format draft PR #33 until validation.

**No PC executable, recompilation, verified symbol recovery, or in-game model rendering is claimed.**
