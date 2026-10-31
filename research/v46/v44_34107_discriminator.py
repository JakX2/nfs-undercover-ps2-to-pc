#!/usr/bin/env python3
"""V44 offline, READ-ONLY 0x34107 record-cadence and size-hypothesis audit.

No semantics are ascribed to 0x34107; pattern/size coincidences are not
proof of cell indices, PVS, partition data, or a writer schema. Source world
stream is opened read-only, report writes are refused if paths collide.
"""
from __future__ import annotations
import argparse
import collections
import hashlib
import json
import mmap
from pathlib import Path
import struct

from v43_spatial_audit import (
    AUX, ROOT, TREE, UNKNOWN, AuditError, SOURCE_SHA,
    checksum, parse_instances, parse_root, read_root_from_stream,
)

BLOCK_WIDTH=128
NODE_WIDTH=48
MAX_ROOT_BYTES=512*1024*1024


def word_pair(r: bytes, offset: int) -> tuple[int,int]:
    return struct.unpack_from('<II', r, offset)


def audit_opaque(payload: bytes, n_instances: int, n_nodes_candidate: int | None):
    """Return observations, NEVER inferred 0x34107 operational semantics."""
    rows=[]
    if len(payload)%BLOCK_WIDTH==0:
        for i in range(len(payload)//BLOCK_WIDTH):
            r=payload[i*BLOCK_WIDTH:(i+1)*BLOCK_WIDTH]
            rows.append({'index':i,'all_zero':not any(r),
                         'nonzero_byte_count':sum(v!=0 for v in r),
                         'head_u32_hex':f'0x{struct.unpack_from("<I",r,0)[0]:08X}',
                         'tail_2x_u32':list(word_pair(r,120)),
                         'sha256':checksum(r)})
    populated=[r for r in rows if not r['all_zero']]
    heads=collections.Counter(r['head_u32_hex'] for r in populated)
    tails=collections.Counter(tuple(r['tail_2x_u32']) for r in populated)
    return {
      'interpretation':'opaque; no established 0x34107 engine semantics or write rules',
      'bytes':len(payload), 'sha256':checksum(payload),
      'instance_count':n_instances,
      'candidate_48byte_34105_node_count':n_nodes_candidate,
      'size_hypotheses':{
          '96_bytes_times_instances_plus_one':len(payload)==96*(n_instances+1),
          '96_bytes_times_instances':len(payload)==96*n_instances,
          '384_bytes_times_48byte_node_count':n_nodes_candidate is not None and len(payload)==384*n_nodes_candidate,
      },
      '128_byte_candidate_blocks':len(rows) if len(payload)%BLOCK_WIDTH==0 else None,
      '128_byte_blocks':rows,
      '128_byte_zero_block_indices':[r['index'] for r in rows if r['all_zero']],
      'populated_block_header_u32_histogram':[{'hex':key,'count':value} for key,value in sorted(heads.items())],
      'populated_block_tail_pair_histogram':[{'u32_pair':list(pair),'count':count} for pair,count in sorted(tails.items())],
      'dominant_tail_pair_share':(max(tails.values())/len(populated) if populated else None),
      'structure_unproven_warning':(
        'Repeated 128B block boundaries/markers are source-backed observations only. '
        'Even if both size hypotheses match, one fixture cannot tell which correlation is causal.'
      ),
      'writable':False,
    }


def audit_root(blob: bytes, *, expected_sha256: str | None = None):
    digest=checksum(blob)
    if expected_sha256 is not None and digest.lower()!=expected_sha256.lower():
        raise AuditError('SHA256 guard mismatch; refusing verified-source label')
    children=parse_root(blob)
    inst,_pad,_digest=parse_instances(blob,children)
    nodes=None
    if TREE in children and len(children[TREE]['data'])%NODE_WIDTH==0:
        nodes=len(children[TREE]['data'])//NODE_WIDTH
    if UNKNOWN not in children:
        raise AuditError('No 0x34107 child in original scene')
    report=audit_opaque(children[UNKNOWN]['data'],len(inst),nodes)
    report['source_root_sha256']=digest
    report['source_root_bytes']=len(blob)
    report['source_sha256_guard_checked']=expected_sha256 is not None
    report['34105_candidate_node_size_bytes']=len(children[TREE]['data']) if TREE in children else None
    report['3410D_32B_per_instance']=AUX in children and len(children[AUX]['data'])==32*len(inst)
    report['loader_scenery_execution_confirmed']=False
    report['carbon_pc_schema_verified']=False
    report['safe_native_34107_writer_exists']=False
    return report


def census_world(source, *, max_roots=None, max_examples=20):
    """Read-only flat chunk-stream walk; no assumption about section geography."""
    if max_roots is not None and not 1 <= max_roots <= 100000:
        raise ValueError('max_roots out of range')
    if not 0<=max_examples<=1000:
        raise ValueError('max_examples out of range')
    stats=collections.Counter()
    examples=[]
    offset=0
    while offset<len(source):
        if offset+8>len(source):
            raise AuditError(f'Truncated top-level chunk at 0x{offset:X}')
        tag, length=struct.unpack_from('<II',source,offset)
        end=offset+8+length
        if end>len(source):
            raise AuditError(f'Chunk at 0x{offset:X} exceeds file')
        stats['top_level_chunks']+=1
        if tag==ROOT:
            stats['scene_roots']+=1
            try:
                if length>MAX_ROOT_BYTES:
                    raise AuditError('Root exceeds conservative max size')
                row=audit_root(bytes(source[offset:end]))
                stats['readable_roots_with_34107']+=1
                h=row['size_hypotheses']
                both=h['96_bytes_times_instances_plus_one'] and h['384_bytes_times_48byte_node_count']
                if both:stats['both_hypotheses_true']+=1
                elif h['96_bytes_times_instances_plus_one']:stats['only_instance_plus_one_hypothesis_true']+=1
                elif h['384_bytes_times_48byte_node_count']:stats['only_node_hypothesis_true']+=1
                else:stats['neither_hypothesis_true']+=1
                blocks=row['128_byte_blocks']
                if len(blocks)>1 and blocks[0]['all_zero'] and all(not r['all_zero'] and r['tail_2x_u32']==blocks[1]['tail_2x_u32'] for r in blocks[1:]) and not any(blocks[0]['tail_2x_u32']):
                    stats['128B_second_to_last_tail_repeat_check']+=1
                if len(examples)<max_examples:
                    examples.append({'root_offset_hex':hex(offset),'root_sha256':row['source_root_sha256'],
                        'instances':row['instance_count'],'candidate_nodes':row['candidate_48byte_34105_node_count'],
                        '34107_bytes':row['bytes'],'size_hypotheses':h,
                        '128B_candidate_blocks':row['128_byte_candidate_blocks'],
                        'dominant_tail_pair_share':row['dominant_tail_pair_share']})
            except (AuditError,struct.error) as e:
                stats['unreadable_root_or_no_34107']+=1
                if len(examples)<max_examples:
                    examples.append({'root_offset_hex':hex(offset),'parse_error':str(e)})
            if max_roots is not None and stats['scene_roots']>=max_roots:
                offset=end
                break
        offset=end
    return {'tool':'v44-readonly-34107-cross-root-hypothesis-census',
            'bytes_available':len(source),'bytes_scanned':offset,
            'counts':dict(stats),'examples':examples,
            'interpretation':'Length correlations are hypotheses only; nonzero pattern != semantics',
            'all_source_data_unmodified':True,'installs_or_patches_created':False}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    sources=ap.add_mutually_exclusive_group(required=True)
    sources.add_argument('--scene',type=Path)
    sources.add_argument('--stream',type=Path,help='Original BUN, single root at --offset')
    sources.add_argument('--world',type=Path,help='Original BUN, flat chunk-stream census')
    ap.add_argument('--offset',type=lambda x:int(x,0),help='Needed with --stream')
    ap.add_argument('--expected-sha256',help='Guard for --scene or --stream')
    ap.add_argument('--max-roots',type=int)
    ap.add_argument('--json',type=Path,required=True)
    args=ap.parse_args()
    if bool(args.stream)!=bool(args.offset is not None):ap.error('--stream requires --offset; --offset requires --stream')
    if args.world and args.expected_sha256:ap.error('--expected-sha256 only applies to a single scene')
    if args.world is None and args.max_roots is not None:ap.error('--max-roots requires --world')
    source=args.scene or args.stream or args.world
    if args.json.suffix.lower()!='.json':ap.error('Output must be a .json report')
    if source.resolve()==args.json.resolve():ap.error('Refusing report-to-source overwrite')
    if args.json.exists():ap.error('Refusing to overwrite existing report')
    if args.world:
        with args.world.open('rb') as file, mmap.mmap(file.fileno(),0,access=mmap.ACCESS_READ) as data:
            report=census_world(data,max_roots=args.max_roots)
    else:
        blob=read_root_from_stream(args.stream,args.offset) if args.stream else args.scene.read_bytes()
        report=audit_root(blob,expected_sha256=args.expected_sha256)
    report['provenance']={'source_basename':source.name,'offset':args.offset,
                         'guard_checked':args.expected_sha256 is not None}
    args.json.parent.mkdir(parents=True,exist_ok=True)
    with args.json.open('x',encoding='utf8') as f:
        json.dump(report,f,indent=2,sort_keys=True)
        f.write('\n')
    print('READ ONLY V44 result:',args.json)
    print('No source or game stream modifications.')

if __name__=='__main__':
    main()
