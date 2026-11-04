# Carbon PC native 0x372xx: byte-lane negatives and strict 3-section follow-up (V3)

**Project:** NFS Undercover PS2/Wii to Carbon PC, world-stream resource registration research.
**Date:** 2026-11-04.
**Classification:** source-only, owner-local, read-only reverse engineering.
**Original Carbon PC stream run in this V3 session:** NOT PERFORMED.
**Validated here:** 98/98 synthetic tests across V1/V2/V3. The tests exercise fabricated record bytes only, not genuine game asset payloads or native loading.

## Why V2 needs another gate

V2 classifies each 4-byte field of the authentic-source-shaped `0x37260`, `0x37250`, and `0x37270` group payloads as either a match to this section's validated scenery/geometry hash sets, a match to another section's sets, a shared/ambiguous match, or no match. Its follow-up rule is exploratory: *two sections with local-only matches* suffice even if the slot also contains unrelated, nonzero values. This can be overly optimistic. Six groups in Carbon PC section 141 also represent one independently selected section, not six independent controls.

V3 adds two independent constraints, **without assigning semantics to any field**:

1. **Predeclared byte-lane/endian negatives.** For the same original opaque payloads and the same independently authenticated model-hash inventories, check 4-byte little-endian words beginning at payload byte offsets `0, 1, 2, 3` (every fourth byte thereafter). Also check aligned big-endian words. Only aligned little-endian is the primary 32-bit candidate layout; the other four analyses are deliberate false-positive controls. Report how many words are zero, sentinel (`0x11111111` or `0xffffffff`), section-specific local-only, shared, foreign-only or unmatched. Report separate counts of independently selected sections with a local-only hit; never count multiple groups as independent sections. Misaligned lanes naturally have one fewer sample per nonempty payload, so compare rates or inspect sample counts, not only raw totals.
2. **Strict all-informative-word triage.** For a given `(record kind, 4-byte word index)` require at least **three genuinely distinct, non-overlapping, index-aligned original sections** with local-only matches. Also require **every nonzero, non-sentinel occurrence** of that slot, across all inspected groups and sections, to be an exclusive local-only hash match. Any unmatched, shared/ambiguous or foreign-only value prevents the strict filter from passing. Zero/sentinel values are excluded from the informative denominator. This is intentionally restrictive, so a real field containing optional non-hash metadata can be rejected without disproving that field's semantics.

### Built-in limits of V3

- A local-only match is still just a **32-bit numerical coincidence** until an independently tested loader model explains it. No significance estimate, relocation procedure, runtime registration ABI, texture sampler relationship or geometry loading is established.
- **Sections 141 and 142 alone cannot pass V3's strict filter**, even if all their nonzero field values match local-only model hashes. The result `insufficient_independent_sections_for_pass=true` is an explicit *insufficient controls* outcome.
- An additional original Carbon PC section must independently pass the existing strict native envelope/geometry/scenery validators. Do not turn a different PC envelope into an artificial negative control; failure of a parser built from 141/142 is not evidence that a different native section lacks `0x372xx` records.
- The source wrapper uses Carbon's original 92-byte `0x34110` section index, verifies every requested 2,048-byte-aligned non-overlapping section range, authenticates the native PC geometry-index/embedded eSolid match and scene hash table, then emits only aggregate counts, record kinds and word indices. It does not report game filenames, source offsets, section positions, hashes, model identities, textures or original resource bytes.
- The observed PC post-scene suffixes remain 1,004 bytes/six groups in section 141 and 204 bytes/one group in section 142. The Undercover PS2 suffix is different and is **not** a drop-in replacement.

## Commands

Keep this kit's files next to the existing `research/world_bridge` source in draft PR #33. Only the explicit original-source invocation reads owner game files. The existing native layout and geometry hash validators must be importable in the same Python environment.

```powershell
# Synthetic-only, no game files needed
python -m unittest -v test_carbon_pc_postscene_dependency_probe.py test_carbon_pc_postscene_cross_section_gate.py test_carbon_pc_postscene_lane_controls.py

# Private, read-only audit of the two known controls
python carbon_pc_postscene_lane_controls.py `
  --carbon-bun 'C:\PrivateBackup\L5RB.BUN' `
  --carbon-stream 'C:\PrivateBackup\STREAML5RB.BUN' `
  --sections 141 142

# Once a third original Carbon PC section has been validated to the SAME profile:
python carbon_pc_postscene_lane_controls.py `
  --carbon-bun 'C:\PrivateBackup\L5RB.BUN' `
  --carbon-stream 'C:\PrivateBackup\STREAML5RB.BUN' `
  --sections 141 142 THIRD_VALIDATED_SECTION_ID
```

## What to decide next

- If the primary aligned little-endian lane has *multiple section-specific matches* and the predeclared negative controls do not, investigate the matching slots further. Treat all fields as unknown until a separate engine or native control explains their purpose.
- If misaligned/big-endian controls also match frequently, reconsider whether the values are IDs, normal binary content or a coincidental small universe of 32-bit patterns. Do not edit post-scene data from a weak correlation.
- If no third comparable original section exists, the strict screen remains indeterminate. Prioritize a broader **native PC section-envelope census** rather than artificially relaxing the independent-source requirement.
- **Do not build a stream-section writer yet.** Four candidate geometry packs, proposed DXT5 textures, identity registration, two unresolved donor image identities, collision and driving/AI remain separate blockers. `main` stays untouched; PR #33 remains draft.
