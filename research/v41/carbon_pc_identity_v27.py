#!/usr/bin/env python3
"""V27: strict, OFFLINE ONLY scenery identity and catalogue insert research.

Source inputs are the user's own Carbon PC and Undercover Wii scene chunks.
One source-verified Undercover mesh component can be inserted into an isolated
Carbon PC sample *without replacing the preexisting Carbon scenery components*.
This does not update the full world stream, collision, sectors, shaders or LOD.
"""
from __future__ import annotations
import argparse, hashlib, json, re, struct
from pathlib import Path
from wii_gx_v17_2 import subchunks
from carbon_pc_scenery_v19 import parse_component
from carbon_scenery_transform_v21 import _header

ROOT = 0x80134000
CATALOGUE=0x80134001
CATALOGUE_INFO=0x134002
ID_DIRECTORY=0x134003
COMPONENT=0x80134010
HEADER=0x134011
VERIFIED_SOURCE_SHA256='979ec656913120a3fa03d56b53469eefc6619b90f499013cb9ac287d2c0b295e'
VERIFIED_PC_SAMPLE_SHA256='58ed457d53bd15e47e14c68e3433ce84fa3b7709d4ef5bdb63ff9cf2b673863b'
class IdentityError(ValueError):pass


def bin_hash(name:str)->int:
    """Black Box BIN hash (seed 0xffffffff, 33*h+c), validated against Wii IDs."""
    if not name or any(ord(c)<32 or ord(c)>126 for c in name):
        raise IdentityError('Name must be nonempty printable ASCII')
    h=0xffffffff
    for char in name.encode('ascii'):
        h=(33*h+char)&0xffffffff
    return h


def chunks(blob,start,end):
    pos=start
    while pos<end:
        if pos+8>end:raise IdentityError('Truncated chunk header')
        kind,n=struct.unpack_from('<II',blob,pos)
        stop=pos+8+n
        if stop>end:raise IdentityError('Invalid chunk length')
        yield (kind,pos,stop)
        pos=stop


def root_parts(blob):
    if len(blob)<8 or struct.unpack_from('<II',blob,0)!=(ROOT,len(blob)-8):
        raise IdentityError('Not one intact 0x80134000 container')
    children=list(chunks(blob,8,len(blob)))
    cats=[c for c in children if c[0]==CATALOGUE]
    if len(cats)!=1:raise IdentityError('Expected exactly one catalogue')
    components=[c for c in children if c[0]==COMPONENT]
    if not components:raise IdentityError('Missing scenery components')
    parent=blob[cats[0][1]+8:cats[0][2]]
    pieces=list(chunks(parent,0,len(parent)))
    idx=[v for v in pieces if v[0]==ID_DIRECTORY]
    inf=[v for v in pieces if v[0]==CATALOGUE_INFO]
    if len(idx)!=1 or len(inf)!=1:raise IdentityError('Unknown catalogue layout')
    index=parent[idx[0][1]+8:idx[0][2]]
    if len(index)%8:raise IdentityError('Malformed directory rows')
    directory=list(struct.iter_unpack('<II',index))
    if any(v!=0 for _,v in directory):raise IdentityError('Directory contains nonzero secondary words')
    ids=[k for k,_ in directory]
    if ids!=sorted(set(ids)):raise IdentityError('Directory not sorted/unique')
    info=bytearray(parent[inf[0][1]+8:inf[0][2]])
    if len(info)!=144:raise IdentityError('Unsupported catalogue info header size')
    advertised=struct.unpack_from('<I',info,0x0c)[0]
    if advertised!=len(components) or len(ids)!=len(components):
        raise IdentityError('Catalogue count / component count / index length disagree')
    entries=[]
    for _,s,e in components:
        a,b=next(iter(subchunks(blob,s+8,e,HEADER)),(None,None))
        if a is None:raise IdentityError('Component missing 0x134011 header')
        meta=_header(blob,s+8,e)
        object_id=struct.unpack_from('<I',blob,meta['marker_offset']+4)[0]
        entries.append({'name':meta['name'],'id':object_id,'bytes':blob[s:e],
                        'offset':s,'size':e-s})
    actual=[v['id'] for v in entries]
    if actual!=ids:raise IdentityError('Component order differs from sorted catalogue directory')
    return {'children':children,'category':cats[0],'catdata':parent,'catparts':pieces,
            'info':info,'index':ids,'entries':entries,'info_pos':inf[0],
            'index_pos':idx[0]}


