# Two independently authenticated Carbon PC scenery/visibility/model-info controls

**2026-11-03. Read-only, source-only research.** This report is based on the owner's original Carbon PC split-PKZIP world archive and Carbon PS2 TRACKS archive. No game binaries or asset data are distributed. This establishes **serialized metadata consistency**, not a loadable or rendered Undercover PC scenery section.

## Reproduction

From the project root with the owner's original archives held locally:

```sh
python research/world_bridge/two_scene_visibility_control.py \
  --pc-volumes /private/carbon_pc/TRACKS.z01 /private/carbon_pc/TRACKS.z02 /private/carbon_pc/TRACKS.z03 /private/carbon_pc/TRACKS.zip \
  --carbon-ps2-zip /private/carbon_ps2/TRACKS.zip \
  --control-count 2
python -m unittest discover -s research/world_bridge -p 'test_*.py' -q
```

**Results:** all **167/167 synthetic world-bridge tests** pass together locally, and the original-archive control probe completes successfully. This includes **12** new tests for distinct section selection, malformed metadata, bad instance indices and unexpected per-info differences. The tool emits only numeric section identifiers and aggregate counts.

## Evidence chain and gate criteria

An eligible **non-Z0** control section must satisfy all of these checks against original sources:

1. The same signed section number has a valid candidate `0x34110` stream row on **both** Carbon PC and Carbon PS2.
2. Each RB stream contains a structurally validated complete `0x80034100` scenery root, parented by that section row's file range.
3. The complete `0x34103` instance payload and `0x34105` scenery-tree payload are **byte-identical across PC/PS2**; the earlier tree validator proves a single acyclic rooted hierarchy with every instance referenced once.
4. That section ID is an ordinary `0x34153` visibility target in **both** the PC and PS2 secondary-area visibility graphs.
5. Each 96-byte scenery instance's signed 16-bit +0x54 index refers to a valid, local 72-byte `0x34102` info record on both platforms, with identical reference indexes.
6. The complete PC `0x34102` info payload is reconstructed **exactly**, with no differences outside the single four-byte per-record console-to-PC hash-slot promotion (copy u32 +0x1C into previously zero +0x18). PC's promoted first slot must be nonzero. No file writes occur.

There are **12** eligible independent scenery roots meeting all six gates. The deterministic two-control default selects these two distinct source sections:

| Section number | Original scenery instances | Original local info records | Distinct in-bounds info references | Byte-exact model-info promotion |
| --- | ---: | ---: | ---: | --- |
| **141** | **29** | **29** | **29** | Yes |
| **142** | **103** | **103** | **103** | Yes |
| **Both** | **132** | **132** | **132** | **132/132** |

The remaining **10** matched controls are retained as additional independently eligible controls. The selected two are **not** claimed to represent Undercover's city, and their model hashes have **not** yet been found in actual PC geometry-resource tables. Their scene roots are source-validated metadata structures, not necessarily individually independent 3D model files.

## Special sections and non-targeted roots

The independent five-platform cross-reference found real, structurally valid `Z0` scenery roots at section ID **2600** in every game's RB stream, while `Z0` is absent from every regular `0x34153` target set. The control selector therefore deliberately *excludes Z0* and does **not** use absence from a drivable visibility target to invalidate a source root. Special loading, overlays or other relationships are still unverified.

## Next experiment and limits

**Next falsifiable milestone:** for both source-pinned Carbon control scenes, locate and parse the actual **geometry-model resource** corresponding to the populated first/second model hash. Verify a whole-resource identity/link in the Carbon PC `STREAML5RB.BUN` geometry packs, then inspect what differs in an Undercover donor-scene resource. This is necessary before attempting any model conversion writer, texture mapping or runtime injection.

The control script does **not** resolve model hashes to geometry, decode texture/material bindings, validate collision meshes, show a Carbon PC loader ABI, patch a game file, or demonstrate any in-game rendering/navigation/traffic.

**Source provenance:** \`track_bundle_probe.py\` (split PKZIP), \`rb_scenery_graph_census.py\` (RB roots within valid section rows), \`visibility_stream_join.py\` (cross-platform visibility graph), and \`scenery_model_hash_bridge.py\` (candidate Carbon PC model info hash-slot behavior). No source input archived on GitHub.
