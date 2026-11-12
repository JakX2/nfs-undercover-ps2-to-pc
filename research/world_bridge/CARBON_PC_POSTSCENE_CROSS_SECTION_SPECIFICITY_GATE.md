# Carbon PC native `0x372xx`: cross-section specificity gate (V2)

**Project:** Need for Speed Undercover PS2/Wii to PC using Carbon PC as the base.  
**Stage:** offline source-only reverse engineering; **do not treat this as an installable section writer.**  
**Date:** 2026-11-04.  
**Original Carbon PC execution in this V2 workspace:** **not performed**.  
**Validation:** 55/55 synthetic tests across V1 + V2 passed locally. No original game files or extracted textures/meshes are included.

## What this changes

The V1 gate checks individual 32-bit words in Carbon's structurally validated post-scene records against exact Carbon PC scene model hashes, indexed geometry hashes and root boundaries. The new V2 gate adds **leave-one-independent-section-out controls**. This avoids treating repeated observations in six control groups from section 141 as if they were six independent sections. It tests **section specificity**, not semantics or runtime loader behavior.

For each 4-byte slot of the opaque `0x37260` prelude, `0x37250` 120-byte body and `0x37270` trailer, the validator classifies non-sentinel values into four disjoint groups:

1. **Local only:** exact match to a verified scene or geometry hash in *this* Carbon section, absent from every *other* inspected section's verified hash sets.
2. **Foreign only:** absent locally, present in at least one *other* verified section.
3. **Ambiguous shared:** present both locally and in another section. This is **not** discriminating evidence for a section-local reference.
4. **Unmatched:** none of those source-backed model/geometry hash sets contain the value.

Zero and the observed sentinel candidates `0x11111111` / `0xffffffff` are excluded from hash-reference classes. V2 also splits local-only matches into **scene-only**, **geometry-only** and **scene-and-geometry**. The last class is especially important because native Carbon scenery-info model hashes often name a geometry-index solid too; that is **one matching identifier, not two independent pieces of evidence**.

A slot only passes the V2 *follow-up filter* when it contains local-only matches in at least **two separately selected sections**, without any foreign-only or ambiguous shared matches. This is a triage rule, **not** statistical significance, proof of a pointer, or evidence that the field should be patched.

## Source backing and limitations

The existing branch validates Carbon PC RB sections 141 and 142 with one native geometry root, a scenery root, and the exact `0x37220`/`0x37260`/`0x37250`/`0x37270` suffix. V2 calls those established validators, including model index and embedded eSolid hash membership, on **the same single in-memory copy of each selected section**. It does not heuristically scan all RB sections, because unsupported original envelopes would otherwise be misclassified as negative controls.

V2 cannot infer field meaning from 141 and 142 without reading the owner's actual bytes. Two sections also provide very weak generalization. A slot's local match may be coincidental, may describe something other than resource registration, or may not survive a section change; more original Carbon controls and negative cases are necessary. The previous 5.0/4.15 MB nominal resource headroom does **not** guarantee valid native index registration, collision, materials, scene lifetime or PC runtime acceptance.

The original PC suffix framing remains:

- Section **141**: six groups; 1,004-byte suffix.
- Section **142**: one group; 204-byte suffix.
- A `0x37250` body carries 120 opaque bytes per group.
- The source Undercover PS2 suffix is structurally different; it is **not** an interchangeable Carbon PC suffix.

## Private reproducible run

Keep the V1 and V2 files beside the existing `research/world_bridge` modules from draft PR #33 (specifically `carbon_pc_native_postscene_layout_gate.py` and `geometry_hash_control.py`). Run in that directory:

```powershell
python -m unittest -v test_carbon_pc_postscene_dependency_probe.py test_carbon_pc_postscene_cross_section_gate.py
python carbon_pc_postscene_cross_section_gate.py `
  --carbon-bun 'C:\PrivateBackup\L5RB.BUN' `
  --carbon-stream 'C:\PrivateBackup\STREAML5RB.BUN' `
  --sections 141 142
```

The V2 JSON nests the earlier V1 field results and the new V2 cross-section-specificity table, with the list of slots passing the *follow-up* filter. No per-resource hashes, model IDs, raw control data, coordinates, original stream offsets or filenames are emitted. The script makes no game-file writes; malformed scenes/geometry, bad sources, duplicate section arguments and unrecognized frame lengths are rejected.

## Next decision

1. **Execute against actual private Carbon PC controls 141 and 142.** Any V2 slot passing the filter is a *candidate worth investigating*; it is not an approved patch field.
2. **Expand to a third independently authenticated original Carbon PC scene** with the *same exact native envelope* if one is available; explicitly document which layouts were excluded and why, rather than silently classifying them as failures.
3. If the same slot is consistently section-specific, test whether its values also correlate with section geometry, scenery or independent PC control records. Investigate runtime semantics only after the byte-level hypothesis survives counterexamples.
4. **No donor insertion or suffix copying until there is a verified, reversible private runtime path.** Other unresolved blockers remain native texture/model identity registration, the two missing image identities in the measured candidate set, materials, collision, roads and AI.

**Status:** V2 source is tested against synthetic fixtures only. PR #33 remains a draft; `main` is unchanged. This ZIP is a source-only research supplement, not a claim that the game loads the port.
