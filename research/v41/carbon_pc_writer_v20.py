#!/usr/bin/env python3
"""Conservative size-preserving editor for verified Carbon PC 0x80134000 scenery.

This is a BINARY EDITOR, not yet a level compiler: material counts, stream
layout, collision, geometry bounds, placements and object identity are kept.
Unknown bytes are left intact, including unknown fields of 52-byte vertices.
Edits are rejected unless V19's strict parser can read the component both
before and after, with no modifications outside explicitly permitted bytes.
"""
from __future__ import annotations
import argparse,hashlib,json,math,os,shutil,struct,tempfile
from pathlib import Path
from carbon_pc_scenery_v19 import GEOM,read_model,parse_component,UnsupportedPC
from wii_gx_v17_2 import subchunks

class UnsafeRewrite(ValueError):pass


def locate(block:bytes,name:str):
    if len(block)<8 or struct.unpack_from('<II',block) != (GEOM,len(block)-8):
        raise UnsafeRewrite('Expected one intact Carbon PC 0x80134000 chunk')
    found=[]
    for a,b in subchunks(block,8,len(block),0x80134010):
        try:m=parse_component(block,a,b)
        except (UnsupportedPC,struct.error):continue
        if m['name']==name:found.append((a,b,m))
    if len(found)!=1:
        raise UnsafeRewrite(f'Expected one decodable component named {name}, found {len(found)}')
    return found[0]


def _float3(values,label):
    if not isinstance(values,list) or len(values)!=3 or any(type(v) not in (float,int) or not math.isfinite(v) or abs(v)>1e6 for v in values):
        raise UnsafeRewrite(f'{label} must be 3 finite numbers')
    return tuple(float(v) for v in values)


def _float2(values,label):
    if not isinstance(values,list) or len(values)!=2 or any(type(v) not in (float,int) or not math.isfinite(v) or abs(v)>1e6 for v in values):
        raise UnsafeRewrite(f'{label} must be 2 finite numbers')
    return tuple(float(v) for v in values)


def _indices(edits,count,label):
    if not isinstance(edits,dict):raise UnsafeRewrite(f'{label} edits must be an object')
    pairs=[]
    for k,v in edits.items():
        if type(k)!=str or not k.isdecimal() or str(int(k))!=k or not 0<=int(k)<count:
            raise UnsafeRewrite(f'Invalid {label} index {k!r}')
        pairs.append((int(k),v))
    return sorted(pairs)


