#!/usr/bin/env python3
"""V60: read-only multi-root constraints for candidate 0x34110 index layouts.

This is a cross-anchor discriminator, NOT a Carbon PC master-table decoder.
Every candidate shape and every root offset must be supplied independently.
Even a unique structural match cannot establish loader/relocation semantics.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import struct
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'v59'))
import v59_master_index_impact_gate as v59

v55 = v59.v55
GateError = v59.IndexErrorV59
MAX_ROOT_ANCHORS = 64
MAX_LAYOUT_HYPOTHESES = 64


def _integer(value, name, minimum=0, maximum=None):
    return v59.uint(value,name,minimum,maximum)


def validate_sources(manifest):
    if not isinstance(manifest,dict):
        raise GateError('manifest must be object')
    for name in ('stream','master','roots','hypotheses'):
        if name not in manifest:
            raise GateError(f'missing manifest.{name}')
    stream=manifest['stream'];master=manifest['master']
    if not isinstance(stream,dict) or not isinstance(master,dict):
        raise GateError('stream/master must be objects')
    for name in ('path','expected_file_sha256','endian'):
        if name not in stream:
            raise GateError(f'missing stream.{name}')
    for name in ('path','expected_file_sha256','chunk_header_offset','endian'):
        if name not in master:
            raise GateError(f'missing master.{name}')
    if stream['endian']!=master['endian']:
        raise GateError('stream/master endian mismatch')
    v55.endian(stream['endian'])
    stream_sha=v55.validate_hex64(stream['expected_file_sha256'],'stream SHA')
    master_sha=v55.validate_hex64(master['expected_file_sha256'],'master SHA')
    stream_path=Path(stream['path']);master_path=Path(master['path'])
    if not stream_path.is_file() or not master_path.is_file():
        raise GateError('source file absent')
    if v55.file_digest(stream_path)!=stream_sha:
        raise GateError('stream whole-file SHA mismatch')
    if v55.file_digest(master_path)!=master_sha:
        raise GateError('master whole-file SHA mismatch')
    roots=manifest['roots'];hypotheses=manifest['hypotheses']
    if not isinstance(roots,list) or not 1<=len(roots)<=MAX_ROOT_ANCHORS:
        raise GateError('1..64 root anchors required')
    if not isinstance(hypotheses,list) or not 1<=len(hypotheses)<=MAX_LAYOUT_HYPOTHESES:
        raise GateError('1..64 explicit layout hypotheses required')
    records=[];labels=set();starts=set()
    file_size=stream_path.stat().st_size
    byteorder=v55.endian(stream['endian'])
    for anchor in roots:
        if not isinstance(anchor,dict):raise GateError('root anchor must be object')
        for name in ('label','offset','expected_root_sha256'):
            if name not in anchor:raise GateError(f'root anchor missing {name}')
        offset=_integer(anchor['offset'],'root offset')
        if offset in starts:raise GateError('duplicate root start is not independent anchor')
        label=anchor['label']
        if not isinstance(label,str) or not label or len(label)>100 or label in labels:
            raise GateError('duplicate/invalid root anchor label')
        labels.add(label);starts.add(offset)
        expected=v55.validate_hex64(anchor['expected_root_sha256'],'root SHA')
        if offset>file_size-8:raise GateError('root offset outside source stream')
        with stream_path.open('rb') as source:
            source.seek(offset)
            header=source.read(8)
            tag,n=struct.unpack(byteorder+'II',header)
            if tag!=v55.ROOT or n>v55.MAX_ROOT-8 or n>file_size-offset-8:
                raise GateError('invalid or out-of-bounds framed ROOT at supplied offset')
            root=header+source.read(n)
        if v55.sha256(root)!=expected:
            raise GateError(f'extracted ROOT fingerprint mismatch for label {label}')
        try:
            v55.children(root,stream['endian'])
        except v55.GateError as exc:
            raise GateError(str(exc)) from exc
        records.append({'label':label,'start':offset,'end':offset+len(root),
                        'sha256':expected,'bytes':len(root)})
    ranges=sorted(records,key=lambda x:x['start'])
    if any(a['end']>b['start'] for a,b in zip(ranges,ranges[1:])):
        raise GateError('overlapping anchored scene roots')
    return records, {'stream_file_sha256':stream_sha,'master_file_sha256':master_sha,
                     'stream_endian':stream['endian']}


def _validate_hypothesis_id(h,ids):
    if not isinstance(h,dict):raise GateError('hypothesis must be object')
    for field in ('id','row_stride','row_count','offset_field'):
        if field not in h:raise GateError(f'missing hypothesis.{field}')
    hid=h['id']
    if not isinstance(hid,str) or not hid or len(hid)>100 or hid in ids:
        raise GateError('duplicate/invalid hypothesis ID')
    ids.add(hid)
    return hid


def load_master_payload(master):
    """Read a bounded, explicitly located chunk once after whole-file SHA guard."""
    at=_integer(master['chunk_header_offset'],'master chunk-header offset')
    size=Path(master['path']).stat().st_size
    if at>size-8:raise GateError('candidate master header outside source file')
    e=v55.endian(master['endian'])
    with Path(master['path']).open('rb') as source:
        source.seek(at)
        tag,n=struct.unpack(e+'II',source.read(8))
        if tag!=v59.TABLE:raise GateError('explicit candidate chunk header not 0x34110')
        if n>v59.MAX_TABLE_BYTES or n>size-at-8:
            raise GateError('candidate master payload outside bounded source file')
        payload=source.read(n)
    return payload


def parse_layout(payload, spec, endian):
    """Validate an explicit row hypothesis against a preauthenticated chunk."""
    count=_integer(spec['row_count'],'row_count',1,v59.MAX_ROWS)
    stride=_integer(spec['row_stride'],'row_stride',4,v59.MAX_ROW_BYTES)
    field=_integer(spec['offset_field'],'offset_field',0,stride-4)
    base=_integer(spec.get('offset_base',0),'offset_base')
    if base>=1<<64:raise GateError('offset_base outside uint64')
    if count*stride!=len(payload):
        raise GateError('chunk length does not match count*stride hypothesis')
    values=[struct.unpack_from(v55.endian(endian)+'I',payload,i*stride+field)[0]+base
            for i in range(count)]
    if any(v>=(1<<64) for v in values):raise GateError('offset base addition overflow')
    return {'row_stride':stride,'row_count':count,'offset_field':field,
            'offset_base':base,'table_sha256':v55.sha256(payload),'values':values}


def evaluate_layouts(manifest):
    roots, provenance=validate_sources(manifest)
    master=manifest['master']; ids=set();out=[]
    try:
        payload=load_master_payload(master)
        payload_error=None
    except GateError as exc:
        payload=None;payload_error=str(exc)
    for h in manifest['hypotheses']:
        hid=_validate_hypothesis_id(h,ids)
        try:
            if payload_error is not None:raise GateError(payload_error)
            m=parse_layout(payload,h,master['endian'])
        except (GateError,ValueError) as exc:
            # An explicit layout can be structurally rejected without deciding
            # whether the entire Carbon stream is invalid.
            out.append({'id':hid,'structural_status':'layout_rejected',
                        'reason':str(exc),'loader_semantics_proven':False})
            continue
        matches=[];value_to_rows={}
        for row,value in enumerate(m['values']):
            value_to_rows.setdefault(value,[]).append(row)
        for root in roots:
            found=value_to_rows.get(root['start'],[])
            interior=[i for i,value in enumerate(m['values']) if root['start']<value<root['end']]
            matches.append({'root_label':root['label'],'root_sha256':root['sha256'],
                            'root_start':root['start'],'matching_candidate_rows':found,
                            'matching_row_count':len(found),
                            'candidate_rows_pointing_inside_root_not_at_start':len(interior),
                            'unique_candidate_row_match':len(found)==1})
        anchored=sum(x['unique_candidate_row_match'] for x in matches)
        distinct_hashes=len({x['root_sha256'] for x in matches if x['unique_candidate_row_match']})
        complete=anchored==len(roots)
        if not complete:
            status='anchor_contradiction_or_ambiguity'
        elif distinct_hashes<2:
            status='single_distinct_root_structural_match_only'
        else:
            status='multiple_distinct_roots_structurally_match_NOT_loader_proof'
        out.append({'id':hid,'structural_status':status,
                    'row_stride':m['row_stride'],'row_count':m['row_count'],
                    'offset_field':m['offset_field'],'offset_base':m['offset_base'],
                    'table_sha256':m['table_sha256'],
                    'root_anchor_count':len(roots),'uniquely_matched_anchor_count':anchored,
                    'uniquely_matched_distinct_root_sha_count':distinct_hashes,
                    'all_anchors_uniquely_matched':complete,
                    'anchor_matches':matches,
                    'loader_semantics_proven':False})
    contenders=[x['id'] for x in out if x.get('all_anchors_uniquely_matched')]
    return {'schema':'v60-multi-anchor-index-constraint-v1',
            'original_file_fingerprints_match':True,
            'source_stream_sha256':provenance['stream_file_sha256'],
            'source_master_sha256':provenance['master_file_sha256'],
            'source_root_count':len(roots),
            'distinct_root_payload_sha_count':len({r['sha256'] for r in roots}),
            'candidate_layouts':out,
            'layouts_matching_all_root_anchors':contenders,
            'layout_ambiguity_flag':len(contenders)>1,
            'multiple_distinct_original_carbon_PC_roots_authenticated':False,
            'carbon_PC_master_index_semantics_proven':False,
            'native_Carbon_loader_and_relocations_verified':False,
            'safe_to_install':False,'read_only':True,
            'caution':'Even a sole multi-anchor structural match is NOT evidence that Carbon PC loader reads these fields; source provenance cannot be authenticated from hashes alone.'}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manifest',required=True,type=Path)
    p.add_argument('--report',required=True,type=Path)
    a=p.parse_args()
    if a.report.exists() or a.report.resolve()==a.manifest.resolve():
        p.error('refusing overwrite of manifest/existing output')
    manifest=json.loads(a.manifest.read_text(encoding='utf-8'))
    source_paths=[]
    if isinstance(manifest,dict):
        source_paths=[Path(spec['path']).resolve() for k in ('stream','master')
                      if isinstance((spec:=manifest.get(k)),dict) and 'path' in spec]
    if a.report.resolve() in source_paths:p.error('refusing to overwrite a source file')
    result=evaluate_layouts(manifest)
    a.report.parent.mkdir(parents=True,exist_ok=True)
    with a.report.open('x',encoding='utf-8') as f:
        json.dump(result,f,sort_keys=True,indent=2);f.write('\n')
    print('V60 read-only candidate index cross-anchor report:',a.report)

if __name__=='__main__':main()