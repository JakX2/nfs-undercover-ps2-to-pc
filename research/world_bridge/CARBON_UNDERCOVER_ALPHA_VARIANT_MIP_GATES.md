# Original Carbon/Undercover texture alpha, cross-variant and mip-chain controls

**2026-11-03. Read-only original owner-supplied archive research.** This work extends the aligned-source base-level RGB verification in `CARBON_UNDERCOVER_TEXTURE_COLOR_GATES.md`. No source texture bytes, actual palette contents, game images, names, hash inventories, serialized original assets or patches are committed.

## Why this gate exists

The Carbon PC↔PS2 same-hash RGB comparison now validates the PS2 indexed layout for all 106 textures in RB sections 141/142. However, simply multiplying PS2 palette alpha by two does **not** reproduce the PC alpha channel in all textures. It would be unsafe to use that result as an unconditionally correct native PC texture conversion policy. Meanwhile, Undercover has two independently stored PS2 texture versions for all 46 identities, permitting a *same-game cross-variant control* without a matching Undercover PC image.

## 1. Carbon PC versus PS2 alpha: explicit candidate comparisons

`carbon_ps2_alpha_provenance_audit.py` decodes original paired image **base levels** using the prior source-backed color/layout path, nearest-neighbor compares the PS2 source palette alpha with the corresponding PC DXT alpha, and records separate MAE scores for `raw`, `double` (saturating 2×), `opaque`, `zero`, `binary_nonzero`, and `binary_ge64`. **The tool does not choose a writer policy.** Individual identities, pixels and per-texture scores stay private. Summary of the complete original 106-pair audit:

| Carbon PC format | Matched textures | DXT alpha finding | Section 141 double-alpha per-texture MAE | Section 142 double-alpha per-texture MAE |
| --- | ---: | --- | ---: | ---: |
| DXT1 | **66** (29+37) | All 66 decoded PC textures are fully opaque, notwithstanding varied PS2 palette alpha | 154.5754 | 151.5104 |
| DXT3 | **6** (1+5) | Saturated 2× candidate is the best of six tested interpretations in every pair | 3.4839 | 7.9322 |
| DXT5 | **34** (6+28) | Strong group difference; 2× alone does not explain section 142 | 1.7752 | 49.4980 |

These averages are **per texture**, not pooled per-pixel, and use the lower-resolution source image grid. DXT1's result proves that the PC DXT1 output is opaque; it does **not** prove that the PS2 alpha bits are meaningless to the PS2 renderer. DXT3/5 values remain cross-platform comparison statistics, not a verified renderer/blending specification. Some texture art and alpha mask channels may differ across platforms. A universal alpha correction **must not** be enabled on these results.

## 2. Undercover PS2 dual-section visual consistency

`undercover_texture_variant_visual_control.py` reopens original Undercover PS2 secondary `TRACKS/L2RB.BUN` and `STREAML2RB.BUN`, validates CRC, exact section bounds and the known 120-byte aligned pixel-data base, and decodes each section's **own** texture bytes and palette with its recorded swizzle flag. It samples section 241 at normalized pixel centers on section 3401's lower-resolution grid; alpha is compared using **raw PS2 alpha** on both sides, without doubling. Results across all **46** original shared identities:

| Verified aggregate | Observed |
| --- | ---: |
| Independently decoded pairs | **46/46** |
| Source dimension relationship | **2× width and 2× height** in section 241, every pair |
| Mean RGB MAE | **5.0890 / 255** |
| Median / maximum RGB MAE | **4.0365 / 14.1839** |
| RGB MAE below 10 / below 20 | **45/46** / **46/46** |
| Mean raw PS2 alpha MAE | **2.9330 / 255** |
| Naive linear-layout baseline RGB MAE | **17.8841 / 255** |
| Identical raw palettes between sections | **1/46** |
| 4-bit pairs | 34, mean RGB **5.3669** |
| 8-bit pairs | 12, mean RGB **4.3016** |
| Swizzle flag pair counts, 241/3401 | 45 × `1/1`, 1 × `1/0` |

