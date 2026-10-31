#!/usr/bin/env python3
"""Experimental UC Wii -> Carbon PC mesh-byte-format *prototype*.

Replaces ONE single-material, 36-byte-format Carbon PC scenery component
inside a private reference geometry container. Rebuilds chunk sizes and
material vertex/index counters. Does NOT make a playable Carbon map:
not updated: bounds, transforms, texture hashes, collision, navigation,
instancing or streaming tables; host scenery name/material remain intact.
Use only as offline geometry-format research, never inject into a live game.
"""
from __future__ import annotations
import argparse,collections,json,math,struct
from pathlib import Path
from carbon_pc_scenery_v19 import read_model,parse_component,GEOM
from carbon_pc_writer_v20 import locate,UnsafeRewrite
from wii_gx_v17_2 import subchunks,read_model as uc_wii_read


def wii_to_pc_buffers(source):
    # Keyed by original Wii GX position/color/UV *corner* indices. The PC's
    # float vertex format needs duplicated positions for UV/color seams.
    tuples={};corners=[]
    for tri in source['face_corner_indices']:
        f=[]
        for corner in tri:
            if corner not in tuples:tuples[corner]=len(tuples)
            f.append(tuples[corner])
        if len(set(f))!=3:raise UnsafeRewrite('Wii draw face degenerates at indexed corners')
        corners.append(tuple(f))
    if len(tuples)>65535:raise UnsafeRewrite('Too many unique Wii corner vertices')
    v=[None]*len(tuples)
    for (pos,col,tex),i in tuples.items():
        xyz=source['positions'][pos]
        rgba=source['colors'][col]
        uv=source['uv_raw'][tex]
        v[i]=(xyz,rgba,(uv[0]/2048,uv[1]/2048))
    # Approximate per-vertex normals by averaging adjacent source-face
    # cross-products. These are deliberately NOT claimed to be source normals.
    n=[[0.,0.,0.] for _ in v]
    for a,b,c in corners:
        p,q,r=(v[i][0] for i in (a,b,c))
        e=[q[j]-p[j] for j in range(3)];f=[r[j]-p[j] for j in range(3)]
        cross=(e[1]*f[2]-e[2]*f[1],e[2]*f[0]-e[0]*f[2],e[0]*f[1]-e[1]*f[0])
        for i in (a,b,c):
            for j in range(3):n[i][j]+=cross[j]
    blob=bytearray()
    for i,(xyz,color,uv) in enumerate(v):
        mag=math.sqrt(sum(k*k for k in n[i]))
        normal=tuple(k/mag for k in n[i]) if mag>1e-12 else (0.,0.,1.)
        blob+=struct.pack('<3f3f4B2f',*xyz,*normal,*color,*uv)
    indexes=b''.join(struct.pack('<3H',*tri) for tri in corners)
    return bytes(blob),indexes,len(v),len(corners)


def _chunks_replace(source,component_start,replacements):
    # Preserve all unrelated chunks and their raw payload bytes. Recalculate
    # each parent chunk's size field on every changed nesting level.
    def parse_slice(begin,end,active=False):
        parts=[];cursor=begin
        while cursor<end:
            if cursor+8>end:raise UnsafeRewrite('Misaligned nested chunk boundary')
            kind,size=struct.unpack_from('<II',source,cursor)
            tail=cursor+8+size
            if tail>end:raise UnsafeRewrite('Bad nested size')
            current=active or kind==0x80134010 and cursor+8==component_start
            if current and kind in replacements:
                if kind & 0x80000000:raise UnsafeRewrite('Cannot replace container directly')
                payload=replacements[kind]
            elif kind & 0xf0000000==0x80000000:
                payload=parse_slice(cursor+8,tail,current)
            else:payload=source[cursor+8:tail]
            if len(payload)>0xffffffff:raise UnsafeRewrite('Chunk too large')
            parts.append(struct.pack('<II',kind,len(payload))+payload)
            cursor=tail
        return b''.join(parts)
    data=parse_slice(8,len(source))
    return struct.pack('<II',GEOM,len(data))+data


