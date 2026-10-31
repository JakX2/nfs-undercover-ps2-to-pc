#!/usr/bin/env python3
"""Verified native Carbon PC scenery bounds reader and bounded field writer.

Carbon PC material 0x134B02: AABB min XYZ at +0x00, max XYZ +0x0C,
144-byte records. Component 0x134011: locate 0x0016 marker and variant
0000/0040/0080, min XYZ at marker+0x14, max at marker+0x24; each
three-float record is followed by an untouched 32-bit field.

V21 deliberately touches ONLY these 48 bytes per edited component (24 header
plus 24 per material); updates no object identity, placements, transforms,
texture bindings, stream tables, collision, or other unknown metadata.
It is an *offline* writer. Do not install prototypes in Carbon PC.
"""
from __future__ import annotations
import argparse, hashlib, json, math, struct
from pathlib import Path
from carbon_pc_writer_v20 import locate, UnsafeRewrite
from carbon_pc_scenery_v19 import parse_component
from wii_gx_v17_2 import subchunks

MARKERS = (b'\x16\x00\x00\x00', b'\x16\x00\x40\x00', b'\x16\x00\x80\x00')
MARGIN = 0.01


def _spans(block, comp_start, comp_end, model):
    mats=list(subchunks(block,comp_start,comp_end,0x134b02))
    heads=list(subchunks(block,comp_start,comp_end,0x134011))
    if len(mats)!=1 or len(heads)!=1:
        raise UnsafeRewrite('Ambiguous bounds-bearing chunks')
    ma,mz=mats[0];ha,hz=heads[0]
    if mz-ma!=model['material_padding']+144*len(model['materials']):
        raise UnsafeRewrite('Unexpected material buffer length')
    head=block[ha:hz]
    # The 0x16 marker may also appear in an adjacent 32-bit field. Three
    # original PC components contain *two* literal 0x16 markers. Only the
    # actual header has the observed zeroed reserved word at marker+0x10.
    # Never pick the first occurrence blindly or infer a field from its name.
    found=[]
    for variant in MARKERS:
        cursor=0
        while True:
            q=head.find(variant,cursor)
            if q<0:break
            if q+0x30<=len(head) and head[q+0x10:q+0x14]==b'\x00'*4:
                found.append((q,variant))
            cursor=q+1
    if len(found)!=1:
        raise UnsafeRewrite('No unique verified 0x134011 header marker')
    q,variant=found[0]
    return (ha,q,variant,ma+model['material_padding'])


def _get_box(raw,offset):
    out=(struct.unpack_from('<3f',raw,offset),struct.unpack_from('<3f',raw,offset+12))
    if not all(math.isfinite(v) for part in out for v in part) or any(x>y for x,y in zip(*out)):
        raise UnsafeRewrite('Invalid source AABB')
    return out


def _box(positions):
    if not positions:raise UnsafeRewrite('Empty vertex run')
    if any(not all(math.isfinite(x) for x in p) for p in positions):
        raise UnsafeRewrite('Nonfinite vertex')
    lo=tuple(min(p[k] for p in positions) for k in range(3))
    hi=tuple(max(p[k] for p in positions) for k in range(3))
    return lo,hi


def _enclosed(box,points,epsilon=3e-6):
    lo,hi=box
    return all(lo[k]-epsilon<=v[k]<=hi[k]+epsilon for v in points for k in range(3))


def _margin_valid(bounds,points,tol=4e-6):
    mn,mx=_box(points)
    lo,hi=bounds
    return all(abs((mn[k]-lo[k])-MARGIN)<=tol and abs((hi[k]-mx[k])-MARGIN)<=tol for k in range(3))


def inspect(block,name):
    a,b,m=locate(block,name)
    ha,q,var,ma=_spans(block,a,b,m)
    materials=[]
    for j,mat in enumerate(m['materials']):
        lo,hi=_get_box(block,ma+j*144)
        st=mat['vertex_offset_global']; v=m['positions'][st:st+mat['vertices']]
        materials.append({'id':j,'vertex_count':len(v),'min':lo,'max':hi,
                          'encloses_vertices':_enclosed((lo,hi),v),
                          'vertex_extrema_plus_0_01':_margin_valid((lo,hi),v)})
    hlow,hhi=(struct.unpack_from('<3f',block,ha+q+0x14),
               struct.unpack_from('<3f',block,ha+q+0x24))
    if not all(math.isfinite(x) for x in hlow+hhi):raise UnsafeRewrite('Bad header bounds')
    ul=tuple(min(s['min'][k] for s in materials) for k in range(3))
    uh=tuple(max(s['max'][k] for s in materials) for k in range(3))
    return {'name':name,'variant':var.hex(),'header_offset':ha+q,
            'header_min':hlow,'header_max':hhi,
            'header_equals_material_union':(hlow,hhi)==(ul,uh),
            'header_encloses_vertices':_enclosed((hlow,hhi),m['positions']),
            'header_vertex_extrema_plus_0_01':_margin_valid((hlow,hhi),m['positions']),
            'materials':materials,'component_vertices':len(m['positions']),
            'component_triangles':len(m['faces'])}


