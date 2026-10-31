# V46 | Evidence-gated Carbon scenery research and Wii 0x34107 marker audit

**NFS Undercover PS2/Wii → Carbon PC native port · Maps/Models Part 2**

## Milestone and limits

This is an **offline, read-only research package**. It does not contain an installable world mod or verified Carbon PC spatial writer. The original Carbon PC full world BUN, the original Carbon PC scenery ROOT at V42's reported stream offset `0x27BAF0C0`, the V42 modified standalone ROOT, and the original Wii executable with `LoaderScenery` are **not present** in this release. Consequently **no new V46 conclusion about Carbon PC's runtime spatial schema or world loading can be made**. V42's prior result remains a user-supplied handoff, not independently re-executed by V46.

Authenticated original input: the 8,488-byte RedBuilding Wii scenery ROOT from V41, SHA-256 `cb08ca728a9b76992aaaefe32b450565ef53246f090cfe296f77d96c5d272e7f`. The `0x34107` child payload is 3,072 bytes, SHA-256 `438eaa867c378de0d381e4815f45ee453395ab458cf73eb1dcc3985d05992e0b`.

## New source-byte evidence

The V44/V45 `128`-byte candidate block organization is independently checked at the **marker-offset level**, not just by looking for repeated values:

* The first 128B block is all-zero; the next **23** blocks are populated.
* All **23/23 populated** candidate blocks have footer `u32[2] = (384,384)` at block offsets `+120` and `+124`.
* A **global unaligned** search finds **25** appearances of the 8-byte `384,384` sequence; **two interior coincidental appearances**, at payload offsets `437` and `2741`, must not be mistaken for additional block boundaries. Exactly **23** marker appearances are aligned to the candidate footers at offsets `248, 376, ..., 3064`.
* All **391** leading `u32` values (`23 × 17`, first 68 bytes of each populated block) are multiples of 256, and bytes `+67..+119` are zero in all 23 populated blocks. The first 68 bytes are unique per populated block.
* The footer value `384` also equals the **384-byte** size of this particular Wii scene's `0x34105` spatial-tree payload. This is a reproducible **size correlation only**, not proof that the values are byte offsets, references, lengths, or linked at runtime.
* The old size ambiguity remains: `3072 = (31+1)*96 = 8*384`. Neither the instance-linked nor the node-linked hypothesis wins from this one scene.

**Never interpret the 128B candidate block as a proved writable or semantically decoded data structure.**

## New V46 tool

`v46_evidence_gate.py` reads a standalone scenery root or a scenery root in a full stream **without modifying either file**. For unknown roots, it reports chunk sizes and SHA-256, evaluates candidate record strides and instance alignment, produces evidence of possible 128-byte marker cadence and possible length correlations, and marks Carbon `0x34105`, Carbon `0x34107`, and runtime registration **unverified**. Successful hash checking confirms file integrity against the hash provided by the caller; it does not independently establish that a supplied stream is an authentic Carbon PC release.

It can optionally compare an original donor root with a V42-style modified root using the existing V45 exact-byte preservation contract, including checking against the verified Wii source record. **This is not a loader correctness proof.** If the source does not match the known Wii fixture, no Wii tree decoding is claimed. V43's 48-byte tree semantics are enabled as **validated** only for the exact Wii source fingerprint.

### Reproduce the verified Wii result

```bash
cd bridge_v46
python -m unittest test_v46 test_v45 test_v44 test_v43 -v
python v46_evidence_gate.py \
  --root fixtures/UC_Wii_RedBuilding_Original_Scene.chunk \
  --expected-root-sha256 cb08ca728a9b76992aaaefe32b450565ef53246f090cfe296f77d96c5d272e7f \
  --json new_wii_report.json
```

### Future Carbon PC check (requires original PC bytes)

```bash
python v46_evidence_gate.py \
  --stream /path/to/original/CarbonPC_WORLD.BUN \
  --offset 0x27BAF0C0 \
  --expected-root-sha256 YOUR_INDEPENDENTLY_VERIFIED_ROOT_SHA256 \
  --candidate /path/to/V42_standalone_root.chunk \
  --wii-fixture fixtures/UC_Wii_RedBuilding_Original_Scene.chunk \
  --json new_carbon_v42_comparison.json
```

`0x27BAF0C0` is a **prior V42 reported** offset, not reverified in V46. It must be checked on the exact correct original build. The original Carbon PC `0x34110` master row406 and UC Wii row348 reportedly have the same numerical section ID `0x343447`; this **does not** establish common world geography. Do not install or patch any game files with these tools. Output paths are exclusive: a pre-existing report is refused.

## Regression

- **V46:** 52/52 targeted tests (source fingerprint, marker alignment vs false positives, candidate shape negatives, CLI file-preservation and source-rejection).
- **V45:** 34/34 prior tests, rerun unchanged.
- **V44:** 30/30 prior tests, rerun unchanged.
- **V43:** 30/30 prior tests, rerun unchanged.
- **V41:** 18/18 prior tests, rerun separately from `bridge_v41` original source.
- **Total 164/164 targeted tests**. Original Carbon PC root and V42 executable/stream tests: **0**.

## Next milestone: V47

1. Acquire genuine original Carbon PC scenery BUN, exact donor ROOT and V42 ROOT candidate; run V46 and V45 on the **real** donor/candidate pair with known stream/root fingerprints.
2. Run the V43/V44 all-scene census across Carbon's original scenes; only report Carbon record rules after independent structural validation (the 48B Wii node schema **may differ**).
3. Obtain a second original Wii section with different instance and tree counts to separate the 0x34107 size hypotheses and see if the aligned 384 footer follows `0x34105` bytes or is an unrelated constant.
4. Obtain and inspect the symbol-rich Wii `LoaderScenery` code and Carbon PC consumer path for allocation, relocation, culling, streaming and child-buffer ownership.
5. Preserve V42 scene ownership, material/TPK, shader, collision and nav blockers until runtime evidence exists.

**No game install changed. No PC runtime verification. No installable patch.**
