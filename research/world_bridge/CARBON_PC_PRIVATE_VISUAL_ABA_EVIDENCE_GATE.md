# Carbon PC private visual A→B→A and stream-read evidence gate

**Scope:** source-only validation of *future* owner-controlled Carbon PC screenshots. This gate does **not** prove Undercover renders in Carbon, that any game process used the staged texture, or that a particular scenery group is visible from the road.

## Why this exists

The previous research selected a higher-coverage **existing** Carbon PC test slot: section **142**, zero-based **DXT5 slot 16**, **128×64**, four source PC mip levels. A compatible high-contrast donor is Undercover PS2 section **241**, zero-based donor ordinal **31**. Earlier original-archive controls found twelve primary-detail scenery instances with this Carbon texture material and two groups of six candidate scenery bounds. The exact model/texture hash inventories, source AABBs, game archives, unpacked images and patched stream copies are not distributed. The published spatial grouping is not a road waypoint or camera position.

The new source-free `carbon_pc_private_visual_evidence_gate.py` asks a separate falsifiable question: **do screenshots of the same camera view show a localized change on the chosen surface while independent background reference regions remain stable, and does that change disappear after restoring the pristine stream?** This is an experimental *pixel-difference candidate*, not a semantic object recognizer.

## Private, user-controlled Windows sequence

1. With the **original** Carbon PC stream installed, visit the intended object and capture a PNG screenshot (`before.png`) from a stationary camera. Keep gameplay HUD, moving cars, motion blur, changing lights and animation out of the cropped test regions as much as possible.
2. Privately stage **Undercover 241/donor 31 → Carbon 142/DXT5 slot 16** with the earlier `private_undercover_dxt5_stream_stage.py` tool. The existing smoke-session tool must pass `preflight` and create a **separate exclusive backup** outside the installation before an **explicit** guarded install. None of those steps is automated by this visual gate.
3. With the **staged** stream still installed, launch the game from the same location, take `staged.png`, and use Process Monitor to capture Carbon's open/read activity for that exact stream. Export a CSV with the standard `Process Name`, `PID`, `Operation`, `Path`, `Result`, `Detail` fields, preserving read `Offset` and `Length`. Run the combined evidence gate **before restoring**, because the existing session validator insists the staged stream is presently installed. **Do not publish** the CSV, private session manifest, screenshot or staged game file.
4. Close `NFSC.exe`. Explicitly call the earlier smoke-session `restore` command, verify original-stream SHA equality via `status`, relaunch the game with the original stream, and capture `restored.png` from the same view. Finally run the *visual-only* three-frame comparison below. Keep the original private captures and ROI worksheet local.

## ROI setup

Create a local `PRIVATE_regions.json` file (not included in the repository). Example **dummy 1280×720 pixel rectangles**, **not** derived from Carbon scenery or a recommended camera pose:

```json
{
  "format": "nfsuc-carbon-visual-roi-v1",
  "target": [450, 270, 300, 200],
  "anchors": [
    [20, 20, 160, 100],
    [1080, 590, 170, 110]
  ]
}
```

All rectangles use `[x, y, width, height]` in screenshot pixels, measured from the top-left; they must be positive-area, disjoint and fully inside the image. Draw the **target** around the suspected changed surface. Draw **two or more independent background anchors** around rigid, distinctive features (e.g. static structures) not covered by the target, steering wheel/HUD, or moving objects. Sky-only/flat-color anchors may be insensitive to camera motion. The tool checks pixel stability, not actual camera pose.

### Run a private comparison

```powershell
python research/world_bridge/carbon_pc_private_visual_evidence_gate.py compare `
  --before-png "C:\PRIVATE_TEST\before.png" `
  --after-png "C:\PRIVATE_TEST\staged.png" `
  --roi-json "C:\PRIVATE_TEST\PRIVATE_regions.json"
