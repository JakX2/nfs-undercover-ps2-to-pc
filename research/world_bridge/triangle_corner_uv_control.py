#!/usr/bin/env python3
"""Read-only original Carbon PC/PS2 face-corner XYZ+UV+texture comparison.

Uses source-verified world/solid/vertex/VIF parsers and whole texture-hash
identity tables. Prints aggregate counts only. No game bytes, hash inventory,
raw vertices or proprietary materials are exported or rewritten.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import struct

from track_bundle_probe import SplitZip
from geometry_hash_control import PLATFORM_PC, PLATFORM_PS2
from pc_ps2_position_control import source_geometry
from pc_native_vertex_control import inspect_pc_solid, _candidate_assignments
from mesh_topology_control import (PC_MESH, PC_TRI_INDICES, PC_VERTEX,
                                   PS2_STRIPS, PS2_STRIP_DATA,
                                   filler_size, parse_ps2_mesh)
from texture_binding_control import source_materials
from vif_strip_probe import decode_strip_header
from triangle_corner_uv_match import match_faces


SECTIONS = (141, 142)


def pc_geometry_attributes(children):
    """Map native PC indexed faces to XYZ, UV and local solid texture index."""
    validated = inspect_pc_solid(children)
    mesh = next(b for cid, b in children if cid == PC_MESH)
    idx = next(b for cid, b in children if cid == PC_TRI_INDICES)
    buffers = [b for cid, b in children if cid == PC_VERTEX]
    pad = filler_size(mesh)
    records = [mesh[pad+144*i:pad+144*(i+1)] for i in range(validated['mesh_records'])]
    indices = struct.unpack_from('<'+str(validated['triangle_indices'])+'H', idx, filler_size(idx))
    mapping = _candidate_assignments(buffers, records, indices)
    xyz, uv, faces, labels = [], [], [], []
    for buffer_id, first_mesh, end_mesh, stride in mapping:
        data = buffers[buffer_id]
        base = len(xyz)
        for off in range(filler_size(data), len(data), stride):
            xyz.append(struct.unpack_from('<3f', data, off))
            uv.append(struct.unpack_from('<2f', data, off+28))
        for mesh_id in range(first_mesh, end_mesh):
            rec = records[mesh_id]
            first, count = (struct.unpack_from('<I', rec, k)[0] for k in (0x64,0x7c))
            tex = rec[0x18]
            for pos in range(first, first+count, 3):
                faces.append(tuple(base+indices[pos+k] for k in range(3)))
                labels.append(tex)
    if len(faces) != validated['triangle_count'] or len(xyz) != (validated.get('vertices_stride_36', 0) + validated.get('vertices_stride_52', 0)):
        raise ValueError('Native PC mesh face/vertex counts do not match validated source')
    return tuple(xyz), tuple(uv), tuple(faces), tuple(labels)


def ps2_geometry_attributes(children):
    """Decode each real VIF strip, retaining per-face texture-table index."""
    checked = parse_ps2_mesh(children)
    entries = next(b for cid,b in children if cid == PS2_STRIPS)
    data = next(b for cid,b in children if cid == PS2_STRIP_DATA)
    xyz, uv, faces, labels = [], [], [], []
    for strip in range(checked['strip_entries']):
        _, nv, npoly, _, qoff, _, _, qsize, _, texture, _ = struct.unpack_from(
            '<HBBfHbbBBbb', entries, 4+16*strip)
        first, last = 8+16*qoff, 8+16*(qoff+qsize)
        if not qsize or last > len(data):
            raise ValueError('PS2 strip VIF packet exceeds strip-data bounds')
        decoded = decode_strip_header(data[first:last], nv, npoly)
        if (len(decoded['position_samples']) != nv or len(decoded['uv_samples']) != nv or
                len(decoded['triangle_index_candidates']) != npoly):
            raise ValueError('PS2 VIF XYZ/UV/face counts contradict strip descriptor')
        base = len(xyz)
        xyz.extend(tuple(float(x) for x in position) for position in decoded['position_samples'])
        uv.extend(tuple(float(x) for x in st) for st in decoded['uv_samples'])
        faces.extend(tuple(base+k for k in face) for face in decoded['triangle_index_candidates'])
        labels.extend([texture]*npoly)
    if len(faces) != checked['strip_polygon_count']:
        raise ValueError('PS2 assembled faces contradict bounded strip counts')
    return tuple(xyz), tuple(uv), tuple(faces), tuple(labels)


def compare_controls(pc_solids, ps_solids, pc_materials, ps_materials,
                     xyz_tol=.01, uv_tol=.01):
    if not pc_solids or set(pc_solids) != set(ps_solids):
        raise ValueError('Carbon PC/PS2 model hash sets disagree')
    a = dict(pc_materials)
    b = dict(ps_materials)
    if (len(a) != len(pc_materials) or len(b) != len(ps_materials) or
            set(a) != set(b) or set(a) != set(pc_solids)):
        raise ValueError('Carbon PC/PS2 material model identities are inconsistent')
    counts = Counter()
    max_xyz = max_uv = 0.
    for model in sorted(pc_solids):
        if a[model]['texture_table'] != b[model]['texture_table']:
            raise ValueError('Original PC/PS2 local texture hash tables differ')
        texture_count = len(a[model]['texture_table'])
        px,pu,pf,pt = pc_geometry_attributes(pc_solids[model])
        sx,su,sf,st = ps2_geometry_attributes(ps_solids[model])
        report = match_faces(px,pu,pf,pt,sx,su,sf,st,texture_count,xyz_tol,uv_tol)
        if not report['all_ps2_faces_matched']:
            raise ValueError('A source-paired PS2 model fails face-corner XYZ/UV/texture matching')
        counts['model_pairs_passing'] += 1
        counts['models_with_equal_face_counts'] += report['unmatched_pc_faces'] == 0
        for key in ('pc_faces','ps2_faces','ps2_faces_assigned_distinct_pc_faces',
                    'unmatched_pc_faces','ps2_faces_with_multiple_pc_candidates',
                    'faces_requiring_periodic_uv_wrap','odd_corner_permutations_provisional'):
            counts[key] += report[key]
        max_xyz = max(max_xyz, report['max_xyz_witness_distance'])
        max_uv = max(max_uv, report['max_periodic_uv_witness_distance'])
    return {**dict(counts), 'max_xyz_witness_distance': max_xyz,
            'max_periodic_uv_witness_distance': max_uv,
            'every_ps2_face_matches_distinct_pc_face_same_texture_and_corner_uv': True}


def analyze(pc_volumes, carbon_ps2_zip, xyz_tol=.01, uv_tol=.01):
    pc_archive = SplitZip(pc_volumes)
    ps_archive = Path(carbon_ps2_zip)
    pc_geometry = source_geometry(pc_archive, 'L5', SECTIONS)
    ps_geometry = source_geometry(ps_archive, 'L5', SECTIONS)
    pc_material = source_materials(pc_archive, 'L5', SECTIONS, PLATFORM_PC)
    ps_material = source_materials(ps_archive, 'L5', SECTIONS, PLATFORM_PS2)
    return {
        'carbon_pc_vs_ps2': {str(sec): compare_controls(
            pc_geometry[sec], ps_geometry[sec], pc_material[sec], ps_material[sec],
            xyz_tol, uv_tol) for sec in SECTIONS},
        'scope': ('Same-hash original Carbon PC/PS2 secondary-area controls only. '
                  'Face-corner XYZ and periodic UV correspondence, and matching per-solid '
                  'texture-table hashes, are established within tolerance. No GPU sampler '
                  'wrap mode, material shader/texture pixels, normals/tangents, mesh '
                  'writer, in-game Undercover rendering, collision or AI verified.')
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--pc-volumes', type=Path, nargs='+', required=True)
    p.add_argument('--carbon-ps2-zip', type=Path, required=True)
    p.add_argument('--xyz-tolerance', type=float, default=.01)
    p.add_argument('--uv-tolerance', type=float, default=.01)
    a = p.parse_args()
    print(json.dumps(analyze(a.pc_volumes, a.carbon_ps2_zip,
                             a.xyz_tolerance, a.uv_tolerance), indent=2))


if __name__ == '__main__':
    main()
