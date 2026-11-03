# Experimental PS2 indexed texture layout gate

**2026-11-03. Source-free, synthetic-only research. Not an Undercover texture converter.**

## Problem

The source-backed `texture_metadata_pixel_bridge.py` verifies PS2 image and palette byte ranges, codecs, dimensions, and mip counts. It **does not** establish whether the image bytes in a source pack are row-major CPU indices, GS VRAM-swizzled pixels, or linear words intended for a 32-bit GS texture upload and subsequent indexed interpretation. The candidate +0x17 platform swizzle flag (195/198 records = 1) is **not** proven to select any of these layouts. The previous exploratory decoder did not consistently correlate Carbon PC and Carbon PS2 same-hash pictures.

## New *offline-only* modules

- `ps2_texture_layout_candidates.py`: bounded, pure in-memory PSMT8/PSMT4 index decoding with three **explicit hypotheses**: `linear`, `gs_vram` and `ct32_transfer`. The last reconstructs a PSMCT32 write at width/2, height/2 (8-bit) or width/2, height/4 (4-bit), then reads the same virtual GS memory as indexed pixels. The implementation checks for unwritten/out-of-range bytes instead of padding silently. All three modes require exact base-image byte counts. This is **not** a universal TIM2 extractor, and is not yet linked into original-source conversion.
- Same module: 32-bit RGBA/BGRA palette interpretation with separately selected `linear` or `csm1` ordering and `raw` or `double` alpha. For CSM1 8-bit, the logical 8..15 and 16..23 entries are swapped within each 32-entry bank; 4-bit palettes are unchanged. These knobs are **hypotheses**, not verified Undercover settings.
- `pc_dxt_reference_decode.py`: bounded, in-memory base-level DXT1, DXT3 and DXT5 decoders and a nearest-neighbor normalized-coordinate mean-absolute-error comparison. This is a deliberately simple baseline for **candidate scoring**, not a GPU-identical renderer. It never writes a PC pack or selects a 'best' mode.
- Both modules require caller-provided bytes and perform no game archive I/O or external writes.

## Independent synthetic controls

A full-page 128×64 8bpp CT32 transfer reproduces **8192/8192** indexed pixels from the independent Sparky/Victor Suba unswizzle8 formula; a full-page 128×128 4bpp transfer reproduces **16,384/16,384** indices from the independent unswizzle4bpp formula. Their SHA-256 output vectors are fixed in the tests. Independent PS2 GS page/block/column tables and CLUT conventions also informed address/nibble checkpoints.

References used for independent comparison and terminology:

- MIT-licensed [PDTools GS memory implementation](https://github.com/Nenkai/PDTools/blob/master/PDTools.Files/Textures/PS2/GSMemory.cs)
- [PS2Textures: independent unswizzle implementations](https://github.com/leeao/PS2Textures/blob/main/PS2Textures.py)
- [PS2 GS pixel mode description](https://github.com/PCSX2/pcsx2/discussions/4313)

Run the new synthetic tests from repo root:

```sh
python -m unittest discover -s research/world_bridge -p 'test_ps2_texture_layout_candidates.py' -v
python -m unittest discover -s research/world_bridge -p 'test_pc_dxt_reference_decode.py' -v
```

These tests prove only deterministic hypothesis behavior on **artificial bytes**, not that any hypothesis matches the Undercover archive. They include expected address vectors, full-page round trips, independent output vectors, CLUT group permutations, alpha handling, DXT reference blocks, size/bounds rejection and dimension-aware metrics. No original images, palettes, source-name lists or game executable patches were committed.

## Next source-backed falsification

1. Read two *independently identified, same-hash* original Carbon PC/PS2 textures with the existing `parse_pack(...)` checks and their own `0x33320002` pixel arrays. Use `base_image_bytes` to isolate each first mip and the recorded palette offset and size.
2. Run explicit combinations of `layout × clut × alpha × channel-order` in memory, and compare against the Carbon PC DXT-decoded first mip. Keep source section and resolution provenance. Do not presume the highest-scoring combination is correct without inspection and cross-texture controls; DXT loss, differing resolutions and texture art variants can create mismatches.
3. Record only **aggregate score distributions** and a clearly marked failing/successful hypothesis, not proprietary pixel bytes, names or per-resource hashes. Confirm whether the proposed +0x17 swizzle indicator actually predicts a layout.
4. Investigate mip chains separately, especially Undercover's mismatched 5-versus-4 mip-level variant. Small mip levels may require independent padding/packing rules and should **fail closed** until proven.
5. Only after source-backed comparisons, implement a separate native Carbon PC texture writer. **No original files have been written and no PC runtime test is claimed.**