def rewrite(block:bytes,name:str,edits:dict|None=None,allow_outside_bounds=False):
    """Return (new bytes, diagnostic report). No-op returns byte-identical data."""
    edits=edits or {}
    if not isinstance(edits,dict) or set(edits)-{'vertices','triangles'}:
        raise UnsafeRewrite('Only vertices and triangles edit objects are supported')
    a,b,model=locate(block,name)
    before=hashlib.sha256(block).hexdigest()
    vmap=[]
    # Map global vertex index to exact 0x134b01 record offset.
    vranges=list(subchunks(block,a,b,0x134b01))
    if len(vranges)!=len(model['vertex_buffers']):raise UnsafeRewrite('Vertex buffer count changed')
    for (start,end),group in zip(vranges,model['vertex_buffers']):
        stride=group['stride']; pad=group['padding']
        if end-start!=pad+stride*group['vertices']:raise UnsafeRewrite('Vertex range mismatch')
        vmap.extend(start+pad+i*stride for i in range(group['vertices']))
    if len(vmap)!=len(model['positions']):raise UnsafeRewrite('Vertex count mismatch')
    ixrange=list(subchunks(block,a,b,0x134b03))
    if len(ixrange)!=1:raise UnsafeRewrite('Cannot identify unique index buffer')
    ixbase=ixrange[0][0]+model['index_padding']
    if ixbase+6*len(model['faces']) > ixrange[0][1]:raise UnsafeRewrite('Index capacity exceeded')
    xmin=[min(v[j] for v in model['positions']) for j in range(3)]
    xmax=[max(v[j] for v in model['positions']) for j in range(3)]
    mutable=bytearray(block);modified=set();vcount=0;tcount=0
    def write_bytes(off,raw):
        for i,x in enumerate(raw):
            if mutable[off+i]!=x:
                mutable[off+i]=x;modified.add(off+i)
    for ix,update in _indices(edits.get('vertices',{}),len(vmap),'vertex'):
        if not isinstance(update,dict) or not update or set(update)-{'position','normal','color','uv'}:
            raise UnsafeRewrite(f'Invalid vertex edit at {ix}')
        off=vmap[ix]
        for key,values in update.items():
            if key in ('position','normal'):
                xyz=_float3(values,key)
                if key=='position' and not allow_outside_bounds and any(v < lo-1e-6 or v>hi+1e-6 for v,lo,hi in zip(xyz,xmin,xmax)):
                    raise UnsafeRewrite(f'Position {ix} outside original component AABB: {xyz}')
                write_bytes(off+(0 if key=='position' else 12),struct.pack('<3f',*xyz))
            elif key=='uv':write_bytes(off+28,struct.pack('<2f',*_float2(values,key)))
            elif key=='color':
                if not isinstance(values,list) or len(values)!=4 or any(type(v)!=int or not 0<=v<=255 for v in values):
                    raise UnsafeRewrite('RGBA must be four uint8 values')
                write_bytes(off+24,bytes(values))
        vcount+=1
    for face_ix,tri in _indices(edits.get('triangles',{}),len(model['faces']),'triangle'):
        if not isinstance(tri,list) or len(tri)!=3 or any(type(v)!=int or v<0 or v>=len(vmap) for v in tri) or len(set(tri))!=3:
            raise UnsafeRewrite(f'Triangle {face_ix} must have 3 distinct valid vertex indices')
        mid=model['triangle_material'][face_ix];mat=model['materials'][mid]
        vstart=mat['vertex_offset_global'];vend=vstart+mat['vertices']
        if any(v<vstart or v>=vend for v in tri):
            raise UnsafeRewrite(f'Triangle {face_ix} crosses native material vertex boundaries')
        # Indices are relative to the 0x134b01 vertex buffer, not component global.
        group=model['vertex_buffers'][mat['vertex_buffer']]
        buffer_start=mat['vertex_offset_global']-mat['vertex_offset_in_buffer']
        local=[v-buffer_start for v in tri]
        if any(v>65535 for v in local):raise UnsafeRewrite('Native 16-bit index overflow')
        write_bytes(ixbase+face_ix*6,struct.pack('<3H',*local))
        tcount+=1
    result=bytes(mutable)
    aa,bb,after_model=locate(result,name)
    if (aa,bb)!=(a,b) or len(after_model['positions'])!=len(model['positions']) or len(after_model['faces'])!=len(model['faces']):
        raise UnsafeRewrite('Post-edit component layout differs')
    # Validate every unchanged object/field, not only edited fields.
    expected_vertices=[tuple(v) for v in model['positions']]
    expected_normals=[tuple(v) for v in model['normals']]
    expected_uv=[tuple(v) for v in model['uv']]
    expected_colors=[tuple(v) for v in model['colors']]
    expected_faces=list(model['faces'])
    for ix,u in _indices(edits.get('vertices',{}),len(vmap),'vertex'):
        for field,target in [('position',expected_vertices),('normal',expected_normals),('uv',expected_uv),('color',expected_colors)]:
            if field in u:
                if field=='color':target[ix]=tuple(u[field])
                else:target[ix]=tuple(struct.unpack('<'+('2f' if field=='uv' else '3f'),struct.pack('<'+('2f' if field=='uv' else '3f'),*u[field])))
    for ix,tri in _indices(edits.get('triangles',{}),len(model['faces']),'triangle'):
        expected_faces[ix]=tuple(tri)
    if (after_model['positions']!=expected_vertices or after_model['normals']!=expected_normals or
        after_model['uv']!=expected_uv or after_model['colors']!=expected_colors or
        after_model['faces']!=expected_faces or after_model['triangle_material']!=model['triangle_material'] or
        after_model['materials']!=model['materials']):
        raise UnsafeRewrite('Strict source-to-destination reparse mismatch')
    actual={i for i,(x,y) in enumerate(zip(block,result)) if x!=y}
    if len(result)!=len(block) or actual!=modified:raise UnsafeRewrite('Unexpected byte changes')
    report={'component':name,'size_preserved':len(result),'total_component_vertices':len(vmap),
        'total_component_triangles':len(model['faces']),'requested_vertex_edits':vcount,
        'requested_triangle_edits':tcount,'bytes_changed':len(modified),
        'sha256_before':before,'sha256_after':hashlib.sha256(result).hexdigest(),
        'outside_edited_fields_unchanged':True,'outside_original_aabb_allowed':allow_outside_bounds,
        'collision_placements_streaming_metadata':'NOT MODIFIED','in_game_test':'NOT PERFORMED'}
    return result,report


def rewrite_stream(src:Path,dst:Path,chunk_offset:int,component:str,edits:dict,allow_outside_bounds=False):
    if src.resolve()==dst.resolve():raise UnsafeRewrite('Refusing to overwrite source stream')
    if chunk_offset<0 or chunk_offset%4:raise UnsafeRewrite('Chunk offset must be nonnegative, 4-byte aligned')
    with src.open('rb') as f:
        f.seek(0,os.SEEK_END);total=f.tell()
        if chunk_offset+8>total:raise UnsafeRewrite('Offset outside source stream')
        f.seek(chunk_offset);typ,length=struct.unpack('<II',f.read(8))
        if typ!=GEOM or chunk_offset+8+length>total:raise UnsafeRewrite('Offset does not identify a complete geometry chunk')
        f.seek(chunk_offset);source=f.read(8+length)
    new,report=rewrite(source,component,edits,allow_outside_bounds)
    # Prefer copying original into a separate output, then replace exactly one chunk.
    shutil.copyfile(src,dst)
    with dst.open('r+b') as f:
        f.seek(chunk_offset);f.write(new)
    report['source_stream_size']=total;report['edited_chunk_offset']=chunk_offset
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('source');p.add_argument('component');p.add_argument('--edit-json')
    p.add_argument('--output');p.add_argument('--report');p.add_argument('--stream-offset',type=lambda s:int(s,0))
    p.add_argument('--allow-outside-bounds',action='store_true')
    a=p.parse_args()
    source=Path(a.source);edits=json.loads(Path(a.edit_json).read_text()) if a.edit_json else {}
    if a.output:
        dest=Path(a.output)
        if dest.resolve()==source.resolve():raise SystemExit('Output cannot overwrite source')
    if a.stream_offset is not None:
        if not a.output:raise SystemExit('Stream editing requires --output')
        report=rewrite_stream(source,dest,a.stream_offset,a.component,edits,a.allow_outside_bounds)
    else:
        out,report=rewrite(source.read_bytes(),a.component,edits,a.allow_outside_bounds)
        if a.output:dest.write_bytes(out)
    if a.report:Path(a.report).write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
