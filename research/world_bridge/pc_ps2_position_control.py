#!/usr/bin/env python3
"""Read-only Carbon PC/PS2 same-hash vertex-cloud comparison.

Authenticates two Carbon world scenery controls, resolves their complete indexed
solids, decodes PC native vertex XYZ and PS2 VIF XYZ, then performs symmetric
bounded nearest-neighbor matching. Exports only aggregate results. Neither
triangle winding nor UV/material correspondence is established by cloud matches.
"""
import argparse
from collections import Counter
import json
import math
from pathlib import Path
import struct
import zipfile

from geometry_hash_control import (GEOM, SOLID_ROOT, PLATFORM_PC, PLATFORM_PS2,
                                   MAX_REGION, parse_geometry_root, parse_solid,
                                   read_chunks)
from mesh_topology_control import (PC_MESH, PC_TRI_INDICES, PC_VERTEX,
                                   PS2_STRIPS, PS2_STRIP_DATA,
                                   filler_size, parse_pc_mesh, parse_ps2_mesh)
from pc_native_vertex_control import inspect_pc_solid, _candidate_assignments
from rb_scenery_graph_census import read_rb
from track_bundle_probe import SplitZip
from vif_strip_probe import decode_strip_header
from visibility_stream_join import read_small
from vertex_cloud_spatial_match import bidirectional_cloud_match

MAX_SECTION_BYTES = 32 * 1024 * 1024


def pc_positions(children):
    """Return in-memory PC XYZ after full mesh-range/bbox validation."""
    info = inspect_pc_solid(children)
    mesh = next(v for cid,v in children if cid == PC_MESH)
    idx = next(v for cid,v in children if cid == PC_TRI_INDICES)
    buffers = [v for cid,v in children if cid == PC_VERTEX]
    mpad = filler_size(mesh)
    rows = [mesh[mpad+144*i:mpad+144*(i+1)] for i in range(info['mesh_records'])]
    ipad = filler_size(idx)
    indices = struct.unpack_from('<'+str(info['triangle_indices'])+'H', idx, ipad)
    mapping = _candidate_assignments(buffers, rows, indices)
    vertices = []
    for buffer_id, first, stop, stride in mapping:
        buf = buffers[buffer_id]
        start = filler_size(buf)
        for pos in range(start, len(buf), stride):
            vertices.append(struct.unpack_from('<3f', buf, pos))
    if len(vertices) != (info.get('vertices_stride_36', 0) +
                         info.get('vertices_stride_52', 0)):
        raise ValueError('Incomplete native PC position decode')
    return vertices


def ps2_positions(children):
    """Reconstruct original PS2 VIF XYZ for every validated strip in a solid."""
    sizes = parse_ps2_mesh(children)
    entry = next(v for cid,v in children if cid == PS2_STRIPS)
    stream = next(v for cid,v in children if cid == PS2_STRIP_DATA)
    positions = []
    for i in range(sizes['strip_entries']):
        _, nvert, npoly, _, qoffset, _, _, qsize, _, _, _ = struct.unpack_from(
            '<HBBfHbbBBbb', entry, 4 + 16*i)
        if qsize == 0:
            raise ValueError('Empty PS2 strip packet')
        first, end = 8 + 16*qoffset, 8 + 16*(qoffset+qsize)
        if end > len(stream):
            raise ValueError('PS2 VIF packet exceeds indexed strip bounds')
        result = decode_strip_header(stream[first:end], nvert, npoly)
        if result['decoded_position_vertices'] != nvert:
            raise ValueError('PS2 decoded vertex count contradicts strip header')
        positions.extend(result['position_samples'])
    if not positions:
        raise ValueError('No PS2 position vertices decoded')
    return positions


