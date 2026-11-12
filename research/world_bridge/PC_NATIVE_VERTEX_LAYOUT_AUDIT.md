# Carbon PC native vertex-buffer, mesh index and tangent controls

**Original-file, read-only audit (2026-11-03).** Verified using the owner's authentic Carbon PC `TRACKS.z01/z02/z03/TRACKS.zip` split-PKZIP world archive. Only original source, synthetic tests, and aggregate statistics are committed; no game mesh, index, vertex, material, hash inventory, texture or executable bytes are published. This is **not** an Undercover PC mesh writer or an in-game rendering test.

## Run

From repository root, with the owner's original split archive kept locally:

```sh
python research/world_bridge/pc_native_vertex_control.py \
  --pc-volumes /private/carbon_pc/TRACKS.z01 \
               /private/carbon_pc/TRACKS.z02 \
               /private/carbon_pc/TRACKS.z03 \
               /private/carbon_pc/TRACKS.zip

python -m unittest discover -s research/world_bridge \
  -p 'test_pc_native_vertex_control.py' -v
```

The checker reads the bounded **82,837,504-byte** Carbon PC `STREAML5RB.BUN`, independently authenticated `0x34110` rows and `0x80034100` scene roots for secondary-area sections **141** and **142**, and the complete `0x80134000` geometry packs in those sections. It checks all embedded `0x80134010` solids; it prints only aggregate source geometry statistics and does **not** alter the source.

## Verified native PC record fields

A candidate **144-byte** `0x00134B02` mesh record now has independent exact consistency checks for:

| Offset within mesh record | Candidate field | Original-file check |
| --- | --- | --- |
| `+0x00..+0x17` | float32 XYZ min/max bounding box | Decoded vertex extrema fit all 367 record bounds to within 0.1 units |
| `+0x40` | u32 vertex count | Every mesh's vertex count partitions the actual PC vertex buffers without leftover vertices |
| `+0x60` | u32 triangle count | Exactly 1/3 of the record's index count in all 367 records |
| `+0x64` | u32 start in the solid's PC 16-bit index stream | Start/count ranges partition the solid's full index buffer contiguously |
| `+0x7C` | u32 triangle-index count | Each index lies inside the corresponding mesh's vertex span, with numbering resetting when a new vertex buffer begins |

The mapping is **unique** for all 132 independently indexed Carbon PC control solids. Crucially, treating indices as global over all buffers fails for some multi-buffer models; they must be interpreted relative to the corresponding vertex buffer.

### Native PC vertex field candidates

The original data resolves to two buffer formats, assigned by **record counts + exact bounded index ranges + mesh-coordinate bounding boxes**, rather than only by division of the buffer length.

| Offset inside vertex | 36-byte record | 52-byte record |
| --- | --- | --- |
| `+0x00..+0x0B` | XYZ, 3 × float32 | Same |
| `+0x0C..+0x17` | Unit normal, 3 × float32 | Same |
| `+0x18..+0x1B` | Packed color u32 | Same |
| `+0x1C..+0x23` | UV, 2 × float32 | Same |
| `+0x24..+0x2F` | Not present | Unit tangent candidate, 3 × float32, or exact NaN sentinel |
| `+0x30..+0x33` | Not present | Handedness/sign candidate: float32 `+1, -1`; zero only for exact NaN sentinel |

Both record formats have finite positions, normals and UVs. All candidate normals have a squared-length error below **1e-7**. Ordinary 52-byte tangent vectors have squared-length error below **1e-7** and absolute dot product with their corresponding normal below **1e-6**, strongly supporting the tangent interpretation.

**Special source edge case:** precisely **20** vertices of the 52-byte format contain all-three-NaN tangent components paired with a **0.0** sign. The validator accepts **only that exact pattern**; it rejects partial NaNs, arbitrary sign values, nonunit tangents and nonorthogonal tangents. A future writer must not accidentally normalize these sentinel values into a different vertex.

## Original Carbon PC source-backed totals

| Metric | Section 141 | Section 142 | Combined |
| --- | ---: | ---: | ---: |
| Indexed solid resources | 29 | 103 | **132** |
| 144-byte mesh records | 127 | 240 | **367** |
| 16-bit triangle indices | 163,452 | 180,699 | **344,151** |
| Triangles | 54,484 | 60,233 | **114,717** |
| 36-byte vertex buffers | 30 | 112 | **142** |
| 36-byte vertices | 97,458 | 74,189 | **171,647** |
| 52-byte vertex buffers | 1 | 15 | **16** |
| 52-byte vertices | 1,758 | 12,421 | **14,179** |
| All vertices | 99,216 | 86,610 | **185,826** |
| Special NaN/zero-sign tangent vertices | 4 | 16 | **20** |

All **132/132 solid resources** have one unique complete vertex-buffer/mesh assignment, and all **367/367 mesh coordinate bounds** match the decoded position extrema to within 0.1 game units. Every one of the **344,151 indices** is inside its correct per-mesh vertex range, after treating the buffer boundary as a possible index reset.

For the 52-byte format: **8,133** vertices have a negative tangent sign, **6,026** positive, and **20** the all-NaN/zero sentinel. No other sign values were observed in these control sections.

## Verification and limits

- **14/14 new synthetic-only tests passed locally.** They include valid single-/mixed-buffer controls, exact NaN tangent sentinel handling, and rejection of out-of-bounds index values, partial NaNs, wrong tangent signs, inconsistent triangle counts, nonfinite UVs, nonunit normals/tangents, nonorthogonality and mismatched bounding boxes.
- The real Carbon PC original-file probe passed for all 132 indexed solids. The source and test files are checked into draft PR #33 and their Git blob hashes were checked against the exact locally tested files.
- **The source-backed command used a local minimal compatibility harness for existing project helper functions.** The new checker itself and its per-solid synthetic tests were run; a full GitHub CI run against all repository modules is still a separate verification step and should not be represented as completed.
- The float32 UVs and tangent interpretation are corroborated by consistency and geometric invariants, but **PC ↔ PS2 exact per-triangle vertex equivalence, triangle winding, PS2 normal conversion and material/texture binding have not yet been established**. These are necessary before generating PC-format bytes or claiming native rendering.
- The report counts only the selected **two** secondary-area control sections, not Carbon's full world or any Undercover game asset.

### Next falsifiable converter experiment

Match a *specific* original Carbon PC control mesh's real triangle-index stream and per-mesh vertex records to the VIF-decoded corresponding Carbon PS2 strip's XYZ, ST, and triangle suppression. Compare geometry and winding under explicit coordinate transforms and tolerances. Use a second independent control mesh and the previously detected two polygon-count mismatches as negative tests. Then implement a **reversible, synthetic-only 36-byte PC vertex/index writer**, keeping all geometry and materials private.

No actual game-file write, model injection, collision, traffic, or playable Tri-City Bay port has been demonstrated.
