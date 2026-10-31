#!/usr/bin/env python3
"""V61: format-neutral, read-only EA scenery/master chunk *candidate* inventory.

For locally supplied Carbon PC or other EA engine streams. Searches source
bytes for 0x80034100 and 0x34110 in both endian orders, checks both payload-
and total-length hypotheses, then independently attempts direct-child framing.

A match is never authenticated provenance, a Carbon layout, a table pointer,
or an engine loader registration. No writer, game binary or patch is produced.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import mmap
import os
from pathlib import Path
import re
import struct

ROOT=0x80034100
MASTER=0x34110
TARGETS=(ROOT,MASTER)
ENDIAN={'little':'<','big':'>'}
HEX64=re.compile(r'^[0-9a-fA-F]{64}$')
MAX_CHUNK=64*1024*1024


class ProbeError(ValueError):
    pass


def _header(buf, at:int, order:str, length_mode:str, max_bytes:int):
    """Return (payload_start, end) of a bounded candidate, else None."""
    if at<0 or at+8>len(buf):
        return None
    tag,length=struct.unpack_from(ENDIAN[order]+'II',buf,at)
    if tag not in TARGETS and not (0x34100<=tag<=0x341FF):
        return None
    if length_mode=='payload':
        if length>max_bytes-8 or length>len(buf)-at-8:
            return None
        end=at+8+length
    elif length_mode=='total':
        if length<8 or length>max_bytes or length>len(buf)-at:
            return None
        end=at+length
    else:
        raise ProbeError('Unsupported chunk length mode')
    return at+8,end


def _children(buf, start:int, end:int, order:str, mode:str,
              max_children:int=4096):
    """Try contiguous direct-child EA chunk frames; never infer semantics."""
    if start==end:
        return {'status':'empty', 'count':0,'records':[]}
    p=start
    rows=[]
    while p<end:
        if p+8>end:
            return {'status':'unparsed','count':len(rows),'records':[]}
        tag,size=struct.unpack_from(ENDIAN[order]+'II',buf,p)
        if tag<0x34100 or tag>0x341FF or len(rows)>=max_children:
            return {'status':'unparsed','count':len(rows),'records':[]}
        h=_header(buf,p,order,mode,max_bytes=end-p)
        if h is None or h[1]>end or h[1]<=p:
            return {'status':'unparsed','count':len(rows),'records':[]}
        payload_start,child_end=h
        rows.append({'id':f'0x{tag:08X}','total_bytes':child_end-p,
                     'payload_sha256':hashlib.sha256(buf[payload_start:child_end]).hexdigest()})
        p=child_end
    return {'status':'contiguous_candidate_children','count':len(rows),'records':rows}


def _identity(st):
    return (st.st_dev,st.st_ino,st.st_size,st.st_mtime_ns,st.st_ctime_ns)


def _read_hex64(v):
    if v is None:return None
    if not isinstance(v,str) or HEX64.fullmatch(v) is None:
        raise ProbeError('Expected archive SHA-256 must have exactly 64 hex digits')
    return v.lower()


def _hypothesis(candidate,buf,stride,field_offset,row_start,reference_offsets,max_rows):
    """Evaluate user-defined *raw integer* column matches, not actual pointers."""
    if stride is None:return None
    start=candidate['_start']+row_start
    end=candidate['_end']
    if start>end:
        return {'eligible':False,'reason':'row_start exceeds candidate payload'}
    count=(end-start)//stride
    remainder=(end-start)%stride
    checked=min(count,max_rows)
    hits=[]
    if reference_offsets:
        e=ENDIAN[candidate['endian']]
        for row in range(checked):
            position=start+row*stride+field_offset
            value=struct.unpack_from(e+'I',buf,position)[0]
            if value in reference_offsets and len(hits)<50:
                hits.append({'row':row,'integer_value':value})
    return {'eligible':True,'row_stride_hypothesis':stride,
            'row_start_hypothesis':row_start,'field_offset_hypothesis':field_offset,
            'row_count_if_hypothesis':count,'trailing_bytes_if_hypothesis':remainder,
            'reference_offsets_supplied':len(reference_offsets),
            'rows_examined':checked,
            'rows_truncated':count>max_rows,
            'matching_raw_integer_values_capped_50':hits,
            'proven_master_index_schema':False,
            'proven_pointer_or_relocation':False}


def scan_archive(path:Path,*,expected_sha256:str|None=None,
                 orders=('little','big'),modes=('payload','total'),
                 max_chunk_bytes=MAX_CHUNK,max_hits=100000,max_candidates=10000,
                 row_stride=None,field_offset=None,row_start=0,
                 reference_offsets=(),max_rows=100000):
    """Return metadata-only results, rejecting unstable or mismatched archives."""
    if not orders or any(o not in ENDIAN for o in orders) or len(set(orders))!=len(orders):
        raise ProbeError('orders must be unique supported byte orders')
    if not modes or any(m not in ('payload','total') for m in modes) or len(set(modes))!=len(modes):
        raise ProbeError('modes must be unique supported length conventions')
    if type(max_chunk_bytes) is not int or not 32<=max_chunk_bytes<=1024*1024*1024:
        raise ProbeError('max_chunk_bytes outside 32..1GiB')
    if type(max_hits) is not int or not 1<=max_hits<=1000000:
        raise ProbeError('max_hits outside 1..1000000')
    if type(max_candidates) is not int or not 1<=max_candidates<=100000:
        raise ProbeError('max_candidates outside 1..100000')
    if type(max_rows) is not int or not 1<=max_rows<=1000000:
        raise ProbeError('max_rows outside 1..1000000')
    if row_stride is None:
        if field_offset is not None or row_start:
            raise ProbeError('row field offset/start require explicit row stride')
    elif (type(row_stride) is not int or not 4<=row_stride<=4096
          or type(field_offset) is not int or not 0<=field_offset<=row_stride-4
          or type(row_start) is not int or not 0<=row_start<=4096):
        raise ProbeError('Invalid explicitly supplied row layout hypothesis')
    refset=set(reference_offsets)
    if any(type(v) is not int or not 0<=v<=0xFFFFFFFF for v in refset):
        raise ProbeError('reference offsets must be uint32 values')
    expected=_read_hex64(expected_sha256)
    with path.open('rb') as fh:
        before=os.fstat(fh.fileno())
        size=before.st_size
        raw_hits=set()
        candidates=[]
        if size:
            with mmap.mmap(fh.fileno(),0,access=mmap.ACCESS_READ) as buf:
                sha=hashlib.sha256(buf).hexdigest()
                if expected is not None and sha!=expected:
                    raise ProbeError('Archive SHA-256 mismatch')
                for order in orders:
                    for tag in TARGETS:
                        needle=struct.pack(ENDIAN[order]+'I',tag)
                        pos=0
                        while (at:=buf.find(needle,pos))>=0:
                            raw_hits.add((at,order,tag))
                            if len(raw_hits)>max_hits:
                                raise ProbeError('signature hit limit exceeded; no report emitted')
                            for mode in modes:
                                spans=_header(buf,at,order,mode,max_chunk_bytes)
                                if spans is None:continue
                                start,end=spans
                                rec={'offset':at,'tag':f'0x{tag:08X}',
                                     'endian':order,'length_mode_hypothesis':mode,
                                     'total_bytes':end-at,
                                     'end_offset_exclusive':end,
                                     # Whole-frame SHA enables independent V62
                                     # alias checks without extracting game bytes.
                                     'framed_chunk_sha256':hashlib.sha256(buf[at:end]).hexdigest(),
                                     'payload_sha256':hashlib.sha256(buf[start:end]).hexdigest(),
                                     'candidate_only':True,
                                     '_start':start,'_end':end}
                                if tag==ROOT:
                                    rec['child_framing_probe']=_children(buf,start,end,order,mode)
                                else:
                                    rec['candidate_row_probe']=_hypothesis(
                                        rec,buf,row_stride,field_offset,row_start,refset,max_rows)
                                candidates.append(rec)
                                if len(candidates)>max_candidates:
                                    raise ProbeError('candidate variant limit exceeded; no report emitted')
                            pos=at+1
                if hashlib.sha256(buf).hexdigest()!=sha:
                    raise ProbeError('Archive changed while scanning; no report emitted')
        else:
            sha=hashlib.sha256(b'').hexdigest()
            if expected is not None and sha!=expected:
                raise ProbeError('Archive SHA-256 mismatch')
        after=os.fstat(fh.fileno())
        try:current=path.stat()
        except OSError as e:raise ProbeError('Archive path vanished while scanning') from e
        if (current.st_dev,current.st_ino)!=(after.st_dev,after.st_ino):
            raise ProbeError('Archive path replaced while scanning')
        if _identity(before)!=_identity(after):
            raise ProbeError('Archive metadata changed while scanning')
    candidates.sort(key=lambda r:(r['offset'],r['tag'],r['endian'],r['length_mode_hypothesis']))
    for r in candidates:
        del r['_start'];del r['_end']
    variants=Counter((r['tag'],r['endian'],r['length_mode_hypothesis']) for r in candidates)
    location_counts=Counter(r['offset'] for r in candidates)
    return {'schema':'v61-format-neutral-scene-and-master-chunk-inventory-v1',
            'archive_sha256':sha,
            'archive_size_bytes':size,
            'trusted_expected_archive_digest_checked':expected is not None,
            'signature_hits':len(raw_hits),
            'candidate_variants':len(candidates),
            'ambiguous_candidate_offsets':sum(n>1 for n in location_counts.values()),
            'variant_counts':[
                {'tag':a,'endian':b,'length_mode_hypothesis':c,'count':n}
                for (a,b,c),n in sorted(variants.items())],
            'candidates':candidates,
            'original_game_provenance_authenticated':False,
            'Carbon_PC_index_layout_proven':False,
            'Carbon_PC_scenery_loader_verified':False,
            'in_game_verified':False,'safe_to_install':False,
            'read_only':True,'atomic_filesystem_snapshot':False,
            'notes':[
                'Both endian and chunk-length conventions are hypotheses; multiple candidates at an offset are unresolved ambiguity.',
                'This flat scan is not exhaustive for compressed, encrypted, or differently framed native Carbon data.',
                '0x34110 header/row plausibility is not proof of a Carbon PC streaming master index ABI.',
                'A raw 32-bit offset coincidence is not a pointer, relocation, loader read, or sector ownership proof.',
                'An archive SHA-256 check verifies bytes, not their provenance or licensing.',
                'Reports omit local paths and original game binary payloads.'
            ]}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--archive',type=Path,required=True)
    ap.add_argument('--expected-sha256')
    ap.add_argument('--report',type=Path,required=True)
    ap.add_argument('--endian',choices=('little','big','both'),default='both')
    ap.add_argument('--length-mode',choices=('payload','total','both'),default='both')
    ap.add_argument('--max-chunk-bytes',type=int,default=MAX_CHUNK)
    ap.add_argument('--max-hits',type=int,default=100000)
    ap.add_argument('--max-candidates',type=int,default=10000)
    ap.add_argument('--row-stride',type=int)
    ap.add_argument('--field-offset',type=int)
    ap.add_argument('--row-start',type=int,default=0)
    ap.add_argument('--reference-offset',type=lambda x:int(x,0),action='append',default=[])
    ap.add_argument('--max-rows',type=int,default=100000)
    a=ap.parse_args()
    if a.report.exists() or a.report.resolve()==a.archive.resolve():
        ap.error('refusing overwrite of source archive or existing report')
    report=scan_archive(
        a.archive,expected_sha256=a.expected_sha256,
        orders=tuple(ENDIAN) if a.endian=='both' else (a.endian,),
        modes=('payload','total') if a.length_mode=='both' else (a.length_mode,),
        max_chunk_bytes=a.max_chunk_bytes,max_hits=a.max_hits,
        max_candidates=a.max_candidates,row_stride=a.row_stride,
        field_offset=a.field_offset,row_start=a.row_start,
        reference_offsets=a.reference_offset,max_rows=a.max_rows)
    a.report.parent.mkdir(parents=True,exist_ok=True)
    with a.report.open('x',encoding='utf-8') as f:
        json.dump(report,f,indent=2,sort_keys=True)
        f.write('\n')
    print('V61 read-only format-neutral inventory:',report['signature_hits'],
          'signature hits;',report['candidate_variants'],'bounded framing variants.')
    print('No Carbon index ABI or original-game provenance authenticated by this scan.')


if __name__=='__main__':
    main()
