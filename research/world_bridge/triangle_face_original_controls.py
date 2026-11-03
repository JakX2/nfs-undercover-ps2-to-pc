#!/usr/bin/env python3
"""Read-only, original-carbon paired triangle geometry and winding controls.

Uses validated source-hash eSolids from PC and PS2 RB sections 141/142. All
vertex positions and triangle faces exist only in memory; prints aggregate
counts, not hashes, models, vertices, UVs, texture names or source assets.
The 0.01-unit face match is existential, NOT a mesh byte writer or a proof of
one-to-one triangle multiplicities, normals, UVs, texture or runtime behavior.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import struct

from geometry_hash_control import PLATFORM_PC, PLATFORM_PS2
from mesh_topology_control import (PC_MESH, PC_TRI_INDICES, PC_VERTEX, PS2_STRIPS,
                                   PS2_STRIP_DATA, parse_pc_mesh, parse_ps2_mesh, filler_size)
from pc_native_vertex_control import inspect_pc_solid, _candidate_assignments
from pc_ps2_position_control import source_geometry
from track_bundle_probe import SplitZip
from triangle_face_spatial_match import bidirectional_face_match
from vif_strip_probe import decode_strip_header

SECTIONS=(141,142)


def pc_triangle_faces(children):
    """Build XYZ faces using the per-buffer native 16-bit index coordinate system."""
    info = inspect_pc_solid(children)
    mesh=next(x for cid,x in children if cid==PC_MESH)
    raw_indices=next(x for cid,x in children if cid==PC_TRI_INDICES)
    buffers=[x for cid,x in children if cid==PC_VERTEX]
    pad=filler_size(mesh)
    records=[mesh[pad+144*i:pad+144*(i+1)] for i in range(info['mesh_records'])]
    index_count=info['triangle_indices']
    indexes=struct.unpack_from('<'+str(index_count)+'H',raw_indices,filler_size(raw_indices))
    map_rows=_candidate_assignments(buffers,records,indexes)
    faces=[]
    for buffer_id,begin,end,stride in map_rows:
        source=buffers[buffer_id]
        start=filler_size(source)
        positions=[struct.unpack_from('<3f',source,offset)
                   for offset in range(start,len(source),stride)]
        for mesh_id in range(begin,end):
            rec=records[mesh_id]
            first,count=(struct.unpack_from('<I',rec,n)[0] for n in (0x64,0x7c))
            for i in range(first,first+count,3):
                faces.append(tuple(positions[indexes[i+j]] for j in range(3)))
    if len(faces)!=info['triangle_count']:
        raise ValueError('PC triangles do not cover the complete validated index buffer')
    return faces


def ps2_triangle_faces(children):
    """Assemble candidate geometry faces from bounds-checked PS2 VIF strips."""
    stats=parse_ps2_mesh(children)
    entries=next(b for cid,b in children if cid==PS2_STRIPS)
    data=next(b for cid,b in children if cid==PS2_STRIP_DATA)
    faces=[]
    for i in range(stats['strip_entries']):
        _flags,nverts,npoly,_density,qoff,_nz,_nt,qsize,_group,_tex,_light=struct.unpack_from(
            '<HBBfHbbBBbb',entries,4+16*i)
        if qsize==0:
            raise ValueError('Empty PS2 strip packet')
        beginning,ending=8+16*qoff,8+16*(qoff+qsize)
        if ending>len(data):
            raise ValueError('PS2 strip packet exceeds bounded strip data')
        packet=decode_strip_header(data[beginning:ending],nverts,npoly)
        xyz=packet['position_samples']
        indices=packet['triangle_index_candidates']
        if len(indices)!=npoly or len(xyz)!=nverts:
            raise ValueError('VIF ADC triangle candidate count contradicts strip descriptor')
        for triangle in indices:
            faces.append(tuple(xyz[v] for v in triangle))
    if len(faces)!=stats['strip_polygon_count']:
        raise ValueError('PS2 mesh triangles do not equal the validated strip counts')
    return faces


def compare_models(pc,ps2,tolerance=0.01):
    if not pc or set(pc)!=set(ps2):
        raise ValueError('Source PC and PS2 solids lack the same indexed model identities')
    totals=Counter()
    for hash_id in sorted(pc):
        pc_faces=pc_triangle_faces(pc[hash_id])
        ps2_faces=ps2_triangle_faces(ps2[hash_id])
        result=bidirectional_face_match(pc_faces,ps2_faces,tolerance)
        totals['models_checked']+=1
        totals['models_with_all_faces_present_bidirectionally']+=int(
            result['all_pc_faces_have_ps2_counterparts'] and
            result['all_ps2_faces_have_pc_counterparts'])
        for prefix in ('pc_to_ps2','ps2_to_pc'):
            for field,val in result[prefix].items():
                totals[prefix+'_'+field]+=val
    return dict(sorted(totals.items()))


def analyze(pc_volumes,ps2_archive,tolerance=0.01):
    if not 0 < tolerance <=0.1:
        raise ValueError('Triangle tolerance must be greater than zero and at most 0.1')
    pc=source_geometry(SplitZip(pc_volumes),'L5',SECTIONS)
    ps=source_geometry(Path(ps2_archive),'L5',SECTIONS)
    reports={str(section):compare_models(pc[section],ps[section],tolerance)
             for section in SECTIONS}
    if any(r.get('ps2_to_pc_unmatched_faces',0) for r in reports.values()):
        raise ValueError('A PS2 candidate face lacks a matching native PC face')
    return {'tolerance_game_units':tolerance,'sections':reports,
            'limitations':('Existential matched triangle geometry only. Duplicated faces '
                           'may match the same target more than once; ambiguous and '
                           'reversed winding candidates are reported separately. '
                           'This does NOT prove exact mesh multisets, normals, UVs, '
                           'materials, texture bindings, or any in-game port.')}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--pc-volumes',nargs='+',required=True,type=Path)
    p.add_argument('--carbon-ps2-zip',required=True,type=Path)
    p.add_argument('--tolerance',type=float,default=0.01)
    args=p.parse_args()
    print(json.dumps(analyze(args.pc_volumes,args.carbon_ps2_zip,args.tolerance),indent=2))

if __name__=='__main__':
    main()
