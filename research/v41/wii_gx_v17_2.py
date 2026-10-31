#!/usr/bin/env python3
"""Undercover Wii GX scenery topology & indexed attributes reader (V17.2, experimental).

Reads original Wii STREAML2RA.BUN from an extracted TRACKS ZIP or a raw BUN.
Supports the verified indexed-3-attribute / GX triangle-strip layout only.
No speculative faces or guesses for unsupported models. All geometry stays in
local source coordinates; no placements, textures, collision or map streaming.

V17.2 reads explicit Wii 0x134800 metadata offsets for vertex colors and
texture coordinates instead of assuming the arrays are tightly packed.
UV coordinates are stored as original signed BE int16s. UV fixed-point scale
and texture identity are NOT known: neither is guessed in the sidecar.
"""
from __future__ import annotations
import argparse
import json
import re
import struct
import zipfile
from pathlib import Path

GX_STRIP_OPCODES = range(0x98, 0xA0)  # GX_DRAW_TRIANGLE_STRIP | VAT[0..7]
STREAM_NAME = 'STREAML2RA.BUN'

class UnsupportedGX(ValueError): pass


def subchunks(data: bytes, first: int, end: int, want: int):
    """Yield exact payload locations of an embedded chunk type."""
    pos = first
    while pos + 8 <= end:
        kind, size = struct.unpack_from('<II', data, pos)
        tail = pos + 8 + size
        if tail > end: raise UnsupportedGX('Nested chunk exceeds parent')
        if kind == want:
            yield pos + 8, tail
        if (kind & 0xF0000000) == 0x80000000:
            yield from subchunks(data, pos + 8, tail, want)
        pos = tail
    if pos != end: raise UnsupportedGX('Unparsed nested bytes')


def leading_11(data):
    i = 0
    while i < len(data) and data[i] == 0x11: i += 1
    return i


