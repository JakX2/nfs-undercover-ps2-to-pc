# Aligned indexed-pixel reconstruction: Carbon controls and Undercover coverage

**2026-11-03. Read-only original-source audit and synthetic regression tests.** All archives were provided by the owner. No original texture bytes, palettes, names, hash inventories, screenshots, model assets, game files or executable patches are committed.

## Corrected pixel-data origin

The earlier `texture_visual_pair_gate.py` treated the first byte of the `0x33320002` payload as image offset zero. This was **incorrect** for all six original Carbon/Undercover streamed texture-pack controls.

- In Carbon PC sections **141/142**, Carbon PS2 **141/142**, and Undercover PS2 **241/3401**, the chunk payload starts 8 bytes past a 128-byte boundary, followed by **120 bytes of `0x11` filler** before the actual pixel/palette array.
- The offsets in `0x33310004` are **relative to the 128-byte-aligned interior base**, not the raw start of the chunk payload. A total-size check against the untrimmed chunk can pass even while decoding from a wrong byte origin.
- New `texture_pixel_base_alignment.py` preserves absolute section-relative chunk positions, computes `(payload_start+127)&~127`, verifies all bytes of filler, and **rechecks each image and palette span against the corrected base**. No offset guessing or silent fallback.
- The earlier metadata-only **308/308 image** and **198/198 palette range** checks remain valid structural observations, but did **not** validate the correct pixel-data origin. This new gate closes that gap for the six packs.

## Decoding path supported by Carbon original-source controls

| PS2 platform `0x33310005` byte `+0x17` | Indexed codec | Candidate source interpretation | Palette order |
| --- | --- | --- | --- |
| `0` | PSMT4 / PSMT8 | Row-major linear indices | Linear / CSM1 respectively |
| `1` | PSMT4 (`0x14`) | PSMCT16 transfer at `(width/2,height/2)`, read from virtual GS as PSMT4 | Linear 16-entry |
| `1` | PSMT8 (`0x13`) | PSMCT32 transfer at `(width/2,height/2)`, read as PSMT8 | CSM1 256-entry |

The new `ps2_ct16_transfer_candidate.py` implements the missing PSMCT16 upload path with bounded GS page/block/column addressing, checked address initialization and synthetic reference vectors. It complements the existing CT32/PSMT8 decoder. Metadata flags are used explicitly, and unknown flags fail closed. Two original Carbon PS2 textures with `+0x17 = 0` are small and correctly decode using a linear path.

## Full original Carbon PC ↔ Carbon PS2 control: 106/106

Matching source texture identity and name, original Carbon PC DXT1/DXT3/DXT5 **base mip** images were decoded and compared at normalized PS2 pixel centers. The results are **not bit-exact texture equivalence**: the platforms use distinct encodings, sizes, filtering and potentially different alpha/material behavior.

| Original section | PS2 indexed depth | Paired and decoded | Correct-path RGB MAE (0–255) | Naive linear RGB MAE |
| --- | --- | ---: | ---: | ---: |
| 141 | 4-bit | **26/26** | **6.6295** | 29.3494 |
| 141 | 8-bit | **10/10** | **3.6544** | 34.7243 |
| 142 | 4-bit | **55/55** | **5.7368** | 22.2231 |
| 142 | 8-bit | **15/15** | **2.8578** | 34.0929 |

- **106/106 original shared identities decoded**; source swizzle flag distribution: **104 flag 1** and **2 flag 0**.
- All **106 RGB errors are below 20/255**. Total mean per-texture RGB MAE: **5.8031** in section 141; **5.1199** in section 142, compared with naive linear baselines **30.8425** and **24.7667**.
- The `double` palette-alpha candidate is **not** PC alpha-equivalent: four format/section groups have mean alpha errors approximately **85–140/255**. Alpha usage and transparency remain unresolved. These numbers do not justify writing an opaque replacement texture.
- Mipmap levels beyond the base mip, PC texture-pack serialization and in-game rendering have **not** been validated.

## Original Undercover PS2 donor sections: 92/92 base-image buffers

All 92 original indexed images build full-sized RGBA **base** buffers without address/format/range failure:

| Original donor section | Total records | 4-bit CT16 transfer | 8-bit CT32 transfer | 4-bit linear | Decoded base buffers |
| --- | ---: | ---: | ---: | ---: | ---: |
| **241** | 46 | 34 | 12 | 0 | **46/46** |
| **3401** | 46 | 33 | 12 | 1 | **46/46** |

The Undercover source packs have the same verified **120-byte aligned-base padding** and share **46 identities**, with **different resolutions** for every same-hash pair. These are two versions: the converter must retain section provenance, mip count and resolution. Unlike Carbon, there is no corresponding same-art Carbon PC texture for a color-fidelity comparison. **An RGBA buffer of the expected length is not proof of Undercover visual correctness.**

## Reproduce (original source archives remain private)

From the repository root, run the six source-free test modules:

```sh
python -m unittest discover -s research/world_bridge -p 'test_ps2_ct16_transfer_candidate.py' -v
python -m unittest discover -s research/world_bridge -p 'test_texture_visual_pair_gate.py' -v
python -m unittest discover -s research/world_bridge -p 'test_carbon_ps2_texture_color_control.py' -v
python -m unittest discover -s research/world_bridge -p 'test_undercover_ps2_texture_layout_coverage.py' -v
python -m unittest discover -s research/world_bridge -p 'test_texture_original_archive_pair_audit.py' -v
```

For owner-only original-source read-only checks:

```sh
python research/world_bridge/carbon_ps2_texture_color_control.py \
  --pc-volumes /private/carbon_pc/TRACKS.z01 /private/carbon_pc/TRACKS.z02 \
    /private/carbon_pc/TRACKS.z03 /private/carbon_pc/TRACKS.zip \
  --carbon-ps2-zip /private/carbon_ps2/TRACKS.zip

python research/world_bridge/undercover_ps2_texture_layout_coverage.py \
  --undercover-ps2-zip /private/undercover_ps2/TRACKS.zip
```

These tools return aggregate counts/metrics only. The real six-original-pack audit and **83/83 synthetic tests** in the isolated continuation workspace passed. This is **not** a claim that a clean GitHub checkout CI run or Carbon PC runtime test has passed.

## Remaining falsifiable gates

1. Recover PS2 **alpha/alpha-usage/blend** behavior and establish shader-equivalent PC output; avoid hardcoding opaque alpha.
2. Decode and verify every original **mipmap level** (including small GS transfer buffer edge cases and Undercover's one five-versus-four-level identity pair).
3. Implement a **separate native Carbon PC DXT texture writer** with original reference metadata and reversible private tests.
4. Load one original Undercover texture through Carbon PC's real texture/resource system; verify shader UV/sampler behavior, then world-sector and collision integration.

**Keep PR draft.** No game asset modifications or proprietary exports. The decoder gates are evidence for a candidate, not an installable PC port.
