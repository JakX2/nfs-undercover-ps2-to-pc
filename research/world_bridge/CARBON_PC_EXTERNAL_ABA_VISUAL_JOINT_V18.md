# V18: Correlated Carbon PC file I/O and reversible A/B/A visual evidence

**2026-11-12. Source-only, read-only owner-local tool. No original assets, model IDs, screenshots, paths or external loader binaries are committed.**

## What V18 adds

The existing V17 Carbon A/B/A file gate checks whether a known-good original Carbon control resource is opened/read by NFSC.exe in the enabled session but not the baseline or restored session, with stock-file read calibration in all three captures.

Separately, the existing strict RGB/RGBA PNG visual gate checks a localized target change with stable background anchors and whether the restored screenshot returns to baseline.

New tool **carbon_pc_external_aba_visual_joint_gate.py** combines both. It provides a pure redacted-report join and a read-only owner-local Windows CLI, requiring baseline/control/restore PNGs and ROI JSON in addition to the original manifest, BUN, stock sentinel, and three private ProcMon CSVs. Image and ROI sources must be separate and unmodified, not symlink/hardlink aliases of other private inputs.

## Evidence categories

- **CORRELATED_FILE_READ_AND_REVERSIBLE_SCREEN_CANDIDATE_NOT_REGISTRATION**: calibrated external file read isolated to B and controlled localized screen change that reverts on A2.
- **ISOLATED_FILE_READ_WITHOUT_REVERSIBLE_VISUAL_CANDIDATE**: file-read evidence but no corresponding controlled visual difference.
- **REVERSIBLE_VISUAL_CANDIDATE_WITHOUT_ISOLATED_FILE_READ**: screenshot evidence but no calibrated external-file read.
- **NO_CORRELATED_FILE_AND_REVERSIBLE_SCREEN_EVIDENCE**: neither independent positive candidate is established.

The tool distinguishes full-file byte coverage from any positive read. **All claims about the actual ASI running, engine resource registration, original file provenance, capture/PNG time alignment, specific Undercover model rendering and game conversion are explicitly FALSE.** Even an A/B/A correlation can be caused by unrelated game state, camera movement, other mods, caching or capture timing.

## Windows command (owner-private illustrative paths)

Run from the repository root on a clean backed-up Carbon test copy. Use one known-good original Carbon BUN and a stock, normally accessed game file as the calibration sentinel.

    python research/world_bridge/carbon_pc_external_aba_visual_joint_gate.py --carbon-game-dir "C:\Carbon-Test" --xnfs-manifest "C:\Carbon-Test\scripts\XNFSModFiles.txt" --original-carbon-bun "C:\Carbon-Test\MODS\KnownGoodPC.BUN" --stock-sentinel-bun "C:\Carbon-Test\TRACKS\STREAML5RB.BUN" --kind geometry --baseline-csv "C:\Private\baseline.csv" --control-csv "C:\Private\control.csv" --restore-csv "C:\Private\restore.csv" --baseline-png "C:\Private\baseline.png" --control-png "C:\Private\control.png" --restore-png "C:\Private\restore.png" --roi-json "C:\Private\roi.json"

The private ROI JSON must match the strict existing format, e.g.:

    {"format":"nfsuc-carbon-visual-roi-v1",
     "target":[100,100,128,128],
     "anchors":[[10,10,80,80],[450,10,80,80]]}

Adjust coordinates to actual screenshots. All three PNGs must show the same camera/view and image dimensions. The game and external loader must be configured separately; the tool cannot attest the run order or whether the loader was actually toggled.

## Source-only regression

New **test_carbon_pc_external_aba_visual_joint_gate.py** includes synthetic Carbon geometry and ProcMon A/B/A captures, PNGs and ROIs. It verifies positive joint classification, file-only and visual-only outcomes, unstable background, failed restoration, calibration failures, malformed reports, private-file immutability and alias/symlink rejection. The code/test commit 0108381a [passed 1,767 tests in GitHub Actions run 43157281259](https://github.com/JakX2/nfs-undercover-ps2-to-pc/actions/runs/43157281259).

## Next decisive milestone

Run a **real owner-local Windows** Carbon session and establish that one known-good ORIGINAL external Carbon resource not only gets read but is successfully **registered and rendered**. Only after independent registration/visual evidence should a converted Undercover PS2/Wii eSolid and matching textures be attempted.

The Carbon PR remains draft. **No Undercover in-game scenery or playable PC conversion is claimed.** The separate Wii-native physics decompilation PR #35 is untouched.
