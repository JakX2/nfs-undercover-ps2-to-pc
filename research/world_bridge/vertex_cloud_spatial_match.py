"""Pure-Python, bounded bidirectional approximate vertex-cloud validation.

This is a geometric *position* check only. Coincident vertices are not evidence
of equal triangles, normals, texture coordinates or material assignments.
"""
from collections import defaultdict
from itertools import product
import math

NEIGHBORS = tuple(product((-1, 0, 1), repeat=3))


def directional_nearest(source, target, tolerance=0.01):
    """For each source position, find a witness target within a spatial grid.

    A target within Euclidean tolerance must be in the same or one adjacent
    cell along every axis. Returns aggregate existence and witness distances.
    """
    if not isinstance(tolerance, (int, float)) or not math.isfinite(tolerance) or tolerance <= 0:
        raise ValueError('Tolerance must be a positive finite distance')
    if len(source) == 0 or len(target) == 0:
        raise ValueError('Both geometry clouds must be nonempty')
    target_cells = defaultdict(list)

    def key(position):
        if len(position) != 3 or not all(math.isfinite(float(v)) for v in position):
            raise ValueError('Nonfinite or non-XYZ source position')
        return tuple(math.floor(float(v)/tolerance) for v in position)

    for position in target:
        target_cells[key(position)].append(tuple(float(v) for v in position))
    max_witness_sq = 0.0
    unmatched = 0
    limit_sq = tolerance*tolerance
    for position in source:
        k = key(position)
        witness = None
        x, y, z = (float(v) for v in position)
        for dx,dy,dz in NEIGHBORS:
            for u,v,w in target_cells.get((k[0]+dx,k[1]+dy,k[2]+dz), ()):
                d2 = (x-u)**2 + (y-v)**2 + (z-w)**2
                if d2 <= limit_sq:
                    witness = d2
                    break
            if witness is not None:
                break
        if witness is None:
            unmatched += 1
        elif witness > max_witness_sq:
            max_witness_sq = witness
    return {'points_checked':len(source), 'unmatched_within_tolerance':unmatched,
            'max_matching_witness_distance':math.sqrt(max_witness_sq),
            'all_points_have_nearby_targets':unmatched == 0}


def bidirectional_cloud_match(pc_positions, ps2_positions, tolerance=0.01):
    a = directional_nearest(pc_positions, ps2_positions, tolerance)
    b = directional_nearest(ps2_positions, pc_positions, tolerance)
    return {'pc_vertices':len(pc_positions),
            'ps2_vertex_occurrences':len(ps2_positions),
            'tolerance':tolerance,
            'pc_to_ps2':a,
            'ps2_to_pc':b,
            'both_directions_match':a['all_points_have_nearby_targets'] and b['all_points_have_nearby_targets']}
