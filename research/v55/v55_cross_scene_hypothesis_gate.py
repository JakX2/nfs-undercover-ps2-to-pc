#!/usr/bin/env python3
"""V55: read-only cross-root, source-provenance-gated scenery layout discriminator.

Tests *candidate arithmetic* for Wii 0x34107; neither a serialized Carbon PC
schema, a visibility decoder, nor an installable world writer. Local original
assets must be supplied by their owners and are never reproduced in reports.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
import os
from pathlib import Path
import re
import struct

ROOT = 0x80034100
SCENE = 0x34101
INSTANCE = 0x34103
TREE = 0x34105
PRECULL = 0x34107
AUX = 0x3410D
MAX_ROOT = 64*1024*1024
MAX_SOURCES = 256
WII_REDBUILDING_SHA = 'cb08ca728a9b76992aaaefe32b450565ef53246f090cfe296f77d96c5d272e7f'
HEX64 = re.compile(r'^[0-9a-fA-F]{64}$')

class GateError(ValueError):
    pass

def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def file_digest(path:Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for part in iter(lambda:f.read(1024*1024),b''):
            h.update(part)
    return h.hexdigest()

def validate_hex64(value, name):
    if not isinstance(value,str) or not HEX64.fullmatch(value):
        raise GateError(f'{name} must be 64 SHA-256 hex digits')
    return value.lower()

def endian(value):
    if value == 'little':return '<'
    if value == 'big':return '>'
    raise GateError('endian must be little or big')

def children(root:bytes, byteorder:str):
    """Return (absolute root-relative payload offset, bytes) for direct children."""
    e=endian(byteorder)
    if len(root)<8 or len(root)>MAX_ROOT:
        raise GateError('root outside bounded size')
    tag,size=struct.unpack_from(e+'II',root)
    if tag!=ROOT or size!=len(root)-8:
        raise GateError('root header or declared length invalid')
    out={};pos=8
    while pos<len(root):
        if pos+8>len(root):raise GateError('truncated child header')
        tag,n=struct.unpack_from(e+'II',root,pos);start=pos+8
        if tag & 0x80000000 or tag in out or n>len(root)-start:
            raise GateError('invalid, duplicate, nested or out-of-bounds child')
        out[tag]=(start,root[start:start+n]);pos=start+n
    if SCENE not in out or INSTANCE not in out:
        raise GateError('missing scenery ID or instance child')
    if len(out[SCENE][1])<4:raise GateError('scene ID child too short')
    return out

def _handle_digest(file_obj) -> str:
    """SHA-256 a currently open file handle, from byte zero, in bounded chunks."""
    file_obj.seek(0)
    h=hashlib.sha256()
    for block in iter(lambda:file_obj.read(1024*1024),b''):
        h.update(block)
    return h.hexdigest()


def _file_snapshot_identity(stat):
    """Best-effort mutation indicators, not an atomic filesystem snapshot."""
    return (stat.st_dev,stat.st_ino,stat.st_size,stat.st_mtime_ns,stat.st_ctime_ns)


def _read_framed_root(file_obj,offset,size,e):
    """Bounded extraction from the same file handle used by _handle_digest."""
    if offset is None:
        if size>MAX_ROOT:
            raise GateError('large stream needs an explicit root offset')
        file_obj.seek(0)
        return file_obj.read(size)
    if offset>size-8:
        raise GateError('root offset outside stream')
    file_obj.seek(offset)
    header=file_obj.read(8)
    if len(header)!=8:
        raise GateError('truncated root header at supplied offset')
    tag,n=struct.unpack(e+'II',header)
    if tag!=ROOT or n>MAX_ROOT-8 or n>size-offset-8:
        raise GateError('invalid framed scenery root at supplied offset')
    payload=file_obj.read(n)
    if len(payload)!=n:
        raise GateError('truncated scenery root payload')
    return header+payload


def read_verified_root(spec:dict):
    """Check whole-file AND root SHA-256 on one open handle (best-effort).

    File and ROOT fingerprints verify exact bytes, not game provenance.
    Double whole-file hashing and fstat/path checks detect many concurrent
    mutations, but do not provide an atomic immutable filesystem snapshot.
    """
    if not isinstance(spec,dict):raise GateError('manifest root entry must be object')
    for key in ('path','label','expected_file_sha256','expected_root_sha256','endian'):
        if key not in spec:raise GateError(f'missing manifest field {key}')
    label=spec['label']
    if not isinstance(label,str) or not label or len(label)>100:
        raise GateError('source label must be nonempty, at most 100 characters')
    path=Path(spec['path'])
    file_sha=validate_hex64(spec['expected_file_sha256'],'file SHA')
    root_sha=validate_hex64(spec['expected_root_sha256'],'root SHA')
    e=endian(spec['endian'])
    hint=spec.get('platform_hint','unknown')
    if hint not in ('wii','carbon_pc','unknown'):
        raise GateError('unsupported platform hint')
    if 'offset' in spec:
        offset=spec['offset']
        if not isinstance(offset,int) or isinstance(offset,bool) or offset<0:
            raise GateError('offset must be a nonnegative integer')
    else:offset=None

    with path.open('rb') as fh:
        before=os.fstat(fh.fileno())
        size=before.st_size
        initial_sha=_handle_digest(fh)
        if initial_sha!=file_sha:
            raise GateError(f'input file fingerprint mismatch for label {label}')
        root=_read_framed_root(fh,offset,size,e)
        if sha256(root)!=root_sha:
            raise GateError(f'extracted root fingerprint mismatch for label {label}')
        # Detect mutations to *other* archive sectors while ROOT stays intact.
        if _handle_digest(fh)!=initial_sha:
            raise GateError(f'input file changed while extracting root for label {label}')
        after=os.fstat(fh.fileno())
        try:
            current=path.stat()
        except OSError as exc:
            raise GateError('source path vanished during root extraction') from exc
        # Replacing a path can update the old inode ctime. Diagnose replacement
        # before raising the more generic file-metadata-changed exception.
        if (current.st_dev,current.st_ino)!=(after.st_dev,after.st_ino):
            raise GateError('source path replaced during root extraction')
        if _file_snapshot_identity(before)!=_file_snapshot_identity(after):
            raise GateError('source metadata changed during root extraction')

    parsed=children(root,spec['endian'])
    return root,parsed,{'label':label,'file_sha256':file_sha,'root_sha256':root_sha,
                        'platform_hint_unverified':hint,'endian':spec['endian'],
                        'stream_offset':offset,
                        'same_open_handle_hash_and_extract':True,
                        'best_effort_file_change_check_passed':True,
                        'atomic_filesystem_snapshot':False}


def candidate_profile(root:bytes, parsed:dict, metadata:dict):
    e=endian(metadata['endian'])
    b=parsed[INSTANCE][1]; start=parsed[INSTANCE][0]
    pad=(-start)&15
    wii96_ok=len(b)>=pad and (len(b)-pad)%96==0
    n96=(len(b)-pad)//96 if wii96_ok else None
    nodebytes=parsed[TREE][1] if TREE in parsed else None
    nodes48=(len(nodebytes)//48 if nodebytes is not None and len(nodebytes)%48==0 and len(nodebytes)>0 else None)
    precbytes=parsed[PRECULL][1] if PRECULL in parsed else None
    p128=(len(precbytes)//128 if precbytes is not None and len(precbytes)%128==0 and len(precbytes)>0 else None)
    aux=parsed[AUX][1] if AUX in parsed else None
    aux32=(len(aux)//32 if aux is not None and len(aux)%32==0 else None)
    references=None
    if wii96_ok and p128 is not None:
        refs=[struct.unpack_from(e+'h',b,pad+96*i+28)[0] for i in range(n96)]
        references={'min':min(refs) if refs else None,'max':max(refs) if refs else None,
                    'out_of_candidate_block_range':sum(v>=p128 for v in refs),
                    'negative_count':sum(v<0 for v in refs),
                    'referenced_nonnegative_distinct_count':len(set(v for v in refs if 0<=v<p128))}
    # Length arithmetic is an observation, not a decoder for 0x34107.
    matches={'length_equals_instance_plus_one_times_96':(n96 is not None and precbytes is not None and len(precbytes)==(n96+1)*96),
             'length_equals_tree_nodes_times_384':(nodes48 is not None and precbytes is not None and len(precbytes)==nodes48*384),
             'length_divisible_by_128':p128 is not None}
    verified=metadata['root_sha256']==WII_REDBUILDING_SHA and metadata['endian']=='little'
    return {**metadata,'source_authentication':'known_exact_original_Wii_RedBuilding' if verified else 'unknown_provenance',
            'root_bytes':len(root),
            'scenery_0x34101_first_u32_hex':f'0x{struct.unpack_from(e+"I",parsed[SCENE][1])[0]:08X}',
            'child_lengths':{f'0x{k:05X}':len(data) for k,(_,data) in parsed.items()},
            'candidate_96_instance_root_alignment_padding':pad,'candidate_96_instance_count':n96,
            'candidate_48_tree_node_count':nodes48,'candidate_128_preculler_block_count':p128,
            'candidate_32_aux_row_count':aux32,'candidate_aux_matches_instances':aux32 is not None and n96==aux32,
            'candidate_preculler_ref_statistics':references,
            'size_hypotheses':matches,
            'source_scenery_instance_payload_sha256':sha256(b),
            'candidate_wii_schema_is_PC_serialization_proof':False,
            'runtime_compatibility_verified':False}

def survey(specs:list[dict]):
    if not isinstance(specs,list) or not 1<=len(specs)<=MAX_SOURCES:
        raise GateError('1..256 root specs required')
    profiles=[]; labels=set()
    for spec in specs:
        root,child,meta=read_verified_root(spec)
        if meta['label'] in labels:raise GateError('duplicate report label')
        labels.add(meta['label'])
        profiles.append(candidate_profile(root,child,meta))
    groups=defaultdict(list);same_instances=defaultdict(list)
    for p in profiles:
        groups[p['root_sha256']].append(p['label'])
        same_instances[(p['scenery_0x34101_first_u32_hex'],p['source_scenery_instance_payload_sha256'])].append(p['label'])
    roots_unique={p['root_sha256']:p for p in profiles}
    # The 0x34101 first word is not proven to be a geographic section ID.
    # Distinguish numeric counterexamples in *all candidate layouts* from
    # authenticated generalization; only one Wii original fixture is pinned.
    counts={key:sum(p['size_hypotheses'][key] for p in roots_unique.values())
            for key in ('length_equals_instance_plus_one_times_96','length_equals_tree_nodes_times_384','length_divisible_by_128')}
    verified_roots=[p for p in roots_unique.values() if p['source_authentication']=='known_exact_original_Wii_RedBuilding']
    return {'schema':'v55-cross-scene-candidate-discriminator-v1',
            'submitted_roots':len(profiles),'unique_root_fingerprints':len(roots_unique),
            'root_labels_repeating_identical_bytes':[v for v in groups.values() if len(v)>1],
            'same_scenery_header_and_instance_payload_groups':[v for v in same_instances.values() if len(v)>1],
            'candidate_arithmetic_passes_on_distinct_roots':counts,
            'known_authenticated_Wii_root_count':len(verified_roots),
            'new_original_Wii_sectors_authenticated':False,
            'independent_cross_scene_replication_established':False,
            'hypotheses_resolved_for_original_game':False,
            'carbon_pc_serialized_0x34107_proven':False,
            'safe_to_install':False,'read_only':True,
            'profiles':profiles,
            'caution':'Distinct SHA fingerprints and matching sizes do not authenticate independent original-game sectors, or reveal unknown chunk semantics.'}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest',type=Path,required=True,help='Local JSON list or {"roots": [...]}; expected SHA-256 guards required')
    parser.add_argument('--report',type=Path,required=True,help='New output file only; no source game bytes copied')
    a=parser.parse_args()
    if a.report.exists() or a.report.resolve()==a.manifest.resolve():
        parser.error('Refusing to overwrite manifest or existing report')
    data=json.loads(a.manifest.read_text(encoding='utf-8'))
    specs=data['roots'] if isinstance(data,dict) and 'roots' in data else data
    if not isinstance(specs,list):raise GateError('manifest must contain roots list')
    # Output cannot overwrite any input. Report also excludes local filenames.
    if any(a.report.resolve()==Path(spec.get('path','')).resolve() for spec in specs if isinstance(spec,dict)):
        parser.error('Refusing overwrite of source')
    summary=survey(specs)
    a.report.parent.mkdir(parents=True,exist_ok=True)
    with a.report.open('x',encoding='utf-8') as f:
        json.dump(summary,f,indent=2,sort_keys=True);f.write('\n')
    print('V55 read-only cross-root candidate survey:',a.report)

if __name__=='__main__':main()