def rebuild(block,name,allow_invalid_source=False):
    """Recompute only source-validated header/material AABBs. No-op is exact.

    Uses the *already decoded* V19 vertices, not estimates or transform guesses.
    Will refuse inconsistent source bounds unless allow_invalid_source=True,
    intended ONLY to repair an explicitly experimental offline transplant.
    """
    original=inspect(block,name)
    if not allow_invalid_source and (not original['header_equals_material_union'] or
        not original['header_vertex_extrema_plus_0_01'] or
        not all(s['vertex_extrema_plus_0_01'] for s in original['materials'])):
        raise UnsafeRewrite('Source AABB does not follow source-verified Carbon rule')
    if original['header_vertex_extrema_plus_0_01'] and all(
        s['vertex_extrema_plus_0_01'] for s in original['materials']) and original['header_equals_material_union']:
        return block,{'name':name,'bytes_changed':0,'no_op':True,
                      'source_bounds_valid':True,'offline_only':True}
    a,b,m=locate(block,name)
    ha,q,var,ma=_spans(block,a,b,m)
    raw=bytearray(block); allowed=set()
    union_lo=[float('inf')]*3;union_hi=[float('-inf')]*3
    def write(offset,values):
        payload=struct.pack('<3f',*values)
        for i,v in enumerate(payload):
            raw[offset+i]=v;allowed.add(offset+i)
    for j,mat in enumerate(m['materials']):
        st=mat['vertex_offset_global']; v=m['positions'][st:st+mat['vertices']]
        mn,mx=_box(v)
        lo=tuple(x-MARGIN for x in mn);hi=tuple(x+MARGIN for x in mx)
        write(ma+144*j,lo);write(ma+144*j+12,hi)
        stored_lo=struct.unpack_from('<3f',raw,ma+144*j)
        stored_hi=struct.unpack_from('<3f',raw,ma+144*j+12)
        for k in range(3):
            union_lo[k]=min(union_lo[k],stored_lo[k]);union_hi[k]=max(union_hi[k],stored_hi[k])
    write(ha+q+0x14,union_lo);write(ha+q+0x24,union_hi)
    output=bytes(raw)
    changed={i for i,(x,y) in enumerate(zip(block,output)) if x!=y}
    if len(block)!=len(output) or not changed<=allowed:
        raise UnsafeRewrite('Rewriter modified non-AABB bytes')
    new=inspect(output,name)
    if (not new['header_equals_material_union'] or
        not new['header_vertex_extrema_plus_0_01'] or
        not all(s['vertex_extrema_plus_0_01'] for s in new['materials'])):
        raise UnsafeRewrite('Rebuilt bounds do not reproduce Carbon PC pattern')
    # All other objects unchanged byte-for-byte because this is size-preserving.
    # Also independently confirm geometry, normals, color, UV, index, material
    # non-bounding fields unchanged via V19 decoding.
    aa,bb,md=locate(output,name)
    if (aa,bb)!=(a,b) or md['positions']!=m['positions'] or md['faces']!=m['faces'] or md['uv']!=m['uv'] or md['normals']!=m['normals'] or md['colors']!=m['colors']:
        raise UnsafeRewrite('Non-bounds decoded data changed')
    return output,{'name':name,'bytes_changed':len(changed),
        'source_bounds_valid':original['header_vertex_extrema_plus_0_01'],
        'destination_bounds_valid':True,'header_matches_material_union':True,
        'changed_only_bounding_fields':True,'byte_length':len(output),
        'before_sha256':hashlib.sha256(block).hexdigest(),
        'after_sha256':hashlib.sha256(output).hexdigest(),
        'offline_only':True,
        'not_rewritten':['texture/shader bindings','transform','placements','collision','navigation','stream dependencies']}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('source');p.add_argument('component');p.add_argument('--output');p.add_argument('--report')
    p.add_argument('--allow-invalid-source',action='store_true',help='ONLY for offline experimental prototypes')
    args=p.parse_args()
    src=Path(args.source).read_bytes()
    data,rep=rebuild(src,args.component,args.allow_invalid_source)
    if args.output:
        dest=Path(args.output)
        if dest.resolve()==Path(args.source).resolve():raise SystemExit('Cannot overwrite source!')
        dest.write_bytes(data)
    if args.report:Path(args.report).write_text(json.dumps(rep,indent=2)+'\n')
    print(json.dumps(rep,indent=2))
if __name__=='__main__':main()
