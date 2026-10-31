#!/usr/bin/env python3
"""V62: metadata-only framing conflicts for V61 Carbon PC chunk candidates.

Finds overlap, same-offset alternative length hypotheses and possible
0x34110 master signatures inside 0x80034100 scenery ROOT candidates.
This is an interval audit, NOT a source-authenticated Carbon parser or proof
of a streaming index, and reads NO original game bytes.
"""
from __future__ import annotations

import argparse
from bisect import bisect_left, bisect_right
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re

ROOT='0x80034100'
MASTER='0x00034110'
HEX64=re.compile(r'^[0-9a-fA-F]{64}$')
VALID_MODES={'payload','total'}
VALID_ORDERS={'little','big'}


class ConflictError(ValueError):
    pass


def _sha(s,label):
    if not isinstance(s,str) or not HEX64.fullmatch(s):
        raise ConflictError(f'{label}: expected 64-hex SHA-256')
    return s.lower()


def _uint(n,label):
    if type(n) is not int or n<0:
        raise ConflictError(f'{label}: expected nonnegative integer')
    return n


def _validate(data, require_guard):
    if not isinstance(data,dict) or data.get('schema')!='v61-format-neutral-scene-and-master-chunk-inventory-v1':
        raise ConflictError('V61 source report schema required')
    if type(data.get('trusted_expected_archive_digest_checked')) is not bool:
        raise ConflictError('V61 archive guard flag missing')
    guard=data['trusted_expected_archive_digest_checked']
    if require_guard and not guard:
        raise ConflictError('archive digest was unguarded; rerun V61 with trusted --expected-sha256 or --allow-unguarded')
    archive_sha=_sha(data.get('archive_sha256'),'archive_sha256')
    size=_uint(data.get('archive_size_bytes'),'archive_size_bytes')
    candidates=data.get('candidates')
    if not isinstance(candidates,list) or len(candidates)>100000:
        raise ConflictError('V61 candidates missing or count beyond 100000')
    if _uint(data.get('candidate_variants'),'candidate_variants')!=len(candidates):
        raise ConflictError('inconsistent candidate variant count')
    result=[]
    seen=set()
    frame_hash_for_span={}
    for i,c in enumerate(candidates):
        if not isinstance(c,dict):
            raise ConflictError('candidate must be JSON object')
        tag=c.get('tag')
        mode=c.get('length_mode_hypothesis')
        order=c.get('endian')
        if tag not in (ROOT,MASTER) or mode not in VALID_MODES or order not in VALID_ORDERS:
            raise ConflictError('unsupported candidate tag/byte order/length mode')
        start=_uint(c.get('offset'),'offset')
        total=_uint(c.get('total_bytes'),'total_bytes')
        end=_uint(c.get('end_offset_exclusive'),'end_offset_exclusive')
        if total<8 or start>size or total>size-start or end!=start+total:
            raise ConflictError('candidate framing range is inconsistent or outside archive')
        digest=_sha(c.get('framed_chunk_sha256'),'framed_chunk_sha256')
        payload=_sha(c.get('payload_sha256'),'payload_sha256')
        key=(start,tag,order,mode)
        if key in seen:
            raise ConflictError('duplicate candidate interpretation in input report')
        seen.add(key)
        span=(start,end)
        prior=frame_hash_for_span.get(span)
        if prior is not None and prior!=digest:
            raise ConflictError('conflicting SHA-256 for identical framed-byte range')
        frame_hash_for_span[span]=digest
        if tag==ROOT:
            child=c.get('child_framing_probe')
            if not isinstance(child,dict) or child.get('status') not in (
                    'unparsed','empty','contiguous_candidate_children'):
                raise ConflictError('root candidate missing child-framing status')
            child_status=child['status']
        else:
            child_status=None
        result.append({
            'candidate_index':i,
            'offset':start,
            'end_offset_exclusive':end,
            'total_bytes':total,
            'tag':tag,
            'endian':order,
            'length_mode_hypothesis':mode,
            'framed_chunk_sha256':digest,
            'payload_sha256':payload,
            'child_framing_status':child_status,
        })
    return result,archive_sha,size,guard


def _prefix_max_ends(rows):
    """Sorted entries, along with the rightmost interval reaching an index."""
    rows=sorted(rows,key=lambda r:(r['offset'],-r['end_offset_exclusive']))
    starts=[r['offset'] for r in rows]
    ends=[]
    best=-1
    for r in rows:
        best=max(best,r['end_offset_exclusive'])
        ends.append(best)
    return rows,starts,ends


