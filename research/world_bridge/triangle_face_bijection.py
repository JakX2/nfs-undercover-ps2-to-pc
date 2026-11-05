"""Pure-stdlib, read-only tolerant triangle geometry matching with unique PC witnesses.

Comparison uses corners in 3D with all 6 permutations, *not* an assumed
vertex order, UV layout or material map. It proves a geometric triangle
assignment within tolerance, not a binary-equivalent PC mesh or renderer ABI.
"""
from collections import defaultdict, deque
from itertools import product
import math

NEIGHBORS=tuple(product((-1,0,1),repeat=3))
PERMS=((0,1,2),(1,2,0),(2,0,1),(0,2,1),(2,1,0),(1,0,2))
MAX_TRIANGLES=250000


def _check_positions(positions):
    if not 0 < len(positions) <= 1000000:
        raise ValueError('Empty or excessive vertex cloud')
    for p in positions:
        if len(p)!=3 or not all(math.isfinite(float(q)) for q in p):
            raise ValueError('Invalid 3D vertex coordinate')


def _check_faces(positions, faces):
    if not 0 < len(faces) <= MAX_TRIANGLES:
        raise ValueError('Empty or excessive triangle list')
    n=len(positions)
    for f in faces:
        if len(f)!=3 or any(type(k) is not int or k<0 or k>=n for k in f):
            raise ValueError('Out-of-bounds triangle vertex index')


def _centroid_cell(face, positions, tol):
    pts=(positions[face[0]],positions[face[1]],positions[face[2]])
    return tuple(math.floor((float(pts[0][k])+float(pts[1][k])+float(pts[2][k]))/(3*tol)) for k in range(3))


def _candidate_fit(face_a, pos_a, face_b, pos_b, tol2):
    """Return best (max squared corner error, winding parity) or None.

    Parity is relative to vertex ordering, not necessarily physical normals;
    near-degenerate geometry can legitimately admit both parities.
    """
    a=[pos_a[q] for q in face_a]
    b=[pos_b[q] for q in face_b]
    best=None
    for parity,order in enumerate(PERMS):
        error=0.0
        for k in range(3):
            v,w=a[k],b[order[k]]
            d2=sum((float(v[c])-float(w[c]))**2 for c in range(3))
            if d2>tol2:
                break
            error=max(error,d2)
        else:
            if best is None or error<best[0]:
                best=(error,0 if parity<3 else 1)
    return best


def match_triangle_faces(pc_positions, pc_triangles, ps2_positions, ps2_triangles, tolerance=.01):
    """Assign each PS2 triangle to a distinct nearby PC triangle.

    Built via spatial centroid cells followed by a bounded alternating-path
    matching (no recursion/SciPy). If no full matching exists, report unmatched
    counts instead of assuming identical topology. Only aggregates returned.
    """
    if not isinstance(tolerance,(int,float)) or not math.isfinite(tolerance) or not 0<tolerance<=1:
        raise ValueError('Invalid triangle matching tolerance')
    _check_positions(pc_positions);_check_positions(ps2_positions)
    _check_faces(pc_positions,pc_triangles);_check_faces(ps2_positions,ps2_triangles)
    tol2=tolerance*tolerance
    grid=defaultdict(list)
    for pc_id,face in enumerate(pc_triangles):
        grid[_centroid_cell(face,pc_positions,tolerance)].append(pc_id)

    neighbors=[]
    alternatives=0
    without_candidates=0
    for face in ps2_triangles:
        k=_centroid_cell(face,ps2_positions,tolerance)
        found=[]
        for dx,dy,dz in NEIGHBORS:
            for pc_id in grid.get((k[0]+dx,k[1]+dy,k[2]+dz),()):
                fit=_candidate_fit(pc_triangles[pc_id],pc_positions,face,ps2_positions,tol2)
                if fit is not None:
                    found.append((fit[0],pc_id))
        found.sort()
        candidates=[id for _,id in found]
        neighbors.append(candidates)
        alternatives+=len(candidates)>1
        without_candidates+=not candidates

    # Incremental augmenting paths, iteration only, no recursion depth hazard.
    pc_owner=[-1]*len(pc_triangles)
    ps_match=[-1]*len(ps2_triangles)
    for ps_id, choices in enumerate(neighbors):
        if not choices:
            continue
        queue=deque([ps_id]);seen_ps={ps_id};parent_pc={};endpoint=-1
        while queue and endpoint<0:
            owner=queue.popleft()
            for pc_id in neighbors[owner]:
                if pc_id in parent_pc:
                    continue
                parent_pc[pc_id]=owner
                prior=pc_owner[pc_id]
                if prior<0:
                    endpoint=pc_id
                    break
                if prior not in seen_ps:
                    seen_ps.add(prior)
                    queue.append(prior)
        if endpoint>=0:
            current=endpoint
            while True:
                prior_ps=parent_pc[current]
                previous_pc=ps_match[prior_ps]
                pc_owner[current]=prior_ps
                ps_match[prior_ps]=current
                if previous_pc<0:
                    break
                current=previous_pc

    matched=sum(x>=0 for x in ps_match)
    aligned=opposite=0
    witness_max2=0.
    for ps_id,pc_id in enumerate(ps_match):
        if pc_id<0:
            continue
        fit=_candidate_fit(pc_triangles[pc_id],pc_positions,ps2_triangles[ps_id],ps2_positions,tol2)
        if fit is None:
            raise ValueError('Internal invalid matched triangle witness')
        witness_max2=max(witness_max2,fit[0]);aligned+=fit[1]==0;opposite+=fit[1]==1
    return {'pc_triangles':len(pc_triangles),'ps2_triangles':len(ps2_triangles),
            'ps2_triangles_with_no_geometric_candidate':without_candidates,
            'ps2_triangles_with_multiple_pc_candidates':alternatives,
            'ps2_triangles_uniquely_assigned':matched,
            'ps2_triangles_not_assigned':len(ps2_triangles)-matched,
            'unused_pc_triangles_after_matching':len(pc_triangles)-matched,
            'relative_permutation_even':aligned,'relative_permutation_odd':opposite,
            'max_corner_witness_distance':math.sqrt(witness_max2),
            'every_ps2_triangle_has_distinct_pc_match':matched==len(ps2_triangles),
            'equal_triangle_counts':len(pc_triangles)==len(ps2_triangles)}
