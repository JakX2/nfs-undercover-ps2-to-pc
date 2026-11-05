# V10: First material-closed Undercover scenery model for a Carbon PC candidate

**Status:** source-only implementation with successful clean-checkout GitHub Actions tests. **No original game-file run of V10 has been performed in this milestone. No live Carbon PC engine registration, rendering, stream patch, collision or Undercover map loading is claimed.**

## Why one model?

V9 confirmed an original Undercover PS2 source-side material-image gap: **48** distinct material identities are used by the RB scenery, but **46** have validated original RB image-index entries. The other **two** were not resolved by the original-source RA/GLOBAL/FRONTEND/CARS/Unknown bank survey under the established strict texture layout. Converting all eight geometry packs at once would mix complete and incomplete material references while the Carbon loader ABI remains unverified.

The V10 gate chooses a **single** scenery-referenced original model and performs its geometry plus image conversion **entirely in memory**. It imposes a deliberately stronger closure criterion than V9: *every local texture-table entry*, including unused entries, must have a real original Undercover image. No missing material is silently rebound or fabricated.

## Deterministic eligibility and selection

For one selected original RB section (241 by default, or 3401), the tool:

1. Validates the owner-supplied ZIP and its CRC-checked \`TRACKS/L2RB.BUN\` and \`TRACKS/STREAML2RB.BUN\` members; resolves the original 92-byte stream section table.
2. Parses the original PS2 texture root and checks every image/palette against the 128-byte aligned pixel-data origin.
3. Validates the four original eSolid geometry packs, retains original pack and solid ordering, and finds the source scene-info primary-detail model identities through the established 72-byte scenery-info reader.
4. Excludes models without a primary scenery reference, models repeated in more than one pack in the same source section, and models with **any** local texture-table identity absent from the validated original image index.
5. Validates PS2 strip material/triangle budgets and excludes models outside an explicit triangle window (default **4–2,048** faces). Ranks survivors by smallest triangle count, then fewest distinct table identities, then more scene references, then original pack and model ordinals. No hash-based arbitrary tie-break or hand-picked model identity is used.

For the top candidate only, V10 decodes PS2 VIF XYZ/UV/faces, checks their material/face counts against the predeclared strip budget, reuses the existing PC-native 36-byte vertex/index/UV converter, and demands exact per-material triangle readback from the PC parser. It builds a DXT5 texture root containing **exactly the candidate's required source texture identities**, preserves their real original hash/name/dimension metadata, validates aligned image spans and BC3 decode, then discards both private candidate byte buffers. Output is **aggregate JSON only**. A successful synthetic/parser result is **not** a Carbon loader acceptance test.

Original \`0x00134011\` eSolid headers and candidate \`0xB3310000\`/pixel descriptor fields remain unverified for retail Carbon ABI. The original primary scene-info field has not been established as the runtime registration mechanism.

## Running against the owner's locally prepared sources

The owner already prepared \`UCPS2\TRACKS.zip\` from original \`TRACKS/L2RB.BUN\` and \`TRACKS/STREAML2RB.BUN\` and has a checkout of the draft research branch. From PowerShell:

\`\`\`powershell
$root = 'C:\Users\Dav\Desktop\nfsuc research'
python "$root\ResearchCode\research\world_bridge\undercover_pc_first_model_gate.py" \`
  --undercover-ps2-tracks-zip "$root\UCPS2\TRACKS.zip" \`
  --source-section 241
\`\`\`

The program **does not** create a model file or game patch. It does not write any source or installation file, does not print the source model hash, model name, original texture identity, original image bytes, location or vertex coordinates, and verifies the source ZIP fingerprint remains unchanged. It prints a reproducible **source pack ordinal and eSolid ordinal** without disclosing the original identity. For an intentionally wider selection window, supply \`--min-triangles 1 --max-triangles 10000\`; this does not weaken the image-index or scene-identity checks.

## Tests and evidence boundary

The new \`test_undercover_pc_first_model_gate.py\` adds **35 synthetic-only tests** covering deterministic ranking, full material-table closure, local duplicate-identity rejection, scene-reference validation, triangle/material accounting, native eSolid+DXT5 construction with the existing repository parsers, corrupted/partial image rejection and reports that cannot expose source identifiers. The complete GitHub Actions \`World bridge source-only tests\` workflow passed **1,560/1,560 tests** on 2026-11-05, after repairing four synthetic fixture/test-helper assertions found by the initial CI run.

All original Undercover game data remains owner-private. This V10 code is committed to **draft PR #33** and must **not** be merged or advertised as a working native port until genuine Carbon loader and renderer behavior is measured.

**Next falsifiable gate:** run V10 on the owner-original source, record the first qualifying section/pack/model *ordinal* and closure counts, then study the minimum Carbon PC scene/texture resource registration necessary for an isolated reversible model-load experiment. Do not attempt to install the parser-shaped pack into the game yet.
