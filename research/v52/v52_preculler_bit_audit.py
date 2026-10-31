#!/usr/bin/env python3
"""V52: offline, read-only observational cross-check for 0x34107 candidate masks.

Uses a pinned ORIGINAL UC Wii scene as the only known authentic fixture.
No result proves Carbon PC serialized layout, game loader, culling semantics,
or that a changed scene can be safely installed.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import struct
import sys

# V50 is the preceding *source-only* candidate-index parser in this repository.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'v50'))
import v50_scenery_index_crosscheck as v50

MASK_BYTES = 68  # 17 leading u32 values are observed in this one Wii fixture
GAP_START = 68
GAP_END = 120
FOOTER_OFFSET = 120
BLOCK_WIDTH = 128
KNOWN_WII_SHA = v50.KNOWN_WII_SHA256


def bits_lsb_first(data: bytes) -> set[int]:
    """Candidate bit index is byte_index*8+LSB_index; NO decoded visibility meaning."""
    return {8*i + j for i, byte in enumerate(data) for j in range(8) if (byte >> j) & 1}


def similarity(a: set[int], b: set[int]) -> float:
    union = a | b
    return len(a & b) / len(union) if union else 1.0


def candidate_centroids(blob: bytes, ch: dict, indices: list[int]):
    """Candidate positions read at instance+32; these are source-file observations."""
    start,payload=ch[v50.INSTANCE]
    pad=(-start) & 15
    coords=[]
    for i in range(len(indices)):
        x=struct.unpack_from('<3f',payload,pad+96*i+32)
        if not all(math.isfinite(k) for k in x):
            raise v50.EvidenceError('Nonfinite candidate instance position')
        coords.append(x)
    members={i:[coords[k] for k,j in enumerate(indices) if j==i] for i in set(indices)}
    return {i:tuple(sum(p[d] for p in loc)/len(loc) for d in range(3)) for i,loc in members.items()}


def audit(root: bytes, expected_sha256: str | None = None) -> dict:
    if expected_sha256 is not None and v50.sha256(root)!=expected_sha256.lower():
        raise v50.EvidenceError('SHA-256 source guard failed')
    ch=v50.children_of(root)
    indices=v50.rows_and_indices(root,ch)
    payload=ch[v50.PRECULLER][1]
    if len(payload)%BLOCK_WIDTH:
        raise v50.EvidenceError('Candidate 0x34107 array not divisible by 128')
    blocks=[payload[p:p+BLOCK_WIDTH] for p in range(0,len(payload),BLOCK_WIDTH)]
    if not blocks:
        raise v50.EvidenceError('No candidate preculler blocks')
    invalid=sorted(set(i for i in indices if i>=len(blocks)))
    negative=Counter(str(i) for i in indices if i<0)
    active=[i for i,b in enumerate(blocks) if any(b)]
    masks={i:bits_lsb_first(blocks[i][:MASK_BYTES]) for i in active}
    allbits=set.union(*masks.values()) if masks else set()
    stablebits=set.intersection(*masks.values()) if masks else set()
    population=Counter(k for i in active for k in masks[i])
    footer_hist=Counter(str(struct.unpack_from('<II',b,FOOTER_OFFSET)) for b in blocks)
    firstword_lowbyte_allzero={i:all(b[4*k]==0 for k in range(17)) for i,b in enumerate(blocks)}
    middle_zero={i:all(v==0 for v in b[GAP_START:GAP_END]) for i,b in enumerate(blocks)}
    distances=[]
    centroid=candidate_centroids(root,ch,indices)
    ids=[i for i in active if i in centroid]
    for ix,i in enumerate(ids):
        for j in ids[ix+1:]:
            distances.append((math.dist(centroid[i],centroid[j]),similarity(masks[i],masks[j]),i,j))
    # Examples, not a proof of spatially-aware visibility semantics.
    shortest=min(distances) if distances else None
    far_high=max((p for p in distances if p[0]>100),key=lambda p:p[1],default=None)
    # Candidate bit indices at 0..543 exclude the opaque bytes 68..127.
    known_original=(v50.sha256(root)==KNOWN_WII_SHA)
    return {
        'schema':'v52-readonly-candidate-bit-audit-v1',
        'source_root_sha256':v50.sha256(root),
        'source_provenance':'known_exact_Wii_RedBuilding_scene' if known_original else 'unknown_root',
        'expected_sha256_guarded':expected_sha256 is not None,
        'instance_count_candidate_96':len(indices),
        'preculler_index_histogram':{str(i):n for i,n in sorted(Counter(indices).items())},
        'preculler_block_count_candidate_128':len(blocks),
        'all_nonnegative_indices_in_candidate_range':not invalid,
        'invalid_nonnegative_preculler_indices':invalid,
        'negative_instance_index_histogram':dict(negative),
        'empty_block_indices':[i for i,b in enumerate(blocks) if not any(b)],
        'populated_block_indices':active,
        'populated_block_unique_candidate_mask_count':len({blocks[i][:MASK_BYTES] for i in active}),
        'leading_17_u32_low_byte_zero_for_all_populated':all(firstword_lowbyte_allzero[i] for i in active),
        'bytes_68_to_119_zero_for_all_populated':all(middle_zero[i] for i in active),
        'footer_u32_pair_histogram':dict(footer_hist),
        'candidate_leading_68B_bits':{
            'bit_order':'LSB-first within bytes, offsets relative to 128-byte block',
            'populated_mask_bitcount_by_block':{str(i):len(masks[i]) for i in active},
            'intersection_set_bit_count':len(stablebits),
            'union_set_bit_count':len(allbits),
            'varying_set_bit_count':len(allbits-stablebits),
            'common_candidate_bit_positions':sorted(stablebits),
            'bit_frequency_histogram':{str(k):v for k,v in sorted(Counter(population.values()).items())},
        },
        'illustrative_pair_not_semantic_proof':{
            'spatially_closest':None if shortest is None else {'blocks':[shortest[2],shortest[3]],'position_distance':shortest[0],'mask_jaccard':shortest[1]},
            'far_apart_yet_similar':None if far_high is None else {'blocks':[far_high[2],far_high[3]],'position_distance':far_high[0],'mask_jaccard':far_high[1]},
        },
        'pinned_wii_fixture_pattern_match':(
            known_original and len(indices)==31 and len(blocks)==24 and active==list(range(1,24))
            and not invalid and len(stablebits)==17 and len(allbits)==92
            and len({blocks[i][:MASK_BYTES] for i in active})==23
            and all(firstword_lowbyte_allzero[i] and middle_zero[i] for i in active)
            and all(struct.unpack_from('<II',blocks[i],FOOTER_OFFSET)==(384,384) for i in active)
        ),
        'possible_128_byte_preculler_interpretation_only':True,
        'carbon_pc_serialized_schema_verified':False,
        'pc_runtime_or_visibility_semantics_verified':False,
        'safe_to_install':False,
        'read_only':True,
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--scene',type=Path,required=True)
    p.add_argument('--offset',type=lambda x:int(x,0))
    p.add_argument('--expected-root-sha256')
    p.add_argument('--report',type=Path,required=True,help='Fresh output JSON; refuses to overwrite any file')
    a=p.parse_args()
    if a.report.exists() or a.report.resolve()==a.scene.resolve():
        p.error('Report path already exists or overlaps input; refusing overwrite')
    root=v50.read_root(a.scene,offset=a.offset)
    report=audit(root,a.expected_root_sha256)
    report['source_stream_offset']=a.offset
    a.report.parent.mkdir(parents=True,exist_ok=True)
    with a.report.open('x',encoding='utf-8') as f:
        json.dump(report,f,indent=2,sort_keys=True)
        f.write('\n')
    print('V52 read-only report:',a.report)

if __name__=='__main__':
    main()