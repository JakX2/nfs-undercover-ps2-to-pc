# Private / local research inputs

All the original game bytes were **excluded** from this GitHub-ready source snapshot. Keep them local and do not commit them (see `.gitignore`).

For reproducing the known source-backed regression tests, the original research bundles stored their test fixture paths as:

| Local-only path relative to repository | Role |
|---|---|
| `research/v41/UC_RedBuilding_Standalone_CarbonPC_V33.chunk` | V41 native PC donor fixture |
| `research/v41/UC_Wii_RedBuilding_Original_Scene.chunk` | V41 original Wii scenery scene |
| `research/v41/undercover_redbuilding_wii.chunk` | Original Wii model source fixture |
| `research/v41/samples/RedBuilding_1B_1C_1Z_Native_PC_V41.chunk` | Native PC-format sample library |
| `research/v46/fixtures/UC_Wii_RedBuilding_Original_Scene.chunk` | Original Wii scene for V43–V46 tests |
| `research/v46/fixtures/RedBuilding_1B_1C_1Z_Native_PC_V41.chunk` | Native PC-format model library fixture |

The Wii original scenery root used in V43–V46 is expected to be 8,488 bytes with SHA-256 `cb08ca728a9b76992aaaefe32b450565ef53246f090cfe296f77d96c5d272e7f`.

These private files may be obtained from your own authorized local extracts or the earlier offline research ZIPs; they are **not bundled here**. The test suites may read additional sample fixtures, as specified by their own scripts.

## Candidate Carbon PC source investigation

The previously reported Carbon donor scene ROOT offset `0x27BAF0C0` belongs to a specific earlier stream build and has **not been independently reverified from this snapshot**. Before any test of that offset, validate the exact original stream revision and root fingerprint. Do not write to original BUN files. PC `0x34105` and `0x34107` should not be decoded using Wii-only rules without independent evidence.
