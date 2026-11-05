# Carbon PC vs Carbon PS2: 114,701 one-to-one triangle geometry controls

**2026-11-03. Original-file, source-only, read-only research.** No source game archives, VIF packets, face lists, texture/model content, hashed asset inventories or executable patches are committed. This is not a converted Undercover model or a playable Tri-City Bay port.

## Reproduction

From the research repository root, with the owner's original Carbon PC four-volume split-PKZIP and original Carbon PS2 TRACKS archive:

```sh
python research/world_bridge/triangle_topology_control.py \
  --pc-volumes /private/carbon_pc/TRACKS.z01 /private/carbon_pc/TRACKS.z02 \
               /private/carbon_pc/TRACKS.z03 /private/carbon_pc/TRACKS.zip \
  --carbon-ps2-zip /private/carbon_ps2/TRACKS.zip \
  --tolerance 0.01

python -m unittest discover -s research/world_bridge -p 'test_triangle_face_bijection.py' -v
python -m unittest discover -s research/world_bridge -p 'test_triangle_topology_control.py' -v
```

The new pure-stdlib `triangle_face_bijection.py` uses a 3D triangle-centroid grid to find **actual triangle candidates** within Euclidean tolerance at **all three corners**, across all six vertex permutations. It then performs an iterative, alternating-path **one-to-one bipartite matching**, so multiple PS2 triangles cannot silently reuse one PC triangle. This is substantially stricter than separately matching nearest vertices or merely comparing polygon counts.

The integration tool `triangle_topology_control.py` checks real per-hash source solids by calling existing validated PC mesh/index-buffer assignment and PS2 VIF/ADC strip decoders. Section IDs, model hash identities and geometry-pack roots must all agree across the selected Carbon PC/PS2 controls. Its only outputs are numeric section IDs and aggregate measurements.

## Real original-archive result

| Authenticated Carbon RB scene | Matched indexed solid identities | Native PC triangles | Decoded PS2 candidate triangles | PS2 triangles assigned to **distinct** matching PC faces | Unused PC faces |
| --- | ---: | ---: | ---: | ---: | ---: |
| **141** | **29** | **54,484** | **54,484** | **54,484** | **0** |
| **142** | **103** | **60,233** | **60,217** | **60,217** | **16** |
| **Total** | **132** | **114,717** | **114,701** | **114,701 / 114,701** | **16** |

- **130/132** models have equal PC and PS2 triangle counts and **complete bijective geometric correspondence**: every PS2 face matches a different PC face, and no PC faces remain.
- Two previously identified control models in section 142 contain **+2** and **+14** extra PC triangles, respectively. Every original PS2 triangle still has a **distinct** matching PC triangle in those models. The extra PC faces remain unpaired and uncharacterized, not deleted or silently ignored.
- Across all source controls, **3,317** PS2 triangle candidates have more than one potential PC face within 0.01 units (**858** in section 141, **2,459** in section 142). A naïve nearest-first pairing would reuse some PC faces; the augmenting-path matching eliminates those collisions.
- The maximum corner-to-corner witness distance for the final one-to-one assignments is **0.009964 game units**, below the explicit 0.01 tolerance. This is a witness maximum for the selected bijection, **not a globally minimal geometric matching** or exact nearest-neighbor figure.

### Provisional winding evidence

The selected geometric correspondence has **114,604** even (cyclic) corner permutations and **97** odd (reversed) permutations. These figures are **not** a proven global winding convention or evidence of 97 broken triangles: they are conditional on which equivalent face was chosen in ambiguous, repeated, tiny or degenerate geometry. Independent area-weighted normal and material/UV comparisons are necessary before fixing the PC writer's index order.

The matching algorithm accepts geometric witnesses regardless of the order in which the three vertices appear. It therefore establishes an **unoriented 3D triangle geometry correspondence**, not full serialized triangle-list equivalence.

## Original-source validation scope

All **132 Carbon PC/PS2 paired solids** across two independently authenticated secondary-area scenes passed the new per-face checks using original archive bytes and a **local compatibility harness** for some previously published project helper functions. The pure matcher was also independently cross-checked against SciPy sparse maximum bipartite matching on the same source data; both found a full one-to-one assignment for all **114,701** PS2 faces. This dual implementation is useful, but the committed analyzer itself has no SciPy dependency.

**26/26 newly added synthetic-only tests passed locally**: 20 tests for geometric matching, missing/duplicated faces, matching augmenting paths, opposite/cyclic vertex permutations, negative coordinates, malformed input and threshold behavior; 6 tests for same-hash control linking, missing models, nonmatching connectivity and extra PC faces.

All **four committed Python files** have Git blob SHA-1 hashes identical to the exact locally tested copies. No full clean-checkout GitHub CI run is claimed.

## What this milestone means, and what it does not

**Supported:** The existing PS2 VIF/ADC decoder, PC native vertex/index decoder and geometry-index mapping together reconstruct the same **unoriented triangle surface geometry to 0.01 units** in all 132 source-matched Carbon controls. This is significantly stronger than bounding-box, model-hash or point-cloud equality.

**Not yet shown:** Triangle winding semantics, normals, tangent generation, UV identity at seams, PS2 strip-to-PC material assignment, textures, 36/52-byte PC vertex writer output, validated PC loader registration, Undercover PC rendering or collision/traffic/AI. None of the selected Carbon control models is a new Undercover PC asset. Even a successful synthetic mesh writer will still require privately testing in the actual Carbon runtime.

### Next falsifiable experiment

For **two distinct control solids with exactly equal face counts**, compare the **PS2 VIF ST/UV pairs** and inferred strip group/material IDs to the corresponding **PC per-vertex float UVs and mesh material names**, using the newly verified one-to-one geometric face assignment. Characterize wrapped coordinates, duplicated UV seams and winding under consistent orientation. Only then build a reversible synthetic-only 36-byte triangle/vertex writer with strict face/material count guards.

**No source game files were modified or published.**