```

While the staged stream is still installed, optionally join the previous **read-only, same-PID exact-image-span ProcMon gate** with the screenshot comparison:

```powershell
python research/world_bridge/carbon_pc_private_visual_evidence_gate.py session `
  --session-dir "C:\PRIVATE_TEST\backup_session" `
  --procmon-csv "C:\PRIVATE_TEST\procmon.csv" `
  --before-png "C:\PRIVATE_TEST\before.png" `
  --after-png "C:\PRIVATE_TEST\staged.png" `
  --roi-json "C:\PRIVATE_TEST\PRIVATE_regions.json"
```

**After the original stream has been restored** and the third screenshot has been captured, run the reversible visual comparison:

```powershell
python research/world_bridge/carbon_pc_private_visual_evidence_gate.py compare `
  --before-png "C:\PRIVATE_TEST\before.png" `
  --after-png "C:\PRIVATE_TEST\staged.png" `
  --restored-png "C:\PRIVATE_TEST\restored.png" `
  --roi-json "C:\PRIVATE_TEST\PRIVATE_regions.json"
```

This tool never creates, modifies, exports or installs any PNG, stream or game file. It returns **aggregate-only** target RGB pixel error/fraction, anchor stability and verdicts. A clear two-shot candidate requires target mean RGB difference ≥15/255, ≥12% of sampled target pixels differing by ≥24/255 per RGB channel on average, and target mean difference ≥3× combined anchor difference + 10. Every anchor must have mean RGB difference ≤6.5/255 and ≤8% changed sampled pixels. These are deliberately explicit *heuristic thresholds*, not calibrated perceptual or engine-rendering guarantees. Each region is capped at 100,000 deterministic pixel samples.

The optional third screenshot is evaluated against the **original** (not the staged) image. A reversible candidate additionally requires stable independent background anchors and restoration target RGB mean <8/255 with <8% changed sample pixels. Poor reversion or poor background stability is reported as an inconclusive/failing visual control. No thresholds are silently tuned to make a specific donor pass.

## Input restrictions and source-only regression result

- One static, noninterlaced 8-bit **RGB or RGBA PNG** per screenshot, ≤64 MiB each, ≤14 million pixels, row ≤32,768 decoded bytes. The PNG parser validates chunk CRCs, zlib integrity, image bounds, IDAT ordering and all standard row filters. PNG screenshot alpha is ignored for **displayed RGB comparison**, not confused with underlying DXT5 alpha. Palette, grayscale, 16-bit, interlaced and animated PNGs, JPEG and other screenshot formats are rejected instead of silently transformed.
- Exactly one private ROI JSON (≤8 KiB), two to eight background anchor rectangles, all disjoint and in-bounds. Symlink inputs and aliased/hard-linked screenshot files fail closed. The successful report does not expose any PNG pixels, user-specific image filenames, file digests, ROI coordinates, original model/texture hashes, Process Monitor PIDs or installed game paths.
- **68/68 new synthetic regression tests** passed locally, covering PNG filtering/integrity/limits, ROI validation, stable/unstable target scenarios, A→B→A controls, no-write behavior and simulated integration with existing session evidence. A separate 1280×720 synthetic screenshot control returned a localized candidate with stable backgrounds; no original gameplay image was used or published.

## Evidence interpretation and remaining blockers

A positive two-shot pixel result only establishes a **localized screen difference candidate**. A positive A→B→A comparison additionally establishes a **reversible visual difference candidate in the supplied three files**, not their actual capture chronology. A positive ProcMon `ReadFile` intersection establishes only that a specific process read a disk byte range after opening a named file. The combined report does not cryptographically connect that read time with the stream's state or the screenshots' capture times. Screenshots can differ due to camera displacement, geometry, lighting, UI, alpha blending, ambient animation, postprocessing or unrelated state. Neither this tool nor the prior source-only CI performs or claims a Carbon PC game launch. A real user-controlled Windows run with visual inspection is still necessary.

**Always keep copyright-protected game data, private PNGs, ProcMon CSVs, camera coordinates, backed-up streams and installed game files off the public research branch.** This is a source-only experimental gate; PR #33 should remain draft and `main` unchanged.
