"""Synthetic-only native-PC-shaped mesh SUBCHUNK fixture generator.

Builds platform-info, 144-byte mesh records, 16-bit triangle index data,
36-byte XYZ/normal/color/UV vertex chunks and per-mesh material-name chunks.
Tests can validate its bytes with the existing Carbon PC source reader.

Not a complete eSolid, not a working Carbon PC model, and not an asset port.
Unknown retail loader fields/texture packs are NOT synthesized or claimed.
"""
import math
import struct

PC_PLATFORM = 0x00134900
PC_VERTEX = 0x00134b01
PC_MESH = 0x00134b02
PC_INDICES = 0x00134b03
PC_MATERIAL = 0x00134c02
FILLER = b'\x11'*4
MAX_MESHES = 512
MAX_VERTICES_PER_MESH = 65_535
MAX_INDICES = 1_000_000


def _v(v, n, field):
    if len(v) != n or any(not isinstance(x, (float,int)) or not math.isfinite(x) for x in v):
        raise ValueError('Invalid '+field+' float vector')
    return tuple(float(x) for x in v)


def make_pc_chunks(meshes):
    """Create deterministic synthetic PC-shaped child chunks, never full eSolid.

    Each mesh is a dict with: positions, normals, uv, triangles, texture_index,
    material_name (synthetic ASCII). One 36-byte vertex buffer per mesh, which
    makes local 16-bit vertex index interpretation explicit.
    """
    if not isinstance(meshes, (tuple,list)) or not 1 <= len(meshes) <= MAX_MESHES:
        raise ValueError('Invalid number of synthetic meshes')
    mesh_bytes = bytearray()
    index_words = []
    vertex_chunks = []
    material_chunks = []
    index_start = 0
    for mesh in meshes:
        try:
            raw_pos, raw_n, raw_uv, triangles = (mesh[k] for k in ('positions','normals','uv','triangles'))
            texture = mesh['texture_index']
            material_name = mesh['material_name']
        except (KeyError, TypeError):
            raise ValueError('Incomplete synthetic mesh record') from None
        if not isinstance(raw_pos,(tuple,list)) or not 3 <= len(raw_pos) <= MAX_VERTICES_PER_MESH:
            raise ValueError('Invalid synthetic vertex count')
        if len(raw_pos) != len(raw_n) or len(raw_pos) != len(raw_uv):
            raise ValueError('Synthetic vertex/normal/UV counts disagree')
        if type(texture) is not int or not 0 <= texture <= 126:
            raise ValueError('Invalid synthetic texture-table index')
        if (not isinstance(material_name,str) or not material_name or len(material_name)>64 or
                not material_name.isascii() or not all(32 <= ord(c) <= 126 for c in material_name)):
            raise ValueError('Invalid synthetic material name')
        if not isinstance(triangles,(tuple,list)) or not triangles:
            raise ValueError('Missing synthetic triangles')
        positions = [_v(p,3,'position') for p in raw_pos]
        normals = [_v(n,3,'normal') for n in raw_n]
        uv = [_v(t,2,'UV') for t in raw_uv]
        if any(abs(sum(v*v for v in n)-1.0) >= .01 for n in normals):
            raise ValueError('Nonunit synthetic vertex normal')
        packed_indices = []
        for face in triangles:
            if len(face) != 3 or any(type(i) is not int or not 0 <= i < len(positions) for i in face):
                raise ValueError('Out-of-bounds synthetic triangle')
            packed_indices.extend(face)
        if index_start+len(packed_indices) > MAX_INDICES:
            raise ValueError('Too many synthetic triangle indices')
        vertex_bytes = bytearray()
        for xyz, n, st in zip(positions, normals, uv):
            vertex_bytes.extend(struct.pack('<3f3fI2f', *xyz,*n,0xffffffff,*st))
        assert len(vertex_bytes) == 36*len(positions)
        vertex_chunks.append((PC_VERTEX,FILLER+bytes(vertex_bytes)))
        material_chunks.append((PC_MATERIAL,material_name.encode('ascii')+b'\0'))
        rec = bytearray(144)
        bbox = [min(p[k] for p in positions) for k in range(3)] + [max(p[k] for p in positions) for k in range(3)]
        struct.pack_into('<6f',rec,0,*bbox)
        struct.pack_into('<I',rec,0x18,texture*0x01010101)
        struct.pack_into('<I',rec,0x40,len(positions))
        struct.pack_into('<I',rec,0x60,len(triangles))
        struct.pack_into('<I',rec,0x64,index_start)
        struct.pack_into('<I',rec,0x7c,len(packed_indices))
        mesh_bytes.extend(rec)
        index_words.extend(packed_indices)
        index_start += len(packed_indices)
    info = bytearray(FILLER+bytes(52))
    struct.pack_into('<I',info,4+8,0x12)
    struct.pack_into('<I',info,4+16,len(meshes))
    struct.pack_into('<I',info,4+44,len(index_words))
    idx = struct.pack('<'+str(len(index_words))+'H',*index_words)
    idx += bytes((-len(idx))%4)
    # The source parser accepts this ordering and validates mesh/vertex/index
    # counts. A game loader may require additional unknown fields and ordering.
    return ([(PC_PLATFORM,bytes(info)),(PC_MESH,FILLER+bytes(mesh_bytes)),
             (PC_INDICES,FILLER*2+idx)] +
            [part for pair in zip(vertex_chunks,material_chunks) for part in pair])
