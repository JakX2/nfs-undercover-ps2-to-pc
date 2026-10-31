#!/usr/bin/env python3
"""V57: read-only, byte-preserving scene-root append layout diagnostic.

A +72/+96/+32 append can change absolute chunk payload addresses even if
all preexisting child bytes remain unchanged. This is an offline structural
risk, NOT evidence of what the Carbon PC scenery loader requires.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'v55'))
import v55_cross_scene_hypothesis_gate as v55

INFO = 0x34102
INST = 0x34103
AUX = 0x3410D
EXPECTED_APPEND = {INFO:72, INST:96, AUX:32}
CHECKED_ALIGNMENTS = (4, 8, 16)

class LayoutError(v55.GateError):
    pass


def layout(root:bytes, order:str) -> dict:
    """Preserve child ordering + ROOT-relative offsets, without writing data."""
    chunks = v55.children(root, order)
    records = []
    for tag, (start, data) in chunks.items():
        records.append({'tag':tag, 'payload_start':start,
                        'payload_end':start+len(data), 'bytes':len(data),
                        'digest':v55.sha256(data)})
    return {'chunks':chunks,'records':records,'size':len(root),'sha256':v55.sha256(root)}


def predict(original:bytes, order:str) -> dict:
    """Simulate ONLY absolute offset shifts; no candidate root is generated."""
    current=layout(original,order)
    chunks=current['chunks']
    missing=[f'0x{k:05X}' for k in EXPECTED_APPEND if k not in chunks]
    if missing:
        raise LayoutError('required V42-style append children missing: '+', '.join(missing))
    progress=0; rows=[]
    for row in current['records']:
        tag=row['tag'];start=row['payload_start'];delta=progress
        rows.append({'child_id':f'0x{tag:05X}',
                     'original_payload_start':start,
                     'projected_payload_start':start+delta,
                     'offset_shift':delta,
                     'original_length':row['bytes'],
                     'projected_length':row['bytes']+EXPECTED_APPEND.get(tag,0),
                     'offset_residue16_before':start%16,
                     'offset_residue16_after':(start+delta)%16,
                     'offset_residue16_changes':delta%16!=0})
        progress+=EXPECTED_APPEND.get(tag,0)
    old=chunks[INST][0];new=old+next(x['offset_shift'] for x in rows if x['child_id']=='0x34103')
    old_pad=(-old)&15;new_pad=(-new)&15
    raw=chunks[INST][1]
    old_compatible=len(raw)>=old_pad and (len(raw)-old_pad)%96==0
    candidate_compatible=(len(raw)+96)>=new_pad and (len(raw)+96-new_pad)%96==0
    return {'schema':'v57-append-address-shift-v1', 'original_root_sha256':current['sha256'],
            'original_root_bytes':current['size'],
            'projected_root_bytes':current['size']+sum(EXPECTED_APPEND.values()),
            'candidate_append_bytes':sum(EXPECTED_APPEND.values()),
            'projected_children':rows,
            'candidate_wii_96_row_layout':{
                'original_root_relative_payload_start':old,
                'projected_root_relative_payload_start':new,
                'original_alignment_prefix_bytes':old_pad,
                'projected_required_alignment_prefix_bytes':new_pad,
                'prefix_bytes_change':new_pad-old_pad,
                'source_shape_compatible':old_compatible,
                'unchanged_prefix_plus_96_append_still_shape_compatible':candidate_compatible,
                'root_relative_alignment_residue_changes':old%16!=new%16,
                'requires_PC_source_and_loader_proof':True},
            'read_only':True,'carbon_pc_serialized_layout_proven':False,
            'safe_to_install':False}


def audit_pair(original:bytes, candidate:bytes, order:str)->dict:
    """Compare exact V42-style append contract and record location movement.

    A satisfying contract is only byte-preservation, not in-game installability.
    """
    a=layout(original,order);b=layout(candidate,order)
    if list(a['chunks'])!=list(b['chunks']):
        raise LayoutError('child order/identity changed')
    if len(candidate)!=len(original)+sum(EXPECTED_APPEND.values()):
        raise LayoutError('candidate total bytes not exactly +200')
    rows=[]
    for old,new in zip(a['records'],b['records']):
        tag=old['tag'];prior=a['chunks'][tag][1];next_data=b['chunks'][tag][1]
        extra=EXPECTED_APPEND.get(tag,0)
        if len(next_data)!=len(prior)+extra:
            raise LayoutError(f'0x{tag:05X} not expected append length')
        if not next_data.startswith(prior):
            raise LayoutError(f'0x{tag:05X} original child bytes not preserved')
        start_shift=new['payload_start']-old['payload_start']
        rows.append({'child_id':f'0x{tag:05X}',
                     'original_payload_start':old['payload_start'],
                     'candidate_payload_start':new['payload_start'],
                     'offset_shift':start_shift,
                     'alignment_residue16_changed':start_shift%16!=0,
                     'original_bytes_unchanged':True})
    forecast=predict(original,order)
    for r,f in zip(rows,forecast['projected_children']):
        if r['candidate_payload_start']!=f['projected_payload_start']:
            raise LayoutError('append projection mismatch')
    return {'schema':'v57-exact-append-pair-audit-v1',
            'original_sha256':a['sha256'],'candidate_sha256':b['sha256'],
            'byte_preserving_append_contract_passed':True,
            'original_root_bytes':len(original),'candidate_root_bytes':len(candidate),
            'children':rows,
            'candidate_wii_96_row_layout':forecast['candidate_wii_96_row_layout'],
            'source_loader_and_alignment_unverified':True,
            'safe_to_install':False,'read_only':True,'carbon_pc_abi_proven':False}


def report_from_manifest(manifest:dict)->dict:
    if not isinstance(manifest,dict) or 'original' not in manifest:
        raise LayoutError('manifest requires original source entry')
    source,_,meta=v55.read_verified_root(manifest['original'])
    out={'schema':'v57-provenance-guarded-append-layout-audit-v1',
         'original_source_authentication':('known_original_Wii_RedBuilding' if meta['root_sha256']==v55.WII_REDBUILDING_SHA and meta['endian']=='little' else 'unknown_provenance'),
         'original':predict(source,meta['endian']),
         'safe_to_install':False,'carbon_pc_abi_proven':False}
    if 'candidate' in manifest:
        candidate,_,cmeta=v55.read_verified_root(manifest['candidate'])
        if cmeta['endian']!=meta['endian']:
            raise LayoutError('original/candidate byte orders must match')
        out['paired_append']=audit_pair(source,candidate,meta['endian'])
    return out


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manifest',required=True,type=Path)
    p.add_argument('--report',required=True,type=Path)
    args=p.parse_args()
    if args.report.exists() or args.manifest.resolve()==args.report.resolve():
        p.error('refusing to overwrite existing report or manifest')
    manifest=json.loads(args.manifest.read_text(encoding='utf-8'))
    for role in ('original','candidate'):
        if role in manifest and isinstance(manifest[role],dict):
            if args.report.resolve()==Path(manifest[role].get('path','')).resolve():
                p.error('refusing to overwrite source root or stream')
    result=report_from_manifest(manifest)
    args.report.parent.mkdir(parents=True,exist_ok=True)
    with args.report.open('x',encoding='utf-8') as f:
        json.dump(result,f,indent=2,sort_keys=True);f.write('\n')
    print('V57 read-only append layout audit complete:',args.report)

if __name__=='__main__':main()