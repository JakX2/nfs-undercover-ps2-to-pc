# Carbon PC versus PS2 streamed texture-index presence

**2026-11-03, read-only original-source research.** Source archives were inspected privately; no game textures, pixels, models, source hash inventories or executable patches are distributed. The attached parser is intentionally bounded and does not decode texture pixels or write game files.

## What the source data establishes

In the original Carbon PC split `TRACKS` archive and Carbon PS2 `TRACKS.zip`, the secondary-area sections **141** and **142** each begin with a complete `0xB3300000` texture-pack root. Its immediate children are two type-zero framing records, a `0xB3310000` descriptor root, and a `0xB3320000` texture-data resource. The descriptor root contains four ordered children: `0x33310001`, **`0x33310002` index**, `0x33310004`, and `0x33310005`.

The `0x33310002` payload consists of sorted, unique **8-byte entries**: a nonzero u32 texture hash followed by a zero pointer word. All four source indexes satisfy these invariants. Only the index layout is interpreted here; the other descriptor and texture-pixel bytes remain opaque.

| Original Carbon RB section | Source solid references (distinct hashes) | PC texture index hashes | PS2 texture index hashes | Referenced but absent from local PC index | Referenced but absent from local PS2 index |
| --- | ---: | ---: | ---: | ---: | ---: |
| **141** | 38 | **37** | **36** | 1 | 2 |
| **142** | 88 | **73** | **70** | 15 | 18 |

For both control sections, the complete **per-solid texture-hash tables are identical between PC and PS2**. All four section-local indexes contain only texture hashes that their local solids reference. At both sections, the PS2 index is a strict subset of the corresponding PC index: **one additional PC-indexed texture** in 141, **three more** in 142. No PS2-only index hash was found in these controls.

Across the two sections combined, there are **126 distinct solid-referenced texture hashes**, **110 distinct PC-indexed hashes**, and **106 distinct PS2-indexed hashes**. Exactly **four** additional unique hashes occur in the union of the PC indexes. There are **16** solid-referenced hashes absent from *both local PC texture indexes* and **20** absent from *both PS2 indexes*. These are **not proven missing game textures**. They may live in other section streams, global assets, shared texture packages or additional loading paths not decoded here.

The full PC and PS2 texture pixels differ in serialized size and data; byte-level format conversion and addressing/sampling semantics are unproven. A texture hash in a local index establishes serialized identity *presence*, not that a particular runtime load succeeds.

## New source-only parser and synthetic tests

- `research/world_bridge/texture_pack_index_probe.py` checks a complete anchored `0xB3300000` frame, nested descriptor order, complete and bounded children, nonempty opaque texture data, an 8-byte sorted hash index with zero pointer words, and defensive maximum sizes.
- `research/world_bridge/test_texture_pack_index_probe.py` contains **18 synthetic-only tests**, all passing locally. The fixtures deliberately contain **no game bytes**. Tests cover altered parent lengths, bad nested layouts, duplicate/zero/unsorted index keys, nonzero pointer words, empty pixel data, extra uninterpreted section bytes, duplicate source texture references, and local-index coverage counts.
- The checker exposes pure functions that report **aggregate coverage counts** without exporting any of the hashes. It does **not** automatically conclude that an absent local index entry is a missing global resource.
- The exact two committed Python blob SHA-1 values were checked against locally tested files. **No clean-checkout CI or integrated CLI run is claimed for this new pure parser.**

The aggregate original-archive counts above were independently obtained from the source stream roots, their nested complete chunk boundaries, the per-solid `0x134012` texture tables and the source index entries. The earlier full original-file `triangle_corner_uv_control.py` validated **114,701** one-to-one Carbon PS2 face matches against PC with XYZ, per-corner periodic UV, and texture-table identity. The new index presence check **adds packaging/resource coverage**, not a second face-match proof.

## Why this matters for Tri-City Bay

A converter must not assume the donor model's needed texture is necessarily inside the model's own section. It must preserve the occurrence-specific per-solid texture table, then separately build and validate the PC-side texture pack/resource dependencies. A donor model hash can also identify *multiple texture-table variants* in the original Undercover PS2 data; mapping by hash alone can overwrite valid material contexts.

**Next falsifiable experiment:** parse the indexed `0x33310004` texture metadata records on two independent PC/PS2 source controls, establish relationships between each index hash and its texture-data payload in `0xB3320000`, then investigate the pixel and sampler-mode differences. Only after confirming texture resource availability and the expected native PC format should a reversible private single-model donor-texture conversion be considered.

No Undercover model has been shown rendering inside Carbon PC yet; texture conversion, runtime registration, collision and traffic remain separate incomplete gates.
