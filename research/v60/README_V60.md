# V60: Multi-anchor `0x34110` layout hypothesis discriminator

**Area:** NFS Undercover Wii/PS2 → Carbon PC, Map & World Conversion / Geometry. Source-only, **read-only**, **not installable**.

## Why

V59 checks whether a **manually specified row** in a candidate streaming master table equals an authenticated scenery ROOT offset. A single matching integer is weak evidence: unrelated fields, another row stride or coincidental values can produce a false match.

V60 expands the test to an explicit set of independently **fingerprint-guarded ROOT byte ranges** within the same stream and multiple manually declared master-table layout hypotheses. It does **not** search blindly for a true Carbon field, and it does not infer loader semantics. All input paths are local, all source files are read-only and game bytes never appear in its JSON report.

The `0x34110` 92-byte-row, offset-at-`+0x14` description documented in [MWEncyclopedia for **Most Wanted 2005 PC**](https://github.com/TsyVM/MWEncyclopedia/blob/main/C15-Track-Streaming/C15-Track-Streaming.md) is an **illustrative external hypothesis only**. It is **not confirmed for Carbon PC**.

## Inputs

A JSON manifest supplies:

```json
{
  "stream": {
    "path": "/local/original_world_stream.bun",
    "expected_file_sha256": "<64_hex_digits>",
    "endian": "little"
  },
  "master": {
    "path": "/local/original_world_master.bun",
    "expected_file_sha256": "<64_hex_digits>",
    "chunk_header_offset": 32,
    "endian": "little"
  },
  "roots": [
    {"label": "source_root_A", "offset": 128, "expected_root_sha256": "<64_hex_digits>"},
    {"label": "source_root_B", "offset": 4096, "expected_root_sha256": "<64_hex_digits>"}
  ],
  "hypotheses": [
    {"id": "illustrative_92_20", "row_stride": 92, "row_count": 4, "offset_field": 20, "offset_base": 0},
    {"id": "alternative_field", "row_stride": 92, "row_count": 4, "offset_field": 24, "offset_base": 0}
  ]
}
```

**These are illustrative values, not real Carbon offsets or a validated Carbon row shape.** SHA values must be obtained independently from the original local files. V60 requires each extracted ROOT's exact SHA-256 and validates `0x80034100` root framing at the explicit offset. Root ranges cannot overlap or reuse the same offset, and row/table sizes must obey V59's bounded, explicit chunk-header constraints. Duplicating identical ROOT payload bytes at different offsets does not make them two distinct source structures.

To run:

```bash
python research/v60/v60_multi_anchor_index_gate.py \
  --manifest /local/V60_manifest.json \
  --report /local/V60_NEW_report.json
```

The report must be a new file. Input streams, master tables, and the manifest cannot be overwritten.

## What the report can establish

For each proposed `0x34110` row shape, it records whether `count * stride` matches the explicitly located chunk, whether the field values uniquely match each ROOT start, which rows fall strictly **inside** each ROOT, and whether multiple candidate layouts satisfy the same anchors. It distinguishes:

- `layout_rejected`: candidate header/stride/count/field cannot be read as declared;
- `anchor_contradiction_or_ambiguity`: at least one source ROOT has zero or multiple matching rows;
- `single_distinct_root_structural_match_only`: all supplied anchors match, but only one distinct ROOT payload structure is represented;
- `multiple_distinct_roots_structurally_match_NOT_loader_proof`: multiple distinct ROOT bytes have uniquely matching row values. This is still **only an arithmetic/structural correspondence**.

Even if one layout uniquely fits several authenticated file hashes, that does not prove a field is a Carbon PC pointer or that the game loader uses the same base/units. SHA-256 verifies exact bytes, **not whether a user-supplied game file is a genuine original Carbon PC source**. The gate never sets `multiple_distinct_original_carbon_PC_roots_authenticated`, `carbon_PC_master_index_semantics_proven` or `safe_to_install` to true.

## Evidence and tests

- **37 asset-free synthetic tests**, checking multiple anchor matches, row-field alternatives, competing valid layouts, wrong hash/offset/endian, duplicate/overlapping roots, cloned payloads, source path exclusion, bounded input and report overwrite protection.
- **Five original Wii-fixture-gated tests**, run only with `NFS_UC_WII_SCENE=/private/path/UC_Wii_RedBuilding_Original_Scene.chunk`. These use the authenticated **8,488-byte Wii RedBuilding root**, SHA-256 `cb08ca728a9b76992aaaefe32b450565ef53246f090cfe296f77d96c5d272e7f`, **inside a synthetic stream/master**. That does not give us a real Wii master or Carbon PC index.
- **42/42 V60 tests** passed locally, plus **178/178** freshly rerun V55–V59 regressions, **220/220 selected offline tests** in this session. Public GitHub Actions runs only the 37 synthetic tests, skipping the five proprietary-source-dependent tests.
- No independent original Carbon PC world stream, genuine Carbon `0x34110` table or source-authenticated V42 donor/candidate pair is available. **No in-game test**.

## Next evidence needed

1. The user's original Carbon PC world stream and master file, with exact SHA-256s and unmodified source provenance.
2. At least two distinct original Carbon scenery roots in the stream, with independent root offsets and fingerprints.
3. Positive and negative field-layout witnesses across multiple rows and ideally **Carbon PC loader consumption**. Matching row arithmetic alone is not enough.
4. World-space placement, 0x34105/0x34107 visibility, model/material/TPK, collision and first in-game RedBuilding render as separate integration gates.

V60 **does not write, patch, reframe, rebuild, relocate or install game files**.