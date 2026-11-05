# Synthetic-only Carbon PC mesh-subchunk writer: initial round-trip gate

**2026-11-03. Synthetic fixtures only.** This is not an Undercover model converter, an installable patch, a complete eSolid resource, or proof that Carbon PC's runtime loads these bytes. No original game model, texture, vertex, material, index, hash list or executable data is written or published.

## What is implemented

`synthetic_pc_mesh_writer.py` can encode an original **synthetic fixture** supplied as a list of artificial mesh records. Each fixture supplies XYZ positions, unit-length normals, UV pairs, triangle index triplets, an in-range local texture-table index, and a synthetic ASCII material name. The tool returns in-memory native-PC-shaped chunk payloads:

| Source-backed PC child ID | Synthetic content | Scope |
| --- | --- | --- |
| `0x00134900` | Candidate platform info: version 0x12, mesh count, total 16-bit index count | Unknown loader-specific fields deliberately left zero |
| `0x00134B02` | 4-byte marker + 144 bytes per mesh record | Bbox, vertex count, triangle count, contiguous index start/count, local texture index |
| `0x00134B03` | 8-byte marker + 16-bit triangle indices, padded to 4-byte boundary | Indices are local to each mesh's vertex buffer |
| `0x00134B01` | 4-byte marker + synthetic 36-byte vertices | Float XYZ, unit normal, packed color and float UV; one buffer per mesh |
| `0x00134C02` | Synthetic ASCII material-name chunk for each mesh | Not a resolved real texture/material resource |

Unknown complete solid parent/chunk fields, actual material-name and texture-hash link semantics, shader state, and the 52-byte tangent format **are not invented** by the writer. It never writes a file to disk and never opens or mutates source archives. Source inputs are synthetically authored, never imported from a game.

## Validation

The **existing** Carbon PC `pc_native_vertex_control.inspect_pc_solid` parser was run directly over bytes produced by the writer. Synthetic fixtures with one and two independent material groups passed every invariant that parser checks, including:

- 144-byte mesh-record count; native 36-byte vertex length
- Complete contiguous 16-bit triangle-index coverage
- Correct vertex-buffer reset semantics and in-bounds per-mesh indices
- Finite position, normal and UV; unit-length normal
- Exact per-mesh bounding coordinate checks and source-compatible material chunk counts

**13/13 new synthetic-only tests passed locally**, including deterministic output, UV seam preservation, multiple textures/material groups and rejection of missing or malformed normals, UVs, material names, negative texture-table indices, out-of-range triangle indices and empty input.

Both source and test code GitHub blob SHAs were checked against the **exact locally tested files**.

## How to reproduce

From repository root:

```sh
python -m unittest discover -s research/world_bridge \
  -p 'test_synthetic_pc_mesh_writer.py' -v
```

## Relationship to previous source-backed controls

The original-file, read-only `triangle_corner_uv_control.py` finds **114,701/114,701** PS2 face occurrences paired one-to-one against Carbon PC control triangles in sections 141/142 when requiring the same local texture-table hash index and three matching XYZ+periodic UV corners. The writer adds a **synthetic** ability to produce *some* of the PC mesh subchunk structure and prove the existing parser accepts that structure. It **does not** demonstrate converting original Undercover PS2 VIF data into PC chunks, that the native game accepts the chunks, or that a real donor model can be rendered.

## Explicit next gates

1. Confirm normals and face orientation on two independently authenticated Carbon PC/PS2 controls (the existing geometry/UV face bijections are permutation-insensitive).
2. Identify actual Carbon PC material-name/texture-pixel pack dependencies, including donor model hash occurrences with different valid texture tables.
3. Validate the additional complete eSolid and geometry pack wrapper metadata needed by Carbon PC's runtime. Use conservative parsing and only synthetic source-free fixtures before attempting a private original-asset conversion.
4. Once exact source-backed, test a reversible owner-local **single-model** donor resource in the actual Carbon PC runtime. Keep all game files private and unmodified until a controlled, restorable test exists.

No playable world, collision, traffic AI, texture asset conversion or native in-game rendering is claimed.
