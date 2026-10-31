# V55: read-only scenery ROOT inventory for full game streams

**Purpose:** investigate more than one original Wii scenery scene without confusing candidate byte layouts, duplicate byte sequences, and independently authenticated original sources. This follows V54's *single* hash-pinned original Wii ROOT; it does **not** claim a second source, native Carbon PC ABI, loader compatibility or an installable patch.

## What the tool does

- Searches a user-supplied, locally stored stream/BUN for little-endian `0x80034100` ROOT headers using memory mapping.
- Rejects out-of-bounds ROOT lengths, malformed/duplicate child chunks, nested child tags, and missing `0x34101` source-scene chunk markers.
- Records per-candidate ROOT SHA-256, byte offset, total size, child IDs/lengths and optional candidate `0x34103` / `0x34107` / `0x3410D` stride checks. Alignment is computed **relative to the ROOT start**, not the enclosing file.
- Detects duplicate versus distinct ROOT byte hashes across one or more input archives, without claiming independent original-game provenance.
- Refuses to overwrite input archives or reports and permits an optional **separate, independently established** SHA-256 per original archive. The integrity hash alone is not a provenance certificate.
- Generates **metadata JSON only**, no original stream bytes, objects, textures or coordinates.

## Command line

Python 3.10+, standard library only:

```sh
python research/v55/v55_scene_inventory.py \
  --stream "/private/undercover_wii/TRACKS_MASTER.BUN" \
  --expected-stream-sha256 YOUR_INDEPENDENTLY_ESTABLISHED_64_HEX_ARCHIVE_SHA \
  --report "/private/reports/v55_wii_inventory.json"
```

For a comparative scan, repeat `--stream` for each original locally supplied file and provide one matching `--expected-stream-sha256` for **each**. Hash guards are optional, but are preferred when an independently measured archive hash exists. Pass `--max-root-bytes` and `--max-roots` to change strict limits. Reports may contain source-derived *metadata* and should remain local until reviewed.

## Interpreting the report

- `source_class: known_exact_Wii_RedBuilding_ROOT` means the bytes match the **single published research fingerprint** `cb08ca...272e7f`; this is not an assertion about where the supplied file came from.
- `unverified_candidate` remains unverified even if child counts and strides align.
- `distinct_root_sha256s > 1` only means distinct byte sequences. It cannot prove a second independently authenticated original Wii scenery scene. File/archive origin and a separate source fingerprint must be independently established.
- `Wii_candidate_stride_consistent` is a *format heuristic*: 96-byte candidate instance rows, 128-byte candidate preculler blocks, and 32-byte auxiliary rows. It does not decode semantics or establish a Carbon PC layout.
- `Carbon_PC_serialized_layout_verified`, `independent_original_scenes_authenticated`, `in_game_verified` and `safe_to_install` remain `false`.

The scan is deliberately limited to source-observed little-endian ROOT framing. Big-endian or compressed streams need separate readers and will not necessarily produce a candidate. Embedded nested ROOTs are deliberately not reported as independent scenes when the enclosing ROOT parses successfully.

## Tests

```sh
python -m unittest discover -s research/v55 -p 'test_v55.py' -v
```

20 synthetic tests cover offsets, alignment, duplicate detection, malformed inputs, digest guards, CLI output and overwrite prevention. **No original game data is committed to GitHub CI.** The local test run used only synthesized ROOT and archive bytes.

## Research next step

Run the tool *locally* against a provenance-verified original Wii archive and inspect structural candidates to find a **second scene with a distinct independently verifiable source location**. Only then attempt a fixed, predeclared, cross-scene comparison. Separately authenticate actual Carbon PC scene roots and derive that platform's record structure without applying Wii heuristics as a proven ABI.
