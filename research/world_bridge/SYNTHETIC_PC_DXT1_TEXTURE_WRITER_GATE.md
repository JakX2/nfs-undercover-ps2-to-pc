# Source-free Carbon-shaped DXT1 writer gate

**2026-11-04. Offline original-source research and synthetic-only writer. No playable game patch or native loader success.**

## What was implemented

- `synthetic_dxt1_texture_writer.py`: deterministic, bounded opaque-only DXT1 encoder accepting RGBA buffers, 4×4 block output with clamped edges, safe 2×2 RGB downsampling and independently encoded mip levels. Opaque black remains opaque. Non-opaque alpha **fails closed** instead of being discarded. Encoded DXT1 colors use RGB565 endpoints and nearest-selector approximation; this is a lossy, non-production encoder, not an optimizer or bit-for-bit recreation of game assets.
- `synthetic_pc_dxt1_pack_envelope.py`: emits an **in-memory, source-free synthetic** `0xB3300000`-shaped pack with one or more `SYNTH_`-prefixed ASCII texture names. Entries use a sorted 8-byte identity index; variable-length 88-byte texture metadata prefix plus length/name; 24-byte PC platform records with `DXT1` at offset `+0x0C`; `0xB3320000` pixel container with 120-byte `0x11` alignment padding and disjoint DXT1 mip spans. It re-parses itself with the **existing** `texture_metadata_pixel_bridge.parse_pack` and `texture_pixel_base_alignment.aligned_pixel_array` functions before returning.
- Two synthetic-only test modules with explicit errors for malformed names, duplicate hashes, improper dimensions/counts, corrupted alignment, invalid alpha and size/offset issues.

The section is **not a verified native Carbon PC resource**. Unknown descriptor/serializer fields use synthetic placeholders, and the otherwise observed framing is forced into place using a synthetic variable-length type-zero child. The module performs **no disk writes**, no texture pack injection and no game runtime interaction.

## Original Carbon PC reference controls (private, read-only)

The owner's original Carbon PC split-PKZIP `TRACKS` archive was read with bounded CRC-checked member extraction. Two original secondary-area texture sections were inspected. No original texture bytes, names, hashes, screenshots, chunks or decoded pictures are included in this report or the repository.

| Verified original source feature | RB 141 | RB 142 |
|---|---:|---:|
| PC texture records | 37 | 73 |
| DXT1 records | 30 | 40 |
| PC platform record size | 24 bytes | 24 bytes |
| Nonzero platform bytes, across all formats | only FOURCC offsets `+12..+15` | only FOURCC offsets `+12..+15` |
| Descriptor header `0x33310001` length | 124 bytes | 124 bytes |
| Pixel header `0x33320001` length | 24 bytes | 24 bytes |
| Root type-zero framing sizes | 48 / 80 bytes | 48 / 120 bytes |
| Pixel-side type-zero framing size | 80 bytes | 80 bytes |
| Pixel-array `0x11` alignment | 120 bytes | 120 bytes |

These observations corroborate the writer's **24-byte FOURCC platform record**, descriptor header length, and alignment hypothesis. They do not reveal the meaning of all 124 descriptor header bytes, texture name hashing, texture modes, PC loader registration or the shader/sampler ABI.

### Original-PC DXT1 re-encoding control

A private script sampled up to 32 block positions per original PC DXT1 image, spreading the samples across the encoded source stream rather than selecting a single image corner. For each sampled **opaque** block, the original DXT1 block was decoded, the resulting 4×4 RGBA was re-encoded by the new source-free encoder, and the newly encoded block was decoded independently for RGB comparison. No blocks were serialized or exported.

| Original source section | DXT1 images | Opaque blocks re-encoded | Mean per-image RGB MAE (0–255) | Highest single-block RGB MAE |
|---|---:|---:|---:|---:|
| 141 | 30 | 960 | 0.0888 | 2.3333 |
| 142 | 40 | 1,236 | 0.2420 | 3.0000 |
| **Total** | **70** | **2,196** | not combined | **3.0000** |

No sampled blocks had transparent pixels and no block was rejected. These are **re-encoding fidelity metrics against an already DXT1-compressed PC baseline**, not PS2→PC conversion error, PS2 alpha reconstruction, exact original block identity or a proof of Carbon PC runtime acceptance.

## Regression suite

```sh
python -m unittest discover -s research/world_bridge \
  -p 'test_synthetic_dxt1_texture_writer.py' -v
python -m unittest discover -s research/world_bridge \
  -p 'test_synthetic_pc_dxt1_pack_envelope.py' -v
python -m unittest discover -s research/world_bridge \
  -p 'test_pc_dxt_reference_decode.py' -v
```

**51/51 focused local tests passed:** 18 DXT1 encoder tests, 20 synthetic pack tests, and 13 previously committed DXT1/DXT3/DXT5 decoder/metric tests. The real-source probe is *private*, independently validated through bounded archive/texture readers; no clean-checkout GitHub CI run claimed for this milestone.

## Explicitly outstanding gates

1. Recover/compare the nonzero original PC `0x33310001` and other wrapper-header values, and establish which fields are fixed, offsets, pointers, section-specific hashes, or loader-derived.
2. Reproduce true PC texture-pack writer metadata, sampler modes and asset registration without copying a donor object and without assuming a synthetic zero-header is game-loadable.
3. Define an explicit Undercover PS2 → PC alpha policy for opaque DXT1 vs DXT3/DXT5. The original PC DXT1 re-encoding control makes **no claim** that Undercover's PS2 alpha can be discarded safely.
4. Privately test an Undercover RGB image against the DXT1 writer, then independently check its wrapper and in-game appearance only after the resource ABI is verified.
5. Keep collision, streaming world placement, traffic and gameplay as separate uncompleted goals.

**Publication boundary:** Source-only code/tests and aggregate reports only. No original game assets, image buffers, hash lists, patched binaries or game files committed. Keep PR #33 draft, leave `main` untouched.
