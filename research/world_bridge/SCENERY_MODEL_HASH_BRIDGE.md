# Scenery model-hash slot and instance-index bridge

**2026-11-03. Original archive analysis, source-only.** The script and synthetic tests do not export, patch or distribute any game's binary assets. All numbers below are grounded in the owner's actual Carbon PC/PS2/Wii and Undercover PS2/Wii RB streaming archives, using the existing bounded section and tree checks. No PC runtime model lookup, texture resolution, rendering, collision, AI or complete port has been demonstrated.

## Reproducible command

```sh
python research/world_bridge/scenery_model_hash_bridge.py \
  --pc-volumes /private/carbon_pc/TRACKS.z01 /private/carbon_pc/TRACKS.z02 /private/carbon_pc/TRACKS.z03 /private/carbon_pc/TRACKS.zip \
  --carbon-ps2-zip /private/carbon_ps2/TRACKS.zip \
  --carbon-wii-volumes /private/carbon_wii/TRACKS.z01 /private/carbon_wii/TRACKS.zip \
  --undercover-ps2-zip /private/undercover_ps2/TRACKS.zip \
  --undercover-wii-zip /private/undercover_wii/TRACKS.zip
python -m unittest discover -s research/world_bridge -p 'test_*.py' -q
```

The work is deliberately restricted to the **47 previously validated RB scenery roots**, not a full map or any RA scene beyond the earlier Z0 checks. Root chunks and section stream locations are validated by `rb_scenery_graph_census.py`. The new source-only probe checks each `0x34102` info record has a 72-byte stride and each `0x34103` instance record has a 96-byte stride after its 4-byte `0x11111111` prefix. It reads a candidate signed 16-bit info index at **instance +0x54** and rejects negative or out-of-range references.

## Primary result: a four-byte Carbon PC field difference

The public reconstructed Most Wanted source identifies a 72-byte `SceneryInfo` with an array of four model hashes at offsets **+0x18, +0x1c, +0x20, +0x24** and 72-byte total stride. Its runtime loader iterates those four slots when resolving model references. That is **other-game reconstructed-source terminology**, not conclusive evidence of Carbon PC's runtime ABI.

In the matching original Carbon RB scene root info arrays:

| Comparison | Common scene IDs | Equal-size info arrays | Arrays identical **before** | Arrays exact after copying slot 1 → slot 0 | Matched info records |
| --- | ---: | ---: | ---: | ---: | ---: |
| Carbon PC vs Carbon PS2 | 13 | 12 | 0 | **12** | **640/640** |
| Carbon PC vs Carbon Wii | 13 | 11 | 0 | **11** | **579/579** |

The entire **640-record Carbon PS2 control payload** becomes byte-for-byte identical to the corresponding Carbon PC `0x34102` payload by copying only the u32 at offset **+0x1c** into **+0x18** in each 72-byte record, leaving all other bytes unchanged. The independently provided Wii version reconstructs **579/579** such records in 11 scenes. The special Z0 scene and additional Wii/PS2 divergence have different info array lengths, so they were deliberately excluded from same-size identity claims.

The in-memory operation is **not** applied to the user's actual files, and the source code refuses records if source slot 0 is nonzero or source slot 1 is zero. The real original-console arrays all satisfy those guards.

## Complete five-platform RB overview

| Source | Scene roots | Scenery info records | Instances | Valid in-bounds instance → info references | Hash slot 0 nonzero | Slot 1 = slot 2 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Carbon PC | 13 | 643 | 643 | 643 | **643** | 643 |
| Carbon PS2 | 14 | 655 | 655 | 655 | 0 | 655 |
| Carbon Wii | 14 | 654 | 654 | 654 | 0 | 654 |
| Undercover PS2 | 3 | 263 | 275 | 275 | 0 | 259 |
| Undercover Wii | 3 | 261 | 273 | 273 | 0 | 257 |
| **Total** | **47** | **2,476** | **2,500** | **2,500** | **643** | **2,458** |

For all **643** Carbon PC records in the examined RB scenes, slot 0 equals slot 1, which equals slot 2, and is nonzero. In all original PS2/Wii records inspected, slot 0 is zero; slot 1 is nonzero. Undercover has a small number of records with differing hashes at slots 1 and 2 (four per source); **the bridge does not overwrite either existing donor slot**, only copies slot 1 into empty slot 0.

### Instance-to-info mapping is not identity in Undercover

At +0x54 within the 96-byte instance candidates, every value points to a local valid 72-byte info record:

- Carbon PC: **643/643** references valid, and all 643 happen to match the instance's ordinal.
- Carbon PS2: **655/655**, all identity.
- Carbon Wii: **654/654**, all identity.
- Undercover PS2: **275/275** valid but only **17** equal the instance ordinal; all **263** info records are targeted.
- Undercover Wii: **273/273** valid but only **17** equal the instance ordinal; all **261** info records are targeted.

The important conversion rule is to **preserve the donor's actual signed 16-bit info indexes**. Sequentially renumbering Undercover's instances would disconnect reused model-information records. This differs from the reconstructed Most Wanted `SceneryInstance` 64-byte layout, whose analogous field is at +0x3e. The observed Carbon/Undercover **96-byte** instance format must take precedence over extrapolating another game's struct.

## Next test gates

1. Identify the actual model resources for the Undercover slot-1 hashes inside its Wii/PS2 geometry packs and trace how Carbon PC's loader resolves its model hash slots. **Matching numeric hashes alone is not proof the models exist on the PC side.**
2. Cross-reference these instance scene IDs with the five-source `0x80034150` visibility tables; preserve all Undercover donor section coordinates and their original instance-to-info links.
3. Test complete **two-root** Carbon PC control packaging and a reversible synthetic test scene without writing to game files or claiming in-game success.

## Quality

**17/17 new synthetic-only tests passed locally. The aggregate world-bridge test suite passes 118/118.** The real archive-backed probe completed and reproduced all comparison counts. All original archives and their extracted members stayed private.

Other-game source references (for possible field terminology only):
- [Most Wanted Scenery.hpp](https://github.com/dbalatoni13/nfsmw/blob/main/src/Speed/Indep/Src/World/Scenery.hpp)
- [Most Wanted Scenery.cpp loader](https://github.com/dbalatoni13/nfsmw/blob/main/src/Speed/Indep/Src/World/Scenery.cpp)
