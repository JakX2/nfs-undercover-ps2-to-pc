# V62 | Ambiguity-safe scene-root anchor handoff

**Scope:** NFS Undercover Wii/PS2 → Carbon PC **Map & World Conversion / Geometry**, offline, read-only. **Not** a scene writer, patch, or Carbon PC loader proof.

## Source review: the V61 → V60 handoff gap

V61 correctly **reports** overlap and can scan bounded windows, but its unverified `v60_anchor_shortlist_unverified_provenance` is built from detected scene-like TLV candidates before rejecting mutually overlapping frames and does not require a complete file scan. A synthetic valid `0x80034100` ROOT placed *inside another candidate ROOT's instance payload* can therefore enter that raw shortlist. A truncated or partial scan might miss a containing ROOT entirely.

Passing a V61 raw shortlist directly to V60 can promote ambiguous offsets into a multi-root *structural hypothesis* audit, where a matching integer is too easily mistaken for true ownership. V62 fixes **that workflow risk** without changing V61's forensic inventory, changing game bytes, or guessing Carbon's loader.

## Conservative V62 gate

The CLI invokes V61 itself on the caller's **whole-file SHA-256-guarded** local stream. `filter_candidates` sorts returned `[offset, end_exclusive)` ROOT ranges, performs an O(n log n) max-end sweep, and excludes **both sides** of any overlap from the V60 handoff. It checks overlaps against *all* framed direct-TLV candidates, not just scene-shaped ones. It also keeps at most one copy of identical ROOT bytes, and caps the V60 shortlist at 64 items, explicitly recording when the cap is reached. An empty root file and zero-candidate scan are supported.

No V60 anchors are released unless the scan is **complete over the entire file**, `start_offset=0`, `stop_offset=file_length` and `scan_complete_within_window=true`. A partial window or an interrupted/capped scan may still report its original V61 observations, but has `eligible_count=0` and `handoff_status=incomplete_scan_no_handoff`. Non-overlapping, distinct candidate roots are then *conditionally eligible for further V60 hypothesis testing only*. A source hash does not authenticate a downloaded/unverified file as an original Carbon world stream.

The output is two objects: unmodified `v61_inventory` and `v62_gate`. The latter provides `eligible_v60_anchor_shortlist_unverified` in V60's anchor shape, with explicit negative `native_carbon_root_ownership_proven`, `native_carbon_master_index_or_loader_proven`, and `safe_to_install` flags.

**Limitation:** A direct-TLV scanner cannot prove an owner for any nested data, especially a root-looking marker inside a *non*-TLV parent that was rejected by V61. Our overlap check only covers candidates V61 successfully framed; it is not Carbon runtime ownership proof.

## Usage

Compute the whole-file SHA-256 for your own original local file. Then run:

```bash
python research/v62/v62_ambiguity_safe_anchor_gate.py \
  --source /path/to/your/original/world.BUN \
  --expected-file-sha256 THE_64_HEX_DIGIT_HASH \
  --endian little \
  --report /path/to/new-v62.json
```

The tool only reads the file and refuses to overwrite either the source or an existing report. For diagnostic partial scans, `--start-offset`, `--stop-offset` and `--max-candidates` are available, but **no shortlist is released for an incomplete scan**.

Only after independent original-file provenance checks should you select nonoverlapping candidate anchors as unverified entries in a V60 manifest. The Carbon master layout, row stride, field offsets, loader behavior and spatial/preculler ABI remain unverified.

## Verification, 2026-10-31

- **32/32 V62** tests run locally: **27 synthetic** (nested/adjacent/duplicate roots, mixed-kind parent, capped/partial scans, 100 nested roots, 65 disjoint roots, big-endian, SHA guards, CLI safety, and synthetic V60 handoff) + **5** exact-original-Wii-fixture tests. The private fixture is the 8,488-byte owner-provided original Wii RedBuilding ROOT, SHA-256 `cb08ca728a9b76992aaaefe32b450565ef53246f090cfe296f77d96c5d272e7f`.
- **154/154 older selected tests** rerun locally: V58 36/36, V59 38/38, V60 42/42, V61 38/38. Total **186/186** selected offline tests in this session.
- Public GitHub CI executes the 27 synthetic V62 tests; the five tests requiring `NFS_UC_WII_SCENE` skip without a privately supplied exact original file. Synthetic V60 tests use fake world streams and a fake master-index table, not a genuine Carbon PC source.
- No original game bytes, ELF, `.BUN`, `.chunk`, models, textures, or private source paths are in this package, PR or evidence summary.

## Next source requirement

The **original Carbon PC world/master archives** and at least two independent original scenery roots are still absent. Need independently authenticated source fingerprints, original root/master offsets and loader ownership before asserting Carbon scene indexing, geometry placement, or culling. First native RedBuilding render is **not verified**. V51's direct-original-Wii V49 regression is also a separate outstanding check.