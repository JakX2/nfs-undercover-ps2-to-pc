# V61: Read-only embedded scenery-ROOT inventory

**Area:** NFS Undercover Wii/PS2 → Carbon PC, **Map & World Conversion / Geometry**. **No game writer, patch or executable modifications.**

## Problem solved

The V43 scenery census assumes a correctly framed top-level chunk stream and advances by the declared top-level chunk lengths. V59/V60 require each ROOT's precise byte offset and a fingerprint. Original Carbon PC master/world archives, whose enclosing framing or root offsets are not yet authenticated in this project, cannot be tested with V60 until candidate roots are located. V61 provides **bounded read-only byte-pattern discovery** as a *candidate inventory*, not an assertion of Carbon serialization.

This is complementary to V43, not a replacement for its top-level chunk walker or spatial-tree validation. In V61 the user explicitly specifies the original local file and its independently computed SHA-256. The scanner uses read-only `mmap` after hashing the complete file once, examines every occurrence of byte-order-specific `0x80034100` in a chosen search window, and checks a bounded frame and candidate direct-child TLV grammar. The window bounds candidate **start addresses**; accepted frames may extend beyond the search stop into the authenticated file.

Candidate results are classified:

- `scenery_direct_TLV_candidate`: framing parses as direct nonnested `(u32 tag, u32 payload_length)` children and includes `0x34101` (at least four bytes) and `0x34103`;
- `other_direct_TLV_candidate`: framed direct TLV parses but lacks the above candidate child combination;
- malformed framing or an incompatible direct-child grammar are counted, **not** declared invalid Carbon data. The actual native Carbon ABI has not been established.

All child IDs, payload lengths and root-relative byte offsets are listed as *observations*. The tool checks duplicate root bytes and overlapping candidate ranges and emits a maximum 64-item shortlist in **V60's anchor shape**. These entries deliberately omit platform/provenance approval. Different hashes and multiple addresses are **not** independently authenticated game scenes. The tool never fabricates a candidate `0x34110` table or field layout.

## Run on an owner-supplied local stream

Obtain the whole-file SHA-256 using your own local file, for example:

```bash
python -c "import hashlib,sys; p=sys.argv[1]; h=hashlib.sha256(); f=open(p,'rb'); [h.update(b) for b in iter(lambda:f.read(4*1024*1024),b'')]; f.close(); print(h.hexdigest())" /path/to/original-world.BUN
```

Then:

```bash
python research/v61/v61_root_candidate_inventory.py \
  --source /path/to/original-world.BUN \
  --expected-file-sha256 YOUR_64_HEX_DIGIT_SOURCE_SHA256 \
  --endian little \
  --report /path/to/new-V61-root-inventory.json
```

For a *known bounded region*, use `--start-offset 0x... --stop-offset 0x...`. The default cap is 2,048 structurally parsed root candidates. `--max-candidates 10000` increases that cap, but a capped inventory sets `scan_complete_within_window: false`. Do not call a capped inventory an exhaustive census.

The report stores only frame/child metadata, candidate offsets and SHA-256s. It has **no original game bytes or local source paths**. Results are not used to patch input files. The output must be a *new* file and cannot replace the source.

## Hand off to V60

Copy selected objects from `v60_anchor_shortlist_unverified_provenance` into the `roots` array of a separate V60 manifest, then **independently verify** the ROOT offsets/fingerprints and original source provenance. Add V60's authenticated `stream` and `master` whole-file SHA fields, explicit candidate `0x34110` chunk-header location and *manually supplied* row-stride/field-position hypotheses. No Carbon table layout can be assumed from this scanner. A V61 regression constructs **two synthetic roots, a synthetic table**, then passes V61's shortlist into V60 to verify the wiring.

## Verification (2026-10-31)

- **34/34 synthetic/asset-free V61 tests**, plus **four** tests using the exact original Wii RedBuilding scene ROOT (8,488 bytes, SHA-256 `cb08ca728a9b76992aaaefe32b450565ef53246f090cfe296f77d96c5d272e7f`), total **38/38 V61**.
- Independently reran V58 **36/36**, V59 **38/38** and V60 **42/42**, bringing the fresh selected regression total to **154/154**.
- Original Wii fixture is *not included* in this source-only project or GitHub. To rerun the four proprietary-fixture tests locally, set `NFS_UC_WII_SCENE` to your own verified original scene file path. Without it, those tests skip.
- Tested original Wii sample: one candidate root at standalone offset zero, two required scenery child IDs present, and child ID order `0x34101, 0x34103, 0x34102, 0x3410D, 0x34105, 0x34107`. The child meanings beyond established Wii observations remain unproven.

## Safety and remaining blockers

A search hit, correct TLV framing, matching SHA-256, or a uniquely matching V60 row **does not authenticate original Carbon PC bytes**. We still lack the real Carbon PC world BUN and master table, authenticated V42 Carbon original/candidate roots, actual Carbon loader/relocation references, and in-game evidence for model/material, visibility and collision. All reports mark PC ABI/loader proof and installability as `false`.

**Next:** Use V61 on *source-authenticated* original Carbon PC stream data, compare its candidate ROOT inventory against V43 top-level walk, and use distinct originals as V60 anchors. Revisit V51's separate direct-Wii-source V49-alignment regression before any native writer work.