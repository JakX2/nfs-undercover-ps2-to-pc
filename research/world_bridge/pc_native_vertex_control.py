#!/usr/bin/env python3
"""Read-only Carbon PC native vertex/index control; aggregate diagnostics only.

Candidate 36/52-byte vertex interpretation is validated against original PC
mesh records, per-mesh bounds, normals and tangent orthogonality. No asset
bytes, model hashes, textures, raw vertices or indices are emitted.
"""
import argparse
from collections import Counter
from functools import lru_cache
import json
import math
from pathlib import Path
import struct

from geometry_hash_control import (GEOM, SOLID_ROOT, PLATFORM_PC, MAX_REGION,
                                   parse_geometry_root, parse_solid, read_chunks)
from mesh_topology_control import (PC_MESH, PC_TRI_INDICES, PC_VERTEX,
                                   filler_size, parse_pc_mesh)
from rb_scenery_graph_census import read_rb
from track_bundle_probe import SplitZip
from visibility_stream_join import read_small

MESH_STRIDE = 144
POSITION_OFFSET = 0
NORMAL_OFFSET = 12
COLOR_OFFSET = 24
UV_OFFSET = 28
TANGENT_OFFSET = 36
HAND_OFFSET = 48
MAX_MODEL_VERTICES = 1_000_000


def _candidate_assignments(vertex_blobs, records, indices):
    """Assign consecutive mesh records to complete buffers, uniquely and safely."""
    counts = [struct.unpack_from('<I', mesh, 0x40)[0] for mesh in records]
    ranges = [(struct.unpack_from('<I', mesh, 0x64)[0],
               struct.unpack_from('<I', mesh, 0x7c)[0]) for mesh in records]
    prefix = [0]
    for count in counts:
        if not 0 < count <= MAX_MODEL_VERTICES:
            raise ValueError('Invalid per-mesh vertex count')
        prefix.append(prefix[-1] + count)
    if prefix[-1] > MAX_MODEL_VERTICES:
        raise ValueError('Unreasonably large model vertex count')

    @lru_cache(None)
    def solve(buffer_id, mesh_id):
        if buffer_id == len(vertex_blobs):
            return [()] if mesh_id == len(records) else []
        blob = vertex_blobs[buffer_id]
        size = len(blob) - filler_size(blob)
        solutions = []
        for stride in (36, 52):
            if size <= 0 or size % stride:
                continue
            target = size // stride
            for stop in range(mesh_id + 1, len(records) + 1):
                total = prefix[stop] - prefix[mesh_id]
                if total > target:
                    break
                if total != target:
                    continue
                local_base = 0
                valid = True
                for j in range(mesh_id, stop):
                    first, count = ranges[j]
                    if count % 3 or first + count > len(indices):
                        valid = False
                        break
                    if any(not local_base <= v < local_base + counts[j]
                           for v in indices[first:first + count]):
                        valid = False
                        break
                    local_base += counts[j]
                if valid:
                    for tail in solve(buffer_id + 1, stop):
                        solutions.append(((buffer_id, mesh_id, stop, stride),) + tail)
                        if len(solutions) > 1:
                            return solutions[:2]
        return solutions

    candidates = solve(0, 0)
    if len(candidates) != 1:
        raise ValueError('Vertex-buffer to mesh-range mapping is not unique')
    return candidates[0]


