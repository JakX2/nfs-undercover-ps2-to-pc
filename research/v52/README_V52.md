# V52: Wii `0x34107` candidate mask diversity (offline only)

**Branch:** Map & World Conversion / Geometry. All observations refer to one
original, SHA-256-pinned *Undercover Wii* RedBuilding scenery root. This is
not a Carbon PC serialized-format proof, runtime visibility decoder, writer,
or game modification.

## Original source and evidence

- Exact original Wii scenery root: **8,488 bytes**, SHA-256
  `cb08ca728a9b76992aaaefe32b450565ef53246f090cfe296f77d96c5d272e7f`.
- `0x34103`: 31 original 96-byte candidate instances after 4 opaque alignment bytes.
- `0x34107`: 24 × 128-byte candidate blocks. Block 0 is all zero and referenced
  by original instances; blocks 1–23 are populated and are all distinct.
- In all 23 populated blocks, the first 17 little-endian `uint32` words have
  byte +0 of each word zero; their candidate mask area is offsets `+0..+67`.
  Bytes `+68..+119` are zero; offsets `+120` and `+124` are the little-endian
  values `384,384`. The numbers equal the size of this fixture's `0x34105`
  spatial-tree payload, which is a correlation **not a semantic decoding**.
- Reading only the first 68 bytes as LSB-first candidate bit fields, there
  are **17 set bit positions shared** by all 23 populated blocks, **92 set
  positions in the union**, and **75 variable positions**. These counts
  intentionally exclude the repeated footer.
- Example *countercheck*: candidate blocks 16 and 18 are separated by
  ~0.456 source-coordinate units and have candidate-mask Jaccard similarity
  ~0.971; blocks 1 and 11 are separated by ~4,161 coordinate units and
  nevertheless share similarity ~0.942. Similar masks do **not** prove
  geographic proximity or a working culler/visibility rule.

## Safety and provenance boundaries

The pinned [third-party `nfsc-rtx` Carbon PC runtime struct](https://github.com/xoxor4d/nfsc-rtx/blob/252b44b877c207a9a70914d92c31f116ad92a469/src/comp/game/structs.hpp)
shows a 128-byte `preculler_info` bit array, and the [runtime hook](https://github.com/xoxor4d/nfsc-rtx/blob/252b44b877c207a9a70914d92c31f116ad92a469/src/comp/comp.cpp)
references it. **Neither reference demonstrates** that Carbon's *on-disk*
`0x34107` data match this Wii fixture's candidate block layout or that the
Wii bit positions control the same visibility sections.

The tool accepts any structurally valid root with source provenance marked
`unknown_root` unless its SHA exactly matches the pinned Wii source.
A caller-supplied expected SHA is an integrity guard only, not provenance proof.
The script never modifies original game data and refuses to overwrite a
report. It emits aggregate counts, examples and hashes, **not game bytes**.

## Run locally with your own legally obtained original game fixture

```bash
# Public GitHub CI: 23 synthetic tests, no proprietary fixture
python -m unittest discover -s research/v52 -p 'test_v52.py' -v

# Optional private source-backed tests: 23 synthetic + 6 original fixture
NFS_UC_WII_SCENE=/private/path/UC_Wii_RedBuilding_Original_Scene.chunk \
    python -m unittest discover -s research/v52 -p 'test_v52.py' -v

# Create an output JSON report in a fresh location
python research/v52/v52_preculler_bit_audit.py \
    --scene /private/path/UC_Wii_RedBuilding_Original_Scene.chunk \
    --expected-root-sha256 cb08ca728a9b76992aaaefe32b450565ef53246f090cfe296f77d96c5d272e7f \
    --report /tmp/v52_wii_bit_summary.json
```

## Tests actually run in the offline research session

- V52: **29/29** (23 synthetic + 6 original-source SHA-pinned tests).
- Independent historical re-runs: V41 **18/18**, V43–V46 **146/146**,
  V50 **24/24**, totaling **188/188** prior selected tests.
- The four private V51 tests using the corrected *GitHub V49* file are still
  pending a direct rerun; the previous GitHub V51 asset-free synthetic CI was
  green. Do not misrepresent these as newly rerun here.
- Carbon PC world stream test: **none**. In-game test: **none**.

## Next milestone: V53

Compare independent *source-authenticated* original Carbon PC scenery roots
and additional original Wii scenes with different instance/node counts. Test
if candidate block stride, footer, bit-mask field boundaries and indexed
membership survive the cross-game comparison. Trace actual Carbon PC scenery
loader/culler consumers before writing any `0x34107` records. The offline
V42 insertion's untouched spatial/preculler arrays remain an **unsafe
integration blocker**, not evidence that Carbon will display the building.