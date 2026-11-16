# Undercover Wii: hosted private Ghidra analysis (standalone deployment)

This source-only, independent deployment is based on the default `main` branch.
It **does not merge** PR #36 or publish Nintendo Wii game code/assets.

## Verified capabilities

- GitHub-hosted Ghidra 12.1.3 with SHA-256 pin and GameCube/Wii Loader 1.3.1.
- Gekko/Broadway PowerPC language, Wii DOL import and callgraph smoke test.
- Synthetic PowerPC regression tests on pull requests, no owner input or secrets.
- An optional **authenticated owner-original** analysis job on `main`, once enabled.

The original job is disabled unless **both** the workflow is merged to default
`main` and repository variable `WII_GHIDRA_PRIVATE_ENABLED` equals `true`.
It also requires three GitHub Actions secrets:

| Secret | Description |
| --- | --- |
| `WII_GDRIVE_SERVICE_ACCOUNT_JSON` | Google service account JSON with Drive readonly scope, created under the owner's Google Cloud project. |
| `WII_ORIGINAL_DOL_ID` | Drive file ID for the original `NfsMWRelease.dol`. |
| `WII_ORIGINAL_ELF_ID` | Drive file ID for the original `NfsMWRelease.elf`. |

The owner needs to enable the Google Drive API and share the **two existing
Drive files** with the service account email as **Viewer**. No PC setup or
server is required. Do not turn on public “anyone with link” sharing. Never
put private JSON credentials, tokens or game bytes in a public issue or PR.

The workflow downloads only the two owner files to an ephemeral hosted runner,
checks exact file sizes and complete SHA-256s before any analysis, then uses
Ghidra's GameCube DOL loader with automatic map-file lookup disabled (otherwise
it opens a GUI dialog in headless mode). Ghidra output and logs remain in
ephemeral runner scratch and are deleted at job end. No game originals,
functions.json, PCode, callgraph CSV or pseudocode is published as an artifact.
Only aggregate function/edge counts are printed on success.

**Important limitation:** Because all original-derived metadata is kept private
and discarded, the hosted job does not yet feed a persistent callgraph into
NWiiRecomp. A later owner-private output destination would be required.
This is analysis infrastructure, **not** evidence of complete original Wii
`__start`, `main()`, graphics, a frame or gameplay. Keep PR #36 in draft.

## Activation steps

1. Merge this **standalone** PR, not the unrelated native recompilation stack.
2. Create the Drive service account, grant the two files Viewer access, and
   configure the three Actions secrets above on the NFS GitHub repository.
3. Set **Settings → Secrets and variables → Actions → Variables →
   `WII_GHIDRA_PRIVATE_ENABLED` = `true`**.
4. Run **Actions → Undercover Wii hosted Ghidra → Run workflow** on `main`.
   Thereafter the original job is scheduled daily at 03:41 UTC, subject to
   runner availability and any repository Actions restrictions.

If the variable is absent or not `true`, the original-binary job is **skipped**.
The synthetic PR smoke is safe without any secrets. We cannot configure GitHub
repository secrets or the owner's Google Cloud account through the current
repository connector; these one-time controls remain owner-managed.

Reproduce source-only regressions:

    python3 -m unittest discover -s research/cloud_ghidra -p 'test_*.py' -v

Tool sources: Ghidra official NSA releases, and
https://github.com/Cuyler36/Ghidra-GameCube-Loader.
