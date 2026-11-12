# V23: Carbon PC scenery eSolid-to-texture dependency closure

**2026-11-12.** Source-backed, owner-local research in Carbon PC conversion draft PR #33. No original game assets, model/texture IDs, image pixels, positions, executables or process data are published. This milestone is not a playable port or proof of loader acceptance.

## Why this is a necessary step

V21 made a controlled in-memory change to one real Carbon PC scenery-info row's two model-hash fields so it refers to our single converted Undercover PS2 eSolid. V22 then verified all four possible model/LOD IDs in the selected original Carbon scenery root were backed by the converted eSolid and owner-supplied native Carbon PC geometry roots.

**V22 did NOT resolve the texture/material dependencies of those original Carbon models.** A Carbon model with an indexed eSolid header can still refer to textures absent from the candidate bundle or the selected Carbon streaming section. Comparing a whole geometry pack's union of texture IDs is insufficient to establish which model needs which image.

**V23** provides explicit, per-eSolid **scene model → complete model material table → actual indexed PC image identity** checks.

## New parser and conservative policy

`research/world_bridge/carbon_pc_scene_material_closure_v23.py`:

1. Independently revalidates the source-backed V20 texture-first Undercover `.pcchunk`, including a single indexed PC eSolid with its complete matching DXT5 material-image identities.
2. Uses the strict original PC eSolid header/index parser on every supplied Carbon PC geometry root. It walks each indexed eSolid separately, decoding that model's full 8-byte texture table through `parse_solid_texture_table`, **including local table slots not used by the single synthetic test triangle**.
3. Validates each native PC `0xB3300000` texture root with the original parser, including sorted image hash index, image metadata, PC codec/FOURCC and resource bounds. The reported identities are aggregate counts only.
4. Follows the original Carbon PC 96-byte instance-to-72-byte info links and includes every nonzero LOD model-hash slot at `+0x18, +0x1c, +0x20, +0x24`. Reports referenced scene material closure separately from unreferenced info rows.
5. Conservatively **blocks duplicated native eSolid IDs, repeated native texture identities across different supplied roots, and collisions between converted Undercover texture IDs and original Carbon image IDs**. No unsupported replace/alias rule is assumed.
6. Refuses to call an incomplete scene complete when a referenced model lacks a supplied native eSolid, even if every **known** model's texture identities happen to resolve.

### Interpretation of the output

- `COMPLETE_FOR_SUPPLIED_PC_SCENE_RESOURCES_NOT_RUNTIME_PROOF`: all nonzero model IDs in the supplied Carbon scene are backed by the converted Undercover eSolid or supplied original Carbon PC eSolids, and all of **those models' indexed texture-table IDs** are backed by supplied original PC texture roots or converted DXT5 images, without native/candidate identity collisions.
- `INCOMPLETE_LOCAL_PC_MODEL_OR_MATERIAL_REFERENCES`: a scene model or an image identity is not backed by the supplied sources. The missing model/image **may exist elsewhere in Carbon's stream cache or game-wide resource registry**.
- `BLOCKED_AMBIGUOUS_MODEL_OR_TEXTURE_IDENTITY`: source roots duplicate model/texture identities or the candidate collides with a Carbon identity, with no proven replacement policy.

**A complete local result does not establish a renderable Carbon stream sector.** It does not reconstruct the post-scene `0x372xx` control semantics, global cache, model visibility, collision, material rendering state, original source image provenance, executable ABI or actual in-game registration. Those separate gates remain open.

## Integrated owner-private workflow

V23 extends the existing Carbon original pair and V21 scene rebind tool. Its new **`--audit-material-closure`** flag requires `--audit-model-closure`.

From the PR #33 checkout, run against a privately owned and previously verified original Carbon PC `TRACKS` pair and a privately generated V20 one-model Undercover `.pcchunk`:

```powershell
python research/world_bridge/carbon_pc_first_model_scene_rebind.py `
  --carbon-game-bun "D:\Private\Carbon\TRACKS\L5RB.BUN" `
  --carbon-game-stream "D:\Private\Carbon\TRACKS\STREAML5RB.BUN" `
  --section 141 `
  --private-candidate "D:\Private\Output\one-undercover-model.pcchunk" `
  --info-index 0 `
  --audit-model-closure `
  --audit-material-closure
```

The `--info-index 0` is just an example; it must select a real, referenced Carbon scenery-info row and pass the strict collision controls. With native paired sources, the auditor:

- Parses the original L5RB 92-byte section table and verifies the complete selected original PC RB 141/142 section and original `0x372xx` framing.
- Extracts **both** native texture and geometry roots from that **same** original stream section without writing or dumping those assets.
- In memory rebinds exactly one original Carbon scene-info row to the converted Undercover model, then audits all scene model and image dependencies.
- Reports counts and classification, not game assets, hashes or private file locations.

A native scene section can depend on models or textures stored outside the one local stream. To include separately extracted *complete owner-original PC roots* for wider closure, repeat either of:

```powershell
--native-carbon-geometry-root "D:\Private\Carbon\OtherNativeGeometry.bin"
--native-carbon-texture-root "D:\Private\Carbon\OtherNativeTextures.bin"
```

These are **independent original PC resource roots**, not arbitrary ID lists. The tool checks their bounded size, path safety and actual indexed format before accepting their identifiers. In `--carbon-pc-scene-root` mode, where no paired section is available to extract original roots, **both** native geometry and texture root inputs must be supplied for full material closure.

**No original Carbon/Undercover assets are modified by default.** The optional V21 private export still requires both `--private-scene-output NEW.pcscene` and `--write-private`, and it is now **blocked unless both requested model and material closure gates pass**. Even with both gates passing, the output is a standalone experimental root and must not be renamed to an installable `.BUN` or placed in the game installation.

## Synthetic regression and CI

- `test_carbon_pc_scene_material_closure_v23.py` covers valid PC eSolid-to-material-to-DXT5 image closure, missing original textures, complete unused table slots, third-LOD references, unreferenced scenery rows, colliding/duplicate IDs, corrupt image metadata, invalid geometry/platforms, bounds and report privacy.
- `test_carbon_pc_scene_material_owner_v23.py` constructs a full original-free Carbon **92-byte indexed L5RB.BUN + STREAML5RB.BUN section 141**, with genuinely indexed PC texture and geometry roots, original-format scenery entries and postscene control framing. It tests native extraction, missing/extra original image packs, exported-scene refusal, source immutability, and CLI flag wiring.

The [V23 implementation CI run 43265817786](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/43265817786) passed **1,896 original-free tests** at code/test commit `6bfc5eb3`. Two earlier iterations failed on a missing parser range argument and a synthetic test helper's default substitution for explicit None; both were corrected before final validation.

## Next source-backed work

1. Inspect the **native original Carbon PC post-scene `0x372xx` control records** for references, offsets and load-order dependencies that must be maintained when reusing an original scene and textures.
2. Determine a safe, format-verified method to compose original Carbon texture, original Carbon geometry and a converted Undercover eSolid into a complete section **without overwriting or guessing unknown control records**. Current candidate+standalone scene roots do not constitute this.
3. Separately establish original Carbon external loader packaging and registration in an owner's real Windows Carbon installation, then attempt a single converted Undercover scenery instance with controlled A/B/A visual evidence.

**No converted Undercover scenery object has yet been demonstrated rendering inside Carbon PC.** Draft PR #33 remains separated from Wii native physics decomp PR #35, and `main` is unchanged.
