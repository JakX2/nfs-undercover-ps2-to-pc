# Carbon PC ↔ PS2 real vertex-position equivalence: 132 original eSolids

**Source-backed, read-only research, 2026-11-03.** The original owner-supplied Carbon PC split world archive and Carbon PS2 `TRACKS.zip` were inspected privately. No original game meshes, strips, vertex lists, material names, model hashes, textures or binaries are published or patched. This is not an Undercover render or a completed conversion.

## Reproduce against your own original archives

```sh
python research/world_bridge/pc_ps2_position_control.py \
  --pc-volumes /private/carbon_pc/TRACKS.z01 /private/carbon_pc/TRACKS.z02 \
               /private/carbon_pc/TRACKS.z03 /private/carbon_pc/TRACKS.zip \
  --carbon-ps2-zip /private/carbon_ps2/TRACKS.zip \
  --tolerance 0.01

python -m unittest discover -s research/world_bridge \
  -p 'test_vertex_cloud_spatial_match.py' -v
python -m unittest discover -s research/world_bridge \
  -p 'test_pc_ps2_position_control.py' -v
```

The new command reuses validated **original** streaming rows, scenery roots, geometry-pack indexes and embedded solid hashes, then matches **the same model-hash identities** across Carbon PC and Carbon PS2 controls **141 and 142**. For every paired solid it:
1. Verifies the native PC **144-byte mesh records**, **16-bit index partitions** and uniquely assigned **36-/52-byte vertex buffers** using `pc_native_vertex_control.py`. Reads source PC XYZ float32 from vertex offset +0.
2. Parses **actual PS2 16-byte strip descriptors** and their bounded VIF packets with the previously source-validated `vif_strip_probe.decode_strip_header`. Reconstructs PS2 XYZ positions using the packed scale and independently serialized source strip-bounds convention.
3. Runs an independent, bidirectional, Euclidean **0.01 game-unit** match over XYZ points. A point in either platform must have at least one nearby point belonging to **the same model hash** on the other platform.
4. Prints **aggregate totals only**. Game bytes are never exported or modified.

The dependency-free spatial witness checker checks all 27 adjacent candidate grid cells using exact Euclidean squared distances, including negative coordinates and cell boundaries. It intentionally stops once it finds a point within tolerance; therefore its reported *witness* distance is **not the exact nearest-neighbor distance**, and no false precision is claimed.

## Original paired model results

| Source-authenticated Carbon RB section | Matched models | PC native XYZ vertices | PS2 decoded XYZ vertex occurrences | Entire two-way position cloud within 0.01 |
| --- | ---: | ---: | ---: | --- |
| **141** | **29** | **99,216** | **100,464** | **29/29** |
| **142** | **103** | **86,610** | **104,539** | **103/103** |
| **Total** | **132** | **185,826** | **205,003** | **132/132** |

All **185,826 PC vertex records** have a nearby point in the matching model's **205,003 PS2 strip vertex occurrences**; every PS2 vertex occurrence likewise has a nearby PC source position. The different vertex occurrence counts are legitimate: consoles may repeat vertices across strips, and the native PC uses its own indexing. Position proximity does **not** establish identical vertex ordering or connectivity.

An independent exploratory calculation using SciPy `cKDTree` (not needed by the committed tool) measured the **true maximum nearest-neighbor distance across both directions as approximately 0.00663 game units**, lower than the explicitly validated 0.01 threshold. The source-only tool uses a pure standard-library grid and reports its bounded match witnesses rather than an exact nearest-neighbor statistic.

This comparison independently corroborates the candidate **16-bit PS2 coordinate scaling/anchor reconstruction**, not just the source strips' own bounding boxes. A wrong coordinate transform would not map *all* PS2 points onto native PC vertices and back for 132 different real models.

## What this does and does not prove

**Supported by real original data:**
- Source-identical model identities across Carbon PC and Carbon PS2 in sections 141 and 142.
- Native PC XYZ interpretation at vertex +0, and PS2 VIF XYZ interpretation from packed SoA positions plus the source bounds/scale.
- Two distinct native PC vertex strides, full per-mesh local index-range assignments and 52-byte tangent sentinels, validated independently in the companion report.
- Geometric equivalence of **point clouds within 0.01 units for all 132 paired models**.

**Not established:** equal face connectivity, triangle winding, shared vertex/face ordering, PS2→PC normal equivalence, UV mapping, material indices, texture names, tangent recalculation, collision or native Carbon PC model-loading ability for Undercover donors. Even the two earlier *polygon-count* discrepancies (+2 and +14 PC triangles) remain negative cases for topology: they do not invalidate the XYZ point-cloud result.

No Carbon PC native mesh writer, modified game archive, injection, gameplay launch or Tri-City Bay rendering is claimed.

## Reproducibility and testing limitations

- **30/30 newly added synthetic tests pass together locally**: 14 native PC record/mixed-buffer/tangent tests, 12 spatial tolerance/negative geometry tests and 4 paired-model join controls.
- The real **132-model** check also passed in two independent implementations: an exploratory SciPy nearest-neighbor runner, and the committed spatial witness logic integrated with local **minimal helper compatibility shims**. This does **not** constitute a run of every committed repository module with full CI. Running the exact CLI in a clean checkout against the original archives remains a separate verification step.
- GitHub file SHA-1s for the new source/test modules were compared with locally tested files. All files are source-only.

### Next falsifiable gate

Pick two separate Carbon PC/PS2 models, map **actual ADC-filtered PS2 triangle triplets** to the matched PC per-mesh indexed triangle sets, and compare winding modulo consistent coordinate orientation. After that, test UV and material identity per triangle, then implement a small reversible **synthetic-only** PC-format vertex/index writer. Use the +2/+14 polygon-count mismatches as expected non-equal topology controls.

The objective remains one correctly rendered Undercover scenery section in native Carbon PC; a matching point cloud is a necessary but not sufficient step.
