#!/usr/bin/env python3
"""Read-only Carbon PC/PS2 same-hash XYZ+periodic UV correspondence controls.

Per-vertex UV witnesses must share a position within XYZ tolerance, and a UV
within periodic tolerance. Does not assert paired *faces* use same material,
texture atlas, PC model shader, normals, or final rendering semantics.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import struct

from pc_native_vertex_control import inspect_pc_solid, _candidate_assignments
from pc_ps2_position_control import source_geometry
from mesh_topology_control import (PC_MESH,PC_TRI_INDICES,PC_VERTEX,
                                   PS2_STRIPS,PS2_STRIP_DATA,
                                   parse_ps2_mesh,filler_size)
from track_bundle_probe import SplitZip
from vif_strip_probe import decode_strip_header
from xyz_uv_spatial_match import bidirectional_xyz_uv


def pc_attributes(children):
    checked=inspect_pc_solid(children)
    mesh=next(b for cid,b in children if cid==PC_MESH)
    indices=next(b for cid,b in children if cid==PC_TRI_INDICES)
    vb=[b for cid,b in children if cid==PC_VERTEX]
    pad=filler_size(mesh)
    records=[mesh[pad+i*144:pad+(i+1)*144] for i in range(checked['mesh_records'])]
    ids=struct.unpack_from('<'+str(checked['triangle_indices'])+'H',indices,filler_size(indices))
    mapping=_candidate_assignments(vb,records,ids)
    positions=[];uv=[]
    for bid,first,last,stride in mapping:
        data=vb[bid]
        for off in range(filler_size(data),len(data),stride):
            positions.append(struct.unpack_from('<3f',data,off))
            uv.append(struct.unpack_from('<2f',data,off+28))
    if len(positions)!=checked.get('vertices_stride_36',0)+checked.get('vertices_stride_52',0):
        raise ValueError('Native Carbon PC vertex/UV count disagrees with validated buffers')
    return tuple(positions),tuple(uv)


def ps2_attributes(children):
    info=parse_ps2_mesh(children)
    entries=next(b for cid,b in children if cid==PS2_STRIPS)
    data=next(b for cid,b in children if cid==PS2_STRIP_DATA)
    xyz=[];uv=[]
    for i in range(info['strip_entries']):
        _,nv,npoly,_,qoff,_,_,qsize,_,_,_=struct.unpack_from('<HBBfHbbBBbb',entries,4+i*16)
        start,end=8+qoff*16,8+(qoff+qsize)*16
        if not qsize or end>len(data):
            raise ValueError('PS2 VIF packet outside strip resource bounds')
        decoded=decode_strip_header(data[start:end],nv,npoly)
        if len(decoded['position_samples'])!=nv or len(decoded['uv_samples'])!=nv:
            raise ValueError('PS2 VIF XYZ/ST vertex count does not match descriptor')
        xyz.extend(decoded['position_samples'])
        uv.extend(decoded['uv_samples'])
    return tuple(xyz),tuple(uv)


def compare_solid_uv(pc_models,ps2_models,xyz_tol=.01,uv_tol=.01):
    if not pc_models or set(pc_models)!=set(ps2_models):
        raise ValueError('Original Carbon PC and PS2 same-hash solid sets differ')
    totals=Counter();max_uv=0.
    for model in sorted(pc_models):
        pc_xyz,pc_uv=pc_attributes(pc_models[model])
        ps_xyz,ps_uv=ps2_attributes(ps2_models[model])
        result=bidirectional_xyz_uv(pc_xyz,pc_uv,ps_xyz,ps_uv,xyz_tol,uv_tol)
        if not result['matches_both_directions']:
            raise ValueError('Same-hash PC/PS2 model fails bidirectional XYZ/UV source check')
        totals['matched_model_pairs']+=1
        for key in ('pc_to_ps2','ps2_to_pc'):
            row=result[key]
            totals[key+'_vertex_records']+=row['vertex_records']
            totals[key+'_integer_uv_tile_offset_rescues']+=row['integer_uv_tile_offset_rescues']
            max_uv=max(max_uv,row['max_periodic_uv_witness_distance'])
    return {**dict(totals),'max_periodic_uv_witness_distance':max_uv,
            'all_vertex_xyz_and_periodic_uv_pairs_matched':True}


def analyze(pc_volumes,carbon_ps2_zip,xyz_tol=.01,uv_tol=.01):
    sections=(141,142)
    pc=source_geometry(SplitZip(pc_volumes),'L5',sections)
    ps2=source_geometry(Path(carbon_ps2_zip),'L5',sections)
    return {'original_control_sections':{str(sec):compare_solid_uv(pc[sec],ps2[sec],xyz_tol,uv_tol) for sec in sections},
            'scope':('This is a bidirectional vertex-attribute match in XYZ/periodic UV, '
                     'not a per-triangle material or texture binding equivalence proof. '
                     'No native PC mesh writer or Undercover in-engine rendering demonstrated.')}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--pc-volumes',type=Path,nargs='+',required=True)
    p.add_argument('--carbon-ps2-zip',type=Path,required=True)
    p.add_argument('--xyz-tolerance',type=float,default=.01)
    p.add_argument('--uv-tolerance',type=float,default=.01)
    a=p.parse_args()
    print(json.dumps(analyze(a.pc_volumes,a.carbon_ps2_zip,a.xyz_tolerance,a.uv_tolerance),indent=2))

if __name__=='__main__':main()
