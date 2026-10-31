#!/usr/bin/env python3
"""V58: provenance-gated, READ-ONLY scene-root stream-envelope impact audit.

A verified +200B append inside a nested root would shift bytes after that root
in a flat stream. Neither literal-number matches nor byte preservation proves
Carbon PC pointer/loader/stream registration compatibility. No patch is made.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'v57'))
import v57_append_layout_gate as v57
v55=v57.v55

APPEND_BYTES=200
MAX_WINDOW=2*1024*1024
MAX_WINDOWS=32
MAX_TOTAL_PROBE=16*1024*1024
MAX_HITS_PER_PATTERN=8

class EnvelopeError(v57.LayoutError):
    pass


def checked_int(n,name,minimum=0):
    if not isinstance(n,int) or isinstance(n,bool) or n<minimum:
        raise EnvelopeError(f'{name} must be an integer >= {minimum}')
    return n


def hashes_equal_ranges(path_a:Path,off_a:int,path_b:Path,off_b:int,n:int)->bool:
    """Streaming equal-byte check; inputs opened for reading only."""
    checked_int(n,'range length')
    chunk=1024*1024
    with path_a.open('rb') as a,path_b.open('rb') as b:
        a.seek(off_a);b.seek(off_b)
        left=n
        while left:
            size=min(left,chunk)
            aa=a.read(size);bb=b.read(size)
            if len(aa)!=size or len(bb)!=size or aa!=bb:return False
            left-=size
    return True


def _bounds(stream_spec,root:bytes):
    stream=Path(stream_spec['path'])
    size=stream.stat().st_size
    offset=stream_spec.get('offset',None)
    if offset is None:
        if size!=len(root):
            raise EnvelopeError('standalone root must equal source file length')
        return ('standalone_root',0,size,size)
    checked_int(offset,'stream ROOT offset')
    if offset+len(root)>size:
        raise EnvelopeError('ROOT extends beyond source stream')
    return ('embedded_ROOT',offset,offset+len(root),size)


def absolute_projection(root:bytes,source_spec:dict,byteorder:str):
    scheme=v57.predict(root,byteorder)
    scope,start,end,size=_bounds(source_spec,root)
    items=[]
    for x in scheme['projected_children']:
        old=start+x['original_payload_start']
        new=start+x['projected_payload_start']
        items.append({'child_id':x['child_id'],
                      'root_relative_original_payload_start':x['original_payload_start'],
                      'root_relative_projected_payload_start':x['projected_payload_start'],
                      'stream_absolute_original_payload_start':old,
                      'stream_absolute_projected_payload_start':new,
                      'absolute_shift':new-old,
                      'old_absolute_mod16':old%16,'new_absolute_mod16':new%16})
    return {'root_scope':scope,'root_stream_offset':start,
            'original_root_end_exclusive':end,
            'projected_root_end_exclusive':end+APPEND_BYTES,
            'original_file_bytes':size,
            'hypothetical_file_bytes_after_insertion':size+APPEND_BYTES,
            'external_prefix_bytes_unmoved':start,
            'external_suffix_bytes_that_would_shift':size-end,
            'external_suffix_displacement_bytes':APPEND_BYTES if scope=='embedded_ROOT' and size>end else 0,
            'child_absolute_offsets':items,
            'projected_root_sha256':None,
            'actual_modified_game_file_generated':False,
            'root_chunk_layout_from_SHA256_guarded_input':True,
            'external_master_table_relocation_verified':False,
            'carbon_pc_loader_compatibility_verified':False,
            'safe_to_install':False}


def strict_exterior_pair(original_spec,original_root,candidate_spec,candidate_root,order):
    """Strict byte-identical *outside* roots. Legitimate relocation changes
    outside ROOT would fail this narrow contract, NOT mean an invalid PC file.
    """
    original_path=Path(original_spec['path']);candidate_path=Path(candidate_spec['path'])
    old_scope,old_start,old_end,old_size=_bounds(original_spec,original_root)
    new_scope,new_start,new_end,new_size=_bounds(candidate_spec,candidate_root)
    if old_scope!='embedded_ROOT' or new_scope!='embedded_ROOT':
        raise EnvelopeError('paired envelope audit requires two embedded ROOTs')
    if old_start!=new_start:
        raise EnvelopeError('ROOT position changed; same-offset contract not applicable')
    if new_size!=old_size+APPEND_BYTES:
        raise EnvelopeError('file envelope is not exactly +200 bytes')
    if new_end!=old_end+APPEND_BYTES:
        raise EnvelopeError('candidate root end has wrong offset')
    if new_size-new_end!=old_size-old_end:
        raise EnvelopeError('external suffix lengths differ')
    layout=v57.audit_pair(original_root,candidate_root,order)
    prefix_ok=hashes_equal_ranges(original_path,0,candidate_path,0,old_start)
    suffix_ok=hashes_equal_ranges(original_path,old_end,candidate_path,new_end,old_size-old_end)
    if not prefix_ok:raise EnvelopeError('external prefix changed (strict no-relocation contract)')
    if not suffix_ok:raise EnvelopeError('external suffix changed (strict no-relocation contract)')
    return {'status':'byte_identical_exterior_with_plus_200_root_only',
            'root_append_contract_passed':layout['byte_preserving_append_contract_passed'],
            'external_prefix_unchanged':True,'external_suffix_unchanged_after_shift':True,
            'suffix_bytes_shifted':old_size-old_end,
            'does_not_verify_external_offsets_or_relocations':True,
            'does_not_disprove_legitimate_relocations_that_modify_exterior':True,
            'safe_to_install':False}


def _literal_patterns(old_root,start,end,children,order):
    locations={'root_start':start,'root_end_exclusive':end}
    for x in children:
        if x['child_id'] in ('0x34105','0x34107'):
            locations['child_'+x['child_id']]=x['stream_absolute_original_payload_start']
    e=v55.endian(order)
    pats=[]
    for name,n in locations.items():
        for bits in (32,64):
            if n >= 1<<bits: continue
            pats.append((name,bits,n,struct.pack(e+('I' if bits==32 else 'Q'),n)))
    return pats


def literal_windows(spec,root,byteorder,projection,windows):
    """Bounded 4/8-byte *numerical coincidence* scan, never pointer discovery."""
    if not isinstance(windows,list) or len(windows)>MAX_WINDOWS:
        raise EnvelopeError('probe windows must be an array of <= 32 windows')
    scope,start,end,size=_bounds(spec,root)
    if scope!='embedded_ROOT' and windows:
        raise EnvelopeError('probe windows require an embedded ROOT in a stream')
    total=0; out=[]
    pats=_literal_patterns(root,start,end,projection['child_absolute_offsets'],byteorder)
    with Path(spec['path']).open('rb') as f:
        for i,w in enumerate(windows):
            if not isinstance(w,dict):raise EnvelopeError('each probe window must be an object')
            off=checked_int(w.get('offset'),'window offset')
            length=checked_int(w.get('length'),'window length',minimum=1)
            if length>MAX_WINDOW or off+length>size:
                raise EnvelopeError('probe window too large or out of stream bounds')
            total+=length
            if total>MAX_TOTAL_PROBE:raise EnvelopeError('aggregate probe windows exceed limit')
            if off<end and off+length>start:
                raise EnvelopeError('probe window overlaps original ROOT; exterior only')
            f.seek(off);data=f.read(length)
            if len(data)!=length:raise EnvelopeError('truncated probe read')
            matches=[]
            for name,bits,number,pattern in pats:
                if len(pattern)>len(data):continue
                pos=0; count=0; offsets=[]
                while (pos:=data.find(pattern,pos))!=-1:
                    count+=1
                    if len(offsets)<MAX_HITS_PER_PATTERN:offsets.append(off+pos)
                    pos+=1
                if count:matches.append({'pattern_name':name,'encoded_bits':bits,
                                         'numeric_value':number,'count':count,
                                         'example_offsets':offsets})
            out.append({'window_index':i,'start':off,'end_exclusive':off+length,
                        'literal_number_matches':matches})
    return {'scope':'only_exterior_windows','total_bytes_examined':total,
            'windows':out,'matches_are_not_proven_pointers':True,
            'no_relocation_writer':True}


def report(manifest):
    if not isinstance(manifest,dict) or 'original' not in manifest:
        raise EnvelopeError('manifest must include an original source entry')
    original,_,meta=v55.read_verified_root(manifest['original'])
    order=meta['endian']
    projection=absolute_projection(original,manifest['original'],order)
    report={'schema':'v58-source-gated-stream-envelope-v1',
            'original_file_sha256':meta['file_sha256'],
            'original_root_sha256':meta['root_sha256'],
            'authenticated_original_Wii_root':meta['root_sha256']==v55.WII_REDBUILDING_SHA and order=='little',
            'projection':projection,'source_platform_hint_not_proof':meta['platform_hint_unverified'],
            'carbon_pc_serialized_and_loader_abi_proven':False,
            'master_table_relocated_or_validated':False,
            'read_only':True,'safe_to_install':False}
    if 'windows' in manifest:
        report['exterior_numeric_probe']=literal_windows(manifest['original'],original,order,projection,manifest['windows'])
    if 'candidate' in manifest:
        candidate,_,cm=v55.read_verified_root(manifest['candidate'])
        if cm['endian']!=order:raise EnvelopeError('source and candidate endian differ')
        report['strict_envelope_pair']=strict_exterior_pair(manifest['original'],original,manifest['candidate'],candidate,order)
    return report


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--manifest',type=Path,required=True)
    ap.add_argument('--report',type=Path,required=True)
    args=ap.parse_args()
    if args.report.exists() or args.report.resolve()==args.manifest.resolve():
        ap.error('refusing to overwrite report or manifest')
    data=json.loads(args.manifest.read_text(encoding='utf-8'))
    if not isinstance(data,dict):ap.error('manifest must be an object')
    for key in ('original','candidate'):
        if key in data and isinstance(data[key],dict):
            p=data[key].get('path')
            if isinstance(p,str) and args.report.resolve()==Path(p).resolve():
                ap.error('refusing to overwrite original or candidate file')
    result=report(data)
    args.report.parent.mkdir(parents=True,exist_ok=True)
    with args.report.open('x',encoding='utf-8') as f:
        json.dump(result,f,sort_keys=True,indent=2);f.write('\n')
    print('V58 read-only envelope audit complete:',args.report)


if __name__=='__main__':main()