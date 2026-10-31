# V57 | Absolute child-address shifts in V42-style scenery ROOT appends

**Project area:** NFS Undercover PS2/Wii → Carbon PC, **Map & World Conversion / Geometry**. This is a **read-only** audit. The file formats and runtime are not proven compatible with Carbon PC. It cannot install, emit, or modify game data.

## Motivation

The earlier V42-style offline contract checks that a candidate appends exactly:

- one 72-byte `0x34102` scenery-info record;
- one 96-byte `0x34103` instance record;
- one 32-byte `0x3410D` auxiliary record;
- leaves all preexisting child payload bytes unchanged.

**That alone is not an address-integrity guarantee.** Increasing a child payload length moves subsequent child headers and payload starts in the root stream. If the info table precedes the instance table, its 72-byte increase changes the root-relative instance start by `72`, i.e. **8 modulo 16**. An unchanged four-byte instance prefix may then fail the candidate Wii 16-byte row-alignment rule. This is a *conditional* problem, not a claimed Carbon PC loader requirement.

## Authenticated Wii example

The original 8,488-byte RedBuilding Wii scenery ROOT SHA-256 `cb08ca728a9b76992aaaefe32b450565ef53246f090cfe296f77d96c5d272e7f` has the direct-chunk order:

`0x34101`, `0x34103`, `0x34102`, `0x3410D`, `0x34105`, `0x34107`.

Under a **pure +96/+72/+32 size projection**, with all original bytes unchanged:

| Child | Original payload start | Projected start | Delta |
|---|---:|---:|---:|
| `0x34101` | 16 | 16 | 0 |
| `0x34103` instance | 92 | 92 | 0 |
| `0x34102` info | 3080 | 3176 | +96 |
| `0x3410D` auxiliary | 4024 | 4192 | +168 |
| `0x34105` candidate spatial tree | 5024 | 5224 | +200 |
| `0x34107` opaque preculler candidate | 5416 | 5616 | +200 |

The projected root length is **8,688 bytes**, not a real converted game file. Importantly, the Wii instance payload starts before the info table and stays anchored at byte 92 (four-byte opaque prefix, first record at byte 96). However, the tree and preculler child payloads move by **200 bytes**. Their absolute 16-byte alignment residues change. No consumer-pointer validity or relocation consequences have been proved.

**This is *not* the Carbon PC V42 donor:** that standalone original Carbon PC root and prototype pair are absent. We do not know its authentic chunk order and must not project the Wii ordering onto Carbon. The earlier V42 report of an 8,616→8,816-byte append remains a separate, unverified user handoff.

## New read-only gate

`v57_append_layout_gate.py`:

1. Accepts a JSON manifest for original source and optional candidate, requiring exact whole-file and extracted-root SHA-256 guards through V55, bounded framing and explicit byte order.
2. Projects the absolute start/end of each original direct child under **exactly one +72/+96/+32 append**, without generating an edited ROOT.
3. Reports root-relative alignment residue changes and whether a byte-preserved 96-byte candidate Wii row table would still have compatible shape.
4. Optionally compares **real original/candidate bytes**, rejecting changed original data, different child order, unexpected child growth and an incorrect total size, without assuming the pair is installable.
5. Leaves Carbon PC serialization, pointers, spatial membership, preculler registration, texture/shader, collision, navigation, and runtime tests **unverified**.

The report contains hashes, lengths, child identifiers and offsets, but no original child bytes or local source file paths. `safe_to_install` remains false in every result. The contract is deliberately fail-closed.

### Usage

```bash
python -m unittest discover -s research/v57 -p 'test_v57.py' -v
NFS_UC_WII_SCENE=/private/original-wii-scene.chunk \
  python -m unittest discover -s research/v57 -p 'test_v57.py' -v
```

The private original fixture must match the exact SHA listed above. Public CI runs only the 26 synthetic tests; the five genuine Wii fixture tests skip without the private input.

Private manifest example (replace all hashes with **independently measured real values**):

```json
{
  "original": {
    "path": "/private/original-root.chunk",
    "label": "verified-source",
    "endian": "little",
    "expected_file_sha256": "<real 64-digit sha256>",
    "expected_root_sha256": "<real 64-digit sha256>"
  }
}
```

For a larger original `.BUN` stream, specify `offset` (JSON nonnegative integer), the real full-stream SHA and the extracted ROOT SHA. Include an optional `candidate` with the same keys to run the paired append audit. All input files are opened read-only. The output file must not already exist:

```bash
python research/v57/v57_append_layout_gate.py \
  --manifest /private/scene-pair.json \
  --report /private/new-layout-report.json
```

## Tests and limits

- **31/31 new V57 tests:** 26 asset-free synthetic (including both child orders, alignment residues, byte preservation, malformed roots and refusal to overwrite originals) and five original-source tests.
- In this session V55 **41/41** and V56 **32/32** independently rerun against the pinned original fixture.
- Earlier V41 through V56 selected suites were reported separately. **Do not sum tests from unrerun suites as a fresh verification.**
- The V51 four direct V49 tests against the original Wii scene remain an open, separately tracked verification gap; V57 does not claim to have executed them.
- **No original Carbon PC world stream or V42 original/candidate pair was available**, so the Carbon-specific result is unresolved. We must not install a scenery patch until actual PC loader/alignment, spatial tree, preculler, world registration and game render tests are confirmed.

## Next V58

Compare authenticated original Carbon PC ROOT and V42 candidate using the paired gate; check relative vs absolute alignment handling in the engine. If missing, investigate consumers of the native spatial-tree records from public reverse-engineering, without substituting their runtime structures for on-disk proof.