#!/usr/bin/env python3
"""Read-only Carbon/Undercover TPK texture-name index and scenery references.

Provenance: the user's PC Carbon, Wii Carbon and Wii Undercover stream
extracts. TPK 0xB3300000 > 0xB3310000 > 0x33310002/04.

Important: 0x134012 is a *texture reference/dependency table* based on
matching named Carbon Wii/PC objects and exact TPK hash-name pairs. It is NOT
proof that modifying the table alone changes material/shader bindings.
0x134B02+0x3C is not universally a texture hash, so never rewrite it here.
"""
from __future__ import annotations
import argparse, collections, json, mmap, re, struct
from pathlib import Path
from wii_gx_v17_2 import subchunks
from carbon_pc_scenery_v19 import parse_component, UnsupportedPC

TPK = 0xB3300000
MANIFEST_PARENT = 0xB3310000
INDEX_KIND = 0x33310002
NAMES_KIND = 0x33310004
SCENERY = 0x80134010
REF_KIND = 0x134012
NAME_RE = re.compile(rb'[A-Z][A-Z0-9_]{4,}')


class InvalidManifest(ValueError):
    pass


def children(data, start, end):
    pos=start
    while pos+8<=end:
        kind,n=struct.unpack_from('<II',data,pos)
        if n>end-pos-8:raise InvalidManifest('Child exceeds parent')
        yield kind,pos+8,pos+8+n
        pos+=8+n
    if pos!=end:raise InvalidManifest('Unaligned trailing bytes')


def _one(data,start,end,kind):
    items=[(a,b) for k,a,b in children(data,start,end) if k==kind]
    if len(items)!=1:raise InvalidManifest(f'Expected exactly one {kind:#x}')
    return items[0]


def manifest_entries(payload):
    """Yield (texture_hash, name) from a TPK payload (without top header).

    The 4-byte index corroborates the hash read 0x4D bytes before the ASCII
    name. The byte preceding the name is a *padded* length, NOT always
    len(name)+1: the PC and Wii examples use +1,+2,+3,+4. A prior parser
    accidentally dropped roughly 75% of Carbon PC texture names by assuming
    +1 only. All returned names are indexed by the TPK's own hash table.
    """
    main=_one(payload,0,len(payload),MANIFEST_PARENT)
    ia,ib=_one(payload,*main,INDEX_KIND)
    na,nb=_one(payload,*main,NAMES_KIND)
    if (ib-ia)%8:raise InvalidManifest('Texture hash index not 8-byte records')
    indexed={}
    for pos in range(ia,ib,8):
        h,zero=struct.unpack_from('<II',payload,pos)
        if zero!=0:raise InvalidManifest('Unsupported nonzero hash index word')
        if h in indexed:raise InvalidManifest('Duplicate texture hash index entry')
        indexed[h]=None
    result={}
    for match in NAME_RE.finditer(payload,na,nb):
        pos=match.start();name=match.group().decode('ascii')
        record=pos-0x4d
        if record<na or pos==na:continue
        if not 1<=payload[pos-1]-len(name)<=4:continue
        h=struct.unpack_from('<I',payload,record)[0]
        if h not in indexed:continue
        # A terminating NUL is required, including for the final entry.
        if pos+len(name)>=nb or payload[pos+len(name)]!=0:continue
        if h in result and result[h]!=name:
            raise InvalidManifest('Conflicting texture names for one hash')
        result[h]=name
    return result, {'index_entries':len(indexed), 'named_entries':len(result),
                    'unnamed_index_hashes':[f'{h:08X}' for h in indexed if h not in result]}


def scan_stream(path):
    """Memory-map an original stream; return metadata only, never image bytes."""
    path=Path(path)
    names={};packs=0;with_names=0;occurrences=collections.Counter()
    unindexed=collections.Counter();examples={}
    with path.open('rb') as f, mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as raw:
        pos=0
        while pos+8<=len(raw):
            kind,n=struct.unpack_from('<II',raw,pos)
            if n>len(raw)-pos-8:raise InvalidManifest(f'Stream chunk overrun at {pos:#x}')
            if kind==TPK:
                packs+=1
                indexed,stats=manifest_entries(raw[pos+8:pos+8+n])
                if indexed:with_names+=1
                for h,name in indexed.items():
                    if h in names and names[h]!=name:
                        raise InvalidManifest(f'Conflicting TPK hash {h:08X}: {names[h]} vs {name}')
                    names[h]=name;occurrences[h]+=1
                    examples.setdefault(h,pos)
                for h in stats['unnamed_index_hashes']:unindexed[h]+=1
            pos+=8+n
        if pos!=len(raw):raise InvalidManifest('Incomplete stream tail')
    return {'source':path.name,'tpk_packs':packs,'packs_with_names':with_names,
            'unique_texture_hashes':len(names), 'names':names,
            'hash_occurrences':occurrences,'first_pack_offset':examples,
            'unresolved_index_hashes':dict(unindexed)}


