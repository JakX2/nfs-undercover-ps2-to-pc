#!/usr/bin/env python3
"""V54: source-gated, read-only sensitivity tests for Wii 0x34107 mask correlations.

A one-scene group-constrained permutation and leave-one-block-out audit is NOT
independent scene validation, a visibility decoder, or proof of Carbon PC ABI.
No game files are written or patched.
"""
from __future__ import annotations
import argparse
import hashlib
import itertools
import json
import math
from pathlib import Path
import random
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'v53'))
import v53_preculler_spatial_controls as v53
v50 = v53.v50
KNOWN_WII_SHA = v53.KNOWN_WII_SHA


def _validate(ids, positions, masks):
    if len(ids)<3 or len(ids)!=len(set(ids)):
        raise v50.EvidenceError('Expected three or more distinct candidate blocks')
    if any(i<0 or i>=len(masks) or i not in positions for i in ids):
        raise v50.EvidenceError('Candidate block or world-position index absent')
    if any(len(positions[i])!=3 or not all(math.isfinite(x) for x in positions[i]) for i in ids):
        raise v50.EvidenceError('Invalid candidate world positions')


def _prepare(ids, positions, masks, *, remove_shared_bits=False):
    _validate(ids, positions, masks)
    if remove_shared_bits:
        common=set.intersection(*(set(masks[i]) for i in ids))
    else:
        common=set()
    mask_list=[frozenset(masks[i]-common) for i in ids]
    pairs=list(itertools.combinations(range(len(ids)),2))
    distance=[math.dist(positions[ids[a]],positions[ids[b]]) for a,b in pairs]
    similarity=[v53.jaccard(mask_list[a],mask_list[b]) for a,b in pairs]
    rho=v53.spearman(distance,similarity)
    if rho is None:
        raise v50.EvidenceError('Undefined correlation: constant distances or masks')
    return mask_list, pairs, distance, similarity, rho, len(common)


def leave_one_block_out(ids, positions, masks, *, remove_shared_bits=False):
    _validate(ids, positions, masks)
    if len(ids)<4:
        raise v50.EvidenceError('Leave-one-out requires 4+ blocks')
    _,_,_,_,baseline,shared=_prepare(ids, positions, masks,remove_shared_bits=remove_shared_bits)
    influence=[]
    for block_id in ids:
        remaining=[i for i in ids if i!=block_id]
        # Baseline shared bits must be computed on same full sample and then
        # kept fixed for jackknife, avoiding change of the feature definition.
        if remove_shared_bits:
            common=set.intersection(*(set(masks[i]) for i in ids))
            reduced=[frozenset(x-common) for x in masks]
            _,_,_,_,rho,_=_prepare(remaining,positions,reduced,remove_shared_bits=False)
        else:
            _,_,_,_,rho,_=_prepare(remaining,positions,masks)
        influence.append({'removed_candidate_block':block_id,'rho':rho,
                          'delta_from_all_blocks':rho-baseline})
    lo=min(influence,key=lambda x:x['rho'])
    hi=max(influence,key=lambda x:x['rho'])
    return {'baseline_rho':baseline,'n_blocks':len(ids),'pairwise_observations_dependent':True,
            'feature_shared_bits_removed_in_baseline':shared,
            'leave_one_out_rho_min':lo['rho'],'leave_one_out_rho_max':hi['rho'],
            'min_rho_removed_block':lo['removed_candidate_block'],
            'max_rho_removed_block':hi['removed_candidate_block'],
            'all_jackknife_rhos_negative':all(x['rho']<0 for x in influence),
            'influence':influence,
            'interpretation':'single_scene_sensitivity_not_independent_replication'}


def within_group_permutation(ids, positions, masks, movable_ids, *,
                             permutations=9999,seed=540,remove_shared_bits=False):
    """Shuffle *only* candidate labels within predeclared source-info cohort.

    Fix other masks. This null tests whether the chosen cohort's spatial
    assignment explains any signal beyond between-cohort structure, NOT
    independence across scenes or proof of a preculling runtime algorithm.
    """
    if not (0<=permutations<=100000):
        raise v50.EvidenceError('Permutation count outside 0..100000')
    if len(set(movable_ids))!=len(movable_ids) or len(movable_ids)<3 or any(x not in ids for x in movable_ids):
        raise v50.EvidenceError('Need 3+ distinct movable blocks from the comparison')
    _m,pairs,dist,sim,observed,shared=_prepare(ids,positions,masks,remove_shared_bits=remove_shared_bits)
    ranks_dist=v53.rank_average(dist)
    ranks_sim=v53.rank_average(sim)
    n=len(ids)
    matrix=[[0.]*n for _ in range(n)]
    for (i,j),rank in zip(pairs,ranks_sim):
        matrix[i][j]=matrix[j][i]=rank
    mean_d=sum(ranks_dist)/len(ranks_dist)
    mean_s=sum(ranks_sim)/len(ranks_sim)
    dc=[v-mean_d for v in ranks_dist]
    denominator=math.sqrt(sum(x*x for x in dc)*sum((x-mean_s)**2 for x in ranks_sim))
    if denominator==0:
        raise v50.EvidenceError('Undefined label-rank variance')
    rng=random.Random(seed)
    indices=[ids.index(i) for i in movable_ids]
    extreme=0
    for _ in range(permutations):
        candidate=list(range(n))
        values=indices[:]
        rng.shuffle(values)
        for src,dst in zip(indices,values):candidate[src]=dst
        rho=sum(dc[k]*(matrix[candidate[a]][candidate[b]]-mean_s) for k,(a,b) in enumerate(pairs))/denominator
        if rho<=observed+1e-12:
            extreme+=1
    return {'rho':observed,'blocks_compared':n,'cohort_movable_block_count':len(movable_ids),
            'other_candidate_mask_labels_fixed':n-len(movable_ids),
            'source_info_cohort_permutation_count':permutations,'seed':seed,
            'one_sided_extreme_count':extreme,
            'one_sided_p_plus_one':(extreme+1)/(permutations+1) if permutations else None,
            'common_mask_bits_removed':shared,
            'null':'shuffle whole masks only within the predeclared source-info cohort; freeze all other masks',
            'interpretation':'single_scene_conditional_exploratory_not_causal_or_PC_loader_proof'}


