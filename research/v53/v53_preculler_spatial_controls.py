#!/usr/bin/env python3
"""V53: source-gated exploratory spatial/preculler-mask correlation audit.

READ-ONLY. Never interprets Wii mask bits as decoded visibility rules;
never establishes Carbon PC serialization, runtime, or safe modification.
Uses no third-party dependencies. A root's expected hash is an integrity
check; known provenance is restricted to the independently pinned Wii fixture.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import itertools
import json
import math
from pathlib import Path
import random
import struct
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'v50'))
import v50_scenery_index_crosscheck as v50

KNOWN_WII_SHA = v50.KNOWN_WII_SHA256
MASK_PREFIX = 68
PRECULL_STRIDE = 128
INSTANCE_STRIDE = 96


def rank_average(values: list[float]) -> list[float]:
    """Ranks are 1-based, with midranks for ties; stable ordering not assumed."""
    result=[0.] * len(values)
    ordered=sorted(range(len(values)), key=lambda k: values[k])
    j=0
    while j < len(ordered):
        end=j+1
        while end<len(ordered) and values[ordered[end]]==values[ordered[j]]:
            end+=1
        average=(j+1+end)/2
        for k in ordered[j:end]: result[k]=average
        j=end
    return result


def pearson(x: list[float], y: list[float]) -> float | None:
    if len(x)!=len(y) or len(x)<3:
        return None
    mx=sum(x)/len(x); my=sum(y)/len(y)
    xx=[v-mx for v in x]; yy=[v-my for v in y]
    vx=sum(v*v for v in xx); vy=sum(v*v for v in yy)
    if vx==0 or vy==0: return None
    return sum(a*b for a,b in zip(xx,yy)) / math.sqrt(vx*vy)


def spearman(x: list[float],y: list[float]) -> float | None:
    return pearson(rank_average(x), rank_average(y))


def bits_lsb(data: bytes) -> frozenset[int]:
    return frozenset(i*8 + k for i,b in enumerate(data) for k in range(8) if b & (1<<k))


def jaccard(x: frozenset[int],y: frozenset[int]) -> float:
    u=x|y
    return len(x&y)/len(u) if u else 1.


def read_instances(root:bytes,children:dict) -> list[dict]:
    start,payload=children[v50.INSTANCE]
    pad=(-start)&15
    if len(payload)<pad or (len(payload)-pad)%INSTANCE_STRIDE:
        raise v50.EvidenceError('Source instance payload does not fit candidate aligned 96-byte rows')
    rows=[]
    for idx in range((len(payload)-pad)//INSTANCE_STRIDE):
        base=pad+idx*INSTANCE_STRIDE
        minimum=struct.unpack_from('<3f',payload,base)
        maximum=struct.unpack_from('<3f',payload,base+16)
        xyz=struct.unpack_from('<3f',payload,base+32)
        flags=struct.unpack_from('<I',payload,base+12)[0]
        preculler=struct.unpack_from('<h',payload,base+28)[0]
        info=struct.unpack_from('<h',payload,base+84)[0]
        if not all(math.isfinite(a) for a in minimum+maximum+xyz):
            raise v50.EvidenceError('Nonfinite position or bounding box')
        if any(a>b for a,b in zip(minimum,maximum)):
            raise v50.EvidenceError('Inverted bounding box')
        midpoint=tuple((a+b)/2 for a,b in zip(minimum,maximum))
        rows.append({'slot':idx,'xyz':xyz,'aabb_midpoint':midpoint,
                     'zero_position':xyz==(0.,0.,0.),'flags':flags,
                     'preculler':preculler,'info':info})
    return rows


def candidate_masks(children:dict) -> list[frozenset[int]]:
    payload=children[v50.PRECULLER][1]
    if not payload or len(payload)%PRECULL_STRIDE:
        raise v50.EvidenceError('Candidate preculler bytes not divisible by 128')
    return [bits_lsb(payload[start:start+MASK_PREFIX]) for start in range(0,len(payload),PRECULL_STRIDE)]


def centroids(rows:list[dict],ids:list[int], *, mode:str) -> dict[int,tuple[float,float,float]]:
    if mode not in ('raw_position','aabb_proxy'):
        raise v50.EvidenceError('Unknown location strategy')
    points={}
    for i in ids:
        members=[r for r in rows if r['preculler']==i]
        if not members:
            raise v50.EvidenceError('Selected block lacks referencing instances')
        coords=[r['aabb_midpoint'] if mode=='aabb_proxy' and r['zero_position'] else r['xyz'] for r in members]
        points[i]=tuple(sum(p[k] for p in coords)/len(coords) for k in range(3))
    return points


def paired_statistics(ids:list[int],locations:dict,masks:list[frozenset[int]], *,
                      drop_common:bool=False, permutations:int=0, seed:int=533):
    """Mantel-style label permutation: permute entire masks, not independent pairs.

    This is an EXPLORATORY single-scene null; avoids pseudoreplicate pairwise
    p-values but cannot validate real engine visibility or generalize scenes.
    """
    if permutations<0 or permutations>100000:raise v50.EvidenceError('Permutation count out of range')
    if len(ids)<3:raise v50.EvidenceError('At least 3 distinct candidate blocks required')
    if len(set(ids))!=len(ids):raise v50.EvidenceError('Repeated candidate block identifiers')
    if any(i<0 or i>=len(masks) for i in ids):raise v50.EvidenceError('Mask index invalid')
    if drop_common:
        shared=set.intersection(*(set(masks[i]) for i in ids))
        candidate={i:frozenset(masks[i]-shared) for i in ids}
    else:
        shared=set()
        candidate={i:masks[i] for i in ids}
    pair_indexes=list(itertools.combinations(range(len(ids)),2))
    distance=[math.dist(locations[ids[a]],locations[ids[b]]) for a,b in pair_indexes]
    mask_matrix=[[1.] * len(ids) for _ in ids]
    for a,b in pair_indexes:
        v=jaccard(candidate[ids[a]],candidate[ids[b]])
        mask_matrix[a][b]=v;mask_matrix[b][a]=v
    similarity=[mask_matrix[a][b] for a,b in pair_indexes]
    observed=spearman(distance,similarity)
    if observed is None:raise v50.EvidenceError('Undefined spatial/mask rank correlation')
    # Pair values are relabeled, not changed: their rank distribution and
    # denominator are invariant under an entire-node label permutation.
    # Precompute rank matrix to avoid sorting inside the Monte Carlo loop.
    d_rank=rank_average(distance)
    s_rank=rank_average(similarity)
    rmat=[[0.] * len(ids) for _ in ids]
    for (a,b),rank in zip(pair_indexes,s_rank):rmat[a][b]=rmat[b][a]=rank
    d_mean=sum(d_rank)/len(d_rank);s_mean=sum(s_rank)/len(s_rank)
    d_center=[x-d_mean for x in d_rank]
    denom=math.sqrt(sum(x*x for x in d_center)*sum((v-s_mean)**2 for v in s_rank))
    if denom==0:raise v50.EvidenceError('Undefined rank-permutation correlation')
    rng=random.Random(seed);extreme=0
    for _ in range(permutations):
        labels=list(range(len(ids)));rng.shuffle(labels)
        trial=(sum(d_center[k]*(rmat[labels[a]][labels[b]]-s_mean)
                   for k,(a,b) in enumerate(pair_indexes))/denom)
        if trial<=observed+1e-12:extreme+=1
    return {
        'blocks_compared':len(ids),'induced_pairs_not_independent':len(pair_indexes),
        'spearman_distance_vs_similarity':observed,
        'pearson_distance_vs_similarity':pearson(distance,similarity),
        'similarity_excludes_shared_bits':drop_common,
        'shared_bit_positions_removed':len(shared),
        'spatial_distance_min':min(distance),'spatial_distance_max':max(distance),
        'mask_jaccard_min':min(similarity),'mask_jaccard_max':max(similarity),
        'label_permutation':{
            'permutations':permutations,'seed':seed,
            'one_sided_negative_extreme_count':extreme,
            'one_sided_p_plus_one':(extreme+1)/(permutations+1) if permutations else None,
            'null':'uniform relabeling of complete candidate masks among fixed spatial points',
            'interpretation':'exploratory_single_scene_only_not_independent_validation'
        }
    }


def audit(root:bytes,*,expected_sha256:str|None=None,permutations:int=1999,seed:int=533)->dict:
    h=v50.sha256(root)
    if expected_sha256 is not None and h!=expected_sha256.lower():
        raise v50.EvidenceError('Exact source SHA-256 mismatch')
    ch=v50.children_of(root)
    rows=read_instances(root,ch)
    masks=candidate_masks(ch)
    histogram=Counter(x['preculler'] for x in rows)
    invalid=sorted(i for i in histogram if i<0 or i>=len(masks))
    if invalid:raise v50.EvidenceError('Source candidate block references invalid index')
    active=sorted(i for i in histogram if masks[i])
    excluded=sorted(i for i in active if any(r['zero_position'] for r in rows if r['preculler']==i))
    stable=[i for i in active if i not in excluded]
    raw=centroids(rows,active,mode='raw_position')
    proxy=centroids(rows,active,mode='aabb_proxy')
    restricted=centroids(rows,stable,mode='raw_position')
    info6=sorted(i for i in stable if all(r['info']==6 for r in rows if r['preculler']==i))
    analyses={
        'all_raw_source_positions':paired_statistics(active,raw,masks,permutations=permutations,seed=seed),
        'exclude_zero_position_groups':paired_statistics(stable,restricted,masks,permutations=permutations,seed=seed),
        'aabb_center_proxy_for_zero_position_groups':paired_statistics(active,proxy,masks,permutations=permutations,seed=seed),
        'exclude_zero_positions_and_shared_mask_bits':paired_statistics(stable,restricted,masks,drop_common=True,permutations=permutations,seed=seed),
        'source_scenery_info_6_only':paired_statistics(info6,restricted,masks,permutations=permutations,seed=seed),
    }
    return {
        'schema':'v53-exploratory-preculler-spatial-controls-v1',
        'source_root_sha256':h,
        'source_provenance':'exact_original_Wii_RedBuilding' if h==KNOWN_WII_SHA else 'unknown',
        'guard_applied':expected_sha256 is not None,
        'instance_count_candidate_96':len(rows),
        'candidate_128_byte_preculler_blocks':len(masks),
        'zero_position_instance_slots':[r['slot'] for r in rows if r['zero_position']],
        'zero_position_instance_aabb_midpoints':{str(r['slot']):list(r['aabb_midpoint']) for r in rows if r['zero_position']},
        'zero_position_instance_flags':{str(r['slot']):f'0x{r["flags"]:08X}' for r in rows if r['zero_position']},
        'zero_position_block_ids':sorted(set(r['preculler'] for r in rows if r['zero_position'])),
        'nonzero_mask_blocks_with_zero_position_rows':excluded,
        'excluded_group_source_info_6_ids':info6,
        'analysis':analyses,
        'source_note':'nonzero AABBs and zero instance position cannot be treated as a geographic origin; AABB midpoint is exploratory proxy only',
        'previous_v52_far_apart_pair_1_11_valid_geographic_counterexample':False if h==KNOWN_WII_SHA else None,
        'not_visibility_semantics':True,'carbon_pc_serialized_schema_verified':False,
        'in_game_verified':False,'safe_to_install':False,'read_only':True,
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--scene',required=True,type=Path)
    p.add_argument('--expected-root-sha256')
    p.add_argument('--offset',type=lambda s:int(s,0))
    p.add_argument('--permutations',type=int,default=1999)
    p.add_argument('--seed',type=int,default=533)
    p.add_argument('--report',type=Path,required=True)
    a=p.parse_args()
    if a.report.resolve()==a.scene.resolve() or a.report.exists():
        p.error('Output already exists or equals input; refusing to overwrite')
    root=v50.read_root(a.scene,offset=a.offset)
    result=audit(root,expected_sha256=a.expected_root_sha256,permutations=a.permutations,seed=a.seed)
    a.report.parent.mkdir(parents=True,exist_ok=True)
    with a.report.open('x',encoding='utf-8') as out:
        json.dump(result,out,indent=2,sort_keys=True);out.write('\n')
    print('V53 read-only evidence saved:',a.report)

if __name__=='__main__':main()