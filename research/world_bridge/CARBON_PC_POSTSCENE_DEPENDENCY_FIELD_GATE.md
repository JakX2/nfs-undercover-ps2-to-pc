# Carbon PC post-scene `0x372xx` field dependency probe

**Stage:** independent read-only research gate. **Source status:** 29 synthetic regression tests pass locally. **Original-source status:** not rerun with the owner's Carbon PC binaries in this package. **Runtime:** no game launch, no files modified, no registration or relocation validated.

## Motivation

PR #33 established that original Carbon PC RB sections 141 and 142 contain native post-scene sequences: eight initial zero bytes, a 24-byte `0x37220` payload, followed by six and one sets respectively of `0x37260` / `0x37250` / `0x37270`. Their sequence lengths are 1,004 and 204 bytes. Those IDs identify empirical framing only. Copying the post-scene suffix onto a donor world section would assume unknown pointers, hashes or dependencies can be preserved. This tool **does not make that assumption**.

## What this gate adds

- Independently validates `0x37220` and every subsequent frame, including first-versus-later `0x37260` payload lengths, triple-agreeing group-count words, and no unparsed trailing bytes.
- Reuses existing source-only `carbon_pc_native_postscene_layout_gate.py` and `geometry_hash_control.py` to require an original Carbon PC section with a valid scenery root and indexed **native PC** geometry solids.
- Treats every 4-byte word in the opaque `0x37260`, `0x37250`, and `0x37270` records as a candidate for *correlation only*. Aggregates by word position across the selected sections.
- Counts exact (non-sentinel) matches to **scenery-info model hashes** and to verified **geometry-index solid hashes**. These are independent, source-validated sets, not raw byte-scans of arbitrary mesh payload.
- Separately counts exact matches to known section-relative/stream-absolute root boundaries, and weak aligned in-range candidates. In-range values do **not** establish pointers or relocation instructions.
- Reports per-slot sample counts, zero counts, nonzero diversity, exact-match totals, number of repeated 120-byte payloads, and distinct values for the still-opaque header word at index 4.
- Emits **only aggregates and word indexes**. No raw hashes, model IDs, file positions, scenery coordinates, string inventories, proprietary chunk bytes or per-resource lists. Does not open the game or write a byte to any original file.

## Reproduce with private owner source files

Place this module and its tests next to the existing `research/world_bridge/` modules from draft PR #33. After privately extracting and verifying the owner's split `TRACKS` archive, run:

```powershell
python -m unittest -v test_carbon_pc_postscene_dependency_probe.py
python carbon_pc_postscene_dependency_probe.py `
  --carbon-bun 'C:\PrivateBackup\L5RB.BUN' `
  --carbon-stream 'C:\PrivateBackup\STREAML5RB.BUN' `
  --sections 141 142
```

This explicitly reads the same two **Carbon PC** controls as the previous gate. `--sections` may specify another *known*, source-validated Carbon PC RB section, but it is not an automatic scan-all mode. Unsupported or malformed layouts raise an error rather than manufacturing a compatibility result. The tool expects extracted original files, not `.z01` split volumes.

## Decision criteria for the next stage

1. If any `0x37250` word position repeatedly matches verified native geometry-index hashes and scenery-info hashes across independent original Carbon sections, investigate it as a possible resource key. Check counterexamples and false matches before naming it.
2. If any word position repeatedly matches actual root boundaries, test whether values are section-relative, STREAM-relative, or another address space using **original controls of differing sizes**. A numeric alignment or range match alone proves nothing.
3. If the fields contain stable values unrelated to the verified scenery/geometry keys, compare other native Carbon sections or another platform before declaring them resource-registration records at all. These control blocks may have a separate purpose.
4. Do **not** implement a loader writer or donor-scene splice until source checks and a reversible private Windows runtime experiment establish safe semantics. Existing blockers remain: unresolved materials, object lifetimes, collision/roads and native loader ABI.

**Scope boundary:** 29/29 synthetic tests validate software behavior. They cannot establish any true original Carbon record correlation, successful Undercover loading or rendering. This package contains no retail assets and should remain on draft PR #33, with `main` untouched.
