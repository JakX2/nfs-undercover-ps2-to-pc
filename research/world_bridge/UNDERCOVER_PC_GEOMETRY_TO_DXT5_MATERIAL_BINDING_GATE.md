# Original Undercover geometry → PC DXT5 material-image binding gate

**Status: private original-archive source control PASSED, 42/42 new synthetic tests passed locally, retail loader/rendering UNVERIFIED.** This is an **offline** byte/identity join, **not** a native Carbon PC texture-registration implementation, installed mod, or gameplay proof.

## Falsifiable question

The earlier research constructed (1) eight separate Carbon-PC-shaped `0x80134000` geometry roots containing all 268 source eSolid occurrences, and (2) a parser-valid PC `0xB3300000` DXT5 texture root containing all 46 original Undercover RB image identities. The source scenery geometry actually uses 48 distinct material texture identities. **How much converted geometry is covered by genuine original-source candidate images, and which original pack partitions are complete?**

The new `undercover_pc_material_image_binding_gate.py` accepts **private** PC-shaped candidate bytes, checks exact sorted texture index and DXT5 image metadata/alignment, then walks **every source-derived PC eSolid** and its original per-solid texture table. The original primary source model identities and eSolid occurrences stay intact. PC native 36-byte vertex/index data is checked with `inspect_pc_solid` and a separate strict PC 144-byte material-mesh triangle/index budget. Each actual used mesh material table index is resolved to the candidate texture identity or counted as unbacked. **Unused material table entries do not count as missing geometry resources.** Repeated IDs across separate model packs are not deduplicated by hash.

The identity provenance check independently compares the complete candidate DXT5 index with the original PS2 source image index. `--require-complete` **fails closed** on any referenced missing image rather than claiming a 48/48 registration. Reports are counts only: no model or texture hash inventories, image names/pixels, raw coordinate data, stream offsets, ZIP locations, or input file paths.

## Original-owner Undercover PS2 archive test

Source: the owner's original Undercover PS2 `TRACKS.zip`, specifically CRC-checked `L2RB.BUN` and `STREAML2RB.BUN` entries and complete validated source stream section rows **241** and **3401**. Original contents were loaded and converted privately, in memory, using the established PS2 VIF decoder and the candidate Carbon PC root/native mesh/texture writers. Four geometry packs per source section were retained. The original ZIP fingerprint was identical before and after the read-only audit. **Generated game bytes never went into the source-only ZIP/GitHub PR.**

| Measurement | Section 241 | Section 3401 | Combined |
|---|---:|---:|---:|
| Original / converted geometry packs | 4 | 4 | **8** |
| Original / converted eSolid occurrences | 135 | 133 | **268** |
| PC material mesh occurrences | 158 | 155 | **313** |
| Converted triangles, all originals preserved | 38,205 | 38,143 | **76,348** |
| Triangles with a PC candidate DXT5 image identity | 37,230 | 37,168 | **74,398** |
| Triangles referencing an unavailable candidate image | **975** | **975** | **1,950** |
| Meshes referencing an unavailable image identity | 20 | 20 | **40** |
| Fully image-backed geometry packs | **3 / 4** | **3 / 4** | **6 / 8** |

**Source candidate identity coverage: 46/48 used material identities** (two unresolved), and **74,398/76,348 = 97.4459%** of converted triangle occurrences. Image-backed material meshes: **273/313**. All **46** candidate image identities exactly match the original Undercover source image index. The PC-shaped DXT5 candidate root contains **1,176,688 bytes**, with four requested mip levels and strict metadata/range/readback checks.

### Critical pack-local result

| Source geometry pack ordinal | Section 241 | Section 3401 | Candidate material image binding |
|---|---:|---:|---|
| Pack 1 | 35,818 triangles | 35,787 triangles | All backed |
| **Pack 2** | **2,278 triangles** | **2,278 triangles** | **1,303 backed / 975 unresolved, in each section** |
| Pack 3 | 41 triangles | 10 triangles | All backed |
| Pack 4 | 68 triangles | 68 triangles | All backed |

The six fully backed packs contain **71,792 triangles**. The two incomplete packs contain **4,556**, of which **2,606 have valid candidate image identities**. They must not be silently deleted, rewritten to arbitrary images, or mistaken for wholly unresolved geometry. Pack ordinals are private source-sequence ordinals and do not establish runtime loading order or game streaming lifetime.

The model identity count is **134 distinct hashes across 268 eSolid occurrences**. Repeated source model identities across the two source sections and an additional repetition across independent packs must be preserved, not used as a deduplication key. This gate preserves pack and model occurrence order, and the independent PC geometry index parser checks each pack.

## Run the read-only original-source audit privately

With all required project `research/world_bridge` Python dependencies available:

```bash
python research/world_bridge/undercover_pc_material_image_binding_gate.py \
  --undercover-ps2-tracks-zip "PATH_TO_PRIVATE_UNDERCOVER_TRACKS.zip"
```

To deliberately test the **fail-closed** complete-registration boundary, append `--require-complete`. Since the original donor currently has two unresolved material texture identities, that mode should refuse completion. It never writes, installs or patches a game file. It prints **aggregate JSON only**.

Run the new regression suite without copyrighted game data:

```bash
PYTHONPATH=research/world_bridge python -m unittest discover \
  -s research/world_bridge -p 'test_undercover_pc_material_image_binding_gate.py' -v
```

## Important boundaries and next required experiments

- **Supported:** source-index identity correspondence between converted PC-shaped geometry/material entries and a parser-valid candidate DXT5 pack for 46 original Undercover RB image identities; full per-mesh triangle budget accounting and original-file read-only integrity.
- **Not supported:** actual Carbon PC texture registration, resource-cache behavior, material sampler/blend correctness, cross-sector scene registration, retail eSolid/texture descriptor ABI, PC shader rendering, collision, traffic/AI, camera/road navigation, or a playable Undercover world.
- **Still unresolved:** the two actually used material identities absent from validated Undercover original TRACKS RA/RB image indexes. Their **1,950 source triangle occurrences** across both source sections are *not* evidence that the original game lacked these images globally. No replacement image, missing identity or material was invented.
- **Next engineering boundary:** source-backed native Carbon PC texture header/registration validation and a private, reversible scene/stream experiment. Keep **all eight** source geometry partitions, even if choosing the six fully image-backed partitions as an isolated **offline test subset**. Never claim the subset is a registered or visually rendered game sector.

The original game archives remain owner-private. The research PR remains **draft**, and `main` must not be modified or merged from this measurement alone.
