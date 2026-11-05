# Six original texture-pack metadata and pixel-range controls

**2026-11-03. Read-only research on the owner's Carbon PC/PS2 and Undercover PS2 original archives.** No proprietary game texture bytes, decoded pictures, actual names, individual hash inventories or patches appear in this repository. No game-file writes or Carbon PC runtime rendering have been performed.

## Reproduction

Run synthetic-only tests from the repository root:

```sh
python -m unittest discover -s research/world_bridge \
  -p 'test_texture_metadata_pixel_bridge.py' -v
```

For real-archive checks, supply the owner's original Carbon PC split-PKZIP volumes (TRACKS.z01, z02, z03 and final TRACKS.zip), Carbon PS2 TRACKS.zip, and Undercover PS2 TRACKS.zip. In each game's secondary-area RB small BUN, parse the bounded 92-byte 0x34110 section table, then locate stream entries **Carbon sections 141/142** or **Undercover sections 241/3401**. Pass each original section slice to `texture_metadata_pixel_bridge.parse_pack(section, 'pc' or 'ps2')`.

The parser verifies the complete `0xB3300000` root, ordered descriptor `0xB3310000` and pixel-data `0xB3320000` subchunks. It correlates sorted 8-byte-per-hash index `0x33310002`, variable-length `0x33310004` metadata records, platform records `0x33310005`, and opaque serialized image array `0x33320002`.

## Empirically supported metadata layout

- The `0x33310004` entries are **not a fixed-stride array**. Each is an 88-byte fixed portion followed by one byte giving the padded ASCII name length, then that many name bytes. The total per record is **89 + padded name length**. The padded name length is 3 modulo 4 and contains a NUL-terminated printable name; source index/name hashes match in all six packs. The debug-name strings are processed only in private memory.
- Candidate metadata offsets **+0x0C** hash, **+0x14** image offset, **+0x18** palette offset, **+0x1C** image byte count, **+0x20** palette byte count, **+0x24** base image size, **+0x28/+0x2A** dimensions, **+0x2E** codec, **+0x32** mip count and **+0x33** texture-mode flag.
- Each PC `0x33310005` platform record is **24 bytes** and contains a FOURCC identifier matching the candidate metadata codec: DXT1, DXT3 or DXT5. Each PS2 platform record is **84 bytes**. The sampled PS2 codec values are 4-bit and 8-bit indexed, with respectively **16/256 palette entries** and **64/1024 palette bytes**.
- Source dimensions are powers of two; width/height log2 fields match their dimensions. Serialized image sizes match the block-compressed DXT or indexed-pixel formula **including mipmaps** in every record.
- All image and palette ranges are in the parent pixel array, and all ranges across a pack are **disjoint**. These checks establish valid source byte slices, **not actual pixel visual correctness**.

## Original-source results

| Source section | Texture records | Codec/type distribution | Valid image ranges | Valid palette ranges |
| --- | ---: | --- | ---: | ---: |
| Carbon PC RB **141** | **37** | DXT1 30, DXT3 1, DXT5 6 | 37 | 0 |
| Carbon PC RB **142** | **73** | DXT1 40, DXT3 5, DXT5 28 | 73 | 0 |
| Carbon PS2 RB **141** | **36** | 4-bit 26, 8-bit 10 | 36 | 36 |
| Carbon PS2 RB **142** | **70** | 4-bit 55, 8-bit 15 | 70 | 70 |
| Undercover PS2 RB **241** | **46** | 4-bit 34, 8-bit 12 | 46 | 46 |
| Undercover PS2 RB **3401** | **46** | 4-bit 34, 8-bit 12 | 46 | 46 |
| **Total** | **308** | 110 PC DXT, 198 PS2 indexed | **308/308** | **198/198** |

Carbon PC versus PS2:
- The shared section index hashes retain **36/36 and 70/70** identical debug names and the same candidate texture-mode flags.
- The PC version's dimensions are **equal or larger in both axes** for each of these **106 shared texture hashes**. Exactly **9** shared textures in section 141 and **34** in section 142 have equal dimensions.
- The PC index contains four additional resource hashes across the two sections; earlier research established that all four are referenced by the same scenery solid texture tables. This is a **local index presence** claim, not a PC texture cache/runtime loading proof.

Undercover PS2 donor sections:
- Section **241** and **3401** each contain the **same 46 indexed texture identities**. All **46 names and candidate texture-mode flags** agree between them, and the compression types match on all 46.
- Every section-241 donor image has dimensions **greater than or equal to** its section-3401 counterpart in both axes. **0/46** image dimensions are identical. The converter must preserve **source section and texture variant context** when resolving donor image resources; a texture hash is not a unique image-resolution identifier.
- Undercover has an exceptional paletted image with **5 mip levels** in section 241 and **4 mip levels** in section 3401, with exact source-image size equations. Most other tested PS2 images have one mip level. A blanket 'PS2 has no mipmaps' assumption would be incorrect.

## 84-byte PS2 platform metadata: additional verified control observations

Across the **198 indexed PS2 texture records** inspected, the candidate pixel storage PSM byte at platform-record +0x04 is either **0x13 for indexed 8-bit** or **0x14 for indexed 4-bit**, agreeing with the per-record codec. A candidate swizzle indicator at platform-record +0x17 is **1 in 195 records, 0 in 3**. This is supported by a separately supplied MIT-licensed Most Wanted PS2 texture research implementation (`tools/src/lib/tex-ps2.ts` in the owner's reference ZIP); **the actual deswizzled color image has not yet been compared with the PC version**, so this field's GPU interpretation remains provisional.

## Quality and next step

- **19/19 new synthetic-only tests passed locally.** Every six-pack read-only archive check passed, including the full mip-size, disjointness, name, hash and platform-stride checks.
- The exact **two committed Python blob hashes** were checked against the local tested files: no test-vs-commit drift.
- This was a local original-archive audit using private section extraction, **not a clean-checkout GitHub CI test**.
- The parser deliberately keeps the texture names and proprietary hash records in RAM and returns only aggregate statistics to its report caller. It does not export original image/palette bytes.

**Next falsifiable gate:** implement and validate a *bounded source-free* PS2 PSMT4/PSMT8 + CSM1 palette decoder and a native PC DXT1/DXT3/DXT5 sample decoder. Check at least two **same-hash Carbon** PC/PS2 image pairs visually or via explicit image-comparison metrics. Only then determine whether the PS2 swizzle/CLUT/alpha conventions map correctly to Carbon PC texture resources. The native Carbon PC texture writer, in-game render, collision, traffic and the full Undercover city remain unresolved.
