# PS2 VIF strip decoding control: Carbon and Undercover world solids

**Read-only original-archive audit, 2026-11-03.** This research uses the owner's locally supplied Carbon PS2 and Undercover PS2 world archives. The only committed artifacts are original source-only tools, synthetic tests, and aggregate statistics. No original model/vertex/UV bytes, per-model hash lists, extracted game files or executable patches are published. **This is not a rendered or playable Undercover world in Carbon PC.**

## Reproduce locally

From repository root, with original owner-provided archives stored privately:

```sh
python research/world_bridge/vif_strip_probe.py \
  --carbon-ps2-zip /private/Carbon_PS2_TRACKS.zip \
  --undercover-ps2-zip /private/UC_PS2_TRACKS.zip

python -m unittest discover -s research/world_bridge -p 'test_*.py' -q
```

The tool revalidates the original RB scenery roots and stream-section rows before accessing only these sources:
- Carbon PS2 `L5RB` sections **141** and **142**; one authenticated geometry pack in each.
- Undercover PS2 `L2RB` sections **241** and **3401**; four authenticated geometry packs in each.

Every solid is first checked through the existing model hash → sorted geometry index → embedded solid-header hash chain. Every 16-byte `0x00134A01` strip descriptor must have a bounded QWORD interval within its parent `0x00134A02` strip-data payload. The new reader parses actual VIF instruction words and UNPACK payload lengths within those exact intervals, with a maximum 4 KiB packet, 512 operations per packet and errors on unknown commands, invalid counts or out-of-bounds data. It never writes original inputs.

## Original-file results

| Original source and RB section | Complete VIF strips | Candidate position vertices | Reconstructed ST/UV pairs | ADC-filtered candidate triangles |
| --- | ---: | ---: | ---: | ---: |
| Carbon PS2 141 | 3,521 | 100,464 | 100,464 | **54,484** |
| Carbon PS2 142 | 3,736 | 104,539 | 104,539 | **60,217** |
| Undercover PS2 241 | 2,031 | 54,737 | 54,737 | **38,205** |
| Undercover PS2 3401 | 2,025 | 54,619 | 54,619 | **38,143** |
| **Total** | **11,313** | **314,359** | **314,359** | **191,049** |

All **11,313/11,313** strips passed the VIF opcode parser, candidate header-to-descriptor vertex counts, SoA XYZ row/tail layout, ST/UV row/tail layout and optional V4-8 color block bounds. All **81,960** identified UNPACK operations were within their own strip packet boundaries.

All candidate XYZ reconstructions are finite and have position minima/maxima within **0.1 source game units** of each packet's serialized bounding box. The coordinates are **still candidate coordinates**, because the 16-bit vertex anchor is reconstructed by rounding a value inferred from the stored bound; it has not been matched to a native Carbon PC vertex buffer. The original bounding boxes appear to include a small tolerance/margin, so do not assume their endpoints are exact vertex extrema.

Of the 11,313 packets, **11,302** use V4-16 candidate XYZ and **11** use V4-32 float candidate XYZ: 1 in Carbon PS2 section 142, 5 in Undercover PS2 section 241, and 5 in Undercover PS2 section 3401. Both layouts passed the coordinate and packet bounds checks.

### ADC triangle suppression is source-consistent on all tested packets

The VIF control row stores candidate per-vertex ADC suppression bits in a nontrivial, pack-count-dependent layout. In every sampled strip, decoding those flags yields exactly the number of triangles specified in the independently parsed `0x00134A01` descriptor:

| Source section | Raw candidate triangles (vertices − 2 per strip) | Suppressed by ADC flags | Triangles surviving ADC |
| --- | ---: | ---: | ---: |
| Carbon PS2 141 | 93,422 | 38,938 | **54,484** |
| Carbon PS2 142 | 97,067 | 36,850 | **60,217** |
| Undercover PS2 241 | 50,675 | 12,470 | **38,205** |
| Undercover PS2 3401 | 50,569 | 12,426 | **38,143** |
| **Total** | **291,733** | **100,684** | **191,049** |

The reader can construct candidate triangle index triplets in RAM after applying the ADC mask. **Their winding/parity has not yet been compared directly with Carbon PC's real `0x00134B03` triangle indices**, and normal/material interpretation remains unresolved. Matching polygon counts are necessary but not sufficient for mesh equivalence.

## Structural layout supported by the real packets

These observed VIF destinations are consistent with the independent Most Wanted PS2 research:
- Destination **0**: V4-8 strip vertex count and vertex packing control.
- Destination **1**: V4-32 control words (a float32 scaling word and candidate triangle suppression bit words).
- Destination **2**: two V3-32 candidate bounding-box rows.
- Destination **5** and partial-row destinations: XYZ in groups of four vertex lanes, with 16-bit or 32-bit components.
- Destination **29** and partial-row destinations: signed 16-bit ST values forming UV candidates with scale 1/4096.
- Destination **45**: V4-8 per-vertex color payload, present in all 11,313 tested packets.

The decoder handles three-vertex strips, full groups of four, and one/two/three-vertex partial groups, with verified exact lane counts. It does **not** promise to decode other games' arbitrary VIF traffic, unusual cyclic UNPACK programs, textures, skinning or all possible model formats.

## Quality and reference

**239/239 synthetic world-bridge tests pass locally**: 219 prior tests and **20 new synthetic-only VIF tests** covering signed/unsigned UNPACK values, variable packed vertex groups, UV lanes, ADC suppression, candidate triangle construction and rejection of malformed packets. The full original-file audit also completed successfully after tightening the bounds check. Both exact locally tested Python files were compared with GitHub blob SHA-1s and matched byte-for-byte.

Independent reference research (conceptual, not wholesale copied source):
- [Rockport Native / Most Wanted PS2 port by Pablo Nolasco and contributors](https://github.com/pablonolascoo/nfs-mw-2005-ps2-port), notably `tools/src/lib/vif.ts` and `tools/src/lib/solid-ps2.ts` (MIT-licensed).
- [Most Wanted reconstructed PS2 eSolidPlat.hpp](https://github.com/dbalatoni13/nfsmw/blob/main/src/Speed/PSX2/Src/Ecstasy/eSolidPlat.hpp), whose older-game comments explicitly caution that type offsets may not apply unchanged to every title.

**Next falsifiable gate:** identify the actual native PC 36-/52-byte vertex attribute layouts and 144-byte mesh record index ranges in the **two known same-hash Carbon controls**, compare recovered PS2 triangle positions/UVs against PC's actual vertex/index representation, and distinguish true winding errors from duplicated/degenerate strip triangles. Only after two source-pinned geometry controls pass a full cross-platform comparison should a reversible **synthetic-only** PC mesh writer be attempted.

**Not achieved:** verified native PC vertex equivalence, exact triangle parity/winding, normals, materials, texture bindings, authored PC mesh output, gameplay rendering, collision, traffic, or complete Undercover-to-Carbon PC integration.
