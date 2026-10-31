# V59: Source-guarded streaming master-index hypothesis and address impact

**Scope:** NFS Undercover Wii/PS2 → Carbon PC, Map & World Conversion / Geometry. Offline, **read-only**, non-installable.

## Why V59 exists

V57 audits original/candidate offsets inside a scenery ROOT; V58 audits the enclosing stream and literal-number coincidences. V59 adds an **explicitly located, caller-supplied `0x34110` table hypothesis** and evaluates which purported stream offsets would remain unchanged or shift under a hypothetical +200-byte ROOT insertion. The tool never auto-classifies Carbon PC data or fabricates the location/format of a master table.

A source-backed reverse-engineering chapter for **Need for Speed: Most Wanted 2005 PC** describes a `0x34110` streaming table with 92-byte rows and a stream offset at row `+0x14`:

https://github.com/TsyVM/MWEncyclopedia/blob/main/C15-Track-Streaming/C15-Track-Streaming.md

**This is *not* Carbon PC evidence**. Row sizes, offset fields, base addressing, master location, section IDs and loader conventions must be independently confirmed for Carbon before this can justify modifying actual Carbon assets. In the V59 tool these values are mandatory caller-supplied hypotheses, not hidden defaults.

## Input manifest

The program takes a JSON file with independent SHA-256 guards for each input. All root scene inputs use the V55 format, including `path`, `label`, `endian`, `offset`, `expected_file_sha256`, and `expected_root_sha256`. The master table location and layout are explicit. Example *illustrative* manifest values (not real Carbon offsets):

```json
{
  "original_stream": {
    "path": "/local/STREAM.BUN",
    "label": "local verified original",
    "endian": "little",
    "offset": 128,
    "expected_file_sha256": "<64 hexadecimal digits of input stream>",
    "expected_root_sha256": "<64 hexadecimal digits of framed root>"
  },
  "original_master": {
    "path": "/local/MASTER.BUN",
    "expected_file_sha256": "<64 hexadecimal digits of master>",
    "chunk_header_offset": 32,
    "row_stride": 92,
    "row_count": 4,
    "offset_field": 20,
    "offset_base": 0,
    "endian": "little"
  },
  "target_row": 1
}
```

The caller-specified `chunk_header_offset` must actually contain little- or big-endian `0x00034110` followed by a declared payload length equal to `row_count * row_stride`. Otherwise the audit refuses the hypothesis. The `target_row` candidate offset must match the *independently SHA-guarded* ROOT position in the stream. These structural checks do **not** authenticate the assumed table layout's semantics. `offset_base` allows an explicit absolute base to be added to each 32-bit row field; there is no silent auto-detection of base/units.

Optionally provide **both** `candidate_stream` (V55 root format) and `candidate_master` (same master schema) to audit a V58-style byte-preserving +200-byte embedded-root pair. Legitimate Carbon relocation edits to the exterior of a world stream would deliberately fail that **narrow no-exterior-change** V58 check, which must **not** be treated as evidence that the native patch is invalid.

Run:

```bash
python research/v59/v59_master_index_impact_gate.py \
  --manifest /local/master_manifest.json \
  --report /local/V59_NEW_report.json
```

The output file **must not already exist**. Source files and manifests are never overwritten. Output contains row candidate numeric values, statuses, source SHA-256s and inferred offsets, not proprietary source bytes or private filenames. The `read_only` flag is always true and `safe_to_install` is always false.

## Row classifications

For original ROOT byte range `[start,end)`:

| Candidate field value | Classification | Hypothetical flat insertion projection |
| --- | --- | --- |
| `value < start` | Before ROOT | Unchanged |
| `value == start` | ROOT start | Unchanged |
| `start < value < end` | Inside ROOT | **Unknown** without verified child-relative mapping |
| `value >= end` | At/after old ROOT end | `value + 200` |

A returned numeric match **does not prove** a row field is a pointer, a master-table entry is interpreted by Carbon, or a packed stream can be safely rewritten. If a candidate master is provided, V59 records unshifted **possibly stale** fields and changes to any other row bytes, without treating either as an installability verdict.

## Test evidence

- **35/35 synthetic** asset-free tests, including verified exact-field selection, root-start anchoring, derived +200 displacement, changed non-offset fields, stale candidate offsets, header/row/length guards, SHA mismatch, malformed manifest, endian mismatch, paired-file exterior mutation, no-path leakage and CLI overwrite safety.
- **3/3 source-hash-pinned Wii fixture tests**. These embed the exact original 8,488-byte Wii RedBuilding ROOT (SHA-256 `cb08ca728a9b76992aaaefe32b450565ef53246f090cfe296f77d96c5d272e7f`) into a **synthetic stream** alongside a **synthetic `0x34110` master table**. This verifies tool framing and source linkage only, **NOT a real Wii or Carbon master-table schema**.
- Reran 36/36 V58 and 31/31 V57 tests locally. V51 original fixture direct parser tests remain separately outstanding.
- No independently authenticated original Carbon PC world/master stream or V42 PC donor/candidate pair is present here. No original game bytes, scene/model assets, textures or executable files are committed.

## Outstanding

1. Obtain owner-supplied genuine Carbon PC master and world stream, fingerprint each entire source and extract the exact candidate scenery ROOT from the reported stream position.
2. Decode the **actual Carbon** `0x34110` row layout using original byte cross-validation, multiple rows, and loader consumer code, not by borrowing MW2005's layout.
3. Read-only compare a genuine V42 donor/prototype pair, inspect any altered master fields and world-relative offsets. Only then consider native scene registration, visibility, relocation and renderer integration.
4. Continue separately verifying collision/road/nav and material-TPK bindings before an installable native RedBuilding world patch.

The V59 report additionally flags **ambiguous target-root rows** (multiple candidate entries whose configured offset equals the root start) and **32-bit field overflow** if an offset projected beyond the configured `offset_base` cannot be represented by the declared u32 field. Neither condition is silently repaired.