def indexed_solids(world, section_rows, scenes, sections, expected_platform):
    """Find complete source-indexed solids without exporting hashes or bytes."""
    output = {}
    for section in sections:
        if section not in section_rows or section not in scenes:
            raise ValueError('Source scene lacks authenticated stream section row')
        offset, nbytes = struct.unpack_from('<II', section_rows[section], 0x14)
        if nbytes > MAX_SECTION_BYTES or offset+nbytes > len(world):
            raise ValueError('Source geometry section out of allowed bounds')
        block = world[offset:offset+nbytes]
        solids = {}
        cursor = 0
        packs = 0
        while True:
            at = block.find(struct.pack('<I', GEOM), cursor)
            if at < 0:
                break
            cursor = at+4
            if at % 4 or at+8 > len(block):
                continue
            size = struct.unpack_from('<I', block, at+4)[0]
            if size > len(block)-at-8:
                continue
            frame = block[at:at+8+size]
            try:
                geom = parse_geometry_root(frame)
            except ValueError:
                continue
            contained_hashes = set()
            for cid, solid in list(read_chunks(frame, 16, len(frame)))[1:]:
                if cid != SOLID_ROOT:
                    raise ValueError('Unexpected resource in authenticated geometry pack')
                namehash, platform, _, _ = parse_solid(solid)
                if platform != expected_platform or namehash in contained_hashes:
                    raise ValueError('Wrong platform or duplicate indexed model')
                contained_hashes.add(namehash)
                if namehash in solids:
                    raise ValueError('Duplicate model hash across Carbon control packs')
                sc = list(read_chunks(solid, 0, len(solid)))
                solids[namehash] = list(read_chunks(sc[-1][1], 0, len(sc[-1][1])))
            if contained_hashes != geom['hashes']:
                raise ValueError('Geometry index differs from actual solid headers')
            packs += 1
            if packs > 16:
                raise ValueError('Too many geometry packs in selected section')
            cursor = at+8+size
        if not solids:
            raise ValueError('No complete indexed source geometry solids')
        output[section] = solids
    return output


def source_geometry(archive, stem, sections):
    scenes, _ = read_rb(archive, stem)
    rows, _, _ = read_small(archive, stem, 'RB')
    member = f'TRACKS/STREAM{stem}RB.BUN'
    if isinstance(archive, SplitZip):
        if archive.entries[member][4] > MAX_REGION:
            raise ValueError('Original PC RB source stream exceeds safety bound')
        world = archive.read(member, limit=MAX_REGION)
    else:
        with zipfile.ZipFile(archive) as z:
            if z.getinfo(member).file_size > MAX_REGION:
                raise ValueError('Original PS2 RB source stream exceeds safety bound')
            world = z.read(member)
    return indexed_solids(world, rows, scenes, sections,
                          PLATFORM_PC if isinstance(archive, SplitZip) else PLATFORM_PS2)


def compare_source_models(pc_models, ps2_models, tolerance=0.01):
    if set(pc_models) != set(ps2_models) or not pc_models:
        raise ValueError('PC/PS2 control models lack identical indexed hash sets')
    totals = Counter()
    farthest = 0.0
    for model_hash in sorted(pc_models):
        pc_cloud = pc_positions(pc_models[model_hash])
        ps2_cloud = ps2_positions(ps2_models[model_hash])
        result = bidirectional_cloud_match(pc_cloud, ps2_cloud, tolerance)
        if not result['both_directions_match']:
            raise ValueError('A paired Carbon PC/PS2 model fails XYZ cloud matching')
        farthest = max(farthest,
                       result['pc_to_ps2']['max_matching_witness_distance'],
                       result['ps2_to_pc']['max_matching_witness_distance'])
        totals['paired_models_passed'] += 1
        totals['pc_vertex_positions'] += len(pc_cloud)
        totals['ps2_vertex_occurrences'] += len(ps2_cloud)
    return {**dict(totals), 'bidirectional_max_witness_distance':farthest,
            'every_source_vertex_has_a_nearby_destination':True,
            'tolerance':tolerance}


def analyze(pc_volumes, carbon_ps2_zip, tolerance=0.01):
    if not math.isfinite(tolerance) or not 0 < tolerance <= 0.1:
        raise ValueError('Unsupported nonpositive or overly broad geometry tolerance')
    sections=(141,142)
    pc = source_geometry(SplitZip(pc_volumes), 'L5', sections)
    ps2 = source_geometry(Path(carbon_ps2_zip), 'L5', sections)
    results = {str(section):compare_source_models(pc[section], ps2[section], tolerance)
               for section in sections}
    return {'carbon_pc_vs_ps2':results,
            'limits':('Bidirectional 3D tolerance witnesses establish XYZ cloud equivalence '
                      'within tolerance, not same vertex order, triangle connectivity, '
                      'triangle winding, normals, UVs, materials, runtime geometry '
                      'loading, collision or a converted Undercover scene.')}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--pc-volumes',type=Path,nargs='+',required=True)
    p.add_argument('--carbon-ps2-zip',type=Path,required=True)
    p.add_argument('--tolerance',type=float,default=0.01)
    a=p.parse_args()
    print(json.dumps(analyze(a.pc_volumes,a.carbon_ps2_zip,a.tolerance),indent=2))


if __name__=='__main__':
    main()