def analyze(v61report, *, require_guard=True, top=10000):
    if type(require_guard) is not bool:
        raise ConflictError('require_guard must be boolean')
    if type(top) is not int or not 1<=top<=100000:
        raise ConflictError('top outside 1..100000')
    records,source_sha,archive_size,guard=_validate(v61report,require_guard)
    # Use O(n log n) sorted endpoint indexes, not quadratic pair enumeration.
    by_start=sorted(records,key=lambda r:(r['offset'],r['end_offset_exclusive'],r['candidate_index']))
    starts=[r['offset'] for r in by_start]
    prefix_max=[]
    running=-1
    for r in by_start:
        running=max(running,r['end_offset_exclusive'])
        prefix_max.append(running)
    at_offset=Counter(starts)
    roots=[r for r in records if r['tag']==ROOT]
    masters=[r for r in records if r['tag']==MASTER]
    root_sorted,root_starts,root_end_max=_prefix_max_ends(roots)
    _,master_starts,_=_prefix_max_ends(masters)
    outputs=[]
    classifications=Counter()
    for r in records:
        start,end=r['offset'],r['end_offset_exclusive']
        # Earlier strict-start intervals reaching this candidate's start.
        before=bisect_left(starts,start)
        earlier=before>0 and prefix_max[before-1]>start
        # Any later strict-start candidate beginning before the current end.
        after=bisect_right(starts,start)
        later=after<len(starts) and starts[after]<end
        siblings=at_offset[start]-1
        overlaps=bool(earlier or later or siblings)
        # Candidate master signature inside any candidate ROOT range.
        # This is conservative: containment of a signature may be legitimate,
        # and header framing of either overlapping candidate is unproven.
        nested_in_root=False
        wholly_inside_root=False
        if r['tag']==MASTER:
            upto=bisect_left(root_starts,start)
            if upto:
                largest_prior_root_end=root_end_max[upto-1]
                nested_in_root=largest_prior_root_end>start
                wholly_inside_root=largest_prior_root_end>=end
        # Count different-position candidate master starts inside a ROOT.
        # Count unique signature positions, not duplicated payload/total modes.
        contained_master_offsets=0
        if r['tag']==ROOT:
            lo=bisect_right(master_starts,start)
            hi=bisect_left(master_starts,end)
            # The sorted master list can have several variants at one offset.
            contained_master_offsets=len(set(master_starts[lo:hi]))
        if r['tag']==ROOT:
            if r['child_framing_status']=='contiguous_candidate_children':
                category='root_with_contiguous_candidate_child_frames'
            else:
                category='root_without_contiguous_candidate_child_frames'
        elif nested_in_root:
            category='master_signature_inside_candidate_root'
        elif overlaps:
            category='master_candidate_with_other_framing_overlap'
        else:
            category='master_candidate_without_detected_span_overlap'
        classifications[category]+=1
        outputs.append({
            **r,
            'competing_interpretations_at_same_offset':siblings,
            'overlap_with_any_other_candidate_variant':overlaps,
            'earlier_start_candidate_overlaps':bool(earlier),
            'later_start_candidate_overlaps':bool(later),
            'master_signature_starts_inside_candidate_root':nested_in_root,
            'master_candidate_wholly_inside_a_candidate_root':wholly_inside_root,
            'master_signature_offsets_inside_this_root':contained_master_offsets,
            'candidate_category':category,
            'format_or_ownership_proven':False,
            'source_game_authenticated':False,
        })
    # Preserve all variants and their order. An evidence triage category is
    # never treated as authoritative ownership of any underlying game bytes.
    outputs.sort(key=lambda r:(r['offset'],r['tag'],r['endian'],r['length_mode_hypothesis']))
    conflict_offsets=sum(n>1 for n in at_offset.values())
    return {
        'schema':'v62-format-neutral-candidate-interval-conflict-v1',
        'source_archive_sha256':source_sha,
        'source_archive_size_bytes':archive_size,
        'source_expected_digest_guard_applied':guard,
        'candidate_variants_total':len(records),
        'distinct_candidate_signature_offsets':len(at_offset),
        'same_offset_competing_interpretation_locations':conflict_offsets,
        'candidate_variants_overlapping_another_variant':sum(r['overlap_with_any_other_candidate_variant'] for r in outputs),
        'master_variants_starting_inside_candidate_ROOTs':sum(r['master_signature_starts_inside_candidate_root'] for r in outputs),
        'master_variants_wholly_inside_candidate_ROOTs':sum(r['master_candidate_wholly_inside_a_candidate_root'] for r in outputs),
        'candidate_categories':dict(sorted(classifications.items())),
        'entries_emitted':min(top,len(outputs)),
        'entries_truncated':top<len(outputs),
        'candidates':outputs[:top],
        'Carbon_PC_master_layout_verified':False,
        'Carbon_PC_loader_or_relocations_verified':False,
        'independent_original_game_source_authenticated':False,
        'in_game_verified':False,'safe_to_install':False,
        'metadata_only':True,
        'notes':[
          'A signature nested inside an apparent ROOT is suspicious as an independent master, but never automatically invalid.',
          'Two overlapping interpretations may both be incorrect; no framing convention is selected as genuine.',
          'Contiguous candidate child frames can be synthetic or incidental, not proof of a Carbon PC ROOT.',
          'Source digest guards, if supplied, verify bytes but do not establish authorized original-game provenance.',
          'Reports carry source SHA-256/offset metadata only; no private file paths or original payload bytes.'
        ],
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--v61-report',required=True,type=Path)
    p.add_argument('--report',required=True,type=Path)
    p.add_argument('--allow-unguarded',action='store_true')
    p.add_argument('--top',type=int,default=10000)
    args=p.parse_args()
    if args.report.exists() or args.report.resolve()==args.v61_report.resolve():
        p.error('refusing overwrite of source report or existing output')
    data=json.loads(args.v61_report.read_text(encoding='utf-8'))
    result=analyze(data,require_guard=not args.allow_unguarded,top=args.top)
    args.report.parent.mkdir(parents=True,exist_ok=True)
    with args.report.open('x',encoding='utf-8') as f:
        json.dump(result,f,indent=2,sort_keys=True)
        f.write('\n')
    print('V62: ',result['candidate_variants_total'],'candidate variants;',
          result['master_variants_starting_inside_candidate_ROOTs'],
          'master variants start inside candidate ROOTs.')
    print('No Carbon PC master index or original source provenance authenticated.')


if __name__=='__main__':
    main()
