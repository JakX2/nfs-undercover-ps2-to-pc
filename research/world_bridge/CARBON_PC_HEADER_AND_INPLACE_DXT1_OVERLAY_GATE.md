# Carbon PC descriptor-header profile and existing-entry DXT1 overlay gate

**2026-11-04. Read-only original-archive observations plus source-free, in-memory modification tests. Not a runtime patch, not a newly registered Undercover texture.**

## Why this gate exists

The prior `synthetic_pc_dxt1_pack_envelope.py` emits a parser-valid Carbon-shaped section, but its `0x33310001` descriptor header is 124 zero bytes, unlike the original Carbon PC resource. The real PC loader's descriptor header, stream registration, section IDs and sampler states are not established by parser acceptance alone. The safe intermediate experiment is therefore to **leave one original PC section envelope and its metadata unchanged**, substituting only the encoded bytes of an already existing opaque DXT1 image inside a private memory buffer.

## New code

- `pc_texture_header_overlay_gate.py`: `profile_pc_texture_headers([sections...])` validates each bounded PC texture pack using independent pre-existing metadata and aligned-pixel parsers. Returns **aggregate statistics only**, including header-byte equality, positions of nonzero 32-bit header words, platform FOURCC-only counts, framing lengths and padding lengths. It never emits the original 124-byte header, texture names, hash inventories, palette bytes or images.
- The same module's `overlay_existing_dxt1(section, existing_hash, opaque_rgba)` requires a valid **existing PC DXT1 entry**. It reads its original width/height/mip count, encodes the replacement RGBA using `synthetic_dxt1_texture_writer.py`, and substitutes **only the original image-data span** at the validated 128-byte-aligned pixel origin. It re-parses the result, confirms the metadata dictionary is identical and checks all prefix/suffix bytes outside the image span. The function returns bytes in memory; **there is no file writer or game executable hook**.
- `test_pc_texture_header_overlay_gate.py`: **20 source-free synthetic tests**, covering header comparison/variation, index presence, real span isolation, multiple existing mip levels, preservation of neighboring textures, determinism, non-DXT1 rejection, corrupt alignment, altered dimensions, format mismatch, unsafe identifiers, insufficient RGBA and any non-opaque alpha.

## Private original Carbon PC archive controls

The owner's split-PKZIP Carbon PC archive was inspected without exporting original texture headers or images. The L5RB stream was read through a bounded reader validating full ZIP CRC and size. For L5RA, only the target uncompressed stream ranges were selected during incremental DEFLATE; **a full archive-member CRC is not claimed for that partial extraction**. Each extracted section was independently validated using the existing texture-pack and corrected pixel-base parsers.

| Original section | PC texture records | Descriptor header bytes | Platform entries FOURCC-only | `0x11` pixel padding | In-memory existing DXT1 overlay |
| --- | ---: | ---: | ---: | ---: | --- |
| L5RA **141** | 2 | 124 | 2/2 | 120 | Passed |
| L5RA **142** | 2 | 124 | 2/2 | 120 | Passed |
| L5RB **141** | 37 | 124 | 37/37 | 120 | Passed |
| L5RB **142** | 73 | 124 | 73/73 | 120 | Passed |
| **Total** | **114** | **4/4 identical binary headers** | **114/114** | **4/4** | **4/4 passed** |

The 4 original descriptor headers have exactly the same 124 bytes, despite different texture counts and varying parent type-zero framing payload sizes. They are **not** all zero. Nonzero 32-bit-aligned header positions occur at offsets `0, 4, 8, 12, 32, 36, 40, 44, 48, 52, 56, 96`; some represent portions of embedded text fields, **not necessarily 12 independent numeric fields**. The value at `+96` is nonzero and stable across these four examples, but **its meaning, pointer/relocation status, and loader handling remain unknown**. No original literal header values or original filenames are committed.

All four private in-memory overlays had (a) unchanged section byte length, (b) an unchanged parsed texture identity/metadata map, (c) a changed existing DXT1 pixel span, and (d) **zero byte changes anywhere outside that span**. The image used for the overlay was a synthetic, fully opaque solid-color fixture and was not saved into or installed over any original game file. Each section's own mip count and image size were preserved.

## Reproduction with synthetic fixtures only

Run from the repository root:

```sh
python -m unittest discover -s research/world_bridge \
  -p 'test_pc_texture_header_overlay_gate.py' -v
```

The focused combined local suite of this module plus `test_synthetic_dxt1_texture_writer.py`, `test_synthetic_pc_dxt1_pack_envelope.py`, and `test_pc_dxt_reference_decode.py` passes **71/71 tests**. No new GitHub CI result or clean-checkout integrated test is claimed.

To reproduce the private original-source profile, the owner must extract the original section slices using their legally owned local game archive and existing bounded section-table tooling. The in-memory overlay requires the target **original Carbon PC section**, the original **existing** identity present within that section, and a dimension-matched fully opaque RGBA image. Never publish the returned section bytes; do not assume Carbon PC will load the result.

## What this does *not* prove

- **No new texture identity or Undercover source asset was inserted.** The overlay replaces a slot already present in Carbon PC and preserves its original metadata. It cannot add textures or place an Undercover world object.
- No proof that the game accepts a replaced texture, that the 124-byte descriptor can be newly synthesized, or that its constant `+96` value is a portable pointer/identifier.
- No proof of the relevant shader sampling, alpha policy, DXT3/DXT5 writer, stream residency, collision, world integration or gameplay behavior.
- No original image pixels, hash lists, original descriptor bytes, patched archives or executable binaries are published; `main` stays unchanged and PR #33 remains draft.

**Next falsifiable gate:** compare untouched genuine Carbon descriptor/header and wrapper structures across more pack families, resolve the constant field at `+96` and the section-table loader registration requirements, then perform a private **game-side** smoke test using a reversible existing-entry DXT1 overlay, never treating parser success as runtime success.