def rewrite_name_hash(component:bytes,new_name:str,source_id:int)->bytes:
    if len(new_name.encode('ascii'))>27:
        raise IdentityError('New component name exceeds the verified 28-byte name limit')
    if source_id!=bin_hash(new_name):raise IdentityError('Source object hash does not match source name')
    if len(component)<8 or struct.unpack_from('<II',component,0)!=(COMPONENT,len(component)-8):
        raise IdentityError('Expected one complete donor 0x80134010 chunk')
    hs=list(subchunks(component,8,len(component),HEADER))
    if len(hs)!=1:raise IdentityError('Missing/ambiguous donor header')
    a,b=hs[0];head=component[a:b]
    obj=_header(component,8,len(component))
    old=obj['name'].encode('ascii');match=re.search(rb'[A-Z][A-Z0-9_]{6,}',head)
    if not match or match.group()!=old:raise IdentityError('Unexpected donor name layout')
    start=match.start()
    if any(head[start+len(old):]):raise IdentityError('Donor name is not NUL terminated / padded')
    newhead=bytearray(head[:start]+new_name.encode('ascii')+b'\x00')
    newhead.extend(b'\x00'*(-len(newhead)%4))
    delta=len(newhead)-len(head)
    if delta<0 or delta>32 or delta%4:raise IdentityError('Unsafe name field resizing')
    local_hash=obj['marker_offset']-a+4
    if local_hash>=start:raise IdentityError('Header hash overlaps name')
    struct.pack_into('<I',newhead,local_hash,source_id)
    hdrpos=a-8
    edited=bytearray(component[:hdrpos])
    edited+=struct.pack('<II',HEADER,len(newhead))+newhead
    edited+=component[b:]
    struct.pack_into('<I',edited,4,len(edited)-8)
    reread=root_header_for_component(bytes(edited))
    if reread['name']!=new_name or reread['id']!=source_id:
        raise IdentityError('Identity write did not survive read-back')
    old_children=[component[s:e] for k,s,e in chunks(component,8,len(component)) if k!=HEADER]
    new_children=[edited[s:e] for k,s,e in chunks(edited,8,len(edited)) if k!=HEADER]
    if old_children!=new_children:
        raise IdentityError('Identity change modified non-header component children')
    return bytes(edited)


def root_header_for_component(comp:bytes):
    h=_header(comp,8,len(comp));val=struct.unpack_from('<I',comp,h['marker_offset']+4)[0]
    return {'name':h['name'],'id':val}


def select_wii_object(wii_bytes,name='XBU_REDBUILDING_1B_00'):
    match=[]
    for a,b in subchunks(wii_bytes,8,len(wii_bytes),COMPONENT):
        h=_header(wii_bytes,a,b)
        if h['name']==name:
            val=struct.unpack_from('<I',wii_bytes,h['marker_offset']+4)[0]
            match.append((name,val))
    if len(match)!=1 or match[0][1]!=bin_hash(name):
        raise IdentityError('Wii source identity missing, ambiguous or noncanonical')
    return match[0]


