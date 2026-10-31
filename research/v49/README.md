# V49: Carbon PC native scenery culling gate (offline, source-only)

**Not a playable port. No game files were modified. No patch writer is included.**

## New reproducible result

The pinned Carbon PC third-party reverse-engineering source (`xoxor4d/nfsc-rtx`, commit `252b44b877c207a9a70914d92c31f116ad92a469`) independently defines a 96-byte runtime `scenery_instance` with a signed `preculler_info_index` at `+0x1C`, a signed `scenery_info_number` at `+0x54`, a 48-byte `tree_node` with ten signed child slots at `+0x1C`, and a 128-byte `preculler_info` visibility bitset. The `scenery_pack` runtime structure has separate spans for instances, tree nodes, and preculler infos. The pinned hook code accesses visibility bits using the instance preculler index. **These are runtime facts from a third-party source, not independently verified serialized chunk mappings or original NFSC.exe disassembly.**

V49 adds a read-only integrated gate that tests three *separate hypotheses* for any supplied original scenery root: 96-byte instance records, 48-byte signed-reference spatial nodes, and 128-byte preculler bitsets. It checks exact instance coverage and descendant AABB unions, nonnegative preculler index ranges, negative index histograms, bitset occupancy, and auxiliary record counts. It does not silently interpret unknown negative indices as valid. If a hypothesis fails, it reports rejection instead of patching data.

The earlier Wii source handoff reports two repeated little/big-endian-independent **numeric** `u32=384` values in the last eight bytes of each populated 128-byte candidate block. Under a *pure bitset* interpretation, the four bit positions are:

- Little-endian encoding of `(384,384)`: **967, 968, 999, 1000** (0-based bit positions within the 128-byte record, LSB-first within each byte).
- Big-endian encoding of `(384,384)`: **976, 991, 1008, 1023**.

This is a **calculation**, not a claim about which visibility sections those bits represent. The previous correlation with the 384-byte tree payload is not sufficient to assign meaning to the footer.

A V42-style append is independently audited: it must preserve the original child order and every original byte, add exactly one 72-byte info, one 96-byte instance and one 32-byte auxiliary row, and point the appended instance at the new info row. The gate then *independently* evaluates the original and candidate trees. In a 2-instance synthetic control, the original tree covers both instances, while the unchanged tree in the 3-instance candidate is correctly rejected for incomplete coverage. The unchanged preculler array is separately flagged. **This is not evidence that the actual V42 Carbon donor uses the same serialized tree.**

## Running (Python standard library only)

```bash
python -m unittest -v test_v49_native_culling.py
python v49_native_culling_gate.py --original /your/authorized/STREAML5RA.BUN --endian little --offset 0x27BAF0C0 --report donor_audit.json
python v49_native_culling_gate.py --original /your/authorized/STREAML5RA.BUN --endian little --offset 0x27BAF0C0 --candidate /your/local/V42_candidate.chunk --report pair_audit.json
python v49_native_culling_gate.py --original /your/authorized/STREAML5RA.BUN --endian little --scan-stream --report pc_scene_census.json
```

Use `--expected-root-sha256` and/or `--expected-file-sha256` to pin source identity when known. Stream scanning uses read-only mmap, but accepts only framed candidates compatible with its parser and is **not guaranteed exhaustive**. A `--limit` makes it explicitly partial. Reports never say `safe_to_install=true`. Output paths identical to inputs are rejected.

## Evidence and verification scope

- **40/40 new asset-free V49 tests passed.** The 215/215 bundled V43–V48 spatial-track regression tests also passed separately, for **255/255 targeted tests**, not a native game-runtime test.
- Ten mounted previous research archives were inspected. No archived file matched the exact supplied original Wii RedBuilding root SHA-256 `cb08ca728a9b76992aaaefe32b450565ef53246f090cfe296f77d96c5d272e7f` or its `0x34107` SHA-256 `438eaa867c378de0d381e4815f45ee453395ab458cf73eb1dcc3985d05992e0b`.
- The original Carbon PC `STREAML5RA.BUN`, original donor at `0x27BAF0C0`, V42 donor/candidate pair, original Wii `LoaderScenery` ELF and `NFSC.exe` were **not available**. No new authentic Carbon PC scene or original Wii `0x34107` content was tested.
- Previous V42 25→26 append, model family hashes and section ID overlap remain earlier **handoff claims**, not revalidated here. Matching section IDs do not establish geographic equivalence.

## Source provenance

- [Pinned Carbon PC structs](https://github.com/xoxor4d/nfsc-rtx/blob/252b44b877c207a9a70914d92c31f116ad92a469/src/comp/game/structs.hpp), Git blob `2ebb2ed91ceeaeef61b55d85aa43b92f7f8ef711`.
- [Pinned runtime preculling hook](https://github.com/xoxor4d/nfsc-rtx/blob/252b44b877c207a9a70914d92c31f116ad92a469/src/comp/comp.cpp), Git blob `2678c85de20d7827287b407e52485139fe837f98`.
- [Pinned vector/matrix definitions](https://github.com/xoxor4d/nfsc-rtx/blob/252b44b877c207a9a70914d92c31f116ad92a469/src/shared/utils/vector.hpp), Git blob `7dcf3b4705205fdb7c68a0e563ffdbc4f50c82b3`.

Only independently authored tools and derived structural facts are packaged, not copied third-party source or game assets.

## Remaining gates

Validate genuine Carbon PC scenery roots, independently identify serialized `0x34105`/`0x34107` mappings, trace Wii and PC loader relocation and streaming registration, verify native material/TPK/shader ownership and collision/navigation, and finally test a safely constructed world in the actual Carbon PC executable. Until then, **offline research only; do not install V42's standalone prototype**.