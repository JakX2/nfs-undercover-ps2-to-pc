# V19: First private one-model Undercover PC chunk-stream candidate

**2026-11-12. Experimental Carbon PC format research; not loader acceptance or a playable port.**

**V20 correction:** This historical V19 report originally documented geometry-first assembly. The current builder instead uses **texture-first, 16-byte-aligned geometry**, matching the selected owner-original Carbon PC source section profile. The old geometry-first private exports are deprecated and explicitly rejected; regenerate them. See [V20 native prefix layout](CARBON_PC_NATIVE_PREFIX_LAYOUT_V20.md).

## What was actually implemented

The existing source-only Undercover PS2 model conversion selects one scenery-info-referenced model, translates its indexed triangles/UVs into a Carbon-PC-shaped eSolid root, and converts its complete original texture-material table to a DXT5 PC-format texture root.

Previously, those two verified resources existed **separately** in memory and the first-model audit only returned aggregate counts.

V19 adds `carbon_pc_first_model_stream_assembly.py`:

- **build_private_pc_first_model_stream(geometry_root, texture_root)** independently checks EXACT PC top-level framing for both complete roots, exactly one indexed eSolid model, full material-table/image identity closure (including unused local material slots), no unreferenced texture IDs, and DXT5-only image records by default.
- At V19 this initially joined exactly two top-level PC resource chunks in **geometry-then-texture** order. **V20 changed the current implementation to texture-then-geometry** after comparing owner-original Carbon PC RB section ordering, while still leaving scene and control data unresolved. It reparses the **whole combined stream** using the independent V16 chunk-stream validator, asserting byte totals, root counts, indexed model and texture counts, and absence of extra/unknown frames.
- The first-model `verify_single_model` now executes this combined readback on the **actual converted geometry and DXT5 textures**, not on fake hash lists. A redacted audit report includes byte counts and explicit unverified game-loader flags.
- **export_private_pc_candidate_stream** can write an owner-private, prevalidated `.pcchunk` file only by explicit opt-in. The function independently reparses the stream, writes with exclusive new-file creation, refuses existing files, symlinks, wrong extensions or unsafe output locations, and verifies the written bytes against memory. No original game files are changed. The extension deliberately avoids suggesting an installable `.BUN`.
- `audit_original` checks the owner-original source ZIP fingerprint **before** its optional private export. The default CLI remains read-only, with no output artifact or proprietary data in stdout. When export is explicitly selected, a private file is created only in the user-chosen existing directory. Its full path and contents are omitted from the public JSON report.

**Important:** The assembled stream is PC-parser-shaped, NOT proven to match Carbon's resource manager's full proprietary `.BUN` container, scene registry, load stage/type, chunk alignment or scene visibility. It is not automatically installable.

## Owner-private usage

From a checkout of PR #33, inspect the original PS2 Undercover TRACKS archive without writing any converted asset:

```powershell
python research/world_bridge/undercover_pc_first_model_gate.py `
  --undercover-ps2-tracks-zip "D:\Private\Undercover\TRACKS.zip" `
  --source-section 241 `
  --pc-header-profile carbon_native_control
```

The `carbon_native_control` profile relies on the independent, previously source-backed Carbon-vs-PS2 eSolid header normalization. If the original selected source header does not pass that strict control, the tool refuses rather than fabricates fields. The original `preserve_source` profile remains the default, for comparative research only.

To make a private, non-installable PC-chunk candidate file, add **both** switches:

```powershell
python research/world_bridge/undercover_pc_first_model_gate.py `
  --undercover-ps2-tracks-zip "D:\Private\Undercover\TRACKS.zip" `
  --source-section 241 `
  --pc-header-profile carbon_native_control `
  --private-candidate-output "D:\Private\Output\one-undercover-model.pcchunk" `
  --write-private
```

The output directory must already exist. The output path must be new and end in `.pcchunk`. The tool cannot overwrite an earlier candidate or install anything into Carbon; do **not** rename and copy the candidate into a live game just because it parsed offline. Generated original-derived bytes stay on the owner's machine and should not be committed or uploaded.

Optional private `--carbon-pc-geometry-root` and `--carbon-pc-texture-root` arguments can still perform the V13 reference-identity collision audit on selected original Carbon PC resource roots, but this is not exhaustive across Carbon's full resource registry.

## Synthetic CI tests

- New `test_carbon_pc_first_model_stream_assembly.py`: material closure, multiple local material slots, exact two-root framing, DXT1 rejection by default, invalid/trailing root handling, strict full-stream readback, output privacy, deterministic byte serialization, opt-in exclusive private export, refusal to overwrite and symlink/traversal/extension safety.
- Expanded `test_undercover_pc_first_model_gate.py`: the **real** synthetic PS2 indexed-texture-to-DXT5 conversion path must assemble the same converted bytes into one PC chunk stream. It tests full-table counts, private in-memory receiver, refused malformed independent stream reads, opt-in CLI flag validation and redacted reports.

The Python source-only GitHub Actions workflow completed **1,794 tests passing** on implementation/test commit `bc5f606d`: [run 43162175009](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/43162175009). Documentation commits must have their own CI checked before reporting latest-head success.

## What remains

1. Verify the **actual external Carbon loader's accepted package format** using a previously known-good original PC resource BUN. The candidate `.pcchunk` has only simple top-level chunks, not verified loader-specific metadata.
2. Run a reversible private Windows A/B/A test with XNFSModFiles, capture calibrated exact-file access and visual evidence; separately check engine resource-manager registration.
3. Only after native controls pass, adapt the candidate's framing/stage/type and attempt **one** real Undercover scenery model and matching texture registration.
4. From a successful scene-render target, work toward a road-sector stream with collision and visibility, then a driveable car and gameplay/mission port.

**No original game resources are shipped with this repo. No Undercover asset has yet been observed rendering in Carbon PC. This is not a playable native Windows game.** Draft PR #33 remains separate from the Wii PowerPC-to-native C++ source reconstruction in PR #35.
