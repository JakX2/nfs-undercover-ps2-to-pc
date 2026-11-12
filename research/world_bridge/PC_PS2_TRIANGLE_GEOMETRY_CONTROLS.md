# Direct Carbon PC versus PS2 triangle-face geometry controls

**Read-only original-source research, 2026-11-03.** Owner-provided, original Carbon PC and Carbon PS2 track archives were used privately. No model vertices, meshes, named hashes, material assets, game archives or executable patches are committed. **This is not a rendered Undercover scene or a completed Carbon PC mesh writer.**

## Reproduce

From a checkout of the draft research branch with Python 3.10+ and the original game archives in private local paths:

```sh
python research/world_bridge/triangle_face_original_controls.py \
  --pc-volumes /private/carbon_pc/TRACKS.z01 /private/carbon_pc/TRACKS.z02 \
               /private/carbon_pc/TRACKS.z03 /private/carbon_pc/TRACKS.zip \
  --carbon-ps2-zip /private/carbon_ps2/TRACKS.zip \
  --tolerance 0.01

python -m unittest discover -s research/world_bridge \
  -p 'test_triangle_face_spatial_match.py' -v
python -m unittest discover -s research/world_bridge \
  -p 'test_triangle_face_original_controls.py' -v
```

The source-backed command first revalidates its original `0x34110` stream rows, scene roots and exact geometry index-to-solid hash linkage in Carbon PC and PS2 secondary-area sections **141** and **142**. It uses native PC 16-bit indices and uniquely assigned 36-/52-byte vertex buffers to form actual PC XYZ triangles. On PS2, it decodes complete VIF packets, ADC triangle-suppression masks and candidate parity/winding to form XYZ triangles from genuine 16-byte strip descriptors.

The dependency-free comparator considers a triangle geometrically present if **all three vertices can be paired with a corresponding triangle within Euclidean distance 0.01 game units each**, allowing any of the six vertex permutations. It bins triangle centroids into 3D spatial cells, then checks all 27 neighboring cells exactly. If all three vertices match, triangle centroids must also be within 0.01; this makes the 27-cell search valid even at negative coordinates. The comparator separately tracks same-only, reversed-only and ambiguous winding candidates.

**Crucial caveat:** this is **existential face presence**, not a one-to-one matching or proof of identical triangle multiplicities. Multiple source triangles may match the same target, especially where faces/vertices are duplicated or degenerate. UVs, normals and material associations are not compared.

## Complete original-data results

| Same-hash Carbon control | Models checked | Bidirectional all-face models | PC triangles | PS2 triangles | All PS2 faces present on PC | PC faces absent from PS2 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| RB section **141** | 29 | **29/29** | 54,484 | 54,484 | **54,484/54,484** | **0** |
| RB section **142** | 103 | **101/103** | 60,233 | 60,217 | **60,217/60,217** | **16** |
| **Total** | **132** | **130/132** | **114,717** | **114,701** | **114,701/114,701** | **16** |

The **16 PC-only face occurrences** are accounted for by precisely two section-142 source models: **+2** and **+14**, the same two models previously identified from independent native-PC index counts versus PS2 strip polygon counts. No PS2 candidate triangle lacks a PC geometric counterpart at tolerance 0.01.

This confirms **actual triangle geometry correspondence**, rather than the earlier weaker correspondence of vertex positions alone. A former heuristic assigning every PS2 vertex to one nearest *PC vertex ID* incorrectly reported hundreds of missing faces in some duplicate-heavy models. Geometry-based **three-vertex tolerance matching** finds those same faces without forcing close PC vertices to share one index.

### Winding, ambiguity and duplicate diagnostics

These numbers are **directed** and count source triangle occurrences:

| Directed comparison | Faces with same-winding candidates only | Reversed-winding only | Both orientations possible | Faces with multiple matching target triangles |
| --- | ---: | ---: | ---: | ---: |
| Carbon PC → Carbon PS2 | **109,834** | **14** | **4,853** | 3,293 |
| Carbon PS2 → Carbon PC | **109,853** | **14** | **4,834** | 3,317 |

A reversed-only result means a geometric candidate was found but none with the source's current candidate cyclic orientation; it is *not* proof that a platform renderer necessarily flips a face. The ambiguous count includes repeated/collocated vertices and cases where more than one permutation or target face is within tolerance. It should not be silently turned into a definitive winding assignment.

The source decoder's strip-parity handling has produced strong geometric correspondence, but a final native-PC converter must still determine material-specific winding, degenerate handling and exact per-face matching/multiplicities.

## Independent crosscheck and tests

Two independent original-data explorations reproduce the **130/132 models and +16 PC-only faces** result:
1. An exploratory SciPy cKDTree built on native PC triangle centroids with explicit permutation checks.
2. The newly committed **standard-library-only** centroid-bucket matcher, with no SciPy or NumPy requirement for the matcher.

The new code includes **26 synthetic-only tests**: 19 geometric tolerance and winding cases, plus 7 source-model integration cases for index-buffer boundaries and missing/extra model faces. They passed together locally. The integrated original-archive command was also run with minimal local compatibility adapters for older research helper modules. A full clean-checkout CI execution has **not** been performed. All **four** newly committed Python source/test file Git blob SHA-1s were compared with the exact locally tested versions and match byte-for-byte.

## Next falsifiable engineering gates

1. Match **UV pairs on the same triangles** in two verified Carbon PC/PS2 models. Positions alone do not locate material seams or prove texturing equivalence.
2. Establish the PC 144-byte mesh record's per-material assignments against PS2 strip descriptors. Investigate whether reversed-only and ambiguous face candidates are degenerate triangles, double-sided faces or decoding artifacts.
3. Perform **one-to-one face matching** or a multiset comparison that accounts for duplicate surfaces. The present existence test is deliberately not that proof.
4. Once two independent paired models have correct triangles, UVs, and material registration, implement a **reversible synthetic-only** PC 36-byte vertex/index writer with strict bounds, index and material checks.
5. Independently verify that the real Carbon PC runtime loads and renders a privately converted single Undercover solid before attempting section-wide scenery, collision, navigation or traffic.

**No playable Undercover-to-Carbon PC map, runtime model injection, rendered donor building, material/texture conversion, collision, AI, or game-file patch has been demonstrated.**