def inspect_pc_solid(platform_children):
    """Validate PC indexed ranges and candidate vertex attributes in RAM."""
    base = parse_pc_mesh(platform_children)
    mesh_data = next(payload for cid, payload in platform_children if cid == PC_MESH)
    index_data = next(payload for cid, payload in platform_children if cid == PC_TRI_INDICES)
    vertex_blobs = [payload for cid, payload in platform_children if cid == PC_VERTEX]
    mpad = filler_size(mesh_data)
    records = [mesh_data[mpad + i*MESH_STRIDE:mpad + (i+1)*MESH_STRIDE]
               for i in range(base['pc_mesh_records'])]
    ipad = filler_size(index_data)
    indices = struct.unpack_from('<' + str(base['pc_triangle_indices']) + 'H', index_data, ipad)
    next_index = 0
    for rec in records:
        triangles, first, count = (struct.unpack_from('<I', rec, k)[0]
                                   for k in (0x60, 0x64, 0x7c))
        if count != triangles*3 or first != next_index:
            raise ValueError('Noncontiguous or inconsistent PC mesh triangle/index range')
        next_index += count
    if next_index != len(indices):
        raise ValueError('PC mesh index ranges do not span the index buffer')

    mapping = _candidate_assignments(vertex_blobs, records, indices)
    totals = Counter()
    max_bbox_error = 0.0
    max_normal_error = 0.0
    max_tangent_error = 0.0
    max_tangent_dot = 0.0
    for buffer_id, begin, end, stride in mapping:
        blob = vertex_blobs[buffer_id]
        data = memoryview(blob)[filler_size(blob):]
        count = len(data)//stride
        totals[f'vertex_buffers_stride_{stride}'] += 1
        totals[f'vertices_stride_{stride}'] += count
        values = []
        for pos in range(0, len(data), stride):
            position = struct.unpack_from('<3f', data, pos + POSITION_OFFSET)
            normal = struct.unpack_from('<3f', data, pos + NORMAL_OFFSET)
            uv = struct.unpack_from('<2f', data, pos + UV_OFFSET)
            if not all(math.isfinite(v) for v in (*position, *normal, *uv)):
                raise ValueError('Nonfinite PC vertex position, normal or UV')
            error = abs(sum(n*n for n in normal) - 1.0)
            max_normal_error = max(max_normal_error, error)
            if error >= 0.01:
                raise ValueError('PC normal is not approximately unit length')
            if stride == 52:
                tangent = struct.unpack_from('<3f', data, pos + TANGENT_OFFSET)
                handedness = struct.unpack_from('<f', data, pos + HAND_OFFSET)[0]
                if all(math.isnan(v) for v in tangent) and handedness == 0.0:
                    # Original Carbon PC has rare explicit all-NaN/zero tangent
                    # sentinels; preserve them, do not normalize or synthesize.
                    totals['tangent_nan_zero_sign_sentinels'] += 1
                else:
                    if not all(math.isfinite(v) for v in tangent) or handedness not in (-1.0, 1.0):
                        raise ValueError('Invalid PC tangent or tangent-sign candidate')
                    tangent_error = abs(sum(v*v for v in tangent) - 1.0)
                    tangent_dot = abs(sum(normal[i]*tangent[i] for i in range(3)))
                    max_tangent_error = max(max_tangent_error, tangent_error)
                    max_tangent_dot = max(max_tangent_dot, tangent_dot)
                    if tangent_error >= 0.01 or tangent_dot >= 0.01:
                        raise ValueError('PC tangent is not unit/perpendicular to normal')
                    totals[f'tangent_sign_{int(handedness)}'] += 1
            values.append(position)
        local_start = 0
        for j in range(begin, end):
            nverts = struct.unpack_from('<I', records[j], 0x40)[0]
            vertices = values[local_start:local_start+nverts]
            if len(vertices) != nverts:
                raise ValueError('PC mesh vertex span exceeds assigned buffer')
            local_start += nverts
            bbox = struct.unpack_from('<6f', records[j], 0)
            if not all(math.isfinite(v) for v in bbox):
                raise ValueError('Nonfinite PC mesh bounding box')
            err = max(*(abs(min(v[k] for v in vertices) - bbox[k]) for k in range(3)),
                      *(abs(max(v[k] for v in vertices) - bbox[k+3]) for k in range(3)))
            max_bbox_error = max(max_bbox_error, err)
            if err >= 0.1:
                raise ValueError('PC mesh vertex coordinates disagree with record bounds')
            totals['bounded_mesh_records'] += 1
        if local_start != count:
            raise ValueError('Vertex-buffer mapping leaves unassigned vertices')
    if totals['bounded_mesh_records'] != len(records):
        raise ValueError('Not every mesh record was checked')
    return {'mesh_records':len(records), 'triangle_indices':len(indices),
            'triangle_count':len(indices)//3, 'vertex_buffers':len(vertex_blobs),
            'unique_buffer_to_mesh_assignment':True,
            'every_index_within_its_mesh_vertex_span':True,
            'all_positions_and_uv_finite':True,
            'all_normals_unit':True,
            'all_tangents_unit_and_perpendicular':True,
            'mesh_bbox_max_error':max_bbox_error,
            'normal_squared_length_max_error':max_normal_error,
            'tangent_squared_length_max_error':max_tangent_error,
            'tangent_orthogonality_max_dot':max_tangent_dot,
            **dict(totals)}


