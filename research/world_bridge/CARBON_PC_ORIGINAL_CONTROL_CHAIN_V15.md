# V15: Correlated Carbon PC original-resource loader control

**2026-11-12. Offline evidence only.** A read-only owner-local audit binds
one external-loader configuration, one validated PC-shaped Carbon resource,
and one ProcMon capture to the **same expected Windows path**. It neither
runs Carbon nor claims successful asset registration.

## Problem closed

Prior V14 tools independently verified XNFSModFiles.txt, a PC geometry or
texture root, and NFSC.exe file reads. They did not establish that the
manifest, actual resource and captured reads referred to the same file.
Also, a scripts manifest could be shadowed by a working-directory
manifest, as the public XNFSModFiles source searches the working
directory first.

## New original-free implementation

- carbon_pc_original_loader_control_chain.py provides the pure
  audit_carbon_original_external_control, binding the manifest's
  relative MODS/*.BUN to one absolute Windows PC resource path.
  File framing and captured disk activity are verified using previous
  strict Carbon format and ProcMon parsers.
- audit_owner_carbon_control_files reads local files privately,
  refuses symlinks and oversized/changed inputs, requires the resource
  inside the selected Carbon PC test game MODS tree, and requires exactly
  ONE manifest in the game root OR scripts. Two manifests are rejected
  as potentially ambiguous/shadowed.
- The CLI is Windows-specific; a synthetic test-only Windows-root
  override lets Linux CI validate the path logic without original files.
- JSON reports contain scalar evidence and counts only, never private
  paths, source bytes, model/texture IDs or PIDs.

The report distinguishes complete same-PID full-file reads,
partial/unknown-range reads, file opens without subsequent reads,
and no captured positive access. All flags for provenance, ASI actually
loaded, engine CreateResourceFile/BeginLoading invoked, native model
registration, visible rendering and Undercover content loading are false.

## Owner-local Windows command

Use a clean, separate backed-up Carbon PC copy. Original Carbon PC
source and the ProcMon CSV must remain private. The following are
fictional example paths:

    python research/world_bridge/carbon_pc_original_loader_control_chain.py --carbon-game-dir "C:\Carbon-Test" --xnfs-manifest "C:\Carbon-Test\scripts\XNFSModFiles.txt" --original-carbon-bun "C:\Carbon-Test\MODS\KnownGoodPC.BUN" --kind geometry --procmon-csv "C:\Private\carbon-external-control.csv"

Example manifest single entry:

    1,1,MODS\KnownGoodPC.BUN

Stage 1/type 1 comes from the public XNFSModFiles example; it is NOT a
proven loader type for arbitrary Undercover scenery. This gate accepts
complete **indexed PC eSolid roots or texture roots**. A genuine
loader-compatible .BUN may have additional chunk/wrapper framing,
so a raw parsed root is not automatically a valid external bundle.

Positive read evidence only confirms file access as seen by ProcMon.
It does not prove Carbon parsed the data, read the same bytes during
capture, invoked loading APIs, registered a model or rendered it.
Caching, mapped file operations and capture filtering can hide I/O.

## Tests

test_carbon_pc_original_loader_control_chain.py verifies synthetic
PC geometry/texture controls, full/partial/open-only capture, no
positive access, wrong manifests/Windows roots/drives, same-PID
correlation, invalid source framing, redacted reports, resource path
scope, manifest shadowing, symlinks, missing files and immutability.

    PYTHONPATH=research/world_bridge python -m unittest discover -s research/world_bridge -p 'test_*.py' -v

The GitHub Actions source-only workflow runs this without proprietary
game files or third-party executable injection.

## Next decisive work

1. Identify a genuine original Carbon bundle whose **external-loader
   packaging** is actually supported; do not assume the root parser
   alone proves a loader-compatible bundle.
2. Capture an owner-local Carbon runtime baseline/control/restore,
   verify exact-file access, and separately establish resource
   registration and rendered output in game.
3. Only then attempt one converted Undercover eSolid and complete
   texture set using the proven loader path.

**Current status:** no verified Carbon external registration or actual
Undercover scenery displayed inside Carbon; no playable conversion.
This is draft PR #33. The independent native C++ Wii physics
reconstruction remains in PR #35.
