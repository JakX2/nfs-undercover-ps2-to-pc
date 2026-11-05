"""Dependency-free comparison of ordered 3D triangle geometry, not mesh bytes.

A triangle counts as matching when each of its three vertices can be paired
within the same Euclidean XYZ tolerance, allowing permutations. Winding and
ambiguous candidates are reported separately. The matching is existential:
it is NOT a one-to-one correspondence or equality of triangle multiplicities,
UVs, normals, materials, or texture assignments.
"""
from collections import defaultdict
from itertools import product
import math

CYCLIC = ((0, 1, 2), (1, 2, 0), (2, 0, 1))
REVERSED = ((0, 2, 1), (2, 1, 0), (1, 0, 2))
NEIGHBORS = tuple(product((-1, 0, 1), repeat=3))
MAX_FACES = 2_000_000


def _validate(faces):
    if not 0 < len(faces) <= MAX_FACES:
        raise ValueError('Triangle-face collection must be nonempty and bounded')
    for face in faces:
        if len(face) != 3:
            raise ValueError('Each triangle must have exactly three vertices')
        for position in face:
            if len(position) != 3 or not all(math.isfinite(float(x)) for x in position):
                raise ValueError('Triangle vertex must have three finite XYZ values')


def _key(face, tolerance):
    return tuple(math.floor(sum(p[axis] for p in face) / (3 * tolerance)) for axis in range(3))


def _pair_winding(src, dst, limit_sq):
    """1 if same cyclic order, 2 if opposite, 3 if both due ambiguity."""
    flags = 0
    for permutations, bit in ((CYCLIC, 1), (REVERSED, 2)):
        for perm in permutations:
            if all(sum((src[i][axis] - dst[perm[i]][axis])**2 for axis in range(3)) <= limit_sq
                   for i in range(3)):
                flags |= bit
                break
    return flags


def directional_face_match(source_faces, target_faces, tolerance=0.01):
    """Report geometric face *presence* and possible winding against target."""
    if not isinstance(tolerance, (int, float)) or not math.isfinite(tolerance) or tolerance <= 0:
        raise ValueError('Triangle tolerance must be positive and finite')
    _validate(source_faces)
    _validate(target_faces)
    cells = defaultdict(list)
    for face in target_faces:
        cells[_key(face, tolerance)].append(face)
    stats = {'source_faces': len(source_faces), 'matched_faces': 0,
             'unmatched_faces': 0, 'same_winding_only': 0,
             'reversed_winding_only': 0, 'winding_ambiguous': 0,
             'faces_with_multiple_matching_targets': 0}
    limit_sq = tolerance*tolerance
    for face in source_faces:
        base = _key(face, tolerance)
        flags = 0
        matches = 0
        for dx, dy, dz in NEIGHBORS:
            for other in cells.get((base[0]+dx, base[1]+dy, base[2]+dz), ()):
                new = _pair_winding(face, other, limit_sq)
                if new:
                    flags |= new
                    matches += 1
        if matches == 0:
            stats['unmatched_faces'] += 1
        else:
            stats['matched_faces'] += 1
            if matches > 1:
                stats['faces_with_multiple_matching_targets'] += 1
            if flags == 1:
                stats['same_winding_only'] += 1
            elif flags == 2:
                stats['reversed_winding_only'] += 1
            else:
                stats['winding_ambiguous'] += 1
    return stats


def bidirectional_face_match(pc_faces, ps2_faces, tolerance=0.01):
    """Symmetric geometric presence; not a perfect triangle-multiset bijection."""
    pc_to_ps2 = directional_face_match(pc_faces, ps2_faces, tolerance)
    ps2_to_pc = directional_face_match(ps2_faces, pc_faces, tolerance)
    return {'pc_faces':len(pc_faces), 'ps2_faces':len(ps2_faces),
            'tolerance':tolerance, 'pc_to_ps2':pc_to_ps2, 'ps2_to_pc':ps2_to_pc,
            'all_ps2_faces_have_pc_counterparts':ps2_to_pc['unmatched_faces'] == 0,
            'all_pc_faces_have_ps2_counterparts':pc_to_ps2['unmatched_faces'] == 0,
            'exact_multiplicity_or_material_equality_proven': False}
