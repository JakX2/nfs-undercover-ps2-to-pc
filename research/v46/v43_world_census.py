#!/usr/bin/env python3
"""READ-ONLY census of original NFS Carbon PC top-level 0x80034100 scenery chunks.

Never assumes an identical section ID signifies identical geography. Counts validated
0x34105 hierarchy candidates using exact AABB union and instance coverage tests,
and gathers shape fingerprints for still-opaque 0x34107 payloads.
"""
from __future__ import annotations
import argparse
import collections
import json
import mmap
import struct
from pathlib import Path
from v43_spatial_audit import ROOT, AuditError, analyze_scene


def census_stream(data, *, max_samples=10, max_roots=None):
    if not 0<=max_samples<=10000:
        raise ValueError('max_samples must be between 0 and 10000')
    if max_roots is not None and not 1 <= max_roots <= 100000:
        raise ValueError('max_roots must be between 1 and 100000')
    off = 0
    counts=collections.Counter()
    failures=collections.Counter()
    shapes=collections.Counter()
    initial_zero_lengths=collections.Counter()
    node_sizes=collections.Counter()
    samples=[]
    while off < len(data):
        if off + 8 > len(data):
            raise AuditError(f'Top-level stream has truncated chunk at offset 0x{off:X}')
        tag,length=struct.unpack_from('<II',data,off)
        limit=off + 8 + length
        if limit>len(data):
            raise AuditError(f'Top-level chunk at offset 0x{off:X} exceeds stream')
        counts['top_level_chunks']+=1
        if tag==ROOT:
            counts['scene_roots']+=1
            raw=bytes(data[off:limit])
            try:
                result=analyze_scene(raw,strict_tree=False)
                counts['structurally_readable_scene_roots']+=1
                if result.get('spatial_34105'):
                    counts['roots_with_exact_48B_tree_and_bbox_membership']+=1
                    node_sizes[result['spatial_34105']['node_count']]+=1
                else:
                    counts['roots_without_verified_48B_tree']+=1
                    failures[result.get('spatial_34105_failure','missing 0x34105')]+=1
                u=result.get('opaque_34107')
                if u is not None:
                    counts['roots_with_34107']+=1
                    shapes[(result['instance_count'],u['payload_size'])]+=1
                    initial_zero_lengths[u['initial_zero_bytes']]+=1
                if len(samples)<max_samples:
                    samples.append({'root_stream_offset':f'0x{off:X}',
                                    'scene_bytes':len(raw),
                                    'instances':result['instance_count'],
                                    '34105_verified':result['spatial_34105'] is not None,
                                    '34105_nodes':result['spatial_34105']['node_count'] if result['spatial_34105'] else None,
                                    '34107_bytes':u['payload_size'] if u else None})
            except (AuditError,struct.error) as e:
                counts['unreadable_scene_roots']+=1
                failures[str(e)]+=1
                if len(samples)<max_samples:
                    samples.append({'root_stream_offset':f'0x{off:X}',
                                    'scene_bytes':len(raw),'parse_error':str(e)})
            if max_roots and counts['scene_roots']>=max_roots:
                off=limit
                break
        off=limit
    if counts['top_level_chunks']==0:
        raise AuditError('Empty world stream')
    return {
        'tool':'v43-readonly-world-scene-census',
        'bytes_available':len(data),
        'bytes_traversed':off,
        'counts':dict(counts),
        'failures_by_reason':dict(failures),
        'verified_node_counts':{str(k):v for k,v in sorted(node_sizes.items())},
        '34107_instance_count_vs_length':[
            {'instances':inst,'opaque_bytes':size,'roots':count}
            for (inst,size),count in sorted(shapes.items())
        ],
        '34107_zero_prefix_bytes':{str(k):v for k,v in sorted(initial_zero_lengths.items())},
        'samples':samples,
        'provenance_notice':'Root offsets are byte positions in this supplied stream only. Scene section IDs/geographies are not inferred.',
        'never_writes_to_game_stream':True,
        'carbon_runtime_loader_verified':False,
    }


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--world',type=Path,required=True,help='Original Carbon PC world-stream file, READ ONLY')
    ap.add_argument('--json',type=Path,required=True,help='New standalone JSON report, not the game file')
    ap.add_argument('--max-samples',type=int,default=12)
    ap.add_argument('--max-roots',type=int,help='Optional limit on scene root count')
    args=ap.parse_args()
    if args.world.resolve()==args.json.resolve():ap.error('Output must never equal the source')
    if args.json.exists():ap.error('Output exists. Refusing to overwrite evidence')
    with args.world.open('rb') as file, mmap.mmap(file.fileno(),0,access=mmap.ACCESS_READ) as data:
        r=census_stream(data,max_samples=args.max_samples,max_roots=args.max_roots)
    args.json.parent.mkdir(parents=True,exist_ok=True)
    args.json.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n',encoding='utf8')
    print('READ ONLY V43: scene roots',r['counts'].get('scene_roots',0))
    print('Spatial trees with exact source AABB unions:',r['counts'].get('roots_with_exact_48B_tree_and_bbox_membership',0))
    print('Report:',args.json)


if __name__=='__main__': main()
