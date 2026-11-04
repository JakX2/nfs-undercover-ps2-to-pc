# Carbon PC DXT5 source-scene spatial smoke-test target gate

**Status:** Read-only, source-backed offline candidate. **NOT** proof of game visibility, a playable camera location, renderer behavior, or Undercover map conversion. Original user-owned game archives, decoded models, texture hashes, game-world positions and edited stream files are not included in this repository or handoff.

## Why this gate exists

The preceding `carbon_pc_dxt5_material_target_rank.py` joins a Carbon PC DXT5 texture slot to PC eSolid texture tables, material triangle counts, and primary scenery-instance model identities. It favored **section 142, zero-based DXT5 slot 16** (12 locally referencing models), but that source-material count did not establish where those objects occur. This gate adds bounded interpretation of the **96-byte scenery instance AABB candidate** and the **48-byte 0x34105 scene spatial tree**, independently verifying each leaf's bounds fit its parent nodes.

## Original user-owned source controls, kept private

The original Carbon PC split `TRACKS.z01`/`.z02`/`.z03`/`.zip` data was used to extract `TRACKS/L5RB.BUN` and `TRACKS/STREAML5RB.BUN` into a **private local directory**, with both decompressed member sizes and CRC32s checked. The original stream was **82,837,504 bytes**. The resulting original section-table intervals were used to inspect sections 141 and 142. Original game assets and private extracted copies remain outside this source package.

| Source-backed observation | Carbon PC section 141 | Carbon PC section 142 |
|---|---:|---:|
| 96-byte scenery instance records | 29 | 103 |
| Candidate 48-byte spatial tree nodes | 7 | 26 |
| Indexed original PC DXT5 slots | 6 | 28 |
| DXT5 slots with a primary scenery/material spatial join | 6 / 6 | 28 / 28 |
| Instance AABBs contained by validated nested tree parent bounds | 29 / 29 | 103 / 103 |

The candidate AABB bounds are the three IEEE-754 `float32` values at **instance row +0x00** (minimum), and the three at **+0x10** (maximum), *relative to the 96-byte instance record after its four-byte 0x11 stream prefix*. A node's own minimum comes from tree row +0x00 and maximum from +0x10, with a child count at +0x0c and ten signed `int16` child reference slots beginning at +0x1c. Negative codes point to nested tree nodes; nonnegative codes are instance ordinals. The source-free validator checks finite ordered extents, parent inclusion for **all leaves and nested nodes**, strict tree connectivity and exactly-once leaf references. The 0.001-unit inclusion tolerance covers floating-point rounding only.

**Specific test target:** Carbon PC section **142 / DXT5 ordinal 16**, the 128×64 four-mip source slot already selected for Undercover PS2 donor **section 241 / donor ordinal 31** by the earlier read-only archive/material controls.

- **12** distinct primary-model instance references and **328** local PC source-material triangle references. Instance AABBs in this sample have overall candidate extent **37.105 × 5.969 × 2.893** in source coordinate axes.
- A deliberately chosen **12 source-coordinate-unit center-distance threshold** produces **two components of six instances**. Their AABB-center means are separated by **33.644 source-coordinate units**. These populations are unchanged when the test threshold is varied between **5 and 30** units. This is a reproducible *proximity heuristic*, not an official unit scale or camera location.
- Alternative section **142 / slot 3** (also 128×64) gives **two four-instance groups**, 440 local source triangle references, and an AABB extent of **35.637 × 2.446 × 1.809**. Section **142 / slot 19** gives two two-instance groups and 1,144 triangle references. These are controls, not proof that one is more visible on-screen.
- The previously tested **142 / slot 0** (256×256) joins only **one** local primary-model instance, with a substantially larger candidate AABB. Thus the new 142/16 target offers a more concentrated repeated-scene test opportunity.

## New source-free API and tests

- `carbon_pc_dxt5_spatial_smoke_target.py`: validates the padded 96-byte instance records and signed-reference 48-byte spatial tree; joins the previously validated model/material profile to one source PC DXT5 ordinal; computes only aggregate counts, bounding-box extents and experimental connected-component populations. The default `--section 142 --slot 16` is **read-only**.
- `test_carbon_pc_dxt5_spatial_smoke_target.py`: **53 synthetic-only tests** covering well-formed and malformed bounds, nested/spatial tree references, missing or repeated instances, ambiguous source-material references, invalid ordinals and cluster stability. Original game data is **never read** by the tests.

To inspect privately extracted, owner-provided Carbon PC originals from a local checkout:

```bash
python research/world_bridge/carbon_pc_dxt5_spatial_smoke_target.py \
  --carbon-bun PRIVATE_ORIGINAL/L5RB.BUN \
  --carbon-stream PRIVATE_ORIGINAL/STREAML5RB.BUN \
  --section 142 --slot 16 --cluster-distance 12
```

No source hashes, private absolute paths or individual XYZ coordinates are emitted. The existing **Undercover donor stream stage**, **private guarded smoke session** and **exact-byte-range ProcMon checker** are separate tools. Their prior findings remain unchanged: an owner-controlled Windows Carbon PC launch, a real stream-read trace and before/after screenshots are still needed to prove a renderer-visible texture change. We must **not** infer a drivable road/camera position from these two static object clusters.

## Limits

The scene hierarchy offsets and primary-detail model join are independently supported by original Carbon PC binary controls but remain candidate interpretations, not a fully verified game runtime ABI. Source-coordinate units have no confirmed physical distance scale. Bounds are instance bounding extents, not an exact object-position transform or camera anchor. Clustering depends on a user-visible threshold and does not establish line of sight, road access, material opacity, or actual game-side image loading. The streamed original data stays private; the staging tools continue to modify **only private copies**. Keep PR #33 **draft** and `main` unchanged until the first genuine in-game render/load evidence exists.
