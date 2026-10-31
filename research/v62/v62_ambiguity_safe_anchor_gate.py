#!/usr/bin/env python3
"""V62: read-only candidate shortlist safety on top of V61 root scanning.

A V61 raw shortlist can contain *overlapping* candidate ROOTs, including a
synthetic ROOT nested in a candidate scenery instance's opaque payload.
It can also be produced from a partial/truncated scan. V62 exposes a stricter
handoff suitable for further HYPOTHESIS tests, not Carbon loader proof.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'v61'))
import v61_root_candidate_inventory as v61

MAX_ELIGIBLE = 64

class OwnershipError(ValueError):
    pass


def filter_candidates(inventory: dict) -> dict:
    """Filter a freshly computed V61 inventory, without interpreting game ABI.

    This function is intentionally conservative: a partial scan may have
    omitted an overlapping ancestor/descendant, so it returns no handoff
    anchors even if the roots it did find appear disjoint.
    """
    if inventory.get('schema') != 'v61-readonly-embedded-root-inventory-v1':
        raise OwnershipError('invalid V61 inventory schema')
    n = inventory.get('file_length_bytes')
    roots = inventory.get('candidate_roots')
    if type(n) is not int or n < 0 or not isinstance(roots, list):
        raise OwnershipError('invalid V61 file length or candidates')
    file_sha = inventory.get('source_file_sha256')
    if not isinstance(file_sha, str) or len(file_sha) != 64:
        raise OwnershipError('no validated source file fingerprint')
    if not inventory.get('read_only') or inventory.get('safe_to_install'):
        raise OwnershipError('input is not read-only or requests installation')
    complete = (inventory.get('search_start_inclusive') == 0 and
                inventory.get('search_stop_exclusive') == n and
                inventory.get('scan_complete_within_window') is True)
    ranges=[]
    for i,root in enumerate(roots):
        a,b,h = root.get('offset'),root.get('end_exclusive'),root.get('root_sha256')
        if (type(a) is not int or type(b) is not int or
            not 0 <= a < b <= n or not isinstance(h,str) or len(h)!=64):
            raise OwnershipError('malformed candidate interval or SHA')
        ranges.append((a,b,i))
    # Max-end sweep: any interval intersecting the current furthest-end
    # interval is ambiguous. Every earlier overlapping interval was already
    # marked when it was inserted. O(N log N) sort, O(N) sweep, bounded report.
    ranges.sort()
    ambiguous=set()
    conflicts=[]
    furthest_end=-1
    furthest_index=None
    for start,end,i in ranges:
        if start < furthest_end:
            ambiguous.update((i,furthest_index))
            conflicts.append((min(roots[i]['offset'],roots[furthest_index]['offset']),
                              max(roots[i]['offset'],roots[furthest_index]['offset'])))
        if end>furthest_end:
            furthest_end=end
            furthest_index=i
    eligible=[]
    seen_hashes=set()
    duplicated=[]
    total_unique_eligible=0
    for i,root in enumerate(roots):
        if root['classification'] != 'scenery_direct_TLV_candidate' or i in ambiguous:
            continue
        h=root['root_sha256']
        if h in seen_hashes:
            duplicated.append(root['offset'])
            continue
        seen_hashes.add(h)
        total_unique_eligible+=1
        if len(eligible)<MAX_ELIGIBLE:
            eligible.append({'label':f'v62_candidate_{len(eligible)+1:03d}',
                             'offset':root['offset'],
                             'expected_root_sha256':h})
    # Do not release any anchor for a partial scan: the scan may not have seen
    # a containing ROOT whose marker lies outside the window, or later roots.
    filtered = eligible if complete else []
    return {
        'schema':'v62-ambiguity-safe-source-only-anchor-gate-v1',
        'source_file_sha256':file_sha,
        'source_file_size_bytes':n,
        'whole_file_scan_complete':complete,
        'raw_v61_shortlist_count':len(inventory.get('v60_anchor_shortlist_unverified_provenance',[])),
        'candidate_root_count':len(roots),
        'overlapping_candidate_offsets':sorted(roots[i]['offset'] for i in ambiguous),
        'overlap_pair_offsets':sorted(set(conflicts)),
        'excluded_ambiguous_candidate_count':len(ambiguous),
        'excluded_same_byte_candidate_offsets':duplicated,
        'eligible_count_before_scan_completeness_gate':total_unique_eligible,
        'shortlist_truncated_at_64':total_unique_eligible>MAX_ELIGIBLE,
        'eligible_count':len(filtered),
        'eligible_v60_anchor_shortlist_unverified':filtered,
        'handoff_status': ('incomplete_scan_no_handoff' if not complete else
                           'overlap_filtered_candidates_only_not_loader_ownership'),
        'source_hash_does_not_prove_original_game_provenance':True,
        'native_carbon_root_ownership_proven':False,
        'native_carbon_master_index_or_loader_proven':False,
        'safe_to_install':False,
        'read_only':True,
    }


def audit_file(source:Path,expected_file_sha256:str,endian:str,
               *,start_offset=0,stop_offset=None,max_candidates=2048):
    scan=v61.audit_file(source,expected_sha256=expected_file_sha256,endian=endian,
                        start_offset=start_offset,stop_offset=stop_offset,
                        max_candidates=max_candidates)
    return {'v61_inventory':scan,'v62_gate':filter_candidates(scan)}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--source',required=True,type=Path)
    ap.add_argument('--expected-file-sha256',required=True)
    ap.add_argument('--endian',required=True,choices=('little','big'))
    ap.add_argument('--start-offset',type=lambda x:int(x,0),default=0)
    ap.add_argument('--stop-offset',type=lambda x:int(x,0))
    ap.add_argument('--max-candidates',type=int,default=2048)
    ap.add_argument('--report',required=True,type=Path)
    a=ap.parse_args()
    if a.report.resolve()==a.source.resolve() or a.report.exists():
        ap.error('refusing to replace a source or existing report')
    result=audit_file(a.source,a.expected_file_sha256,a.endian,
                      start_offset=a.start_offset,stop_offset=a.stop_offset,
                      max_candidates=a.max_candidates)
    a.report.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf-8')

if __name__=='__main__':main()