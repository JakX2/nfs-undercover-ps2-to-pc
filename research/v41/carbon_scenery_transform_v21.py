#!/usr/bin/env python3
"""Read Carbon/Undercover shared 0x134011 local bounds and affine matrix.

The 16 little-endian floats at marker+0x34 form a row-major, row-vector
4x4 matrix. Last row holds translation. For 65 named Carbon Wii/PC objects,
all 64 matrix bytes match; 65 Wii/PS2 also match in the reference set.

An *offline-only* guarded matrix transplant is provided to carry the Wii
RedBuilding's source transform into the existing V21 PC mesh-format sample.
This does NOT fix world-sector placement, collision, navigation or runtime
references. Never install the sample into a game stream.
"""
from __future__ import annotations
import argparse, hashlib, itertools, json, math, re, struct
from pathlib import Path
from wii_gx_v17_2 import subchunks
from carbon_pc_writer_v20 import locate, UnsafeRewrite
from carbon_pc_bounds_v21 import inspect

MARKERS=(b'\x16\x00\x00\x00',b'\x16\x00\x40\x00',b'\x16\x00\x80\x00')
HEAD=0x134011
COMP=0x80134010
GEOM=0x80134000
NAME=re.compile(rb'[A-Z][A-Z0-9_]{6,}')


def _valid_matrix(m, tol=1e-3):
    if len(m)!=16 or not all(math.isfinite(v) and abs(v)<1e7 for v in m):return False
    if any(abs(m[i])>tol for i in (3,7,11)) or abs(m[15]-1)>tol:return False
    # All 198 Carbon PC reference matrices are rigid transforms, not scale
    # or shear. Refuse to claim that a general arbitrary matrix is verified.
    rows=[m[0:3],m[4:7],m[8:11]]
    for i in range(3):
        for j in range(3):
            dot=sum(rows[i][k]*rows[j][k] for k in range(3))
            if abs(dot-(1 if i==j else 0))>tol:return False
    return True


def _header(block, a, b):
    h=list(subchunks(block,a,b,HEAD))
    if len(h)!=1:raise UnsafeRewrite('Missing/ambiguous 0x134011 header')
    start,end=h[0];data=block[start:end]
    name=NAME.search(data)
    if not name:raise UnsafeRewrite('Unnamed 0x134011 component')
    candidates=[]
    for variant in MARKERS:
        pos=0
        while True:
            q=data.find(variant,pos)
            if q<0:break
            if q+0x74<=len(data) and data[q+0x10:q+0x14]==b'\0'*4:
                candidates.append((q,variant))
            pos=q+1
    if len(candidates)!=1:raise UnsafeRewrite('No unique supported 0x134011 matrix header')
    q,variant=candidates[0]
    lo=struct.unpack_from('<3f',data,q+0x14)
    hi=struct.unpack_from('<3f',data,q+0x24)
    if not all(math.isfinite(v) for v in lo+hi) or any(x>y for x,y in zip(lo,hi)):
        raise UnsafeRewrite('Invalid local bounds')
    m=struct.unpack_from('<16f',data,q+0x34)
    if not _valid_matrix(m):raise UnsafeRewrite('Unsupported non-rigid/non-affine 4x4 matrix')
    return {'name':name.group().decode('ascii'),'header_start':start,
            'matrix_offset':start+q+0x34,'marker_offset':start+q,
            'variant':variant.hex(),'matrix':m,'matrix_bytes':data[q+0x34:q+0x74],
            'local_min':lo,'local_max':hi,'translation':m[12:15]}


def locate_header(block,name):
    if len(block)<8 or struct.unpack_from('<II',block)!=(GEOM,len(block)-8):
        raise UnsafeRewrite('Expected intact 0x80134000 scenery container')
    found=[]
    for a,b in subchunks(block,8,len(block),COMP):
        headers=list(subchunks(block,a,b,HEAD))
        if len(headers)!=1:continue
        h=block[slice(*headers[0])]
        match=NAME.search(h)
        if match and match.group().decode('ascii')==name:
            found.append((a,b,_header(block,a,b)))
    if len(found)!=1:raise UnsafeRewrite(f'Expected unique component {name}, got {len(found)}')
    return found[0]


