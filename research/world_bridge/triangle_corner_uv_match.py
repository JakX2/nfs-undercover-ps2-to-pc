"""Source-free face-corner XYZ/UV/texture matching with distinct PC witnesses.

Requires corresponding XYZ and periodic UV values at all three corners of a
single face, under one of six possible corner permutations. Faces must carry the
same LOCAL texture-table index. Only aggregate counts leave this module.

This is not proof of sampler wrap modes, normals, tangent space, or GPU output.
"""
from collections import defaultdict, deque, Counter
from itertools import product
import math

PERMS = ((0, 1, 2), (1, 2, 0), (2, 0, 1),
         (0, 2, 1), (2, 1, 0), (1, 0, 2))
OFFSETS = tuple(product((-1, 0, 1), repeat=3))
MAX_FACES = 250_000
MAX_VERTICES = 1_000_000


def _check(vertices, uv, faces, textures, texture_count):
    if not (0 < len(vertices) <= MAX_VERTICES and len(vertices) == len(uv)):
        raise ValueError('Invalid XYZ/UV arrays')
    if not (0 < len(faces) <= MAX_FACES and len(faces) == len(textures)):
        raise ValueError('Invalid face/texture-label arrays')
    for xyz, st in zip(vertices, uv):
        if (len(xyz) != 3 or len(st) != 2 or
                not all(math.isfinite(float(x)) for x in (*xyz, *st))):
            raise ValueError('Nonfinite XYZ/UV source vertex')
    for tri, texture in zip(faces, textures):
        if len(tri) != 3 or any(type(i) is not int or not 0 <= i < len(vertices) for i in tri):
            raise ValueError('Invalid triangle vertex index')
        if type(texture) is not int or not 0 <= texture < texture_count:
            raise ValueError('Out-of-range triangle texture index')


def _centroid_cell(tri, xyz, t):
    return tuple(math.floor(sum(float(xyz[i][k]) for i in tri)/(3*t)) for k in range(3))


def _fit(ptri, pxyz, puv, stri, sxyz, suv, xyz2, uv2):
    """Choose valid face permutation with lowest max XYZ and periodic UV error."""
    best = None
    for perm_id, perm in enumerate(PERMS):
        maxxyz = maxuv = 0.
        needs_wrap = False
        for corner in range(3):
            a = ptri[corner]
            b = stri[perm[corner]]
            dx2 = sum((float(pxyz[a][d]) - float(sxyz[b][d]))**2 for d in range(3))
            if dx2 > xyz2:
                break
            du = [float(puv[a][d]) - float(suv[b][d]) for d in range(2)]
            periodic = [v - round(v) for v in du]
            du2 = sum(v*v for v in periodic)
            if du2 > uv2:
                break
            needs_wrap |= sum(v*v for v in du) > uv2
            maxxyz = max(maxxyz, dx2)
            maxuv = max(maxuv, du2)
        else:
            candidate = (maxxyz, maxuv, int(needs_wrap), int(perm_id >= 3))
            if best is None or candidate < best:
                best = candidate
    return best


def match_faces(pc_xyz, pc_uv, pc_faces, pc_texture,
                ps_xyz, ps_uv, ps_faces, ps_texture,
                texture_count, xyz_tolerance=.01, uv_tolerance=.01):
    """Find a distinct PC face for every PS2 face constrained by XYZ+UV+label.

    Matching is an augmenting-path bipartite assignment, not greedy nearest.
    Returns only aggregate diagnostic counts, with no source triangles or IDs.
    """
    if (type(texture_count) is not int or not 1 <= texture_count <= 127 or
            not all(isinstance(v, (float, int)) and math.isfinite(v) and 0 < v <= .1
                    for v in (xyz_tolerance, uv_tolerance))):
        raise ValueError('Invalid texture-table size or matching tolerances')
    _check(pc_xyz, pc_uv, pc_faces, pc_texture, texture_count)
    _check(ps_xyz, ps_uv, ps_faces, ps_texture, texture_count)

    cells = defaultdict(list)
    for i, (face, texture) in enumerate(zip(pc_faces, pc_texture)):
        cells[(texture, *_centroid_cell(face, pc_xyz, xyz_tolerance))].append(i)

    xyz2, uv2 = xyz_tolerance**2, uv_tolerance**2
    edges = []
    no_options = ambiguous = 0
    for face, texture in zip(ps_faces, ps_texture):
        centroid = _centroid_cell(face, ps_xyz, xyz_tolerance)
        candidates = []
        for dx, dy, dz in OFFSETS:
            for pc_i in cells.get((texture, centroid[0]+dx, centroid[1]+dy, centroid[2]+dz), ()):
                fit = _fit(pc_faces[pc_i], pc_xyz, pc_uv, face, ps_xyz, ps_uv, xyz2, uv2)
                if fit is not None:
                    candidates.append((fit, pc_i))
        candidates.sort()
        edges.append([i for fit, i in candidates])
        no_options += not candidates
        ambiguous += len(candidates) > 1

    # Full augmenting-path matching guarantees no one PC face is reused.
    owner = [-1]*len(pc_faces)
    assigned = [-1]*len(ps_faces)
    for i, choices in enumerate(edges):
        if not choices:
            continue
        pending = deque([i])
        visited = {i}
        parents = {}
        terminal = None
        while pending and terminal is None:
            ps_i = pending.popleft()
            for pc_i in edges[ps_i]:
                if pc_i in parents:
                    continue
                parents[pc_i] = ps_i
                previous = owner[pc_i]
                if previous == -1:
                    terminal = pc_i
                    break
                if previous not in visited:
                    visited.add(previous)
                    pending.append(previous)
        if terminal is not None:
            pc_i = terminal
            while True:
                ps_i = parents[pc_i]
                prior_pc = assigned[ps_i]
                owner[pc_i] = ps_i
                assigned[ps_i] = pc_i
                if prior_pc == -1:
                    break
                pc_i = prior_pc

    stats = Counter()
    max_xyz2 = max_uv2 = 0.
    for ps_i, pc_i in enumerate(assigned):
        if pc_i == -1:
            continue
        fit = _fit(pc_faces[pc_i], pc_xyz, pc_uv,
                   ps_faces[ps_i], ps_xyz, ps_uv, xyz2, uv2)
        if fit is None:
            raise ValueError('Internal inconsistent matched face')
        max_xyz2 = max(max_xyz2, fit[0])
        max_uv2 = max(max_uv2, fit[1])
        stats['faces_requiring_periodic_uv_wrap'] += fit[2]
        stats['odd_corner_permutations'] += fit[3]
    matched = sum(i != -1 for i in assigned)
    return {
        'pc_faces': len(pc_faces), 'ps2_faces': len(ps_faces),
        'ps2_faces_with_no_corner_candidate': no_options,
        'ps2_faces_with_multiple_pc_candidates': ambiguous,
        'ps2_faces_assigned_distinct_pc_faces': matched,
        'unmatched_ps2_faces': len(ps_faces) - matched,
        'unmatched_pc_faces': len(pc_faces) - matched,
        'faces_requiring_periodic_uv_wrap': stats['faces_requiring_periodic_uv_wrap'],
        'odd_corner_permutations_provisional': stats['odd_corner_permutations'],
        'max_xyz_witness_distance': math.sqrt(max_xyz2),
        'max_periodic_uv_witness_distance': math.sqrt(max_uv2),
        'all_ps2_faces_matched': matched == len(ps_faces),
    }
