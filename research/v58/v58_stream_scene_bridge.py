#!/usr/bin/env python3
"""V58: read-only archive-to-candidate-scene bridge.

Scans locally supplied archives for bounded ROOT records and runs the
existing V57 candidate Wii graph checker on framed roots. The JSON summary
contains only source-derived metadata, while the optional *private* manifest
contains local file paths for subsequent V55/V57 hash-gated analysis.

A candidate is never authenticated by framing, layout, source path or SHA alone.
No Carbon PC serialization, streaming, culling, installability or gameplay
compatibility is asserted.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import mmap
import os
from pathlib import Path
import struct
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'v56'))
import v56_cross_root_semantic_gate as graph

prior = graph.prior
MAX_ROOT = prior.MAX_ROOT


class ScanError(ValueError):
    pass


def _metadata_identity(stat):
    return (stat.st_dev, stat.st_ino, stat.st_size,
            stat.st_mtime_ns, stat.st_ctime_ns)


def _parse_root(data: mmap.mmap, offset: int, order: str):
    """Return bounded, source-observed scenery ROOT and children or None.

    Keep the strict source-observed V55 framing: first 0x34101 and 0x34103
    records must be present. Other Carbon/console layouts could differ.
    """
    e=prior.endian(order)
    if offset<0 or offset+8>len(data):
        return None
    typ, length=struct.unpack_from(e+'II',data,offset)
    if typ!=prior.ROOT or length<16 or length>MAX_ROOT-8 or length>len(data)-offset-8:
        return None
    raw=bytes(data[offset:offset+8+length])
    try:
        children=prior.children(raw,order)
    except prior.GateError:
        return None
    return raw,children


def scan_archive(path:Path,*,expected_stream_sha256:str|None=None,
                 order:str='little',source_hint:str='wii',
                 max_hits:int=100000,max_roots:int=10000) -> dict:
    """Find source-framed candidate ROOTs in a single stable input handle.

    Source and root fingerprints are integrity checks, *not* game provenance.
    """
    if source_hint not in ('wii','carbon_pc','unknown'):
        raise ScanError('source_hint must be wii, carbon_pc or unknown')
    e=prior.endian(order)
    if not 1<=max_hits<=1000000 or not 1<=max_roots<=100000:
        raise ScanError('max_hits or max_roots out of permitted range')
    if expected_stream_sha256 is not None:
        expected_stream_sha256=prior.validate_hex64(expected_stream_sha256,'archive SHA')
    magic=struct.pack(e+'I',prior.ROOT)
    records=[]
    candidates_inspected=0
    malformed_or_other_layout=0
    with path.open('rb') as fh:
        before=os.fstat(fh.fileno())
        size=before.st_size
        if size:
            with mmap.mmap(fh.fileno(),0,access=mmap.ACCESS_READ) as data:
                fingerprint=hashlib.sha256(data).hexdigest()
                if expected_stream_sha256 is not None and fingerprint!=expected_stream_sha256:
                    raise ScanError('Archive SHA-256 mismatch')
                pos=0
                while (offset:=data.find(magic,pos))!=-1:
                    candidates_inspected+=1
                    if candidates_inspected>max_hits:
                        raise ScanError('ROOT signature hit limit exceeded; no partial report')
                    result=_parse_root(data,offset,order)
                    if result is None:
                        malformed_or_other_layout+=1
                        pos=offset+1
                        continue
                    raw,children=result
                    root_sha=hashlib.sha256(raw).hexdigest()
                    meta={'label':f'candidate_{offset:012X}','root_sha256':root_sha,
                          'file_sha256':fingerprint,'endian':order,
                          'platform_hint_unverified':source_hint,'stream_offset':offset}
                    candidate={
                        'offset':offset,'root_bytes':len(raw),'root_sha256':root_sha,
                        'child_tags':[f'0x{key:05X}' for key in sorted(children)],
                        'source_class': ('known_exact_Wii_RedBuilding_root'
                                         if root_sha==prior.WII_REDBUILDING_SHA and order=='little'
                                         else 'unverified_candidate'),
                    }
                    if source_hint=='wii':
                        findings=graph.audit_one(raw,children,meta)
                        candidate['candidate_wii_graph_status']=findings['candidate_wii_graph_status']
                        if 'candidate_rejection_reason' in findings:
                            candidate['candidate_wii_rejection']=findings['candidate_rejection_reason']
                        candidate['candidate_instance_count']=findings.get('candidate_instance_count')
                        candidate['candidate_tree_node_count']=findings.get('candidate_tree',{}).get('candidate_48_nodes')
                        candidate['candidate_preculler_block_count']=findings.get('candidate_precull',{}).get('candidate_128_blocks')
                    else:
                        candidate['candidate_wii_graph_status']='not_evaluated_for_non_Wii_source'
                    records.append(candidate)
                    if len(records)>max_roots:
                        raise ScanError('Candidate ROOT limit exceeded; no partial report')
                    pos=offset+len(raw)
                if hashlib.sha256(data).hexdigest()!=fingerprint:
                    raise ScanError('Archive changed while scanned; no report emitted')
        else:
            fingerprint=hashlib.sha256(b'').hexdigest()
            if expected_stream_sha256 is not None and fingerprint!=expected_stream_sha256:
                raise ScanError('Archive SHA-256 mismatch')
        after=os.fstat(fh.fileno())
        try:
            current=path.stat()
        except OSError as exc:
            raise ScanError('Archive path vanished during scan') from exc
        if (current.st_dev,current.st_ino)!=(after.st_dev,after.st_ino):
            raise ScanError('Archive path replaced during scan')
        if _metadata_identity(before)!=_metadata_identity(after):
            raise ScanError('Archive metadata changed during scan')
    counts=Counter(x['root_sha256'] for x in records)
    statuses=Counter(x['candidate_wii_graph_status'] for x in records)
    return {
        'schema':'v58-source-framed-candidate-scene-inventory-v1',
        'archive_sha256':fingerprint,
        'archive_size_bytes':size,
        'archive_integrity_guard_applied':expected_stream_sha256 is not None,
        'endian':order,'source_hint_unverified':source_hint,
        'signature_matches_examined':candidates_inspected,
        'signature_matches_not_matching_expected_layout':malformed_or_other_layout,
        'candidate_root_occurrences':len(records),
        'distinct_candidate_root_sha256s':len(counts),
        'duplicate_candidate_root_occurrences':sum(n-1 for n in counts.values()),
        'candidate_wii_graph_status_counts':dict(sorted(statuses.items())),
        'records':records,
        'independent_original_scenes_authenticated':False,
        'carbon_pc_disk_abi_verified':False,
        'engine_loader_verified':False,'safe_to_install':False,'read_only':True,
        'source_identity_independently_authenticated':False,
        'atomic_filesystem_snapshot':False,
        'notes':[
            'SHA-256 guards provide integrity, not authenticity or independent source provenance.',
            'Search requires 0x34101 and 0x34103 chunks, so genuine alternate scene layouts may be missed.',
            'Wii candidate graph consistency does not prove visibility semantics or Carbon PC ABI.',
            'The inventory intentionally omits original binary payloads and local paths.',
        ]
    }


def build_private_manifest(path:Path,report:dict) -> dict:
    """Local-only manifest for independently checking each candidate in V55/V57."""
    entries=[]
    for candidate in report['records']:
        entries.append({
            'label':f'offset_{candidate["offset"]:012X}',
            'path':str(path.resolve()),
            'endian':report['endian'],
            'platform_hint':report['source_hint_unverified'],
            'offset':candidate['offset'],
            'expected_file_sha256':report['archive_sha256'],
            'expected_root_sha256':candidate['root_sha256'],
        })
    return {'roots':entries}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--archive',required=True,type=Path)
    p.add_argument('--expected-archive-sha256')
    p.add_argument('--endian',choices=('little','big'),default='little')
    p.add_argument('--source-hint',choices=('wii','carbon_pc','unknown'),default='wii')
    p.add_argument('--report',required=True,type=Path,
                   help='New metadata-only JSON report')
    p.add_argument('--private-manifest',type=Path,
                   help='Optional local-only V55/V57 manifest with absolute archive paths')
    p.add_argument('--max-hits',type=int,default=100000)
    p.add_argument('--max-roots',type=int,default=10000)
    a=p.parse_args()
    outputs=[a.report]+([a.private_manifest] if a.private_manifest else [])
    if len({q.resolve() for q in outputs})!=len(outputs):
        p.error('Report paths must be distinct')
    if any(q.exists() or q.resolve()==a.archive.resolve() for q in outputs):
        p.error('Refusing overwrite of source or existing output')
    result=scan_archive(a.archive,expected_stream_sha256=a.expected_archive_sha256,
                        order=a.endian,source_hint=a.source_hint,
                        max_hits=a.max_hits,max_roots=a.max_roots)
    for q in outputs:q.parent.mkdir(parents=True,exist_ok=True)
    # Create all outputs exclusively; manifest is deliberately a private local file.
    with a.report.open('x',encoding='utf-8') as f:
        json.dump(result,f,indent=2,sort_keys=True);f.write('\n')
    if a.private_manifest:
        with a.private_manifest.open('x',encoding='utf-8') as f:
            json.dump(build_private_manifest(a.archive,result),f,indent=2,sort_keys=True)
            f.write('\n')
    print('V58 read-only: ',result['candidate_root_occurrences'],
          'candidate ROOT(s); ',result['distinct_candidate_root_sha256s'],
          'distinct fingerprints')
    print('Archive untouched. Original game provenance not established by this scan.')


if __name__=='__main__':
    main()
