# V56: cross-root candidate Wii graph-consistency gate

**Area:** NFS Undercover Wii/PS2 → Carbon PC, Map & World Conversion / Geometry. **Read-only, offline research.** Neither a game patch nor proof of Carbon PC scenery serialization.

## Why we needed a new gate

V55 tests whether a scene *fits* three candidate `0x34107` byte-length relationships. Arithmetic alone cannot determine whether its 96-byte instance entries reference any of the candidate preculler blocks, whether its 48-byte tree actually covers those instances, or whether the tree bounding boxes are internally consistent. A deliberately corrupted synthetic root can satisfy **both** competing length equations even when all its candidate preculler references are out of range or its tree omits instances. V56 separates these cases rather than promoting size equality into format evidence.

## Source-backed RedBuilding findings

Against the independently pinned **8,488-byte original Wii ROOT** (SHA-256 `cb08ca728a9b76992aaaefe32b450565ef53246f090cfe296f77d96c5d272e7f`):

| Field | Source-backed candidate-Wii observation |
|---|---:|
| Root-relative prefix before `0x34103` instances | 4 opaque bytes |
| `0x34102` candidate 72-byte scenery-info rows | 13 |
| `0x34103` 96-byte instance rows | 31 |
| `0x34105` candidate 48-byte spatial tree nodes | 8 |
| Instance coverage from tree node 0 | All 31, exactly once |
| Maximum absolute descendant AABB-union difference | **0.0** |
| `0x34107` candidate 128-byte blocks | 24, all referenced |
| Zero-filled preculler blocks | 1 |
| `0x3410D` candidate 32-byte auxiliary rows | 31 |

The original still satisfies **both** length equations `(31+1) × 96 = 8 × 384 = 3072`. V56's *internal-consistency* finding neither resolves the opaque `0x34107` semantics nor makes it safe to write Carbon PC scenery files.

## New cross-reference checks

- File and ROOT SHA-256 guards, explicit endianness and bounded direct-chunk inventory inherited from V55.
- Root-relative candidate 16-byte instance alignment, finite non-inverted instance AABBs, and in-range candidate scenery-info references.
- Candidate 128-byte preculler references checked against the actual block count; shared blocks are allowed and unreferenced blocks are reported, not automatically forbidden.
- Candidate 48-byte tree child refs checked for missing nodes, cycles and duplicate node visitation; original-instance coverage must be exact-once; every tree-node AABB must equal its descendant instance AABB union (default exact tolerance).
- Candidate 32-byte auxiliary count must agree with candidate instance count; missing info/tree/preculler/auxiliary chunks fail the **Wii candidate** consistency check.
- Root duplicates excluded from unique counts. Unknown/provided platform labels do **not** authenticate new original scenes.
- `carbon_pc_disk_abi_proven`, `safe_to_install` and independent cross-scene claims remain **false**, even for a complete synthetic or source-verified Wii candidate graph.

A failed **candidate Wii** check on a real Carbon PC root does *not* mean the Carbon file is corrupt. Carbon PC's serialized schema is still unverified, and the tool intentionally avoids silently assuming Wii compatibility.

## Run without game assets

```bash
python -m unittest discover -s research/v56 -p test_v56.py -v
```

This runs **26 synthetic tests** and skips six private-original tests. To run all **32** locally, set `NFS_UC_WII_SCENE` to your original, exact SHA-pinned Wii scene ROOT. **Do not commit or redistribute that binary.**

## Read-only local audit

Build a private manifest as documented in [V55](../v55/README_V55.md), then run:

```bash
python research/v56/v56_cross_root_semantic_gate.py \
  --manifest /private/manifest.json \
  --report /private/new-v56-report.json
```

No output overwrite is permitted. Output includes SHA hashes, candidate references/counts and errors but no game bytes, paths or unredacted scene contents. If using a PC BUN with a ROOT offset, both its full-file and extracted ROOT SHA-256 must be known independently. `platform_hint` is a hint, **not authentication**.

## Tests / limitations

- **V56:** 26 synthetic + six pinned original Wii fixture = **32/32**.
- Re-ran prior selected V41, V43–V46, V50, V52–V54 tests: **284/284**; V55: **41/41**; combined V56 set: **357/357 selected offline tests**. This is a selection of current suites, not all historical code or a native game execution.
- V51's dedicated direct V49 fixture check remains a separate unresolved test in the research history and is not counted here.
- No independent second authenticated original Wii scenery sector or source-authenticated Carbon PC ROOT, PC game loader/culling, shader/TPK, world streaming, collision/nav, or in-game rendering confirmed.

**Next V57:** use this gate with an independently sourced second Wii root and original Carbon PC streams. If neither becomes available, investigate the PC loader and keep any proposed write schemas explicitly provisional.