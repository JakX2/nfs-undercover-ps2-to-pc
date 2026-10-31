#!/usr/bin/env python3
"""V40: READ-ONLY scenery-info LOD-reference auditor and isolated record preview.

Works on supplied original NFS Carbon PC world stream; never writes a game BUN.
A 72-byte UC Wii SceneryInfo may be converted to an explicitly INCOMPLETE PC
record preview, strictly leaving all unknown bytes unchanged. A usable PC scene
also needs native geometry for EVERY referenced LOD and correct section/linking.
"""
from __future__ import annotations
import collections, hashlib, json, mmap, re, struct
from pathlib import Path

GEO_ROOT=0x80134000
CATALOGUE=0x80134001
ID_DIRECTORY=0x134003
SCENE_ROOT=0x80034100
INFO=0x34102
INST=0x34103
class SceneReferenceError(ValueError):pass

def u32(blob, p):return struct.unpack_from('<I',blob,p)[0]
def bin_hash(name):
    h=0xffffffff
    for x in name.upper().encode('ascii'):h=(h*33+x)&0xffffffff
    return h

def frame(blob,start=0,limit=None):
    if limit is None:limit=len(blob)
    at=start
    while at<limit:
        if at+8>limit:raise SceneReferenceError('Truncated chunk header')
        tag,n=struct.unpack_from('<II',blob,at)
        end=at+8+n
        if end>limit:raise SceneReferenceError(f'Chunk {tag:08X} exceeds parent')
        yield tag,at,at+8,end
        at=end

def native_geometry_ids(data):
    """Parse complete original Carbon PC top-level stream, catalogue IDs only.

    Return catalogue hash multiset; empty/corrupt catalogues fail closed.
    """
    ids=collections.Counter();roots=0
    for tag,at,p,end in frame(data):
        if tag!=GEO_ROOT:continue
        roots+=1
        cats=[(s,e) for k,_,s,e in frame(data,p,end) if k==CATALOGUE]
        if len(cats)!=1:raise SceneReferenceError('Expected one geometry catalogue')
        direct=[(s,e) for k,_,s,e in frame(data,*cats[0]) if k==ID_DIRECTORY]
        if len(direct)!=1:raise SceneReferenceError('No unique geometry index')
        s,e=direct[0]
        if (e-s)%8:raise SceneReferenceError('Invalid native index stride')
        hashes=[]
        for q in range(s,e,8):
            h,reserved=struct.unpack_from('<II',data,q)
            if reserved:raise SceneReferenceError('Unexpected catalogue index flag')
            ids[h]+=1;hashes.append(h)
        if hashes!=sorted(set(hashes)):raise SceneReferenceError('Unsorted/duplicate native catalogue')
    if not roots:raise SceneReferenceError('No geometry catalogues')
    return ids,roots

def info_rows(root, *, validate=True):
    """Iterate actual 72-byte scenery info entries within one original root."""
    if u32(root,0)!=SCENE_ROOT or u32(root,4)!=len(root)-8:
        raise SceneReferenceError('Not one original scene root')
    infos=[(s,e) for k,_,s,e in frame(root,8,len(root)) if k==INFO]
    if len(infos)!=1:raise SceneReferenceError('No unique 0x34102 info table')
    s,e=infos[0]
    if (e-s)%72:raise SceneReferenceError('Bad 72-byte info stride')
    for p in range(s,e,72):
        row=root[p:p+72]
        raw=row[:24].split(b'\0',1)[0]
        if not raw or any(c<32 or c>126 for c in raw):
            raise SceneReferenceError('Bad scenery name')
        yield raw.decode('ascii'),row,p

def first_instance_of_name(root,name):
    infos=list(info_rows(root));idxs=[i for i,x in enumerate(infos) if x[0].upper()==name.upper()]
    if len(idxs)!=1:raise SceneReferenceError('Scenery source name missing or ambiguous')
    parts=[(s,e) for k,_,s,e in frame(root,8,len(root)) if k==INST]
    if len(parts)!=1:raise SceneReferenceError('Missing placed instances')
    start,end=parts[0];start=(start+15)&~15
    if (end-start)%96:raise SceneReferenceError('Unexpected instance stride')
    for p in range(start,end,96):
        if struct.unpack_from('<h',root,p+0x54)[0]==idxs[0]:
            return infos[idxs[0]][1],root[p:p+96]
    raise SceneReferenceError('No placed instance found for name')

