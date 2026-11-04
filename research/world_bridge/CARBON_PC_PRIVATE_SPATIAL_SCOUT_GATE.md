# Carbon PC private spatial scout for a controlled DXT5 smoke test

Status: **source-only research code; runtime / road / camera location not proven.**

## Why this gate exists

Previous original Carbon PC source audit showed that the existing texture slot at **section 142, zero-based DXT5 slot 16** is used by **12 primary-detail scenery instances** arranged in **two groups of 6**, when using an experimental 12-source-coordinate-unit proximity threshold. Earlier controls validated **132 of 132** scenery-instance AABBs against the scene tree across sections 141 and 142. Those findings are carried forward, not new empirical observations from this module.

Our selected donor for a future reversible game-side smoke test remains **original Undercover PS2 section 241, zero-based source ordinal 31** into **Carbon PC section 142, DXT5 slot 16**. No new hash is registered.

This new gate closes a *tooling* gap: a user can privately produce a list of the exact **original Carbon scenery instance candidate bounds and group centers** for local debugging or a future object/map viewer, without posting original data. This does **not** identify road nodes, road centerlines, world origin, camera direction, a safe drivable coordinate or a location accessible inside the stock game. The identity and source-coordinate join remains an inferred offline interpretation of Carbon's serialized scenery ABI.

## Defaults and outputs

`carbon_pc_private_spatial_scout.py` imports the pre-existing source-backed Carbon PC texture, material, scene and spatial-tree validators and joins DXT5 slot identity to occurrence-specific meshes, primary-detail scenery records and 96-byte instance AABBs. It validates the 48-byte tree containment and groups centers with the experimental threshold.

**Default CLI is read-only** and prints **aggregate-only** dimensions, counts, bounding extents and cluster sizes. No private model hashes, texture hashes, absolute XYZ coordinates, original filenames or file digests are included in its report.

Run against owner-supplied, locally extracted original Carbon PC files:

```bash
python research/world_bridge/carbon_pc_private_spatial_scout.py \
  --carbon-bun "<private>/L5RB.BUN" \
  --carbon-stream "<private>/STREAML5RB.BUN" \
  --section 142 --slot 16
```

Optional owner-only private coordinate export (never commit/share this CSV):

```bash
python research/world_bridge/carbon_pc_private_spatial_scout.py \
  --carbon-bun "<private>/L5RB.BUN" \
  --carbon-stream "<private>/STREAML5RB.BUN" \
  --section 142 --slot 16 --cluster-distance 12 \
  --private-csv "<separate-private-folder>/PRIVATE_carbon_slot16_scout.csv"
```

The tool refuses existing output paths, symlinked paths, repository and game `TRACKS` folders, output filenames without the `PRIVATE_` prefix or `.csv` suffix, duplicate instance ordinals, nonfinite coordinates and malformed CSV schemas. It creates the CSV exclusively and, on POSIX systems, uses mode `0600`. It never installs a game resource or edits any input file.

Private CSV columns include section and DXT5 ordinal, source scenery instance ordinal, experimental cluster ID and size, group-center XYZ, group-min/max XYZ, and instance-min/max XYZ. These coordinates are **model-derived candidate scenery locations**, not an engine-camera API or GPS coordinates.

## Validation

- **46 new synthetic regression tests** for source coordinate grouping, per-instance completeness, identical-model deduplication, invalid scene hierarchy, opt-in CSV schema, and exclusive private-file safety.
- **99/99 focused local tests** passed when combined with the pre-existing 53 tests for validated spatial-tree containment and source slot grouping.
- The new source and tests contain **no original game assets or private game coordinates**. No CSV is generated as part of tests and no original Carbon file is exported or modified.
- The earlier original Carbon source measurements above are retained as evidence from prior runs; the new opt-in CSV exporter has not yet been tested inside the actual game, and it does not by itself prove an in-game position or visibility.

## Next falsifiable gate

Combine this private local geometry hint with a **real user-controlled Windows test**: create a reversible Undercover donor DXT5 staged stream, back up original data, run Carbon, collect both a ProcMon read spanning the changed image and reproducible before/after screenshots, then restore exact original bytes. Attempting to infer a road path solely from source AABBs would be a false-positive risk. No runtime texture rendering, new Undercover identity registration, road navigation, collision or complete world port is established here.
