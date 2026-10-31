#!/usr/bin/env python3
"""V59: READ-ONLY, explicit-hypothesis 0x34110 master-index impact audit.

The 92-byte row / +0x14 offset shape is publicly documented for MOST
WANTED PC, NOT authenticated for Carbon PC. This tool never auto-discovers a
Carbon index layout, writes a game file, or asserts installability.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'v58'))
import v58_stream_envelope_gate as v58
v55=v58.v55

TABLE=0x34110
MAX_ROWS=50000
MAX_ROW_BYTES=1024
MAX_TABLE_BYTES=64*1024*1024
APPEND_BYTES=200
HEX64=re.compile(r'^[0-9a-fA-F]{64}$')

class IndexErrorV59(v58.EnvelopeError):pass

def uint(v,name,minimum=0,maximum=None):
    if type(v) is not int or v<minimum or (maximum is not None and v>maximum):
        raise IndexErrorV59(f'{name} out of allowed integer range')
    return v

def validate_master(spec, label):
    """Reader of a MANUALLY located candidate 34110 table, not schema detection.

    All bytes come from independently SHA-guarded local input. Only the selected
    field is interpreted as a candidate stream offset, never a proven pointer.
    """
    if not isinstance(spec,dict):raise IndexErrorV59(f'{label} must be object')
    for k in ('path','expected_file_sha256','chunk_header_offset','row_stride','row_count','offset_field','endian'):
        if k not in spec:raise IndexErrorV59(f'missing {label}.{k}')
    path=Path(spec['path'])
    if not path.is_file():raise IndexErrorV59(f'{label} path is not a file')
    sha=spec['expected_file_sha256']
    if not isinstance(sha,str) or not HEX64.fullmatch(sha):raise IndexErrorV59(f'{label} invalid SHA256')
    if v55.file_digest(path)!=sha.lower():raise IndexErrorV59(f'{label} file SHA256 mismatch')
    order=spec['endian']
    e=v55.endian(order)
    location=uint(spec['chunk_header_offset'],'chunk_header_offset')
    count=uint(spec['row_count'],'row_count',minimum=1,maximum=MAX_ROWS)
    stride=uint(spec['row_stride'],'row_stride',minimum=4,maximum=MAX_ROW_BYTES)
    off_field=uint(spec['offset_field'],'offset_field',maximum=stride-4)
    base=uint(spec.get('offset_base',0),'offset_base')
    if base>=1<<64:raise IndexErrorV59('offset_base outside uint64')
    n=count*stride
    if n>MAX_TABLE_BYTES:raise IndexErrorV59('candidate table too large')
    size=path.stat().st_size
    if location+8+n>size:raise IndexErrorV59('candidate chunk outside master input')
    with path.open('rb') as f:
        f.seek(location)
        header=f.read(8)
        tag,declared=struct.unpack(e+'II',header)
        if tag!=TABLE:raise IndexErrorV59('explicit chunk header not 0x34110')
        if declared!=n:raise IndexErrorV59('chunk length does not match count*stride hypothesis')
        rows=f.read(n)
    if len(rows)!=n:raise IndexErrorV59('short candidate table')
    values=[struct.unpack_from(e+'I',rows,i*stride+off_field)[0] for i in range(count)]
    if any(base+v>=(1<<64) for v in values):raise IndexErrorV59('offset-base addition overflow')
    return {'file_sha256':sha.lower(),'table_sha256':v55.sha256(rows),
            'chunk_header_offset':location,'row_stride':stride,'row_count':count,
            'offset_field':off_field,'offset_base':base,'endian':order,
            'rows':rows,'values':[base+v for v in values]}

def status_of_offset(value,root_start,root_end):
    if value<root_start:return 'before_root_unchanged'
    if value==root_start:return 'root_start_unchanged'
    if value<root_end:return 'inside_root_requires_child_specific_mapping'
    return 'at_or_after_old_root_end_plus_200_if_flat_insertion'

def audit_rows(original_master,original_root_offset,root_size,candidate_master=None):
    start=original_root_offset;end=start+root_size
    rows=[];counts={}
    if candidate_master is not None:
        for k in ('row_stride','row_count','offset_field','offset_base','endian','chunk_header_offset'):
            if candidate_master[k]!=original_master[k]:
                raise IndexErrorV59(f'candidate master {k} differs from explicit layout')
    step=original_master['row_stride']; field=original_master['offset_field']; base=original_master['offset_base']
    for i,raw in enumerate(original_master['values']):
        st=status_of_offset(raw,start,end)
        counts[st]=counts.get(st,0)+1
        predicted=(raw+APPEND_BYTES if st.startswith('at_or_after') else
                   (raw if st!='inside_root_requires_child_specific_mapping' else None))
        representable=(None if predicted is None else 0<=predicted-base<=0xFFFFFFFF)
        record={'row':i,'candidate_stream_offset':raw,'address_relation':st,
                'predicted_offset_if_flat_plus_200':predicted,
                'prediction_fits_declared_u32_field':representable}
        if candidate_master is not None:
            cval=candidate_master['values'][i]
            old=original_master['rows'][i*step:(i+1)*step]
            new=candidate_master['rows'][i*step:(i+1)*step]
            changed=[j for j in range(step) if old[j]!=new[j]]
            other=[j for j in changed if not field<=j<field+4]
            prediction=record['predicted_offset_if_flat_plus_200']
            record.update({'candidate_master_offset':cval,
                           'candidate_matches_flat_insertion_projection':cval==prediction if prediction is not None else None,
                           'candidate_offset_delta':cval-raw,
                           'non_offset_field_changed_byte_count':len(other),
                           'candidate_row_changed_byte_count':len(changed),
                           'raw_row_bytes_preserved':not changed,
                           'master_field_semantics_unverified':True})
            if other:record['non_offset_field_changes_warning']=True
        rows.append(record)
    return {'candidate_rows':rows,'classification_counts':counts,
            'matched_literal_offset_field_is_not_proven_stream_pointer':True,
            'flat_insertion_projection_not_verified_Carbon_loader_requirement':True}

def report(manifest):
    if not isinstance(manifest,dict) or 'original_stream' not in manifest or 'original_master' not in manifest:
        raise IndexErrorV59('required original_stream and original_master')
    if 'offset' not in manifest['original_stream']:
        raise IndexErrorV59('embedded root offset required')
    original,_,meta=v55.read_verified_root(manifest['original_stream'])
    start=meta['stream_offset'];end=start+len(original)
    stream_path=Path(manifest['original_stream']['path'])
    if stream_path.stat().st_size<len(original)+start:
        raise IndexErrorV59('ROOT outside original stream')
    master=validate_master(manifest['original_master'],'original_master')
    if master['endian']!=meta['endian']:
        raise IndexErrorV59('master and root byte-order hypothesis differ')
    n=len(master['values'])
    row=uint(manifest.get('target_row'), 'target_row',maximum=n-1)
    target=master['values'][row]
    if target!=start:
        raise IndexErrorV59('selected master row does not point to verified ROOT position under explicit offset-field hypothesis')
    cm=None; candidate_verified=False
    if 'candidate_stream' in manifest or 'candidate_master' in manifest:
        if 'candidate_stream' not in manifest or 'candidate_master' not in manifest:
            raise IndexErrorV59('candidate comparison requires BOTH candidate_stream and candidate_master')
        candidate,_,cmeta=v55.read_verified_root(manifest['candidate_stream'])
        if cmeta['endian']!=meta['endian']:
            raise IndexErrorV59('candidate ROOT byteorder differs')
        v58.strict_exterior_pair(manifest['original_stream'],original,manifest['candidate_stream'],candidate,meta['endian'])
        cm=validate_master(manifest['candidate_master'],'candidate_master')
        for key in ('row_stride','row_count','offset_field','offset_base','endian','chunk_header_offset'):
            if cm[key]!=master[key]:
                raise IndexErrorV59(f'candidate master {key} differs from explicit layout')
        if cm['values'][row]!=start:
            raise IndexErrorV59('candidate target master row no longer points to root start')
        candidate_verified=True
    findings=audit_rows(master,start,len(original),cm)
    root_start_rows=[i for i,x in enumerate(master['values']) if x==start]
    result={'schema':'v59-explicit-master-table-hypothesis-v1',
            'source_stream_sha256':meta['file_sha256'],'source_root_sha256':meta['root_sha256'],
            'source_master_sha256':master['file_sha256'],'source_candidate_master_chunk_sha256':master['table_sha256'],
            'target_row':row,'target_offset_matches_pinned_root':True,
            'rows_with_candidate_offset_equal_to_root_start':root_start_rows,
            'target_row_mapping_is_unique_under_hypothesis':len(root_start_rows)==1,
            'root_start':start,'original_root_end_exclusive':end,
            'hypothetical_end_after_200byte_append':end+APPEND_BYTES,
            'row_layout':{'id':'0x34110','header_offset':master['chunk_header_offset'],
                          'row_stride':master['row_stride'],'row_count':n,'candidate_offset_field':master['offset_field'],
                          'offset_base':master['offset_base']},
            'rows':findings,'candidate_stream_and_master_passed_narrow_byte_contract':candidate_verified,
            'candidate_source_master_sha256':cm['file_sha256'] if cm else None,
            'candidate_master_chunk_sha256':cm['table_sha256'] if cm else None,
            'row_layout_evidence_level':'user_supplied_hypothesis_not_authenticated_Carbon_PC',
            'world_index_field_semantics_proven':False,'stream_relocations_verified':False,
            'carbon_PC_runtime_verified':False,'safe_to_install':False,'read_only':True}
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manifest',type=Path,required=True)
    p.add_argument('--report',type=Path,required=True)
    args=p.parse_args()
    manifest=json.loads(args.manifest.read_text(encoding='utf-8'))
    sources=[args.manifest.resolve()]
    for key in ('original_stream','original_master','candidate_stream','candidate_master'):
        if isinstance(manifest.get(key),dict) and 'path' in manifest[key]:
            sources.append(Path(manifest[key]['path']).resolve())
    if args.report.resolve() in sources or args.report.exists():p.error('refusing to overwrite any input or existing report')
    result=report(manifest)
    args.report.parent.mkdir(parents=True,exist_ok=True)
    with args.report.open('x',encoding='utf-8') as f:
        json.dump(result,f,indent=2,sort_keys=True);f.write('\n')
    print('V59 candidate master index impact reported:',args.report)
if __name__=='__main__':main()