def read_component(block: bytes, start: int, end: int):
    get = lambda kind: list(subchunks(block, start, end, kind))
    header = get(0x134011)
    meta = get(0x134800)
    binary = get(0x134802)
    if len(header) != 1 or len(meta) != 1 or len(binary) != 1:
        raise UnsupportedGX('Missing/ambiguous Wii GX subchunks')
    head_data = block[header[0][0]:header[0][1]]
    found = re.search(rb'[A-Z][A-Z0-9_]{6,}', head_data)
    name = found.group().decode('ascii') if found else 'UNNAMED'
    header_data = block[meta[0][0]:meta[0][1]]
    binary_data = block[binary[0][0]:binary[0][1]]
    h = leading_11(header_data)
    if header_data[h:h+4] != b'\x00\x16\x00\x00':
        raise UnsupportedGX('Unsupported GX metadata variant')
    if len(header_data) < h + 8:
        raise UnsupportedGX('Truncated GX header')
    strips = int.from_bytes(header_data[h+4:h+6], 'big')
    if len(header_data) < h+28:
        raise UnsupportedGX('Truncated 0x134800 array-offset metadata')
    # Wii metadata values are big-endian byte offsets relative to the first
    # byte AFTER the leading 0x11 padding. Offsets for colors / texcoords
    # include alignment padding after the preceding attribute array.
    payload_len, command_end, last_payload_byte, color_start, uv_start = struct.unpack_from('>IIIII', header_data, h+8)
    if last_payload_byte != payload_len-4:
        raise UnsupportedGX('Unexpected GX metadata length/trailer relationship')
    if command_end > color_start or color_start > uv_start or uv_start > payload_len:
        raise UnsupportedGX('Inconsistent GX attribute offsets')
    if payload_len != len(binary_data)-leading_11(binary_data):
        raise UnsupportedGX('GX metadata payload size disagrees with binary chunk')

    if strips < 1 or strips > 16384:
        raise UnsupportedGX('Invalid strip count')
    pos = leading_11(binary_data)
    primitives = []
    maxpos = maxcol = maxtex = -1
    for si in range(strips):
        if pos + 3 > len(binary_data):
            raise UnsupportedGX('Truncated GX strip header')
        opcode = binary_data[pos]
        vertices = int.from_bytes(binary_data[pos+1:pos+3], 'big')
        if opcode not in GX_STRIP_OPCODES or vertices < 3 or vertices > 512:
            raise UnsupportedGX(f'Unsupported GX primitive 0x{opcode:02x} / {vertices} vertices')
        # Observed layout has three 8-bit indices per draw vertex:
        # (position index, color index, texture-coordinate index).
        record_size = ((3 + vertices*3 + 31) // 32) * 32
        if pos + record_size > len(binary_data):
            raise UnsupportedGX('GX strip overruns data chunk')
        payload = binary_data[pos+3:pos+3+vertices*3]
        padding = binary_data[pos+3+vertices*3:pos+record_size]
        if any(padding):
            raise UnsupportedGX('Unexpected nonzero GX strip padding')
        triad = [tuple(payload[3*i:3*i+3]) for i in range(vertices)]
        maxpos = max(maxpos, *(v[0] for v in triad))
        maxcol = max(maxcol, *(v[1] for v in triad))
        maxtex = max(maxtex, *(v[2] for v in triad))
        primitives.append({'vat': opcode & 7, 'vertices': triad})
        pos += record_size
    npos, ncol, ntex = maxpos+1, maxcol+1, maxtex+1
    base = leading_11(binary_data)
    if pos-base != command_end:
        raise UnsupportedGX('Draw command boundaries disagree with GX metadata')
    colors_off = base + color_start
    uv_off = base + uv_start
    if (pos+npos*6 > colors_off or colors_off+ncol*4 > uv_off or
            uv_off+ntex*4 > base+payload_len or base+payload_len != len(binary_data)):
        raise UnsupportedGX('GX indexed attribute arrays exceed metadata offsets')
    # Position scaling independently checked against Undercover PS2 positions.
    locations = [tuple(c / 256.0 for c in struct.unpack_from('>hhh', binary_data, pos+6*i))
                 for i in range(npos)]
    colors = [tuple(binary_data[colors_off+4*i:colors_off+4*i+4]) for i in range(ncol)]
    uvs_raw = [struct.unpack_from('>hh', binary_data, uv_off+4*i) for i in range(ntex)]
    faces = []
    corner_indices = []
    for primitive in primitives:
        vv = primitive['vertices']
        for i in range(len(vv)-2):
            a,b,c = (vv[i],vv[i+1],vv[i+2]) if i%2 == 0 else (vv[i+1],vv[i],vv[i+2])
            face = (a[0],b[0],c[0])
            if len(set(face)) == 3:
                faces.append(face)
                corner_indices.append((a,b,c))
    return {'name':name, 'positions':locations,'colors':colors,
            'uv_raw':uvs_raw,'faces':faces,'face_corner_indices':corner_indices,
            'strips':strips,
            'draw_vertices':sum(len(p['vertices']) for p in primitives),
            'vat_indexes':sorted(set(p['vat'] for p in primitives)),
            'gx_offsets': {'payload_length':payload_len,'draw_end':command_end,
                           'color_start':color_start,'uv_start':uv_start,
                           'position_alignment_bytes': colors_off-(pos+npos*6),
                           'color_alignment_bytes': uv_off-(colors_off+ncol*4)},
            'bytes_unparsed_trailer':len(binary_data)-(uv_off+ntex*4)}


def read_model(block: bytes, only_component: str|None = None):
    if struct.unpack_from('<I',block,0)[0] != 0x80134000:
        raise ValueError('Expected a 0x80134000 Wii geometry container')
    items = []
    errors = []
    for a,b in subchunks(block,8,len(block),0x80134010):
        # Discover source component name before deciding whether it is wanted
        h = list(subchunks(block,a,b,0x134011))
        label = 'UNNAMED'
        if h:
            m = re.search(rb'[A-Z][A-Z0-9_]{6,}',block[h[0][0]:h[0][1]])
            if m:label=m.group().decode('ascii')
        if only_component and only_component.upper() != label.upper():
            continue
        try: items.append(read_component(block,a,b))
        except UnsupportedGX as exc: errors.append({'component':label,'error':str(exc)})
    return items,errors


def file_stream(path):
    if zipfile.is_zipfile(path):
        archive = zipfile.ZipFile(path)
        matches = [s for s in archive.namelist() if s.split('/')[-1].upper() == STREAM_NAME]
        if len(matches) != 1:
            archive.close()
            raise ValueError(f'Need exactly one {STREAM_NAME} in ZIP')
        return archive, archive.open(matches[0]), archive.getinfo(matches[0]).file_size
    fd = open(path,'rb')
    fd.seek(0,2); size=fd.tell(); fd.seek(0)
    return None,fd,size


def find_model(path, asset='RedBuilding', instance=1, component=None):
    if instance < 1: raise ValueError('Instance must be >= 1')
    archive,stream,total = file_stream(path)
    seen=0; position=0
    try:
        while position+8 <= total:
            header=stream.read(8)
            if len(header)!=8: raise ValueError('Truncated top-level chunk header')
            kind,size=struct.unpack('<II',header)
            if size > total-position-8:
                raise ValueError(f'Invalid chunk size at 0x{position:x}')
            if kind == 0x80134000:
                probe=stream.read(min(256,size))
                if asset.lower().encode() in probe.lower():
                    seen+=1
                    if seen==instance:
                        block=header+probe+stream.read(size-len(probe))
                        models,errors=read_model(block, component)
                        return position,models,errors
                stream.seek(size-len(probe),1)
            else:
                stream.seek(size,1)
            position+=8+size
        raise LookupError(f'Only found {seen} geometry containers matching {asset!r}')
    finally:
        stream.close()
        if archive:archive.close()


def export_obj(models,out):
    target=Path(out)
    target.parent.mkdir(parents=True,exist_ok=True)
    vertex_index=0;total=0
    with target.open('w',encoding='utf8') as f:
        f.write('# NFS Undercover Wii / GX triangle strips; original model-local positions.\n')
        f.write('# Wii signed BE int16 positions /256; strip parity preserved.\n')
        for model in models:
            f.write('\no '+model['name']+'\n')
            for vert in model['positions']:f.write('v %.7f %.7f %.7f\n'%vert)
            for face in model['faces']:
                f.write('f %d %d %d\n'%tuple(vertex_index+i+1 for i in face))
            vertex_index+=len(model['positions']);total+=len(model['faces'])
    return {'path':str(target),'vertices':vertex_index,'faces':total}


def export_glb(models,out):
    try: import trimesh
    except ImportError as exc:
        raise RuntimeError('Optional GLB export requires pip install trimesh') from exc
    sc=trimesh.Scene()
    for index,model in enumerate(models):
        if model['faces']:
            # Wii positions are Z-up, glTF expects Y-up. This positive-determinant
            # rotation makes the imported mesh upright in Blender (also Z-up).
            verts=[(x,z,-y) for x,y,z in model['positions']]
            mesh=trimesh.Trimesh(vertices=verts,faces=model['faces'],process=False)
            sc.add_geometry(mesh, geom_name=f"{index}_{model['name']}")
    Path(out).parent.mkdir(parents=True,exist_ok=True)
    sc.export(str(out))


def export_indexed_attributes_json(models, out):
    """Lossless for recovered indexed source attributes; no UV normalization."""
    result={'version':'17.2',
       'disclaimer':'Original GX color bytes and signed-int16 UV table. Per-corner indexes are (position,color,uv). UV fixed-point scale, material assignment, and texture identity have not been verified.',
       'components':[{k:m[k] for k in (
         'name','positions','colors','uv_raw','faces','face_corner_indices',
         'gx_offsets','vat_indexes','bytes_unparsed_trailer')} for m in models]}
    path=Path(out);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    return str(path)


def export_color_preview_glb(models, out):
    """Experimental glTF COLOR_0 preview. No material/texture claim."""
    try:
        import numpy as np
        import trimesh
    except ImportError as exc:
        raise RuntimeError('Color preview GLB requires numpy + trimesh') from exc
    sc=trimesh.Scene()
    for num,m in enumerate(models):
        vert=[];rgba=[];faces=[]
        for corners in m['face_corner_indices']:
            base=len(vert)
            for pi,ci,ti in corners:
                x,y,z=m['positions'][pi]
                vert.append((x,z,-y))
                rgba.append(m['colors'][ci])
            faces.append((base,base+1,base+2))
        mesh=trimesh.Trimesh(vertices=np.asarray(vert,dtype=float),faces=np.asarray(faces,dtype=np.int64),process=False)
        mesh.visual.vertex_colors=np.asarray(rgba,dtype=np.uint8)
        sc.add_geometry(mesh,geom_name=f'{num}_{m["name"]}')
    Path(out).parent.mkdir(parents=True,exist_ok=True)
    sc.export(str(out))


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('source',type=Path,help='ExtractedTRACKS wii.zip or raw STREAML2RA.BUN')
    ap.add_argument('--asset',default='RedBuilding')
    ap.add_argument('--instance',type=int,default=1)
    ap.add_argument('--component',help='Optional exact source component name')
    ap.add_argument('--obj',type=Path,default=Path('wii_gx_model.obj'))
    ap.add_argument('--glb',type=Path,default=None)
    ap.add_argument('--attributes-json',type=Path,default=None)
    ap.add_argument('--color-preview-glb',type=Path,default=None)
    ap.add_argument('--report',type=Path,default=Path('wii_gx_model_report.json'))
    a=ap.parse_args()
    offset,models,errors=find_model(a.source,a.asset,a.instance,a.component)
    out=export_obj(models,a.obj) if models else None
    if models and a.glb:export_glb(models,a.glb)
    if models and a.attributes_json:export_indexed_attributes_json(models,a.attributes_json)
    if models and a.color_preview_glb:export_color_preview_glb(models,a.color_preview_glb)
    report={'version':'17.2','source_offset':offset,'asset':a.asset,
      'instance':a.instance,'component_filter':a.component,
      'decoded_components':[{'name':m['name'],'vertices':len(m['positions']),
         'faces':len(m['faces']),'strips':m['strips'],
         'draw_vertices':m['draw_vertices'],'vat_indexes':m['vat_indexes'],
         'bytes_unparsed_trailer':m['bytes_unparsed_trailer']} for m in models],
      'skipped_components':errors,'obj':out,
      'attribute_index_counts':[{'name':m['name'],'colors':len(m['colors']),
             'uv':len(m['uv_raw']),'gx_offsets':m['gx_offsets']} for m in models],
      'warning':'Validates only one Wii GX data variant. UV fixed-point scale, texture assignment and material settings are unverified.'}
    a.report.parent.mkdir(parents=True,exist_ok=True)
    a.report.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
    if not models:raise SystemExit(2)

if __name__=='__main__':main()
