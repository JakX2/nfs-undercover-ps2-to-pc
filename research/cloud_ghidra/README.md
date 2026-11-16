# Undercover Wii: hosted Ghidra without a PC installation

Hosted Ghidra was deployed to default main via PR #37. The CI workflow
.github/workflows/wii-ghidra-hosted.yml uses SHA-256-pinned Ghidra 12.1.3
plus GameCube/Wii Loader 1.3.1 and Gekko/Broadway PowerPC definitions.

## Original Wii inputs: the same Drive-link method as SiN

No Google Cloud project or service-account credentials are required.
The original Wii DOL and ELF currently have Google Drive
"Anyone with the link: Viewer" permissions, as verified from Drive metadata.
Note that anyone with the link can access those files. A GitHub Actions
secret conceals the ID from routine public configuration and logs; it
does not turn link sharing into authenticated access.

In GitHub repository Settings → Secrets and variables → Actions, create
these TWO repository secrets:

| Secret | Value |
| --- | --- |
| WII_ORIGINAL_DOL_ID | Google Drive file ID of NfsMWRelease.dol |
| WII_ORIGINAL_ELF_ID | Google Drive file ID of NfsMWRelease.elf |

Then, under Settings → Secrets and variables → Actions → Variables, set
the repository VARIABLE WII_GHIDRA_PRIVATE_ENABLED to true.

The original job is gated by that variable and runs on manual dispatch
from main or daily at 03:41 UTC. Source-only pull request smoke runs
without any game files or secret values. No PC-side setup is required.

## Full binary verification and privacy

- Uses the gdown==5.2.0 library silently, downloading into a fresh
  owner-only temporary directory on the hosted Actions runner.
- Rejects duplicate/malformed/missing IDs, missing content and file
  size or SHA-256 mismatches. On failure temporary staging is deleted.
- Expected NfsMWRelease.dol: 6,433,280 bytes, SHA-256
  16a09adcf1987c1f3617d10f3a1cb830f32886afb583f9f8f88e0963ae5fe1f4.
- Expected NfsMWRelease.elf: 11,151,296 bytes, SHA-256
  fd9681f2b06e961667bcad2eea6aaf6c762e0f30d666376d1ebb5f2946455ab0.
- No owner binaries, Ghidra project/database, original symbol index,
  generated C++ or full Ghidra code/decompilation are uploaded to Actions
  artifacts or committed to this public repository.
- The private job uses -loader GameCubeLoader and -loader-autoloadMaps false
  to avoid GUI map-file dialogs, and discards the private index after checks.
- This workflow checks a synthetic DOL on pull requests; that is not
  evidence of original-game analysis. Actual original code must run under
  the gated job before that milestone is claimed.

## Native recompilation CI

The draft native port remains on PR #36, branch
research/wii-native-recomp-preflight, separately from the merged cloud workflow.
Its private native CI can use the very same two Actions secrets to fetch
owner game files for SHA-pinned V68 tests after the enable variable is set.

The last verified continuous original startup checkpoint is V26 at
0x805206B4 (test-only stop), while the direct-entry OSInit test reached
0x804EFA34. No original main, frontend, first frame or playable game yet.

Test independently authored staging regressions:

    python3 -m unittest discover -s research/cloud_ghidra -p 'test_*.py' -v

This approach depends on GitHub Actions quotas and Drive link availability.
If public link access is later revoked, a properly authenticated access
method will be needed instead.
