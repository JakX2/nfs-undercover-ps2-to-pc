# V10: Original Undercover Wii JDLZ validation

Date: 2026-11-13. Owner-original assets were used locally for validation only; **they are excluded from Git and the source-only ZIP**.

## Wii JDLZ v02 decoder validation

The source-only C++20 `jdlz_decoder_v10.h` validates header magic/version, 16-byte header lengths, output allocation caps, dual flag streams, both distance/length encodings, truncated packets, output bounds and backward-reference ranges. LZ77 overlapping copies are supported. For embedded data, `input_consumed` reports the entire compressed block length, including unused trailing bytes (observed in real files).

The implementation was independently verified by comparing its decoded bytes to the owner's existing uncompressed game archive files:

| JDLZ file | Uncompressed match target | Output bytes | SHA-256 of exact decoded file | Match |
|---|---|---:|---|---|
| GLOBAL/GAMEPLAY.LZC | GLOBAL/GAMEPLAY.BIN | 1,272,960 | 2bc52b0aaf25d4f5a821bc2998fe6ff66b62720ccbf902b3b7ca9883e2007645 | Exact |
| GLOBAL/GLOBALB.LZC | GLOBAL/GLOBALB.BUN | 5,002,204 | ae2ca0d324d563a0d3d3b9b6930159dfcdd6fa6714256572b0c8a116411b8409 | Exact |
| GLOBAL/INGAMEB.LZC | GLOBAL/INGAMEB.BUN | 693,532 | 1965677c1054f13815eb1160f4452adfb50242f528f632df3849582f5338aa4d | Exact |
| FRONTEND/FRONTB1.LZC | FRONTEND/FRONTB1.BUN | 5,445,760 | 96db7b563f09dd8c1512d1f58e687294ebe094ad0b054847b08369bcc3658166 | Exact |
| FRONTEND/DEMOFRONTB1.LZC | FRONTEND/DEMOFRONTB1.BUN | 13,400,832 | 0620884939a6a3a17e31c024f26059fac63555e03d2224edabdaaff83fe3fa19 | Exact |
| **Total** | | **25,815,288** | | **5/5** |

The byte-for-byte claim is based on direct full-buffer comparison, not just header or hash matching. The exact SHA-256 values above are for regression diagnostics only; no original game bytes are distributed.

## Original executable function map (ELF symbol table)

- `JLZDecompress__FPUcPUc` at **`0x802DC8C4`** (388-byte PPC function)
- `HUFF_decompress__FPUcPUc` at **`0x802DCA48`** (3,420-byte PPC function)
- `HUFFDecompress__FPUcPUc` at **`0x802DF030`** (92-byte PPC wrapper)
- `DecompressInPlace__FPviib` at **`0x802DF778`** (320-byte PPC function)

These names/addresses originate from the owner's actual Undercover Wii ELF; they identify candidates for future call tracing. They do not by themselves prove which one is called for every compressed asset.

## Format distinction

`GLOBAL/GLOBALA.LZC` begins with `HUFF` and is **not JDLZ**. Its header reports an uncompressed size of 265,564 bytes. Its matching `GLOBAL/GLOBALA.BUN` has that length, but no HUFF decode has been verified in V10. This is the next independent compression-family task.

## Test evidence and current boundaries

- Synthetic decoder checks: **91/91**, including out-of-bounds and truncated-input rejection, long/short references and padding handling.
- Original-free deterministic mutation cases: **20,000**, under GCC AddressSanitizer+UndefinedBehaviorSanitizer with no detected memory errors.
- Five original LZC/BIN/BUN pairs: **byte-exact C++ decoder comparison**.
- Decoder is a **standalone native component**, not yet wired into the actual Wii resource or execution system. We have not completed native linking, boot, or a render loop.

Public implementation cross-check: [OpenNFSTools JDLZ.cs](https://github.com/MWisBest/OpenNFSTools/blob/master/LibNFS/Compression/JDLZ.cs). The V10 source is independently authored and bounded.