def choose_pc_info_lod(source_row, target_geometry_ids):
    """Produce an *offline-only candidate* with source +0x18 filled per PC fallback.

    This does NOT populate a valid Carbon PC scenery sector or prove that any
    remaining source fields, shaders, transforms, collision or streamer work.
    """
    if len(source_row)!=72:raise SceneReferenceError('Bad source row width')
    raw=source_row[:24].split(b'\0',1)[0]
    try:name=raw.decode('ascii')
    except UnicodeDecodeError as ex:raise SceneReferenceError('Invalid source name') from ex
    if not name:raise SceneReferenceError('Empty name')
    slots=struct.unpack_from('<4I',source_row,24)
    if slots[0]!=0:raise SceneReferenceError('Expected untouched Wii/PS2 +0x18 zero')
    if slots[1]!=bin_hash(name):raise SceneReferenceError('Source 1B hash/name mismatch')
    if not re.search(r'_[0-9][bB]_[0-9][0-9]$',name):
        raise SceneReferenceError('Only named 1B scenery LOD pattern supported')
    a_name=re.sub(r'(?i)(_[0-9])b(_[0-9][0-9])$',r'\1A\2',name)
    h_a=bin_hash(a_name)
    h_b=slots[1]
    if h_b not in target_geometry_ids:
        raise SceneReferenceError('1B model not present in native Carbon PC catalogue')
    first=h_a if h_a in target_geometry_ids else h_b
    dest=bytearray(source_row);struct.pack_into('<I',dest,24,first)
    result=bytes(dest);missing=sorted(set(h for h in struct.unpack_from('<4I',result,24) if h not in target_geometry_ids))
    changed=[k for k,(a,b) in enumerate(zip(source_row,result)) if a!=b]
    return result,{
        'name':name,'source_hash_words':[f'0x{x:08X}' for x in slots],
        'candidate_hash_words':[f'0x{x:08X}' for x in struct.unpack_from('<4I',result,24)],
        'high_detail_rule':'1A exists in target catalogue' if first==h_a else 'fallback to existing 1B',
        'changed_byte_offsets':changed,
        'missing_target_lod_hashes':[f'0x{x:08X}' for x in missing],
        'all_referenced_models_present':not missing,
        'status':'OFFLINE INFO-ROW PREVIEW ONLY, NOT A GAME PATCH'
    }

def strict_require_complete(candidate_row,geometry_ids):
    for h in struct.unpack_from('<4I',candidate_row,24):
        if h not in geometry_ids:
            raise SceneReferenceError(f'Unresolved native LOD model hash 0x{h:08X}')
    return True

def audit_native_references(stream:Path,root_offsets):
    with stream.open('rb') as fd,mmap.mmap(fd.fileno(),0,access=mmap.ACCESS_READ) as mm:
        ids,nroots=native_geometry_ids(mm)
        stats=collections.Counter();failure_samples=[]
        for off in root_offsets:
            if u32(mm,off)!=SCENE_ROOT:raise SceneReferenceError('Index contains non-scenery offset')
            root=mm[off:off+8+u32(mm,off+4)]
            for name,row,_ in info_rows(root):
                fields=struct.unpack_from('<4I',row,24)
                stats['total_info_records']+=1
                for i,h in enumerate(fields):
                    stats[f'lod_slot_{i}_nonzero']+=int(bool(h))
                    stats[f'lod_slot_{i}_resolves_to_PC_geometry']+=int(h in ids)
                if fields[0]==fields[1]:stats['first_slot_equals_B_slot']+=1
                match=re.search(r'_[0-9][bB]_[0-9][0-9]$',name)
                if match:
                    ah=bin_hash(re.sub(r'(?i)(_[0-9])b(_[0-9][0-9])$',r'\1A\2',name))
                    if ah in ids:
                        stats['canonical_B_with_A_model_in_catalogue']+=1
                        stats['canonical_B_with_A_slot_correct']+=int(fields[0]==ah)
                    else:
                        stats['canonical_B_without_A_model_in_catalogue']+=1
                        stats['canonical_B_without_A_falls_back_to_B']+=int(fields[0]==fields[1])
                if fields[0] not in ids and len(failure_samples)<15:
                    failure_samples.append({'name':name,'first_slot_hash':f'0x{fields[0]:08X}'})
        return {'source_stream':stream.name,'original_geometry_roots':nroots,
                'unique_native_geometry_IDs':len(ids),'native_ID_occurrences':sum(ids.values()),
                'stats':dict(stats),'unresolved_first_slot_examples':failure_samples,
                'limitation':'Catalogue join is static only. Hash found somewhere in the stream does not imply section-aware loading.'}

def native_single_root_ids(root):
    if u32(root,0)!=GEO_ROOT or u32(root,4)!=len(root)-8:
        raise SceneReferenceError('Bad standalone geometry root')
    ids,roots=native_geometry_ids(root)
    if roots!=1:raise SceneReferenceError('Only one standalone geometry root allowed')
    return ids