This supports **internal color and alpha consistency** across two independently stored PS2 texture versions even though 45/46 original palettes are byte-distinct. It is a far stronger Undercover-specific check than merely obtaining correctly sized RGBA buffers. It does **not** independently prove that either texture is sampled or blended identically in the original PS2 engine, nor that its PC writer/shader equivalent is known.

## 3. Undercover PS2 exact mip-chain boundaries and same-sized levels

`ps2_mip_chain_control.py` splits the validated image byte span strictly according to each record's dimensions, bit depth and mip count; the decoder takes the recorded flag for **each level**, and rejects truncated data or layouts with unwritten GS addresses rather than making up bytes.

| Original Undercover section | Texture records | Fully decoded mip buffers | Extra buffers beyond base |
| --- | ---: | ---: | ---: |
| 241 | 46 | **50** | **4** |
| 3401 | 46 | **49** | **3** |
| **Total** | **92** | **99/99** | **7** |

Each section contains **45** single-level textures. The remaining texture has **5** levels in 241 (base 256×128) and **4** in 3401 (base 128×64). The four equal-sized pairs are 241 levels **1–4** versus 3401 levels **0–3**; RGB MAEs range **1.4022–1.5417 /255**, average **1.4765**, and mean raw alpha MAE is **2.7795**. These are *independently reconstructed, same-sized* source textures. This validates practical level splitting and decoded cross-section appearance for the one sampled multi-mip identity, not general PS2 non-base mip GPU conventions for all possible dimensions/codecs.

## Tests and reproduction

All **121/121 synthetic-only** tests under the current focused research workspace pass locally, including **38 new** tests across the alpha (14), cross-variant (10) and mip (14) modules. These are source-free fixtures with deliberate malformed metadata, wrong dimensions, wrong flags and truncated mip payloads. The original-source comparison ran separately against the owner's actual Carbon PC split ZIP, Carbon PS2 ZIP and Undercover PS2 ZIP. It is not included in CI, because game archives stay private.

From the repository root:

```sh
python -m unittest discover -s research/world_bridge -p 'test_carbon_ps2_alpha_provenance_audit.py' -v
python -m unittest discover -s research/world_bridge -p 'test_undercover_texture_variant_visual_control.py' -v
python -m unittest discover -s research/world_bridge -p 'test_ps2_mip_chain_control.py' -v

# Read-only original archive audits. Prints aggregate statistics, no images.
python research/world_bridge/carbon_ps2_alpha_provenance_audit.py \
  --pc-volumes /private/carbon_pc/TRACKS.z01 /private/carbon_pc/TRACKS.z02 \
  /private/carbon_pc/TRACKS.z03 /private/carbon_pc/TRACKS.zip \
  --carbon-ps2-zip /private/carbon_ps2/TRACKS.zip
python research/world_bridge/undercover_texture_variant_visual_control.py \
  --undercover-ps2-zip /private/undercover_ps2/TRACKS.zip
python research/world_bridge/ps2_mip_chain_control.py \
  --undercover-ps2-zip /private/undercover_ps2/TRACKS.zip
```

## What is NOT yet solved

- There is no independently validated **PS2 alpha-to-Carbon PC material/texture writer policy**, and the substantial section-142 DXT5 mismatch needs further research.
- The native Carbon PC DXT texture serializer/writer, shader addressing and in-game texture streaming are not implemented in this work.
- Mips beyond those present in the two validated Undercover sections, especially tiny 4-bit swizzled levels requiring unmapped GS memory, remain unsupported on purpose.
- No game archive modified, no original source pixels shipped, no renderer/runtime recognition verified, and no playable Tri-City Bay build created. Keep PR #33 **draft**; leave `main` unchanged.

**Suggested next falsifiable gate:** create a source-free PC DXT1 writer and round-trip validator for an *opaque synthetic* texture first, then privately generate one selected Undercover image and check its native stream-resource framing and runtime dependencies. Preserve alpha as a separate, explicitly unresolved gate for translucent/masked materials.
