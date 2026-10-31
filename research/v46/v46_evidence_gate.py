#!/usr/bin/env python3
"""V46: read-only, evidence-gated scenery-root inspector.

Never guesses a Carbon PC 0x34105/0x34107 schema from Wii data.
An explicit expected root SHA is an integrity check, not proof of platform origin.
Provenance of full PC world streams must be established independently.
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
    ROOT, INST, TREE, UNKNOWN, AUX, INFO, AuditError, SOURCE_SHA,
    analyze_34105, checksum, parse_instances, parse_root, read_root_from_stream,
)
from v45_scene_compat_gate import compare_v42_style_roots, get_root

CANDIDATE_STRIDES=(24,32,36,40,44,48,52,56,64,72,96,128)
MARKER=struct.pack('<II',384,384)
MAX_SINGLE_ROOT=512*1024*1024


def audit_34107_cadence(raw: bytes) -> dict:
    """Strictly descriptive byte-offset analysis. No field semantics."""
    occurrences=[]
    cursor=0
    while (where:=raw.find(MARKER,cursor))!=-1:
        occurrences.append(where)
        cursor=where+1
    result={
        'bytes':len(raw), 'sha256':checksum(raw),
        'u32_pair_384_384_all_occurrences':len(occurrences),
        'u32_pair_384_384_offsets':occurrences[:2000],
        'candidate_128_byte_aligned':bool(raw) and len(raw)%128==0,
        'semantic_0x34107_record_decode_proven':False,
    }
    if not result['candidate_128_byte_aligned']:
        result['candidate_128_byte_blocks']=None
        return result
    blocks=[raw[i:i+128] for i in range(0,len(raw),128)]
    populated=[(i,b) for i,b in enumerate(blocks) if any(b)]
    footers=[struct.unpack_from('<II',b,120) for _,b in populated]
    dwords=[struct.unpack_from('<17I',b) for _,b in populated]
    aligned_hits=[i*128+120 for i,b in populated if b[120:128]==MARKER]
    result.update({
      'candidate_128_byte_blocks':len(blocks),
      'zero_block_indices':[i for i,b in enumerate(blocks) if not any(b)],
      'populated_block_indices':[i for i,_ in populated],
      'populated_block_count':len(populated),
      'populated_128_byte_footer_pairs_histogram':[
        {'value':list(pair),'count':count} for pair,count in sorted(collections.Counter(footers).items())
      ],
      'aligned_384_384_footer_occurrences':len(aligned_hits),
      'offgrid_384_384_occurrences':len(set(occurrences)-set(aligned_hits)),
      'all_populated_17_leading_u32_are_multiples_of_256':all((v&0xff)==0 for row in dwords for v in row),
      'leading_u32_tested':17*len(dwords),
      'all_populated_bytes_67_through_119_zero':all(not any(b[67:120]) for _,b in populated),
      'populated_first_68_bytes_distinct':len({bytes(b[:68]) for _,b in populated})==len(populated),
    })
    return result


def inventory_and_gate(blob: bytes, *,expected_sha256: str|None=None) -> dict:
    if expected_sha256 is not None and checksum(blob).lower()!=expected_sha256.lower():
        raise AuditError('Supplied original root SHA256 does not match actual bytes')
    chunks=parse_root(blob)
    is_wii_fixture=checksum(blob)==SOURCE_SHA
    scene={'root_sha256':checksum(blob),'root_size':len(blob),
       'source_identity':'exact-original-UC-Wii-RedBuilding-fixture' if is_wii_fixture else 'unknown-provenance-root',
       'caller_supplied_sha256_guard_passed':expected_sha256 is not None,
       'original_carbon_pc_provenance_verified':False,
       'native_pc_34105_schema_verified':False,
       'native_pc_34107_schema_verified':False,
       'chunk_inventory':[
         {'id':f'0x{tag:08x}','size':row['payload_size'],'sha256':checksum(row['data'])}
         for tag,row in chunks.items()],
       'read_only':True,'game_mod_ready':False,
    }
    if TREE in chunks:
        raw=chunks[TREE]['data']; scene['tree_34105_bytes']=len(raw)
        scene['candidate_divisible_node_strides_bytes']=[w for w in CANDIDATE_STRIDES if len(raw)%w==0]
    if INST in chunks:
        try:
            instances,pad,_ = parse_instances(blob,chunks)
            scene['candidate_96byte_instance_count']=len(instances)
            scene['candidate_96byte_instance_padding']=pad
            scene['candidate_96byte_instance_decode_success']=True
            if AUX in chunks:scene['aux_32B_per_candidate_instance']=len(chunks[AUX]['data'])==32*len(instances)
            if is_wii_fixture and TREE in chunks:
                t=analyze_34105(chunks[TREE]['data'],instances)
                scene['wii_fixture_48byte_tree_exactly_verified']=True
                scene['wii_fixture_tree_nodes']=t['node_count']
        except (AuditError,struct.error) as exc:
            scene['candidate_96byte_instance_decode_success']=False
            scene['candidate_96byte_instance_decode_error']=str(exc)
    if UNKNOWN in chunks:
        raw=chunks[UNKNOWN]['data']
        scene['34107_cadence']=audit_34107_cadence(raw)
        if TREE in chunks and scene['34107_cadence'].get('candidate_128_byte_aligned'):
            footers=scene['34107_cadence']['populated_128_byte_footer_pairs_histogram']
            treebytes=len(chunks[TREE]['data'])
            scene['34107_all_populated_footer_words_equal_34105_payload_bytes']=(
                len(footers)==1 and footers[0]['value']==[treebytes,treebytes]
            )
            scene['34107_footer_tree_size_correlation_is_not_pointer_proof']=True
        if scene.get('candidate_96byte_instance_decode_success'):
            scene['34107_size_equals_96_times_candidate_instance_count_plus_one']=len(raw)==96*(scene['candidate_96byte_instance_count']+1)
        if TREE in chunks and len(chunks[TREE]['data'])%48==0:
            scene['34107_size_equals_384_times_candidate_48byte_nodes']=len(raw)==384*(len(chunks[TREE]['data'])//48)
    return scene


def main():
    p=argparse.ArgumentParser(description=__doc__)
    src=p.add_mutually_exclusive_group(required=True)
    src.add_argument('--root',type=Path,help='Standalone scene root (Wii/PC claimed only by provenance)')
    src.add_argument('--stream',type=Path,help='Original whole-stream BUN, with --offset')
    p.add_argument('--offset',type=lambda x:int(x,0),help='Root offset inside --stream')
    p.add_argument('--expected-root-sha256',help='Caller-established original root integrity fingerprint')
    p.add_argument('--candidate',type=Path,help='Standalone V42-style modified root, paired comparison')
    p.add_argument('--wii-fixture',type=Path,help='Optional exact original Wii fixture for paired comparison')
    p.add_argument('--json',type=Path,required=True)
    args=p.parse_args()
    if bool(args.stream)!=bool(args.offset is not None):p.error('--stream requires --offset, and --offset requires --stream')
    if args.wii_fixture and not args.candidate:p.error('--wii-fixture requires --candidate')
    input_files=[x for x in (args.root,args.stream,args.candidate,args.wii_fixture) if x]
    if args.json.suffix.lower()!='.json':p.error('Report must be JSON')
    if args.json.exists():p.error('Refusing to replace existing report')
    if args.json.resolve() in [x.resolve() for x in input_files]:p.error('Refusing output/input overlap')
    blob=read_root_from_stream(args.stream,args.offset) if args.stream else get_root(args.root,None)
    report={'milestone':'V46','source_basename':(args.stream or args.root).name,
            'source_stream_offset':args.offset,'root':inventory_and_gate(blob,expected_sha256=args.expected_root_sha256),
            'no_game_files_modified':True,'no_installer_written':True}
    if args.candidate:
        candidate=get_root(args.candidate,None)
        wii=args.wii_fixture.read_bytes() if args.wii_fixture else None
        report['v42_style_byte_comparison']=compare_v42_style_roots(blob,candidate,source_wii=wii,
                                                  expected_original_sha=args.expected_root_sha256)
    args.json.parent.mkdir(parents=True,exist_ok=True)
    with args.json.open('x',encoding='utf8') as f:
        json.dump(report,f,indent=2,sort_keys=True)
        f.write('\n')
    print('V46 read-only evidence report:',args.json)
    print('Carbon PC layout still unknown without source-authenticated Carbon root and loader evidence')

if __name__=='__main__':main()