def source_uniqueness_gate(primary:bytes, additional:list[bytes], expected_hashes:list[str]):
    """Guard against mistaking repeated copies for independent original scenes.

    Different hashes alone never authenticate a game extract as original.
    """
    if len(additional)!=len(expected_hashes):
        raise v50.EvidenceError('One independently supplied expected SHA-256 required per additional input')
    digests=[v50.sha256(primary)]
    for data,h in zip(additional,expected_hashes):
        if len(h)!=64 or any(c not in '0123456789abcdefABCDEF' for c in h):
            raise v50.EvidenceError('Expected SHA-256 malformed')
        got=v50.sha256(data)
        if got!=h.lower():
            raise v50.EvidenceError('Additional source SHA-256 mismatch')
        digests.append(got)
    return {'sources_submitted':len(digests),'distinct_root_sha256s':len(set(digests)),
            'duplicate_input_roots_found':len(set(digests))!=len(digests),
            'at_least_two_distinct_roots':len(set(digests))>=2,
            'independent_original_scenes_authenticated':False,
            'different_hashes_do_not_authenticate_game_provenance':True,
            'new_scene_layout_validated':False,'Carbon_PC_runtime_compatible':False}


def audit(root:bytes, *, expected_sha256:str|None=None, permutations=9999,seed=540,
          additional_roots:list[bytes]|None=None,additional_hashes:list[str]|None=None):
    digest=v50.sha256(root)
    if expected_sha256 is not None and digest!=expected_sha256.lower():
        raise v50.EvidenceError('Primary source SHA-256 mismatch')
    child=v50.children_of(root)
    rows=v53.read_instances(root,child)
    masks=v53.candidate_masks(child)
    active=sorted({r['preculler'] for r in rows if r['preculler']>=0 and r['preculler']<len(masks) and masks[r['preculler']]})
    if any(r['preculler']<0 or r['preculler']>=len(masks) for r in rows):
        raise v50.EvidenceError('Candidate source index outside block array')
    nonzero=[i for i in active if not any(r['zero_position'] for r in rows if r['preculler']==i)]
    groups=sorted(i for i in nonzero if all(r['info']==6 for r in rows if r['preculler']==i))
    loc=v53.centroids(rows,nonzero,mode='raw_position')
    if len(groups)<3:
        raise v50.EvidenceError('Insufficient source-info-6 cohort for constrained test')
    return {
        'schema':'v54-single-scene-robustness-and-source-uniqueness-v1',
        'primary_source_sha256':digest,
        'source_authentication':'known_original_Wii_scene' if digest==KNOWN_WII_SHA else 'unknown',
        'input_sha_guard_applied':expected_sha256 is not None,
        'candidate_nonzero_position_blocks':len(nonzero),'cohort_info6_blocks':len(groups),
        'group_locked_permutation':within_group_permutation(nonzero,loc,masks,groups,
                                          permutations=permutations,seed=seed),
        'group_locked_permutation_without_shared_bits':within_group_permutation(nonzero,loc,masks,groups,
                                          permutations=permutations,seed=seed,remove_shared_bits=True),
        'all_nonzero_block_jackknife':leave_one_block_out(nonzero,loc,masks),
        'info6_cohort_jackknife':leave_one_block_out(groups,loc,masks),
        'source_uniqueness':source_uniqueness_gate(root,additional_roots or [],additional_hashes or []),
        'single_scene_only':True,'preculler_bit_semantics_proven':False,
        'Carbon_PC_serialized_schema_proven':False,'in_game_verified':False,
        'safe_to_install':False,'read_only':True}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--scene',type=Path,required=True)
    ap.add_argument('--expected-root-sha256',required=True)
    ap.add_argument('--additional-scene',type=Path,action='append',default=[])
    ap.add_argument('--additional-sha256',action='append',default=[])
    ap.add_argument('--permutations',type=int,default=9999)
    ap.add_argument('--seed',type=int,default=540)
    ap.add_argument('--report',type=Path,required=True)
    a=ap.parse_args()
    source_paths=[a.scene,*a.additional_scene]
    if a.report.exists() or a.report.resolve() in {p.resolve() for p in source_paths}:
        ap.error('Refusing overwrite of input or existing report')
    if len(a.additional_scene)!=len(a.additional_sha256):
        ap.error('One --additional-sha256 needed for each --additional-scene')
    root=v50.read_root(a.scene)
    extra=[v50.read_root(f) for f in a.additional_scene]
    report=audit(root,expected_sha256=a.expected_root_sha256,
                 permutations=a.permutations,seed=a.seed,
                 additional_roots=extra,additional_hashes=a.additional_sha256)
    a.report.parent.mkdir(parents=True,exist_ok=True)
    with a.report.open('x',encoding='utf-8') as f:
        json.dump(report,f,indent=2,sort_keys=True);f.write('\n')
    print('V54 read-only spatial sensitivity saved:',a.report)

if __name__=='__main__':main()