def world_bounds(info):
    m=info['matrix'];lo=info['local_min'];hi=info['local_max']
    pts=[(x,y,z) for x,y,z in itertools.product((lo[0],hi[0]),(lo[1],hi[1]),(lo[2],hi[2]))]
    transformed=[tuple(sum(v[k]*m[4*k+j] for k in range(3))+m[12+j] for j in range(3)) for v in pts]
    return {'min':tuple(min(p[j] for p in transformed) for j in range(3)),
            'max':tuple(max(p[j] for p in transformed) for j in range(3))}


def transplant_matrix(pc_block,pc_name,wii_block,wii_name):
    """Copy only the 64 matrix bytes into an already bounds-repaired PC sample.

    This copies the original *Wii matrix*, not the object identity or a stream
    placement. It is an offline format experiment and cannot be installed.
    """
    a,b,mod=locate(pc_block,pc_name)
    _,_,dest=locate_header(pc_block,pc_name)
    _,_,source=locate_header(wii_block,wii_name)
    checked=inspect(pc_block,pc_name)
    if not checked['header_equals_material_union'] or not checked['header_vertex_extrema_plus_0_01']:
        raise UnsafeRewrite('PC geometry local bounds must be rebuilt first')
    if dest['variant']!=source['variant']:
        raise UnsafeRewrite('Source and target object header variants differ')
    before=hashlib.sha256(pc_block).hexdigest()
    off=dest['matrix_offset'];edited=bytearray(pc_block)
    edited[off:off+64]=source['matrix_bytes']
    output=bytes(edited)
    changes={i for i,(x,y) in enumerate(zip(pc_block,output)) if x!=y}
    if len(output)!=len(pc_block) or any(i<off or i>=off+64 for i in changes):
        raise UnsafeRewrite('Unexpected bytes changed outside the matrix')
    aa,bb,after_mod=locate(output,pc_name)
    _,_,after=locate_header(output,pc_name)
    if (aa,bb)!=(a,b) or after['matrix_bytes']!=source['matrix_bytes']:
        raise UnsafeRewrite('Matrix readback failed')
    if (mod['positions']!=after_mod['positions'] or mod['faces']!=after_mod['faces'] or
        mod['uv']!=after_mod['uv'] or mod['colors']!=after_mod['colors'] or
        mod['normals']!=after_mod['normals'] or mod['materials']!=after_mod['materials']):
        raise UnsafeRewrite('Geometry or material data changed')
    return output,{
        'pc_carrier_name':pc_name,'undercover_source_name':wii_name,
        'matrix_bytes_changed':len(changes),'matrix_only_write':True,
        'same_chunk_length':len(output)==len(pc_block),
        'source_wii_translation':source['translation'],
        'pc_carrier_translation_before':dest['translation'],
        'pc_carrier_translation_after':after['translation'],
        'transformed_local_aabb':world_bounds(after),
        'source_wii_world_aabb':world_bounds(source),
        'source_wii_matrix_bytes_match':after['matrix_bytes']==source['matrix_bytes'],
        'before_sha256':before,'after_sha256':hashlib.sha256(output).hexdigest(),
        'offline_only':True,'in_game_test':'NOT PERFORMED',
        'unresolved':['source texture asset/PC shader binding', 'object identity',
                      'world-sector references','collision','navigation','stream table offsets']}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('pc_source');p.add_argument('pc_component');p.add_argument('wii_source');p.add_argument('wii_component')
    p.add_argument('--output');p.add_argument('--report')
    args=p.parse_args()
    pc=Path(args.pc_source).read_bytes();wii=Path(args.wii_source).read_bytes()
    result,report=transplant_matrix(pc,args.pc_component,wii,args.wii_component)
    if args.output:
        dest=Path(args.output)
        if dest.resolve()==Path(args.pc_source).resolve():raise UnsafeRewrite('Refusing to overwrite original')
        dest.write_bytes(result)
    if args.report:Path(args.report).write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
