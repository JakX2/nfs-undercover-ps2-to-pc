#!/usr/bin/env python3
"""V56: fail-closed, read-only *candidate Wii* scenery graph consistency gate.

A size match is not a serialized-format proof. This script uses the V55
fingerprint-gated root loader, then reports whether the Wii 96/48/128/32
hypotheses also satisfy cross-reference, tree coverage and AABB invariants.
Every other game/platform stays unverified regardless of its numerical fit.
No patch, serialized writer or game bytes are emitted.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
import math
from pathlib import Path
import struct
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'v55'))
import v55_cross_scene_hypothesis_gate as prior

WII_SHA=prior.WII_REDBUILDING_SHA
INFO=0x34102

class CandidateError(prior.GateError):
    pass


def candidate_rows(children:dict, order:str):
    if prior.INSTANCE not in children:
        raise CandidateError('instance chunk absent')
    start,raw=children[prior.INSTANCE];pad=(-start)&15
    if len(raw)<pad or (len(raw)-pad)%96:
        raise CandidateError('96-byte rows not aligned to root-relative 16-byte candidate boundary')
    n=(len(raw)-pad)//96
    if not n:raise CandidateError('no candidate instances')
    e=prior.endian(order);rows=[]
    if INFO not in children:raise CandidateError('candidate 72-byte scenery info table absent')
    ib=children[INFO][1]
    if not ib or len(ib)%72:raise CandidateError('scenery info table not a nonempty 72-byte candidate array')
    info_count=len(ib)//72
    for i in range(n):
        base=pad+i*96
        mn=struct.unpack_from(e+'3f',raw,base)
        mx=struct.unpack_from(e+'3f',raw,base+16)
        pos=struct.unpack_from(e+'3f',raw,base+32)
        prec,info=struct.unpack_from(e+'h',raw,base+28)[0],struct.unpack_from(e+'h',raw,base+84)[0]
        if not all(map(math.isfinite,mn+mx+pos)) or any(a>b for a,b in zip(mn,mx)):
            raise CandidateError(f'instance {i}: non-finite/inverted AABB or non-finite stored position')
        if info_count is not None and (info<0 or info>=info_count):
            raise CandidateError(f'instance {i}: info index outside candidate info table')
        rows.append({'min':mn,'max':mx,'position':pos,'preculler':prec,'info':info})
    return rows,pad,info_count


def candidate_precull(children:dict,rows:list):
    if prior.PRECULL not in children:raise CandidateError('preculler child absent')
    b=children[prior.PRECULL][1]
    if not b or len(b)%128:raise CandidateError('preculler not a nonempty 128-byte candidate array')
    count=len(b)//128
    refs=[r['preculler'] for r in rows]
    if any(x<0 or x>=count for x in refs):
        raise CandidateError('preculler instance reference outside candidate block array')
    hist=Counter(refs)
    return {'candidate_128_blocks':count,'referenced_distinct':len(hist),
            'unreferenced_blocks':count-len(hist),
            'zero_blocks':sum(b[i:i+128]==bytes(128) for i in range(0,len(b),128)),
            'maximum_reference_count':max(hist.values()),
            'source_format_semantics_proven':False}


def candidate_tree(children:dict,rows:list,order:str,tolerance:float=0.0):
    if prior.TREE not in children:raise CandidateError('spatial tree child absent')
    b=children[prior.TREE][1]
    if not b or len(b)%48:raise CandidateError('spatial tree not a nonempty 48-byte candidate array')
    if not math.isfinite(tolerance) or tolerance<0:raise CandidateError('invalid tolerance')
    e=prior.endian(order);nodes=[]
    for i in range(len(b)//48):
        start=i*48
        mn=struct.unpack_from(e+'3f',b,start)
        mx=struct.unpack_from(e+'3f',b,start+16)
        cnt=struct.unpack_from(e+'H',b,start+12)[0]
        if cnt>10 or not all(map(math.isfinite,mn+mx)) or any(a>c for a,c in zip(mn,mx)):
            raise CandidateError(f'tree node {i}: invalid count or bounds')
        refs=list(struct.unpack_from(e+str(cnt)+'h',b,start+28)) if cnt else []
        nodes.append((mn,mx,refs))
    active=set();visited=set();leaf_indices=[];err=0.0
    def walk(i:int):
        nonlocal err
        if i<0 or i>=len(nodes):raise CandidateError('spatial tree references out-of-range child')
        if i in active:raise CandidateError('spatial tree cycle')
        if i in visited:raise CandidateError('spatial tree child referenced multiple times')
        active.add(i)
        mn,mx,refs=nodes[i];desc=[]
        for j in refs:
            if j<0:
                desc.extend(walk(-j))
            elif j<len(rows):
                leaf_indices.append(j);desc.append(rows[j])
            else:raise CandidateError('spatial tree references nonexistent instance')
        if not desc:raise CandidateError('empty spatial tree node')
        for axis in range(3):
            err=max(err,abs(mn[axis]-min(r['min'][axis] for r in desc)),
                        abs(mx[axis]-max(r['max'][axis] for r in desc)))
        active.remove(i);visited.add(i)
        return desc
    walk(0)
    if len(visited)!=len(nodes):raise CandidateError('unreachable spatial tree nodes')
    if len(leaf_indices)!=len(rows) or len(set(leaf_indices))!=len(rows):
        raise CandidateError('spatial tree does not cover each instance exactly once')
    if err>tolerance:raise CandidateError('spatial node AABBs do not match instance descendant unions')
    return {'candidate_48_nodes':len(nodes),'covered_instances_exactly_once':len(rows),
            'max_absolute_aabb_union_error':err,'source_format_semantics_proven':False}


def audit_one(root:bytes,ch:dict,meta:dict,tolerance:float=0.0):
    size=prior.candidate_profile(root,ch,meta)
    result={'label':meta['label'],'root_sha256':meta['root_sha256'],
            'source_authentication':size['source_authentication'],
            'candidate_size_hypotheses':size['size_hypotheses'],
            'candidate_wii_graph_status':'rejected','read_only':True,
            'carbon_pc_abi_proven':False,'safe_to_install':False,
            'cross_scene_replication_established':False}
    try:
        rows,pad,info_count=candidate_rows(ch,meta['endian'])
        result['candidate_instance_count']=len(rows)
        result['candidate_instance_alignment_padding']=pad
        result['candidate_info_count']=info_count
        result['candidate_precull']=candidate_precull(ch,rows)
        result['candidate_tree']=candidate_tree(ch,rows,meta['endian'],tolerance)
        if prior.AUX in ch:
            b=ch[prior.AUX][1]
            if len(b)!=len(rows)*32:raise CandidateError('aux 32-byte count differs from instances')
            result['candidate_aux32_count']=len(rows)
        else:raise CandidateError('aux32 table missing')
        result['candidate_wii_graph_status']='candidate_internally_consistent'
        result['candidate_row_shape_only_not_PC_disk_proof']=True
    except CandidateError as exc:
        result['candidate_rejection_reason']=str(exc)
    return result


def survey(specs:list[dict],tolerance:float=0.0):
    if not isinstance(specs,list) or not 1<=len(specs)<=prior.MAX_SOURCES:
        raise CandidateError('manifest must provide 1..256 source entries')
    results=[];seen=set();submitted=0
    for spec in specs:
        root,parsed,meta=prior.read_verified_root(spec)
        submitted+=1
        if meta['root_sha256'] in seen:continue
        seen.add(meta['root_sha256'])
        results.append(audit_one(root,parsed,meta,tolerance))
    return {'schema':'v56-candidate-Wii-graph-consistency-v1',
            'submitted_roots':submitted,'distinct_root_fingerprints':len(results),
            'known_authenticated_original_Wii_scenes':sum(r['source_authentication']=='known_exact_original_Wii_RedBuilding' for r in results),
            'new_independent_original_scenes_authenticated':False,
            'carbon_pc_disk_abi_proven':False,'safe_to_install':False,'read_only':True,
            'warning':'A complete synthetic candidate Wii graph is still not proof of a Carbon PC loader schema; other file SHA guards alone do not authenticate original source.',
            'roots':results}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manifest',required=True,type=Path)
    p.add_argument('--report',required=True,type=Path)
    p.add_argument('--aabb-tolerance',type=float,default=0.0)
    a=p.parse_args()
    if a.report.exists() or a.manifest.resolve()==a.report.resolve():p.error('refusing report overwrite')
    specs=json.loads(a.manifest.read_text(encoding='utf-8'))
    if isinstance(specs,dict):specs=specs.get('roots')
    if not isinstance(specs,list):p.error('manifest needs a roots list')
    if any(isinstance(s,dict) and a.report.resolve()==Path(s.get('path','')).resolve() for s in specs):
        p.error('refusing source overwrite')
    if not math.isfinite(a.aabb_tolerance) or a.aabb_tolerance<0:p.error('invalid AABB tolerance')
    result=survey(specs,a.aabb_tolerance)
    a.report.parent.mkdir(parents=True,exist_ok=True)
    with a.report.open('x',encoding='utf-8') as f:
        json.dump(result,f,indent=2,sort_keys=True);f.write('\n')
    print('V56 read-only candidate Wii graph gate:',a.report)

if __name__=='__main__':main()