def add_redbuilding(carbon_pc:bytes,prototype_v26:bytes,wii_bytes:bytes):
    """Conservative append with full parent manifest rebuild, no game-stream changes."""
    sha=hashlib.sha256(prototype_v26).hexdigest()
    if sha!=VERIFIED_SOURCE_SHA256:
        raise IdentityError('Prototype SHA-256 differs from verified V26 sample')
    original=root_parts(carbon_pc)
    source=root_parts(prototype_v26)
    wii_name,wii_id=select_wii_object(wii_bytes)
    donor=next((c for c in source['entries'] if c['name']=='AXOU_PARKLAMPA_1B_00'),None)
    if donor is None:raise IdentityError('V26 donor lamp is absent')
    newcomponent=rewrite_name_hash(donor['bytes'],wii_name,wii_id)
    if any(e['id']==wii_id or e['name']==wii_name for e in original['entries']):
        raise IdentityError('Object ID or name already exists in Carbon catalogue')
    # Verify old vs V26 source child: borrowed name and shader/material may change,
    # but the untouched original must still be present in the new output.
    newmod=parse_component(newcomponent,8,len(newcomponent))
    if (newmod['name']!=wii_name or len(newmod['positions'])!=400 or
        len(newmod['faces'])!=260):
        raise IdentityError('New component geometry deviates from verified V26 mesh')
    all_entries=[e['bytes'] for e in original['entries']]+[newcomponent]
    all_entries.sort(key=lambda item:root_header_for_component(item)['id'])
    ids=[root_header_for_component(item)['id'] for item in all_entries]
    if ids!=sorted(set(ids)):raise IdentityError('New object hashes collide')
    cat=original['catdata'];info_kind,info_s,info_e=original['info_pos']
    idx_kind,idx_s,idx_e=original['index_pos']
    newcat=bytearray()
    for kind,s,e in original['catparts']:
        if kind==CATALOGUE_INFO:
            info=bytearray(cat[s+8:e]);struct.pack_into('<I',info,0x0c,len(ids));
            newcat+=struct.pack('<II',kind,len(info))+info
        elif kind==ID_DIRECTORY:
            index=b''.join(struct.pack('<II',k,0) for k in ids)
            newcat+=struct.pack('<II',kind,len(index))+index
        else:newcat+=cat[s:e]
    before=original['category']
    result=bytearray();result+=struct.pack('<II',ROOT,0)
    for kind,s,e in original['children']:
        if (kind,s,e)==before:
            result+=struct.pack('<II',CATALOGUE,len(newcat))+newcat
        elif kind==COMPONENT:pass
        else:result+=carbon_pc[s:e]
    # No unrecognized trailing children were dropped; insertion order is
    # supported only for original catalogues preceding all components.
    if original['children'].index(before)!=next(i for i,v in enumerate(original['children']) if v[0]==COMPONENT)-1:
        raise IdentityError('Unexpected catalogue position in original geometry container')
    first_component=next(i for i,v in enumerate(original['children']) if v[0]==COMPONENT)
    if any(v[0]!=COMPONENT for v in original['children'][first_component:]):
        raise IdentityError('Unrecognized non-component records after first scenery component')
    result+=b''.join(all_entries)
    struct.pack_into('<I',result,4,len(result)-8)
    rebuilt=bytes(result)
    after=root_parts(rebuilt)
    if len(after['entries'])!=len(original['entries'])+1 or after['index']!=ids:
        raise IdentityError('New index/readback mismatch')
    oldset={e['id']:e['bytes'] for e in original['entries']}
    newset={e['id']:e['bytes'] for e in after['entries']}
    if any(newset.get(i)!=raw for i,raw in oldset.items()):
        raise IdentityError('Original Carbon object bytes changed')
    added=newset.get(wii_id)
    if added!=newcomponent:raise IdentityError('New component was not preserved')
    reread=parse_component(added,8,len(added))
    if len(reread['positions'])!=400 or len(reread['faces'])!=260:
        raise IdentityError('New geometry reader failed')
    return rebuilt,{
        'stage':'offline-only, NOT game-installable','prototype_sha256':sha,
        'original_objects':len(original['entries']),'new_objects':len(after['entries']),
        'catalogue_hash_count':len(after['index']),'new_name':wii_name,
        'new_hash':f'0x{wii_id:08X}','new_component_bytes':len(newcomponent),
        'new_vertices':len(reread['positions']),'new_triangles':len(reread['faces']),
        'all_original_components_byte_identical':True,
        'new_component_in_sorted_directory':True,
        'new_component_preserves_V26_material_fields':True,
        'source_pc_sha256':hashlib.sha256(carbon_pc).hexdigest(),
        'result_sha256':hashlib.sha256(rebuilt).hexdigest(),
        'missing':['in-stream block offsets/relocations','world sector registration',
                   'collision and navigation','independent shader/material implementation',
                   'LOD and global object IDs','actual Carbon PC load test']}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('carbon_pc_sample');p.add_argument('v26_sample');p.add_argument('redbuilding_wii_source')
    p.add_argument('--output',required=True);p.add_argument('--report')
    args=p.parse_args()
    paths=[Path(args.carbon_pc_sample),Path(args.v26_sample),Path(args.redbuilding_wii_source)]
    dest=Path(args.output)
    if any(dest.resolve()==x.resolve() for x in paths):raise SystemExit('Refusing to overwrite any source input')
    # Command-line writing is intentionally limited to the original small
    # research sample. Do not let this tool patch a complete installed stream.
    if hashlib.sha256(paths[0].read_bytes()).hexdigest()!=VERIFIED_PC_SAMPLE_SHA256:
        raise SystemExit('Input Carbon chunk is not the verified 29-object V27 sample')
    blob,report=add_redbuilding(*(p.read_bytes() for p in paths))
    dest.write_bytes(blob)
    if args.report:Path(args.report).write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
