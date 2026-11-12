"""Read-only pure-Python two-way XYZ/UV source-match predicates.

Allows integer UV tile offsets, but requires a real XYZ-nearby vertex and
UV-nearby coordinates. A per-vertex witness does not prove per-face material,
texture ID or winding compatibility, especially at seams.
"""
from collections import defaultdict
from itertools import product
import math

NEIGHBORS=tuple(product((-1,0,1),repeat=3))
MAX_VERTICES=1000000


def _validate(points, uvs):
    if len(points)!=len(uvs) or not 0<len(points)<=MAX_VERTICES:
        raise ValueError('XYZ/UV vertex counts disagree or are empty/excessive')
    for p,uv in zip(points,uvs):
        if len(p)!=3 or len(uv)!=2 or not all(math.isfinite(float(v)) for v in tuple(p)+tuple(uv)):
            raise ValueError('Nonfinite or invalid XYZ/UV coordinates')


def _cell(p,tol):
    return tuple(math.floor(float(v)/tol) for v in p)


def _distance2(p,q):
    return sum((float(p[i])-float(q[i]))**2 for i in range(len(p)))


def directional_xyz_uv(source_xyz, source_uv, target_xyz, target_uv, xyz_tol=.01, uv_tol=.01):
    if any(not isinstance(t,(float,int)) or not math.isfinite(t) or not 0<t<=0.1
           for t in (xyz_tol,uv_tol)):
        raise ValueError('Invalid XYZ or UV tolerance')
    _validate(source_xyz,source_uv);_validate(target_xyz,target_uv)
    cells=defaultdict(list)
    for k,p in enumerate(target_xyz):
        cells[_cell(p,xyz_tol)].append(k)
    no_xyz=no_uv=rescued=0
    max_uv_witness_sq=0.
    max_xyz_witness_sq=0.
    for i,p in enumerate(source_xyz):
        cell=_cell(p,xyz_tol)
        best=None
        xyz_found=False
        raw_match=False
        for dx,dy,dz in NEIGHBORS:
            for j in cells.get((cell[0]+dx,cell[1]+dy,cell[2]+dz),()):
                xyz_err=_distance2(p,target_xyz[j])
                if xyz_err>xyz_tol*xyz_tol:
                    continue
                xyz_found=True
                uv_err_raw=_distance2(source_uv[i],target_uv[j])
                raw_match|=uv_err_raw<=uv_tol*uv_tol
                uv_delta=[float(source_uv[i][c])-float(target_uv[j][c]) for c in range(2)]
                uv_wrapped=[v-round(v) for v in uv_delta]
                uv_err=sum(v*v for v in uv_wrapped)
                if uv_err <= uv_tol*uv_tol and (best is None or uv_err<best[0]):
                    best=(uv_err,xyz_err)
        if not xyz_found:
            no_xyz+=1
        elif best is None:
            no_uv+=1
        else:
            rescued+=not raw_match
            max_uv_witness_sq=max(max_uv_witness_sq,best[0])
            max_xyz_witness_sq=max(max_xyz_witness_sq,best[1])
    return {'vertex_records':len(source_xyz),
            'missing_xyz_witnesses':no_xyz,
            'missing_periodic_uv_witnesses':no_uv,
            'integer_uv_tile_offset_rescues':rescued,
            'max_periodic_uv_witness_distance':math.sqrt(max_uv_witness_sq),
            'max_xyz_witness_distance':math.sqrt(max_xyz_witness_sq),
            'all_vertices_have_xyz_and_periodic_uv_match':no_xyz+no_uv==0}


def bidirectional_xyz_uv(pc_xyz,pc_uv,ps2_xyz,ps2_uv,xyz_tol=.01,uv_tol=.01):
    pc=directional_xyz_uv(pc_xyz,pc_uv,ps2_xyz,ps2_uv,xyz_tol,uv_tol)
    ps2=directional_xyz_uv(ps2_xyz,ps2_uv,pc_xyz,pc_uv,xyz_tol,uv_tol)
    return {'pc_to_ps2':pc,'ps2_to_pc':ps2,
            'matches_both_directions':pc['all_vertices_have_xyz_and_periodic_uv_match'] and ps2['all_vertices_have_xyz_and_periodic_uv_match']}