def transplant(carbon_block:bytes,donor:str,undercover_block:bytes,source_name='XBU_REDBUILDING_1B_00'):
    source_models,source_errors=uc_wii_read(undercover_block,source_name)
    if source_errors or len(source_models)!=1:raise UnsafeRewrite('Undercover Wii source not uniquely decoded')
    src=source_models[0]
    a,b,dst=locate(carbon_block,donor)
    if len(dst['materials'])!=1 or dst['materials'][0]['stride']!=36 or len(dst['vertex_buffers'])!=1:
        raise UnsafeRewrite('PC donor must have exactly one 36-byte material/buffer')
    vbytes,ibytes,nverts,nfaces=wii_to_pc_buffers(src)
    # Keep original format flag, shader record, object name and unknown fields.
    mats=list(subchunks(carbon_block,a,b,0x134b02))
    if len(mats)!=1:raise UnsafeRewrite('Material span ambiguous')
    pad=dst['material_padding']
    original=carbon_block[slice(*mats[0])]
    rec=bytearray(original[pad:])
    if len(rec)!=144:raise UnsafeRewrite('Material entry is not exactly 144 bytes')
    struct.pack_into('<I',rec,0x40,nverts)
    struct.pack_into('<I',rec,0x60,nfaces)
    struct.pack_into('<I',rec,0x64,0)
    struct.pack_into('<I',rec,0x7c,3*nfaces)
    vpad=(-len(vbytes))%16
    # Existing strict V19 parser recognizes 0x11 leading vertex padding;
    # 16-byte-aligned total is a convention of known native samples.
    if vpad%4:raise UnsafeRewrite('Non-word-aligned vertex payload')
    ixpad=8
    native=_chunks_replace(carbon_block,a,{
        0x134b02: original[:pad]+bytes(rec),
        0x134b03: b'\x11'*ixpad+ibytes,
        0x134b01: b'\x11'*vpad+vbytes,
    })
    models,errs=read_model(native,donor)
    if errs or len(models)!=1:raise UnsafeRewrite(f'Converted prototype not parseable: {errs}')
    m=models[0]
    if len(m['positions'])!=nverts or len(m['faces'])!=nfaces:
        raise UnsafeRewrite('PC reparse counts disagree')
    # Verify topology is preserved, not just count or vertex coordinates.
    pc_verts=m['positions']
    src_faces=src['faces']
    # Source indices can contain equal XYZ coordinates at distinct GX slots;
    # compare the per-triangle positions directly rather than nearest-index IDs.
    src_face_xyz=[tuple(src['positions'][idx] for idx in face) for face in src_faces]
    pc_face_xyz=[tuple(pc_verts[idx] for idx in face) for face in m['faces']]
    if len(pc_face_xyz)!=len(src_face_xyz) or any(
        any(max(abs(x-y) for x,y in zip(v,w))>0.00001 for v,w in zip(pa,pb))
        for pa,pb in zip(pc_face_xyz,src_face_xyz)):
        raise UnsafeRewrite('Wii -> PC per-corner topology/coordinates mismatch')
    # Parse full reference file. All other PC components must remain identical
    # in decoded geometry, and their bytes are preserved by the chunk rewriter.
    before_models,before_err=read_model(carbon_block)
    after_models,after_err=read_model(native)
    if before_err or after_err or len(before_models)!=len(after_models):
        raise UnsafeRewrite('Neighbour components failed to decode')
    for x,y in zip(before_models,after_models):
        if x['name']!=donor and x!=y:raise UnsafeRewrite('Neighbour PC component changed')
    return native,{'source':src['name'],'pc_carrier':donor,'positions_in_wii':len(src['positions']),
        'original_wii_triangles':len(src['faces']),'pc_vertex_records':nverts,
        'pc_triangles':nfaces,'native_v19_readback':'PASS',
        'source_triangle_winding':'PRESERVED','uv_divisor':2048,
        'normal_method':'approximate area-weighted triangle normals',
        'source_file_bytes':len(carbon_block),'proof_file_bytes':len(native),
        'limitations':['Donor material/texture metadata not converted',
        'Source bounding box not rebuilt', 'No collision, navigation, placement or world streaming changes',
        'Not safe to put into Carbon PC TRACKS yet']}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('carbon_pc_chunk');p.add_argument('donor');p.add_argument('wii_redbuilding_chunk');p.add_argument('output');p.add_argument('--report');args=p.parse_args()
    src=Path(args.carbon_pc_chunk).read_bytes();uc=Path(args.wii_redbuilding_chunk).read_bytes()
    native,rep=transplant(src,args.donor,uc)
    Path(args.output).write_bytes(native)
    if args.report:Path(args.report).write_text(json.dumps(rep,indent=2)+'\n')
    print(json.dumps(rep,indent=2))