def audit_pc_sections(volumes, section_ids=(141, 142)):
    source = SplitZip(volumes)
    scenes, _ = read_rb(source, 'L5')
    stream_rows, _, _ = read_small(source, 'L5', 'RB')
    name = 'TRACKS/STREAML5RB.BUN'
    if source.entries[name][4] > MAX_REGION:
        raise ValueError('RB original stream exceeds inspection bound')
    stream = source.read(name, limit=MAX_REGION)
    report = {}
    for section in section_ids:
        if section not in scenes or section not in stream_rows:
            raise ValueError('Selected scene lacks authenticated stream and scenery root')
        offset, size = struct.unpack_from('<II', stream_rows[section], 0x14)
        data = stream[offset:offset+size]
        cursor = 0
        summaries = []
        while True:
            start = data.find(struct.pack('<I', GEOM), cursor)
            if start < 0:
                break
            cursor = start + 4
            if start % 4 or start+8 > len(data):
                continue
            length = struct.unpack_from('<I', data, start+4)[0]
            if length > len(data)-start-8:
                continue
            frame = data[start:start+8+length]
            try:
                parse_geometry_root(frame)
            except ValueError:
                continue
            for cid, raw_solid in list(read_chunks(frame, 16, len(frame)))[1:]:
                if cid != SOLID_ROOT:
                    raise ValueError('Non-solid in previously validated PC geometry pack')
                h, platform, _, _ = parse_solid(raw_solid)
                if platform != PLATFORM_PC:
                    raise ValueError('Non-PC platform found inside PC geometry pack')
                solid_children = list(read_chunks(raw_solid, 0, len(raw_solid)))
                platform_bytes = solid_children[-1][1]
                platform_children = list(read_chunks(platform_bytes, 0, len(platform_bytes)))
                summaries.append(inspect_pc_solid(platform_children))
            cursor = start+8+length
        if not summaries:
            raise ValueError('No validated PC geometry resources in selected section')
        totals = Counter()
        for result in summaries:
            for key, value in result.items():
                if isinstance(value, int) and not isinstance(value, bool):
                    totals[key] += value
        report[str(section)] = {'solid_resources':len(summaries),
                                **dict(sorted(totals.items())),
                                'all_solids_unique_vertex_buffer_mapping':True,
                                'all_solids_validated_mesh_bboxes':True}
    return {'sections':report,
            'scope':('Carbon PC original RB control sections only. Candidate decoded '
                     '36/52 byte vertex formats validated against native index ranges, '
                     'bounded boxes, normal and tangent geometry. No full PS2↔PC '
                     'coordinate/UV equality, normals/texture mapping, PC mesh writer, '
                     'runtime rendering or Undercover import is demonstrated.')}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--pc-volumes', type=Path, nargs='+', required=True)
    a = p.parse_args()
    print(json.dumps(audit_pc_sections(a.pc_volumes), indent=2))


if __name__ == '__main__':
    main()
