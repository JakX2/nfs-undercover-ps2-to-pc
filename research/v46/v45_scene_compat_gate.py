#!/usr/bin/env python3
"""V45: safe, read-only cross-version scenery-root and opaque-byte structure gate.

This script describes SOURCE BYTES and conservative diffs only. It does not
assert that a Wii 48B hierarchy is a Carbon PC hierarchy, nor decode 0x34107.
No writer, no installable patches, no world-file modifications.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import struct

from v43_spatial_audit import (
    ROOT, INFO, INST, AUX, TREE, UNKNOWN, AuditError,
    SOURCE_SHA, parse_root, parse_instances, analyze_34105, checksum,
    read_root_from_stream,
)

WII_INSTANCE_SIZE=96
KNOWN_INFO_WIDTH=72
KNOWN_AUX_WIDTH=32
CANDIDATE_BLOCK=128
MAX_ROOT_SIZE=512*1024*1024


def payload_instances(root: bytes, chunks: dict) -> tuple[bytes, bytes, list[bytes]]:
    if INST not in chunks:
        raise AuditError('No 0x34103 instance chunk')
    piece=chunks[INST]
    lo=piece['payload_offset']
    aligned=(lo+15)&~15
    hi=lo+piece['payload_size']
    if aligned>hi or (hi-aligned)%WII_INSTANCE_SIZE:
        raise AuditError('Instance row framing is not the explicit V42 96B candidate')
    return root[lo:aligned], root[aligned:hi], [root[o:o+96] for o in range(aligned,hi,96)]


def _u32s(b:bytes):
    return list(struct.unpack('<'+'I'*(len(b)//4),b))


def contiguous_ranges(offsets):
    ranges=[]
    for n in sorted(set(offsets)):
        if not ranges or n>ranges[-1][1]+1:
            ranges.append([n,n])
        else:
            ranges[-1][1]=n
    return [{'start':a,'end_exclusive':b+1,'length':b-a+1} for a,b in ranges]


def opaque_34107_lane_map(raw:bytes):
    if len(raw)%CANDIDATE_BLOCK:
        return {'bytes':len(raw),'candidate_128_byte_blocks':None,
                'reason':'Payload not 128-byte divisible; no lane decoding performed'}
    blocks=[raw[i:i+CANDIDATE_BLOCK] for i in range(0,len(raw),CANDIDATE_BLOCK)]
    populated=[b for b in blocks if any(b)]
    if not populated:
        return {'bytes':len(raw),'candidate_128_byte_blocks':len(blocks),
                'populated_blocks':0,'no_semantic_record_claim':True}
    constant_off=[i for i in range(128) if len({b[i] for b in populated})==1]
    zero_off=[i for i in range(128) if all(b[i]==0 for b in populated)]
    variable_off=[i for i in range(128) if i not in constant_off]
    variable_dwords=[i for i in range(32) if len({struct.unpack_from('<I',b,i*4)[0] for b in populated})>1]
    return {'bytes':len(raw),'candidate_128_byte_blocks':len(blocks),
            'populated_blocks':len(populated),'zero_blocks':sum(not any(b) for b in blocks),
            'constant_byte_offset_ranges':contiguous_ranges(constant_off),
            'zero_byte_offset_ranges':contiguous_ranges(zero_off),
            'variable_byte_offset_ranges':contiguous_ranges(variable_off),
            'variable_dword_indices':variable_dwords,
            'populated_head_68_bytes_all_unique':len({b[:68] for b in populated})==len(populated),
            'populated_footer_u32_pairs':sorted({struct.unpack_from('<II',b,120) for b in populated}),
            'populated_common_all_zero_window_68_to_119':all(b[68:120]==bytes(52) for b in populated),
            'no_semantic_record_claim':True}


def stale_membership_probe(scene: bytes, expected_source_hash: str=SOURCE_SHA):
    if checksum(scene)!=expected_source_hash:
        raise AuditError('Unrecognized source fixture; cannot run original-byte-backed mutation probe')
    chunks=parse_root(scene)
    inst,_pad,_hash=parse_instances(scene,chunks)
    if TREE not in chunks:
        raise AuditError('Fixture lacks 0x34105')
    baseline=analyze_34105(chunks[TREE]['data'],inst)
    new_record=dict(inst[26])
    new_record['slot']=len(inst)
    mutated=inst+[new_record]
    try:
        analyze_34105(chunks[TREE]['data'],mutated)
    except AuditError as e:
        return {'probe':'IN MEMORY ONLY; virtual extra instance slot',
                'original_instances':len(inst),'virtual_instances':len(mutated),
                'verified_original_nodes':baseline['node_count'],
                'unmodified_tree_rejected':True,'rejection_reason':str(e),
                'carbon_pc_applicability_verified':False}
    raise AuditError('Unexpectedly accepted a new instance with unchanged spatial membership')


def compare_v42_style_roots(original:bytes,candidate:bytes, source_wii:bytes|None=None,
                             expected_original_sha:str|None=None):
    """Strict, format-limited original vs prototype comparison. Never writes input."""
    if expected_original_sha and checksum(original)!=expected_original_sha:
        raise AuditError('Donor PC root does not match specified source SHA256')
    old=parse_root(original); new=parse_root(candidate)
    if set(old)!=set(new):
        raise AuditError('Child type inventory changed')
    if list(old)!=list(new):
        raise AuditError('Child ordering changed')
    required={INFO,INST,AUX,TREE,UNKNOWN}
    if not required<=set(old):
        raise AuditError('Required V42-style scene children missing')
    if len(old[INFO]['data'])%KNOWN_INFO_WIDTH:
        raise AuditError('Donor info table does not have 72B stride')
    ninfo=len(old[INFO]['data'])//KNOWN_INFO_WIDTH
    old_pad,old_flat,old_rows=payload_instances(original,old)
    new_pad,new_flat,new_rows=payload_instances(candidate,new)
    if ninfo!=len(old_rows):
        raise AuditError('Donor has unequal info and instance rows; cannot apply V42-specific contract')
    if len(old[AUX]['data'])!=len(old_rows)*KNOWN_AUX_WIDTH:
        raise AuditError('Donor aux count differs from instances')
    checks={
        'children_order_identical':list(old)==list(new),
        'original_opaque_children_byte_identical':all(old[k]['data']==new[k]['data'] for k in old if k not in {INFO,INST,AUX}),
        'original_96B_instances_byte_identical':new_pad==old_pad and new_flat.startswith(old_flat),
        'original_72B_infos_byte_identical':new[INFO]['data'].startswith(old[INFO]['data']),
        'original_32B_aux_byte_identical':new[AUX]['data'].startswith(old[AUX]['data']),
        'one_appended_instance':len(new_rows)==len(old_rows)+1,
        'one_appended_info':len(new[INFO]['data'])==len(old[INFO]['data'])+KNOWN_INFO_WIDTH,
        'one_appended_aux':len(new[AUX]['data'])==len(old[AUX]['data'])+KNOWN_AUX_WIDTH,
        'root_size_delta_200_bytes':len(candidate)-len(original)==200,
        'new_info_index_points_to_appended_info':len(new_rows)==len(old_rows)+1 and struct.unpack_from('<h',new_rows[-1],0x54)[0]==ninfo,
    }
    if source_wii is not None:
        if checksum(source_wii)!=SOURCE_SHA:
            raise AuditError('Provided Wii source does not match verified original 8488B fixture')
        wparts=parse_root(source_wii)
        _p,_d,wi=payload_instances(source_wii,wparts)
        if len(wi)!=31:
            raise AuditError('Unexpected Wii fixture instance count')
        source=wi[26]
        appended=new_rows[-1]
        checks['new_record_matches_Wii_instance26_except_info_index']=appended[:0x54]==source[:0x54] and appended[0x56:]==source[0x56:]
        checks['new_aux_exactly_matches_Wii_instance26']=new[AUX]['data'][-32:]==wparts[AUX]['data'][26*32:27*32]
    checks['all_checked_byte_contracts_pass']=all(checks.values())
    return {'tool':'v45-readonly-paired-root-byte-contract','original_root_sha256':checksum(original),
        'candidate_root_sha256':checksum(candidate), 'original_root_bytes':len(original),
        'candidate_root_bytes':len(candidate),'original_instance_count':len(old_rows),
        'candidate_instance_count':len(new_rows),'checks':checks,
        'attention': '0x34105 and 0x34107 are unchanged; this is a BYTE contract only, NOT proof of spatial membership, runtime registration, or rendering.',
        'carbon_pc_34105_schema_proven':False,'carbon_pc_34107_schema_proven':False,
        'game_install_safe':False,'writer_exists':False}


def get_root(path:Path,offset:int|None):
    if offset is not None:
        return read_root_from_stream(path,offset)
    size=path.stat().st_size
    if size<8 or size>MAX_ROOT_SIZE:
        raise AuditError('Expected standalone root; for full world BUN supply --original-offset')
    with path.open('rb') as f:
        h=f.read(8)
        if struct.unpack_from('<II',h,0)!=(ROOT,size-8):
            raise AuditError('Standalone root framing invalid; full world streams require --original-offset')
        return h+f.read()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--wii-scene',type=Path,help='Original source Wii RedBuilding scene for read-only analysis')
    p.add_argument('--original-pc',type=Path,help='Original PC root or original game stream')
    p.add_argument('--original-offset',type=lambda v:int(v,0))
    p.add_argument('--candidate-pc',type=Path,help='Standalone V42-style PC prototype root')
    p.add_argument('--original-pc-sha256')
    p.add_argument('--json',type=Path,required=True,help='New JSON report, never existing input')
    a=p.parse_args()
    if not a.wii_scene and not (a.original_pc and a.candidate_pc):
        p.error('Provide --wii-scene and/or both --original-pc and --candidate-pc')
    if bool(a.original_pc)!=bool(a.candidate_pc):
        p.error('--original-pc and --candidate-pc must be supplied together')
    if a.original_offset is not None and a.original_pc is None:
        p.error('--original-offset requires --original-pc')
    inputs=[x.resolve() for x in (a.wii_scene,a.original_pc,a.candidate_pc) if x]
    if a.json.resolve() in inputs: p.error('Refusing to overwrite original inputs')
    if a.json.exists(): p.error('Output report exists; refusing overwrite')
    result={'tool':'v45-readonly-scene-compatibility-gate','game_files_modified':False,'installable_mod_created':False,
            'known_contrast':'Undercover Wii fixture 96B instances/48B 0x34105 nodes; publicly described Most Wanted 2005 PC 64B/36B; Carbon PC must be independently checked'}
    src=None
    if a.wii_scene:
        src=a.wii_scene.read_bytes()
        if checksum(src)!=SOURCE_SHA:
            raise AuditError('Wii original scene SHA mismatch')
        parts=parse_root(src)
        result['verified_wii_source_sha256']=checksum(src)
        result['wii_34105_stale_membership_probe']=stale_membership_probe(src)
        result['wii_34107_lane_map']=opaque_34107_lane_map(parts[UNKNOWN]['data'])
    if a.original_pc:
        original=get_root(a.original_pc,a.original_offset)
        candidate=get_root(a.candidate_pc,None)
        result['pc_candidate_byte_contract']=compare_v42_style_roots(original,candidate,source_wii=src,expected_original_sha=a.original_pc_sha256)
    a.json.parent.mkdir(parents=True,exist_ok=True)
    with a.json.open('x',encoding='utf8') as f:
        json.dump(result,f,indent=2,sort_keys=True)
        f.write('\n')
    print('V45 READ ONLY report',a.json)
    print('No game streams were modified; Carbon PC culling schema not claimed verified.')

if __name__=='__main__': main()
