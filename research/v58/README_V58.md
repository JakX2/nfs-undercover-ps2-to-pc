# V58 | Scene-root envelope shifts and outside-root numeric probes

**Project:** NFS Undercover PS2/Wii → Need for Speed Carbon PC, **Map & World Conversion / Geometry**.

## What changes compared with V57

V57 checks which **child payload addresses inside a root** move when three records are appended (+72 scenery-info, +96 instance, +32 auxiliary = **+200 bytes**). V58 lifts that read-only projection to an **embedded root in an arbitrary enclosing byte stream**, including the displacement of every byte that follows the root. V58 does **not** write a new root, game archive or installable mod.

Two separate risks should not be conflated:

1. **Byte-preserving envelope:** a candidate increases the scene root by exactly 200 bytes and preserves the original *external prefix and suffix*, with the old suffix appearing exactly 200 bytes later. This is a narrow and testable byte contract.
2. **External references:** an old absolute stream offset may still be written somewhere in the unchanged exterior; conversely, updating such a reference would violate the narrow byte-preservation contract. **Neither a numeric match nor a changed exterior proves a pointer, relocation or valid Carbon PC stream table.** Identifying authentic consumers requires the original Carbon executable, source-authenticated world stream and loader behavior.

The optional **exterior numeric probe** scans only deliberately bounded out-of-root windows, looking for 32-bit and 64-bit little- or big-endian encodings of the original root start/end and candidate original spatial-tree/preculler starts. It reports numbers, counts and example byte offsets, never calls these matches pointers, and never scans the opaque root payload as if it were a pointer table. No automatic patching is provided.

## Authentic Wii example versus synthetic enclosing streams

The available SHA-256 pinned Wii RedBuilding root is **8,488 bytes**, digest `cb08ca728a9b76992aaaefe32b450565ef53246f090cfe296f77d96c5d272e7f`. **It is a standalone ROOT fixture**, not a Carbon PC `.BUN` stream. V57/V58 project the original Wii payload locations without creating a modified file:

| Root-relative payload start | Original | After hypothetical +200 total append |
|---|---:|---:|
| `0x34103` instances | 92 | 92 |
| `0x34102` model info | 3,080 | 3,176 |
| `0x3410D` auxiliary | 4,024 | 4,192 |
| `0x34105` spatial-tree candidate | 5,024 | 5,224 |
| `0x34107` opaque candidate | 5,416 | 5,616 |

A separate **synthetic stream** places an invented small scene ROOT after a 64-byte prefix and before a `ending-tail` suffix, then uses an invented appended scene ROOT. This demonstrates, using controlled test data only, that the suffix would move 200 bytes and that a deliberately embedded old root-end integer in the unchanged prefix is still discoverable by a bounded raw-number search. This is **not** independent real Carbon evidence and **not** an interpretation of a Carbon master table.

## Use the source-verified reader

File: `research/v58/v58_stream_envelope_gate.py`; requirements: only Python 3.10+ standard library, `research/v57/v57_append_layout_gate.py` and `research/v55/v55_cross_scene_hypothesis_gate.py`.

The private manifest must include `original`, optionally `candidate`, and optional `windows` for numeric probes. Every source requires independently measured *whole-file* and *extracted-root* SHA-256 values and explicit `endian`. For an embedded root specify `offset` in **absolute stream bytes**:

```json
{
  "original": {
    "path": "/private/original-carbon-world.BUN",
    "label": "original-source-with-provenance",
    "endian": "little",
    "platform_hint": "carbon_pc",
    "offset": 666562752,
    "expected_file_sha256": "<real 64-digit file SHA-256>",
    "expected_root_sha256": "<real 64-digit root SHA-256>"
  },
  "windows": [{"offset": 0, "length": 4096}]
}
```

**The numeric stream offset is only an example**: independently re-read the actual supplied file before using it. `platform_hint` is a user label, not proof of source platform. Do not use sample placeholder digests; the tool fails closed. If you provide `candidate`, it must be a whole enclosing candidate stream containing a root at the same offset, with its own real whole-file/root digests. Candidate bytes are **not generated** by this tool. The strict pair audit rejects changes to prefix or suffix, while explicitly noting that legitimate relocations might require precisely those changes.

```bash
python research/v58/v58_stream_envelope_gate.py \
  --manifest /private/root-stream-manifest.json \
  --report /private/new-envelope-report.json

python -m unittest discover -s research/v58 -p 'test_v58.py' -v
NFS_UC_WII_SCENE=/private/exact-original-redbuilding-wii.chunk \
  python -m unittest discover -s research/v58 -p 'test_v58.py' -v
```

Output is JSON with hashes, counts, projected offsets, optional bounded numerical coincidences, and `safe_to_install:false`. The tool never overwrites an output, manifest, original game source or candidate. Manifest paths and original game bytes do not appear in the report.

## Testing and source boundaries

- **36/36 V58** offline tests: **31 synthetic** fixture-free tests and **five optional authenticated Wii** fixture tests (the latter skip on public CI).
- In the same local V58 session, **31/31 V57**, **32/32 V56**, **41/41 V55** tests rerun against available fixtures. **140/140 freshly selected offline tests** across V55–V58. Earlier V41–V54 suites were not rerun in this session.
- Public GitHub Actions executes only the 31 asset-free V58 tests. Original `.chunk`, `.BUN`, model, texture, ELF and other game-owned data never enter the public repository.
- We **still do not have** a source-authenticated original Carbon PC stream, the old V42 original/candidate pair, Carbon PC loader/pointer evidence, shader/TPK registration, collision/navigation, or an in-game RedBuilding render. No PC integration result can be claimed.

## Next V59

Run the envelope and V57 paired-root audits on genuine owner-provided Carbon PC streams and candidate roots, separately verify master-index offsets before considering writes, then pursue runtime consumers of spatial tree and preculler records. If the originals remain unavailable, continue read-only, source-backed validation instead of inventing PC compatibility.