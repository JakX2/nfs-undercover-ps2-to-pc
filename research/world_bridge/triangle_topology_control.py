#!/usr/bin/env python3
"""Read-only same-hash PC/PS2 triangle geometry matching in Carbon controls.

Comparisons require actual source-indexed solids in two original RB scenes,
complete PC native mesh/vertex/index partitions and PS2 VIF/ADC strips.
The geometric tolerance does not establish UV/material/normal equivalence, or
that a PC writer/in-game rendering works. Only aggregate numbers are emitted.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import struct

from geometry_hash_control import PLATFORM_PC, PLATFORM_PS2
from mesh_topology_control import (PC_MESH, PC_TRI_INDICES, PC_VERTEX,
                                   PS2_STRIPS, PS2_STRIP_DATA,
                                   parse_ps2_mesh, filler_size)
from pc_native_vertex_control import inspect_pc_solid, _candidate_assignments
from pc_ps2_position_control import source_geometry
from track_bundle_probe import SplitZip
from triangle_face_bijection import match_triangle_faces
from vif_strip_probe import decode_strip_header


def pc_faces(children):
    """Recover source-checked PC world XYZ and *buffer-relative* triangle IDs."""
    checked=inspect_pc_solid(children)
    mesh=next(blob for cid,blob in children if cid==PC_MESH)
    triangles=next(blob for cid,blob in children if cid==PC_TRI_INDICES)
    buffers=[blob for cid,blob in children if cid==PC_VERTEX]
    p=filler_size(mesh)
    rows=[mesh[p+144*i:p+144*(i+1)] for i in range(checked['mesh_records'])]
    index_word_count=checked['triangle_indices']
    indexed=struct.unpack_from('<'+str(index_word_count)+'H',triangles,filler_size(triangles))
    assignment=_candidate_assignments(buffers,rows,indexed)
    vertices=[]
    faces=[]
    for bid,first,last,stride in assignment:
        buf=buffers[bid]
        start=filler_size(buf)
        global_base=len(vertices)
        for off in range(start,len(buf),stride):
            vertices.append(struct.unpack_from('<3f',buf,off))
        for mesh_id in range(first,last):
            first_index,count=(struct.unpack_from('<I',rows[mesh_id],x)[0] for x in (0x64,0x7c))
            for at in range(first_index,first_index+count,3):
                faces.append(tuple(global_base+indexed[at+k] for k in range(3)))
    if len(vertices)!=checked.get('vertices_stride_36',0)+checked.get('vertices_stride_52',0):
        raise ValueError('Source native PC vertex count disagrees with assigned buffers')
    if len(faces)!=checked['triangle_count']:
        raise ValueError('Source native PC face count disagrees with index count')
    return tuple(vertices),tuple(faces)


def ps2_faces(children):
    """Use source-validated QWORD strip packets and ADC-filtered face indices."""
    info=parse_ps2_mesh(children)
    strip_entries=next(blob for cid,blob in children if cid==PS2_STRIPS)
    packet_bytes=next(blob for cid,blob in children if cid==PS2_STRIP_DATA)
    vertices=[];faces=[];polygons=0
    for i in range(info['strip_entries']):
        _,nv,npoly,_,qoff,_,_,qsize,_,_,_=struct.unpack_from('<HBBfHbbBBbb',strip_entries,4+16*i)
        start=8+16*qoff;end=8+16*(qoff+qsize)
        if not qsize or end>len(packet_bytes):
            raise ValueError('Source strip packet exceeds QWORD size bounds')
        decoded=decode_strip_header(packet_bytes[start:end],nv,npoly)
        coords=decoded['position_samples']
        triangles=decoded['triangle_index_candidates']
        if len(coords)!=nv or len(triangles)!=npoly:
            raise ValueError('PS2 strip vertex/ADC-triangle sizes disagree with descriptor')
        base=len(vertices)
        vertices.extend(tuple(float(v) for v in p) for p in coords)
        faces.extend(tuple(base+v for v in triangle) for triangle in triangles)
        polygons+=npoly
    if len(faces)!=info['strip_polygon_count'] or polygons!=info['strip_polygon_count']:
        raise ValueError('PS2 candidate faces differ from validated strip polygon total')
    return tuple(vertices),tuple(faces)


def compare_solid_controls(pc_models,ps2_models,tolerance=.01):
    """Require full one-to-one geometric embedding, no exported model IDs."""
    if not pc_models or set(pc_models)!=set(ps2_models):
        raise ValueError('PC and PS2 model identity sets disagree')
    totals=Counter()
    max_corner_witness=0.
    mismatch_distribution=Counter()
    for model_id in sorted(pc_models):
        pc_vertices,pc_triangles=pc_faces(pc_models[model_id])
        ps_vertices,ps_triangles=ps2_faces(ps2_models[model_id])
        result=match_triangle_faces(pc_vertices,pc_triangles,ps_vertices,ps_triangles,tolerance)
        if not result['every_ps2_triangle_has_distinct_pc_match']:
            raise ValueError('A same-hash Carbon PS2 model has unmatched triangle geometry')
        difference=result['unused_pc_triangles_after_matching']
        mismatch_distribution[difference]+=1
        totals['verified_model_pairs']+=1
        totals['models_with_identical_triangle_counts']+=difference==0
        for key in ('pc_triangles','ps2_triangles','ps2_triangles_uniquely_assigned',
                    'ps2_triangles_with_multiple_pc_candidates',
                    'unused_pc_triangles_after_matching',
                    'relative_permutation_even','relative_permutation_odd'):
            totals[key]+=result[key]
        max_corner_witness=max(max_corner_witness,result['max_corner_witness_distance'])
    return {**dict(totals),
            'pc_minus_ps2_triangle_count_difference_models':dict(sorted((str(k),v) for k,v in mismatch_distribution.items())),
            'max_corner_witness_distance':max_corner_witness,
            'all_ps2_triangles_have_distinct_matching_pc_triangles':True}


def analyze(pc_volumes,carbon_ps2_zip,tolerance=.01):
    sections=(141,142)
    pc=source_geometry(SplitZip(pc_volumes),'L5',sections)
    ps2=source_geometry(Path(carbon_ps2_zip),'L5',sections)
    result={str(section):compare_solid_controls(pc[section],ps2[section],tolerance) for section in sections}
    return {'carbon_pc_vs_ps2':result,
            'limits':('Per-model unique 3D triangle geometry within tolerance. '
                      'Candidate winding-parity counts are match-dependent on repeated '
                      'and near-degenerate faces. This does not prove vertex or triangle '
                      'order, normals, material/UV mapping, PC writer correctness, '
                      'runtime model loading or any playable Undercover scene.')}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--pc-volumes',type=Path,nargs='+',required=True)
    p.add_argument('--carbon-ps2-zip',type=Path,required=True)
    p.add_argument('--tolerance',type=float,default=.01)
    a=p.parse_args()
    print(json.dumps(analyze(a.pc_volumes,a.carbon_ps2_zip,a.tolerance),indent=2))

if __name__=='__main__':main()
