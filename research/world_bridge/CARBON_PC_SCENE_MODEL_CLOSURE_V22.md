# V22: Source-verified Carbon PC scenery model-reference closure

**2026-11-12.** Draft Carbon PC conversion research in PR #33. Read-only by default; no original Carbon or Undercover assets, game executables, private hashes, textures or world positions are distributed.

## What changed since V21

V21 created a PC-shaped DXT5/eSolid candidate from one Undercover PS2 model and could update precisely **two model-hash fields** of one existing Carbon PC scenery-info row, preserving every original scenery-instance reference and every other byte. But the original scene often contains more than one scenery model. An otherwise structurally valid scene patch may reference other Carbon objects that are not present in its accompanying converted geometry.

**V22 closes that specific offline evidence gap.** New `carbon_pc_scene_model_closure_v22.py`:

1. Strictly reparses the V20 texture-first PC candidate with one eSolid and its complete DXT5 material-image set.
2. Strictly validates the native Carbon PC `0x80034100` scenery root and its original 72-byte scenery-info records and 96-byte instance-to-info links.
3. Requires the chosen, referenced scenery-info row's `+0x18` and `+0x1c` PC model IDs both match the indexed converted Undercover eSolid; refuses duplicate references to that new candidate in other source model LOD slots.
4. Checks **all four potential model slots** of every referenced scenery-info row at `+0x18/+0x1c/+0x20/+0x24`, not only the two edited slots. Zero slots are ignored. It also separately tracks all info rows, including ones not currently referenced by a scenery instance.
5. Validates each owner-supplied original Carbon PC geometry root using the independent strict `parse_geometry_root` reader, which checks the sorted model index against actual eSolid header identities and platform. A set of naked, unaudited hash values cannot serve as evidence.
6. Reports missing references from the supplied native roots, duplicate native identity ambiguity, and collisions between the new Undercover model and original Carbon models, without printing any model IDs, names, positions or asset bytes.

**Result meanings:**

- `COMPLETE_FOR_SUPPLIED_SCENE_AND_GEOMETRY_NOT_RUNTIME_PROOF`: every nonzero scenery model slot in the supplied scene resolves to the Undercover eSolid or one of the supplied Carbon PC geometry roots, with no index collision or ambiguous duplicated source model identity.
- `INCOMPLETE_REFERENCES_IN_SUPPLIED_NATIVE_GEOMETRY`: at least one referenced or additional scenery-info model ID is not present in the *supplied* source roots. The missing model **may exist elsewhere in Carbon's global resource manager**. This is a local audit failure, not proof of a missing in-game asset.
- `BLOCKED_COLLISION_OR_AMBIGUOUS_NATIVE_MODEL_ID`: the candidate shares a model identity with a native Carbon PC eSolid, or two supplied original roots repeat an identity. This is conservatively blocked until a proven override/alias policy exists.

## Integrated with the original Carbon files

`carbon_pc_first_model_scene_rebind.py` now provides the explicit **`--audit-model-closure`** option.

In native-source mode, the tool reads the owner's original Carbon PC `TRACKS/L5RB.BUN` section index and its paired `TRACKS/STREAML5RB.BUN`, validates original section **141 or 142** including the `0x372xx` post-scene framing, extracts its own indexed geometry root, patches the source scenery-info entry **in memory**, then audits the patched scene against that local native Carbon geometry root plus the converted Undercover model.

Use this command from the PR #33 checkout, with illustrative owner-local paths:

```powershell
python research/world_bridge/carbon_pc_first_model_scene_rebind.py `
  --carbon-game-bun "D:\Private\Carbon\TRACKS\L5RB.BUN" `
  --carbon-game-stream "D:\Private\Carbon\TRACKS\STREAML5RB.BUN" `
  --section 141 `
  --private-candidate "D:\Private\Output\one-undercover-model.pcchunk" `
  --info-index 0 `
  --audit-model-closure
```

If other relevant source Carbon PC eSolid packs have been independently extracted as complete original-format PC geometry roots, repeat:

```powershell
--native-carbon-geometry-root "D:\Private\Carbon\OtherPCGeometryRoot.bin"
```

These extra inputs are checked for file size, symlinks, source changes and valid PC geometry. In the alternate `--carbon-pc-scene-root` mode, you **must** supply at least one original Carbon PC geometry root to run closure, since that mode has no paired native section to extract its own geometry.

The audit is **read-only by default**. Optional `--private-scene-output NEW.pcscene --write-private` still creates an owner-local file outside any `TRACKS` directory, never overwrites old data or modifies game files. **When `--audit-model-closure` is enabled, the exporter refuses to write unless the local reference gate passes completely.** Do not rename that private file to `.BUN` or install it as a real Carbon stream.

## Validation

Pure original-free tests:

- New `test_carbon_pc_scene_model_closure_v22.py` checks source-backed PC eSolid indexing, selected row identity, all four model/LOD hash slots, referenced versus unreferenced info rows, missing native models, extra unused models, repeated native hashes, native/candidate collision, corrupt model roots, platform mismatches, invalid instance indices, and private ID redaction.
- Expanded `test_carbon_pc_first_model_scene_rebind.py` covers a **complete synthetic original Carbon RB section** with an actual indexed PC geometry root, bounded scene and authentic-shaped `0x372xx` control framing; it verifies local closure, missing model reports, supplemental source geometry roots, refusal to export when incomplete, permitted exclusive private export when locally complete, CLI dispatch, and preservation of original game files.

**1,866 original-free Python tests passed** on implementation/test commit `3def6ce1` in [GitHub Actions run 43260031832](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/43260031832). The documentation-only head should be checked separately.

## Remaining limitations and roadmap

**This is local model identity closure, not complete runtime dependency closure.**

The current gate does not independently resolve native Carbon eSolid material textures, model IDs from every other Carbon stream section or global resource registry, actual `0x372xx` post-scene control semantics, visibility/occlusion indices, collision, placement effects, texture sampling, executable ABI, ASI runtime registration or rendering. A fully backed set of original scene model hash slots can still fail to load.

The next decisive work is a **private, source-backed full-sector dependency census**, especially original Carbon scene-control references and texture dependencies, followed by a real owner-local Windows test with a known-good external Carbon BUN and a controlled original-vs-modified rendering comparison. No original assets are published, and no Undercover model has been demonstrated inside running Carbon PC.

PR #33 remains draft, `main` untouched. The parallel Wii PowerPC-to-native C++ decompilation remains in PR #35.
