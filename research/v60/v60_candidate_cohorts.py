#!/usr/bin/env python3
"""V60: compare *metadata only* from multiple V58 archive inventories.

A ROOT SHA difference is not an independent scene. Compare 0x34103 payload
fingerprints and prioritize structurally consistent *candidate Wii* scenery
graphs that can differentiate two size hypotheses for opaque 0x34107.

Never authenticates a game source or infers Carbon PC's serialized ABI.
Never reads or modifies original game files, emits paths or writes game bytes.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import re

HEX64 = re.compile(r'^[0-9a-fA-F]{64}$')
VALID_HINTS = {'wii','carbon_pc','unknown'}
CONSISTENT = 'candidate_internally_consistent'


class CohortError(ValueError):
    pass


def sha(value, field):
    if not isinstance(value,str) or not HEX64.fullmatch(value):
        raise CohortError(f'{field}: expected 64 SHA-256 hex digits')
    return value.lower()


def nonnegative_int(value, field):
    if type(value) is not int or value < 0:
        raise CohortError(f'{field}: expected nonnegative integer')
    return value


def optional_sha(value, field):
    return sha(value,field) if value is not None else None


def _validate_report(report, index, require_guard):
    if not isinstance(report,dict):
        raise CohortError('inventory must be a JSON object')
    if report.get('schema')!='v58-source-framed-candidate-scene-inventory-v1':
        raise CohortError('incompatible inventory schema; regenerate with V58')
    guard = report.get('archive_integrity_guard_applied')
    if type(guard) is not bool:
        raise CohortError('missing archive fingerprint-guard status')
    if require_guard and not guard:
        raise CohortError('archive is unguarded; supply trusted hash to V58 or --allow-unguarded')
    source = report.get('source_hint_unverified')
    if source not in VALID_HINTS:
        raise CohortError('unknown source hint')
    whole_sha = sha(report.get('archive_sha256'), 'archive_sha256')
    size=nonnegative_int(report.get('archive_size_bytes'), 'archive_size_bytes')
    data=report.get('records')
    if not isinstance(data,list) or len(data)>100000:
        raise CohortError('inventory records absent or exceed 100000')
    if nonnegative_int(report.get('candidate_root_occurrences'),'candidate_root_occurrences') != len(data):
        raise CohortError('candidate occurrence count disagrees with records')
    records=[]
    for row in data:
        if not isinstance(row,dict):
            raise CohortError('invalid ROOT candidate record')
        offset=nonnegative_int(row.get('offset'),'offset')
        length=nonnegative_int(row.get('root_bytes'),'root_bytes')
        if length<8 or offset>size or length>size-offset:
            raise CohortError('ROOT candidate range exceeds claimed archive')
        rootsha=sha(row.get('root_sha256'),'root_sha256')
        instance=sha(row.get('candidate_instance_payload_sha256'),'candidate_instance_payload_sha256')
        scene=sha(row.get('candidate_scene_payload_sha256'),'candidate_scene_payload_sha256')
        tree=optional_sha(row.get('candidate_tree_payload_sha256'),'candidate_tree_payload_sha256')
        precull=optional_sha(row.get('candidate_preculler_payload_sha256'),'candidate_preculler_payload_sha256')
        status=row.get('candidate_wii_graph_status')
        if not isinstance(status,str) or not status:
            raise CohortError('missing candidate graph status')
        if source!='wii' and status!='not_evaluated_for_non_Wii_source':
            raise CohortError('non-Wii source unexpectedly has Wii structural verdict')
        counts=(row.get('candidate_instance_count'),
                row.get('candidate_tree_node_count'),
                row.get('candidate_preculler_block_count'))
        if source=='wii' and status==CONSISTENT:
            if any(type(x) is not int or x<=0 for x in counts):
                raise CohortError('consistent Wii graph needs positive candidate counts')
            if tree is None or precull is None:
                raise CohortError('consistent Wii graph missing candidate table fingerprints')
        records.append({'source_index':index,'archive_sha256':whole_sha,'offset':offset,
                        'root_bytes':length,'root_sha256':rootsha,
                        'instance_sha256':instance,'scene_sha256':scene,
                        'tree_sha256':tree,'preculler_sha256':precull,
                        'graph_status':status,'platform_hint_unverified':source,
                        'counts':counts})
    if nonnegative_int(report.get('distinct_candidate_root_sha256s'),'distinct_candidate_root_sha256s') != len({r['root_sha256'] for r in records}):
        raise CohortError('distinct ROOT count disagrees with records')
    return {'archive_sha256':whole_sha,'size':size,'guard':guard,
            'source':source,'records':records}


def classify(n_instances,n_nodes,n_blocks):
    """Numerical relationship only, never 0x34107 meaning or PC disk proof."""
    count_bytes=n_blocks*128
    a=count_bytes==(n_instances+1)*96
    b=count_bytes==n_nodes*384
    if a and b:return 'both_hypotheses'
    if a:return 'instance_count_only'
    if b:return 'tree_count_only'
    return 'neither_hypothesis'


def compare(inventories, *, require_guard=True, top=100):
    """Group V58 candidate inventory metadata without original game inputs."""
    if not isinstance(inventories,list) or not 1<=len(inventories)<=128:
        raise CohortError('expected 1..128 V58 inventory objects')
    if type(require_guard) is not bool:
        raise CohortError('require_guard must be boolean')
    if type(top) is not int or not 1<=top<=10000:
        raise CohortError('top must be within 1..10000')
    entries=[_validate_report(r,i,require_guard) for i,r in enumerate(inventories)]
    archive_ids={x['archive_sha256'] for x in entries}
    candidates=[x for e in entries for x in e['records']]
    root_groups=defaultdict(list)
    for x in candidates:
        root_groups[x['root_sha256']].append(x)
    # Two contradictory metadata records sharing identical exact ROOT bytes
    # indicate corrupt report data, not an exotic new format.
    for rootsha, rows in root_groups.items():
        baseline=rows[0]
        for item in rows[1:]:
            for key in ('instance_sha256','scene_sha256','tree_sha256',
                        'preculler_sha256','graph_status','counts'):
                if item[key]!=baseline[key]:
                    raise CohortError('conflicting metadata for identical ROOT fingerprint')
    wii_rows=[rows[0] for rows in root_groups.values()
              if rows[0]['platform_hint_unverified']=='wii' and rows[0]['graph_status']==CONSISTENT]
    instance_groups=defaultdict(list)
    for row in wii_rows:
        instance_groups[row['instance_sha256']].append(row)
    raw_pattern_counts=Counter(classify(*r['counts']) for r in wii_rows)
    priority={'instance_count_only':0,'tree_count_only':0,
              'neither_hypothesis':1,'both_hypotheses':2}
    recommended=[]
    for instance_sha,rows in instance_groups.items():
        best=min(rows,key=lambda x:(priority[classify(*x['counts'])],
                                    x['root_sha256']))
        pattern=classify(*best['counts'])
        recommended.append({
            'root_sha256':best['root_sha256'],
            'instance_payload_sha256':instance_sha,
            'hypothesis_pattern':pattern,
            'candidate_instance_count':best['counts'][0],
            'candidate_tree_node_count':best['counts'][1],
            'candidate_preculler_block_count':best['counts'][2],
            'candidate_wii_graph_status':CONSISTENT,
            'same_instance_distinct_ROOT_count':len(rows),
            'occurrences_of_representative_ROOT':len(root_groups[best['root_sha256']]),
            'source_report_index':best['source_index'],
            'source_archive_sha256':best['archive_sha256'],
            'source_offset':best['offset'],
            'source_provenance_verified':False,
            'pc_layout_verified':False,
        })
    recommended.sort(key=lambda r:(priority[r['hypothesis_pattern']],
                                   r['instance_payload_sha256']))
    duplicate_roots=sum(len(rows)-1 for rows in root_groups.values())
    same_instance_multi_root=sum(len(rows)>1 for rows in instance_groups.values())
    distinct_instance_count=len(instance_groups)
    return {
        'schema':'v60-unverified-cross-stream-candidate-cohorts-v1',
        'input_inventory_reports':len(entries),
        'distinct_archive_sha256s':len(archive_ids),
        'unguarded_inventory_reports':sum(not e['guard'] for e in entries),
        'total_candidate_ROOT_occurrences':len(candidates),
        'exact_ROOT_duplicate_occurrences':duplicate_roots,
        'distinct_candidate_ROOT_sha256s':len(root_groups),
        'consistent_candidate_Wii_ROOT_sha256s':len(wii_rows),
        'distinct_consistent_Wii_instance_payload_sha256s':distinct_instance_count,
        'same_instance_different_ROOT_groups':same_instance_multi_root,
        'candidate_hypothesis_patterns_on_distinct_Wii_ROOTs':dict(sorted(raw_pattern_counts.items())),
        'priority_count_total':len(recommended),
        'priority_entries_emitted':len(recommended[:top]),
        'priority_entries_truncated':len(recommended)>top,
        'priority_candidates':recommended[:top],
        'independent_original_Wii_scenes_authenticated':False,
        'original_Carbon_PC_scenes_authenticated':False,
        'Carbon_PC_preculler_serialization_proven':False,
        'culling_meaning_proven':False,
        'in_game_verified':False,
        'safe_to_install':False,
        'read_only':True,
        'warnings':[
          'Only source-generated metadata digests and layout hypotheses are compared, never original game bytes.',
          'Different archives, ROOTs and instance payload SHA-256s cannot independently authenticate source-game provenance.',
          'Candidate-only arithmetic correlations can be coincidental or confounded, and do not identify preculler semantics.',
          'The priority list is a source-investigation shortlist, not proof that these are genuine Wii scenery sections.',
          'Carbon PC source hints are not treated as Wii-compatible serialization.',
        ]
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--inventory',type=Path,action='append',required=True,
                   help='V58 metadata-only JSON, repeatable')
    p.add_argument('--report',type=Path,required=True,
                   help='New summary JSON filename only')
    p.add_argument('--allow-unguarded',action='store_true',
                   help='Explicitly accept source archives not originally digest guarded')
    p.add_argument('--top',type=int,default=100)
    a=p.parse_args()
    if a.report.exists() or a.report.resolve() in {x.resolve() for x in a.inventory}:
        p.error('refusing overwrite of existing report or input')
    data=[json.loads(x.read_text(encoding='utf-8')) for x in a.inventory]
    output=compare(data,require_guard=not a.allow_unguarded,top=a.top)
    a.report.parent.mkdir(parents=True,exist_ok=True)
    with a.report.open('x',encoding='utf-8') as f:
        json.dump(output,f,indent=2,sort_keys=True);f.write('\n')
    print('V60 metadata-only:',output['distinct_candidate_ROOT_sha256s'],
          'distinct candidate roots,',output['distinct_consistent_Wii_instance_payload_sha256s'],
          'candidate Wii instance payloads')
    print('Not source-authenticated, not Carbon PC ABI or a game patch.')


if __name__=='__main__':
    main()