def refs_for_component(block,start,end):
    refs=list(subchunks(block,start,end,REF_KIND))
    if len(refs)!=1:raise InvalidManifest('Expected one 0x134012 texture-reference chunk')
    a,b=refs[0]
    if (b-a)%8:raise InvalidManifest('0x134012 is not 8-byte entries')
    pairs=list(struct.iter_unpack('<II',block[a:b]))
    if any(zero!=0 for _,zero in pairs):raise InvalidManifest('Unsupported 0x134012 second field')
    return [h for h,_ in pairs]


def named_components(block):
    for a,b in subchunks(block,8,len(block),SCENERY):
        try:mod=parse_component(block,a,b)
        except (UnsupportedPC,struct.error):continue
        yield a,b,mod


def audit_reference_chunks(samples,pc_index,wii_index=None):
    total=collections.Counter();refs=collections.Counter();material_ids=collections.Counter();
    matched_examples=[]
    for path in samples:
        raw=Path(path).read_bytes()
        for a,b,mod in named_components(raw):
            total['components']+=1
            r=refs_for_component(raw,a,b)
            total['reference_occurrences']+=len(r)
            for h in r:
                refs[h]+=1
                if h in pc_index['names']:total['resolved_pc_ref_occurrences']+=1
                if wii_index and h in wii_index['names']:total['resolved_wii_ref_occurrences']+=1
            for mat in mod['materials']:
                h=struct.unpack_from('<I',bytes.fromhex(mat['source_record_hex']),0x3c)[0]
                material_ids[h]+=1
                total['material_occurrences']+=1
                if h in r:total['material_0x3c_found_in_134012']+=1
                if h in pc_index['names']:total['material_0x3c_found_in_pc_tpk']+=1
            if mod['name']=='AXOU_PARKLAMPA_1B_00':
                matched_examples.append({'component':mod['name'],
                    'references':[{'hash':f'{h:08X}','texture':pc_index['names'].get(h)} for h in r]})
    return {
        'totals':dict(total),
        'unique_134012_hashes':len(refs),
        'unique_134012_resolved_pc':len(set(refs)&set(pc_index['names'])),
        'unresolved_pc_134012':[{'hash':f'{h:08X}','occurrences':n} for h,n in sorted(refs.items()) if h not in pc_index['names']],
        'unique_material_0x3c_values':len(material_ids),
        'unique_material_0x3c_resolved_pc':len(set(material_ids)&set(pc_index['names'])),
        'examples':matched_examples,
        'caution':'0x134012 is a validated texture dependency list; the exact 0x134B02 shader/texture binding semantics are NOT yet established.'
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('carbon_pc_stream');p.add_argument('carbon_wii_stream');p.add_argument('undercover_wii_stream')
    p.add_argument('sample_pc_chunks',nargs='+')
    p.add_argument('--output',default='CARBON_TEXTURE_REFERENCE_MAP_V21.json')
    args=p.parse_args()
    pc=scan_stream(args.carbon_pc_stream)
    wii=scan_stream(args.carbon_wii_stream)
    uc=scan_stream(args.undercover_wii_stream)
    shared=set(pc['names'])&set(wii['names'])
    disagreements=[f'{h:08X}' for h in shared if pc['names'][h]!=wii['names'][h]]
    if disagreements:raise InvalidManifest(f'Carbon PC/Wii texture name mismatch {disagreements[:5]}')
    summary=audit_reference_chunks(args.sample_pc_chunks,pc,wii)
    red_hash=0x2CAB30BD
    result={
        'sources':{'pc':pc['source'],'carbon_wii':wii['source'],'undercover_wii':uc['source']},
        'tpk_packs':{'pc':pc['tpk_packs'],'carbon_wii':wii['tpk_packs'],'undercover_wii':uc['tpk_packs']},
        'unique_tpk_hashes':{'pc':len(pc['names']),'carbon_wii':len(wii['names']),'undercover_wii':len(uc['names'])},
        'carbon_pc_wii_shared_hash_names':len(shared),
        'carbon_pc_wii_shared_name_disagreements':len(disagreements),
        'sample_scenery':summary,
        'undercover_redbuilding':{
            'source_ref_hash':f'{red_hash:08X}',
            'undercover_wii_tpk_name':uc['names'].get(red_hash),
            'undercover_wii_pack_occurrences':uc['hash_occurrences'][red_hash],
            'in_carbon_pc_tpk':red_hash in pc['names'],
            'requires_pc_compatible_texture_asset':True,
            'game_ready':False},
        'limitations':['PC texture hash-name index is not a shader/material binding decoder',
                       'TPK metadata scan does not decode PC pixel data',
                       'Undercover RedBuilding texture is not present in the supplied Carbon PC texture stream',
                       'No stream insertion, collision, navigation or runtime loading performed']}
    Path(args.output).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
