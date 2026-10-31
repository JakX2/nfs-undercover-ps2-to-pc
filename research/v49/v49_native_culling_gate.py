#!/usr/bin/env python3
"""V49: read-only 96/48/128-byte scenery-culling hypothesis and append audit.

The layouts match publicly reverse-engineered Carbon PC *runtime* structures
at xoxor4d/nfsc-rtx commit 252b44b877c207a9a70914d92c31f116ad92a469.
This DOES NOT establish serialized 0x34105/0x34107 equivalence or installability.
All inputs are read-only; no native scenery writer is provided.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
import math
import mmap
from pathlib import Path
import struct

ROOT=0x80034100
SCENE=0x34101; INFO=0x34102; INSTANCE=0x34103
TREE=0x34105; PRECULL=0x34107; AUX=0x3410D
MAX_ROOT=64*1024*1024
PINNED_COMMIT='252b44b877c207a9a70914d92c31f116ad92a469'
PINNED_STRUCTS_BLOB='2ebb2ed91ceeaeef61b55d85aa43b92f7f8ef711'
PINNED_CULL_HOOK_BLOB='2678c85de20d7827287b407e52485139fe837f98'
WII_REDBUILDING_SHA='cb08ca728a9b76992aaaefe32b450565ef53246f090cfe296f77d96c5d272e7f'

class GateError(ValueError):
    pass

def digest(b):
    return hashlib.sha256(b).hexdigest()

def endian_prefix(value):
    if value not in ('little','big'):
        raise GateError('endian must be little or big')
    return '<' if value=='little' else '>'

def parse_root(b:bytes,endian:str):
    e=endian_prefix(endian)
    if len(b)<8 or len(b)>MAX_ROOT:
        raise GateError('root outside bounded size')
    rid,size=struct.unpack_from(e+'II',b)
    if rid!=ROOT or size!=len(b)-8:
        raise GateError('root ID or declared length mismatch')
    pos=8; out={}
    while pos<len(b):
        if pos+8>len(b):raise GateError('truncated child header')
        cid,n=struct.unpack_from(e+'II',b,pos);pos+=8
        if cid&0x80000000 or cid in out or n>len(b)-pos:
            raise GateError('nested, duplicate or out-of-bounds child')
        out[cid]=b[pos:pos+n];pos+=n
    if any(k not in out for k in (SCENE,INFO,INSTANCE)):
        raise GateError('mandatory scenery children absent')
    if len(out[SCENE])<4 or len(out[INFO])%72:
        raise GateError('invalid scene identifier or 72-byte info rows')
    return out

def extract_root(path:Path,endian:str,offset:int|None=None,expected_file_sha:str|None=None):
    e=endian_prefix(endian)
    if expected_file_sha:
        h=hashlib.sha256()
        with path.open('rb') as f:
            for block in iter(lambda:f.read(4*1024*1024),b''):
                h.update(block)
        if h.hexdigest()!=expected_file_sha.lower():
            raise GateError('input file SHA256 guard failed')
    if offset is None:
        if path.stat().st_size>MAX_ROOT:
            raise GateError('standalone root too large: provide --offset')
        b=path.read_bytes()
    else:
        if offset<0 or offset+8>path.stat().st_size:
            raise GateError('offset outside file')
        with path.open('rb') as f:
            f.seek(offset);hdr=f.read(8)
            rid,n=struct.unpack(e+'II',hdr)
            if rid!=ROOT or n>MAX_ROOT-8 or n>path.stat().st_size-offset-8:
                raise GateError('invalid framed root at offset')
            b=hdr+f.read(n)
    parse_root(b,endian)
    return b

def child_payload_offset(root:bytes,endian:str,child_id:int):
    """Return absolute offset in the ROOT for a validated direct child payload.

    This matters because UC Wii pads instance rows to a 16-byte *root*
    boundary, rather than starting the first record at payload byte zero.
    The observation does NOT establish Carbon PC's serialized ABI.
    """
    e=endian_prefix(endian)
    pos=8
    while pos<len(root):
        cid,n=struct.unpack_from(e+'II',root,pos)
        if cid==child_id:
            return pos+8
        pos+=8+n
    raise GateError(f'child 0x{child_id:05X} absent from root')


def instance96_padding(root:bytes,endian:str):
    """Candidate 16-byte absolute alignment of the first 96-byte instance."""
    return (-child_payload_offset(root,endian,INSTANCE)) & 15


def instances96(ch:dict[int,bytes],endian:str,root:bytes):
    e=endian_prefix(endian);b=ch[INSTANCE]
    pad=instance96_padding(root,endian)
    if len(b)<pad or (len(b)-pad)%96:
        raise GateError('aligned 96-byte instance hypothesis not size-compatible')
    out=[];ninfos=len(ch[INFO])//72
    for i in range((len(b)-pad)//96):
        p=pad+i*96
        mn=struct.unpack_from(e+'3f',b,p)
        mx=struct.unpack_from(e+'3f',b,p+16)
        xyz=struct.unpack_from(e+'3f',b,p+32)
        info=struct.unpack_from(e+'h',b,p+84)[0]
        prec=struct.unpack_from(e+'h',b,p+28)[0]
        if not all(map(math.isfinite,mn+mx+xyz)) or any(a>b for a,b in zip(mn,mx)):
            raise GateError(f'instance {i} has invalid bounding box/position')
        if info>=ninfos:
            raise GateError(f'instance {i} has out-of-range nonnegative model-info index')
        out.append({'min':mn,'max':mx,'position':xyz,'info':info,'preculler':prec})
    return out

def tree48_audit(tree:bytes,rows:list[dict],endian:str,tolerance:float=0.0):
    e=endian_prefix(endian)
    if not math.isfinite(tolerance) or tolerance<0:
        raise GateError('invalid AABB tolerance')
    if not tree or len(tree)%48:
        raise GateError('tree not a nonempty 48-byte array')
    nodes=[]
    for i in range(len(tree)//48):
        b=tree[48*i:48*(i+1)]
        mn=struct.unpack_from(e+'3f',b,0);mx=struct.unpack_from(e+'3f',b,16)
        count=struct.unpack_from(e+'H',b,12)[0]
        if count>10 or not all(map(math.isfinite,mn+mx)) or any(a>b for a,b in zip(mn,mx)):
            raise GateError(f'invalid tree node {i}')
        refs=list(struct.unpack_from(e+str(count)+'h',b,28)) if count else []
        nodes.append({'min':mn,'max':mx,'refs':refs})
    active=set();visited=set();leaves=[];max_error=0.0
    def walk(i):
        nonlocal max_error
        if not 0<=i<len(nodes):raise GateError(f'tree node {i} out of range')
        if i in active:raise GateError('tree cycle')
        if i in visited:raise GateError('tree node referenced more than once')
        active.add(i);desc=[]
        for ref in nodes[i]['refs']:
            if ref>=0:
                if ref>=len(rows):raise GateError('tree references out-of-range instance')
                leaves.append(ref);desc.append(rows[ref])
            else:
                if -ref==0:raise GateError('invalid child node zero reference')
                desc.extend(walk(-ref))
        if not desc:raise GateError('tree node has no descendants')
        for k in range(3):
            min_actual=min(x['min'][k] for x in desc)
            max_actual=max(x['max'][k] for x in desc)
            max_error=max(max_error,abs(nodes[i]['min'][k]-min_actual),abs(nodes[i]['max'][k]-max_actual))
        active.remove(i);visited.add(i)
        return desc
    walk(0)
    if len(visited)!=len(nodes):raise GateError('unreachable tree nodes')
    if len(leaves)!=len(rows) or len(set(leaves))!=len(rows):
        raise GateError(f'incomplete/duplicate instance coverage: covered={len(set(leaves))}, expected={len(rows)}')
    if max_error>tolerance:
        raise GateError(f'node AABB union differs: {max_error}')
    return {'status':'candidate_48_byte_tree_pass','nodes':len(nodes),'covered_instances':len(rows),
            'max_aabb_error':max_error,'semantic_scope':'hypothesis_only_not_PC_loader_proof'}

def bit_positions(b:bytes):
    """LSB-first bit positions within each byte, no semantic interpretation."""
    return [8*i+bit for i,byte in enumerate(b) for bit in range(8) if byte&(1<<bit)]

def preculler128_audit(payload:bytes,rows:list[dict],endian:str):
    e=endian_prefix(endian)
    if len(payload)%128:raise GateError('0x34107 not divisible by 128')
    blocks=[payload[i:i+128] for i in range(0,len(payload),128)]
    pos=[bit_positions(b) for b in blocks]
    refs=[x['preculler'] for x in rows]
    invalid=sorted(set(x for x in refs if x>=len(blocks)))
    nonnegative=set(x for x in refs if x>=0)
    negative=Counter(str(x) for x in refs if x<0)
    footer=Counter(str(struct.unpack_from(e+'II',b,120)) for b in blocks)
    return {'status':'128_byte_preculler_hypothesis_only',
            'bytes':len(payload),'blocks':len(blocks),'sha256':digest(payload),
            'zero_blocks':sum(not b for b in pos),'bit_count_by_block':[len(p) for p in pos],
            'referenced_block_indices':sorted(nonnegative),
            'unreferenced_block_indices':sorted(set(range(len(blocks)))-nonnegative),
            'invalid_nonnegative_indices':invalid,
            'negative_instance_index_histogram':dict(negative),
            'footer_u32_pair_histogram':dict(footer),
            'bit_order':'bit index = 8*byte_offset + least-significant-bit position',
            'source_status':'third_party_runtime_abi; serialized_chunk_mapping_unverified'}

def audit_root(b:bytes,endian:str,expected_sha:str|None=None,tolerance:float=0.0):
    if expected_sha and digest(b)!=expected_sha.lower():
        raise GateError('root SHA256 guard failed')
    ch=parse_root(b,endian);e=endian_prefix(endian)
    out={'sha256':digest(b),'bytes':len(b),'endian':endian,
         'section_id':f'0x{struct.unpack_from(e+"I",ch[SCENE])[0]:08X}',
         'child_lengths':{f'0x{k:05X}':len(v) for k,v in ch.items()},
         'info_count_72':len(ch[INFO])//72,
         'instance_stride_candidates':[s for s in (64,96) if len(ch[INSTANCE])%s==0],
         'candidate_instance96_root_alignment_padding_bytes':instance96_padding(b,endian),
         'pc_serialized_abi_proven':False,'safe_to_install':False}
    try:
        rows=instances96(ch,endian,b)
    except GateError as exc:
        out['instance96']={'status':'candidate_rejected','reason':str(exc)}
        return out
    out['instance96']={'status':'candidate_structurally_accepted','count':len(rows),
                       'model_info_negative_indices':dict(Counter(str(x['info']) for x in rows if x['info']<0))}
    if TREE in ch:
        try:out['tree48']=tree48_audit(ch[TREE],rows,endian,tolerance)
        except GateError as exc:out['tree48']={'status':'candidate_rejected','reason':str(exc)}
    else:out['tree48']={'status':'missing'}
    if PRECULL in ch:
        try:out['preculler128']=preculler128_audit(ch[PRECULL],rows,endian)
        except GateError as exc:out['preculler128']={'status':'candidate_rejected','reason':str(exc)}
    else:out['preculler128']={'status':'missing'}
    if AUX in ch:
        out['aux32']={'count_candidate':len(ch[AUX])//32 if len(ch[AUX])%32==0 else None,
                      'count_matches_instance96':len(ch[AUX])==32*len(rows)}
    return out

def audit_append(original:bytes,candidate:bytes,endian:str,expected_original_sha:str|None=None):
    if expected_original_sha and digest(original)!=expected_original_sha.lower():
        raise GateError('original root SHA256 guard failed')
    a=parse_root(original,endian);b=parse_root(candidate,endian)
    if list(a)!=list(b):raise GateError('child ordering/identity changed')
    if AUX not in a:raise GateError('missing auxiliary array in donor')
    for cid,old in a.items():
        new=b[cid]
        if cid in (INFO,INSTANCE,AUX):
            stride={INFO:72,INSTANCE:96,AUX:32}[cid]
            if not new.startswith(old) or len(new)!=len(old)+stride:
                raise GateError(f'0x{cid:05X} is not exactly one-row append')
        elif new!=old:raise GateError(f'0x{cid:05X} original bytes changed')
    oldrows=instances96(a,endian,original);newrows=instances96(b,endian,candidate)
    if len(newrows)!=len(oldrows)+1 or newrows[-1]['info']!=len(a[INFO])//72:
        raise GateError('new instance/index inconsistent with one appended info')
    old=audit_root(original,endian);new=audit_root(candidate,endian)
    return {'status':'byte_preserving_append_only_NOT_installable',
            'original_sha256':digest(original),'candidate_sha256':digest(candidate),
            'old_instance_count':len(oldrows),'new_instance_count':len(newrows),
            'original_instance_padding_bytes':instance96_padding(original,endian),
            'candidate_instance_padding_bytes':instance96_padding(candidate,endian),
            'new_preculler_index':newrows[-1]['preculler'],
            'tree_original':old.get('tree48'),'tree_candidate':new.get('tree48'),
            'preculler_candidate':new.get('preculler128'),
            'tree_bytes_unchanged':a.get(TREE)==b.get(TREE),
            'preculler_bytes_unchanged':a.get(PRECULL)==b.get(PRECULL),
            'safe_to_install':False,
            'missing_gates':['original_Carbon_PC_loader','serialized_spatial_tree_semantics',
              'preculler_registration','stream_ownership_relocations','material_TPK_shader',
              'collision_navigation','executable_in_game_test']}

def scan_stream(path:Path,endian:str,limit:int|None=None):
    e=endian_prefix(endian);size=path.stat().st_size
    result={'bytes':size,'endian':endian,'accepted':[],'rejected':0,
            'accepted_count_is_NOT_exhaustive_if_limit_set':limit is not None}
    if size==0:return result
    marker=struct.pack(e+'I',ROOT)
    with path.open('rb') as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as mm:
        pos=0
        while (pos:=mm.find(marker,pos))!=-1:
            if pos+8<=size:
                n=struct.unpack_from(e+'I',mm,pos+4)[0]
                if n<=MAX_ROOT-8 and n<=size-pos-8:
                    try:
                        b=mm[pos:pos+8+n]
                        x=audit_root(b,endian)
                        result['accepted'].append({'offset':pos,'audit':x})
                        if limit is not None and len(result['accepted'])>=limit:break
                    except GateError:result['rejected']+=1
                else:result['rejected']+=1
            pos+=1
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--original',required=True,type=Path,help='read-only standalone root or BUN')
    p.add_argument('--candidate',type=Path,help='optional read-only V42-style standalone candidate')
    p.add_argument('--endian',required=True,choices=['little','big'])
    p.add_argument('--offset',type=lambda s:int(s,0),help='original stream root offset')
    p.add_argument('--expected-file-sha256')
    p.add_argument('--expected-root-sha256')
    p.add_argument('--scan-stream',action='store_true')
    p.add_argument('--limit',type=int)
    p.add_argument('--report',type=Path)
    a=p.parse_args()
    if a.scan_stream and (a.offset is not None or a.candidate or a.expected_root_sha256):
        p.error('whole-stream scan incompatible with offset/candidate/root SHA')
    if a.limit is not None and (a.limit<1 or not a.scan_stream):
        p.error('--limit requires --scan-stream and a positive value')
    if a.report and a.report.resolve() in {a.original.resolve(),a.candidate.resolve() if a.candidate else None}:
        p.error('refusing to overwrite an input file')
    if a.scan_stream:
        if a.expected_file_sha256:
            h=hashlib.sha256()
            with a.original.open('rb') as f:
                for chunk in iter(lambda:f.read(4*1024*1024),b''):h.update(chunk)
            if h.hexdigest()!=a.expected_file_sha256.lower():raise GateError('input file SHA256 guard failed')
        out={'scan':scan_stream(a.original,a.endian,a.limit)}
    else:
        original=extract_root(a.original,a.endian,a.offset,a.expected_file_sha256)
        out={'original':audit_root(original,a.endian,a.expected_root_sha256)}
        if a.candidate:
            candidate=extract_root(a.candidate,a.endian)
            out['append']=audit_append(original,candidate,a.endian,a.expected_root_sha256)
    out['provenance']={'upstream_commit':PINNED_COMMIT,'structs_blob':PINNED_STRUCTS_BLOB,
        'cull_hook_blob':PINNED_CULL_HOOK_BLOB,'input_authenticity_requires_external_provenance':True}
    out['runtime_tested']=False;out['safe_to_install']=False
    s=json.dumps(out,indent=2)+'\n'
    if a.report:a.report.write_text(s,encoding='utf-8')
    else:print(s,end='')

if __name__=='__main__':main()