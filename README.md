# Need for Speed Undercover (PS2/Wii) → Carbon PC: native scenery research

**Offline reverse-engineering source snapshot through V46. Not a playable port.**

This repository-ready snapshot includes **original Python tooling, tests, documentation, and summaries** derived from the V41 and V46 research packages. V46 includes source/test modules from V43–V45. Original proprietary game streams, extracted models, scene `.chunk` files, textures and GLB previews are **intentionally excluded**. Do not add those to a public repository.

## What has actually been verified

- **V41 (offline):** RedBuilding model family 1B/1C/1Z converted into a native-format Carbon PC scenery library, with original object identifiers and LOD references for the test scene. Normals are reconstructed and the borrowed Carbon shader is not runtime-verified.
- **V43 (Wii source fixture):** the exact original Undercover Wii test scene has 31 96-byte instance records and a valid 8-node, 48-byte-per-node `0x34105` tree. Its references and descendant AABBs are byte-verified **for that fixture only**.
- **V44–V46 (Wii source fixture):** `0x34107` has a candidate 128-byte record cadence and a repeated `(384,384)` footer. Its semantic meaning is **unresolved**.
- **Regression:** full fixture-backed tests were rerun before stripping proprietary assets: V41 18/18 and V43–V46 146/146, for 164/164 selected offline tests. This snapshot itself cannot rerun fixture-dependent tests until the user supplies their own locally extracted inputs.

## What is not verified

- V42's original Carbon PC scenery root and modified root are **not included** here. The V42 25→26 insertion reported previously was not independently retested in V46.
- Original Carbon PC world stream, Carbon `0x34105` / `0x34107` schemas, section ownership, relocation, loader/runtime behavior, shader/TPK registration, collisions, nav and in-game placement have **not** been verified with these sources.
- A matching numerical section ID between Wii and Carbon does not establish matching geography.
- **Do not install or apply outputs from this research directly to game files.**

## Layout

- `research/v41/`: source and tests for native-format model LOD conversion.
- `research/v46/`: source, tests and docs for V43–V46 spatial/opaque chunk analysis.
- `docs/INPUTS.md`: instructions for keeping authorized game extracts local and untracked.
- `scripts/check.py`: safe syntax check; optional fixture-backed regression runner.

## Run

```bash
python scripts/check.py
```

With your own authorized game extracts placed in their expected local fixture paths (see `docs/INPUTS.md`):

```bash
python scripts/check.py --with-fixtures
```

The project does not contain game data and does not grant a license to third-party game assets. A software license for the newly authored tools can be chosen separately.
