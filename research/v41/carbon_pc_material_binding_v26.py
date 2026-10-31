#!/usr/bin/env python3
"""V26: tightly guarded Carbon PC *direct-texture* scenery material rebind.

Source-verified, OFFLINE ONLY.  In 198 reference Carbon PC components, 128/406
materials have a literal 0x134B02+0x3c u32 equal to a hash in their parent
0x134012 u32/zero texture-dependency table. Others do not, including many
special shader/vertex format records. We change BOTH fields only in the
supported single-material, no-ambiguity case. We don't interpret shaders,
lighting, object identity, collision or streaming.

Warning: this does not claim that the game will render these assets correctly.
"""
from __future__ import annotations
import argparse,collections,hashlib,json,struct
from pathlib import Path
from wii_gx_v17_2 import subchunks
from carbon_pc_writer_v20 import locate,UnsafeRewrite
from carbon_pc_scenery_v19 import parse_component,read_model
from carbon_texture_refs_v21 import refs_for_component
from carbon_pc_tpk_groups_v25 import strict_full_layout_v25

SCENE=0x80134010
MAT=0x134b02
REF=0x134012
ERR=UnsafeRewrite


def source_wii_one_texture(wii_chunk:bytes,name:str)->int:
    """Read a source identity ONLY when every matching Wii LOD uses same hash."""
    found=[]
    for a,b in subchunks(wii_chunk,8,len(wii_chunk),SCENE):
        head=list(subchunks(wii_chunk,a,b,0x134011))
        if len(head)!=1:continue
        import re
        match=re.search(rb'[A-Z][A-Z0-9_]{6,}',wii_chunk[slice(*head[0])])
        if match and match.group().decode('ascii')==name:
            hashes=refs_for_component(wii_chunk,a,b)
            if len(hashes)!=1 or not hashes[0]:raise ERR('Wii object is not a single-source-texture component')
            found.append(hashes[0])
    if len(found)!=1:raise ERR(f'Expected one Wii component named {name}, got {len(found)}')
    return found[0]


def analyze_direct_bindings(chunk:bytes):
    """Conservative evidence classification; does not infer unrecognized shaders."""
    tally=collections.Counter();components=[]
    for a,b in subchunks(chunk,8,len(chunk),SCENE):
        try:
            mod=parse_component(chunk,a,b);refs=refs_for_component(chunk,a,b)
        except (ValueError,struct.error):continue
        row=[]
        tally['components']+=1
        tally['reference_entries']+=len(refs)
        for i,m in enumerate(mod['materials']):
            rec=bytes.fromhex(m['source_record_hex'])
            flags=struct.unpack_from('<I',rec,0x30)[0]
            value=struct.unpack_from('<I',rec,0x3c)[0]
            fmt=m['vertex_format']
            matching=[j for j,h in enumerate(refs) if h==value]
            direct=(flags==0 and fmt==0x4000 and len(matching)==1)
            tally['materials']+=1
            if direct:tally['direct_materials']+=1
            else:tally['unsupported_or_indirect_materials']+=1
            if flags==0 and fmt==0x4000:tally['simple_format_materials']+=1
            if value in refs:tally['literal_0x3c_in_0x134012']+=1
            row.append({'index':i,'fmt':f'{fmt:08X}','flags':flags,
                'field_0x3c':f'{value:08X}','slot_index':matching[0] if direct else None,
                'direct_supported':direct})
        components.append({'name':mod['name'],'ref_hashes':[f'{h:08X}' for h in refs],
            'materials':row})
    return {'totals':dict(tally),'components':components,
                'caveat':'literal match is evidence for a direct texture field, not proof of renderer behavior'}


def rebind_single_material(chunk:bytes,name:str,new_hash:int,require_old_hash:int|None=None):
    """Only retarget supported single-material PC models, preserving all other bytes.

    In-place local edit; no object-list, stream-index, or total-size changes.
    """
    if type(new_hash)!=int or not 0<new_hash<=0xffffffff:
        raise ERR('New texture hash must be nonzero unsigned 32-bit integer')
    a,b,mod=locate(chunk,name)
    refs=refs_for_component(chunk,a,b)
    if len(mod['materials'])!=1:raise ERR('Only single-material scenery is supported')
    mat=mod['materials'][0]
    record=bytes.fromhex(mat['source_record_hex'])
    flags=struct.unpack_from('<I',record,0x30)[0]
    old=struct.unpack_from('<I',record,0x3c)[0]
    if flags!=0 or mat['vertex_format']!=0x4000:
        raise ERR('Unsupported shader/vertex-layout combination; not direct-texture case')
    if require_old_hash is not None and old!=require_old_hash:
        raise ERR('Old texture hash differs from expected donor hash')
    if refs.count(old)!=1:raise ERR('Material hash does not identify exactly one dependency slot')
    if new_hash!=old and new_hash in refs:raise ERR('New texture already listed in this object dependencies')
    ranges=list(subchunks(chunk,a,b,MAT))
    if len(ranges)!=1:raise ERR('Missing or ambiguous material table')
    ma,mb=ranges[0]
    # Strict V19 parser checks the leading 0x11 filler. A single 144-byte
    # record is always the final 144 bytes for the sole material.
    if not (144<=mb-ma<=159 and chunk[ma:mb-144]==b'\x11'*(mb-ma-144)):
        raise ERR('Unexpected single-material table layout')
    mat_field=mb-144+0x3c
    ref_ranges=list(subchunks(chunk,a,b,REF))
    if len(ref_ranges)!=1:raise ERR('Missing or ambiguous texture-dependency table')
    ra,rb=ref_ranges[0]
    if rb-ra!=len(refs)*8:raise ERR('Texture dependency table count changed')
    ref_index=refs.index(old);ref_field=ra+8*ref_index
    if struct.unpack_from('<I',chunk,mat_field)[0]!=old or struct.unpack_from('<II',chunk,ref_field)!=(old,0):
        raise ERR('Material-reference offsets did not validate')
    mutable=bytearray(chunk)
    struct.pack_into('<I',mutable,mat_field,new_hash)
    struct.pack_into('<I',mutable,ref_field,new_hash)
    result=bytes(mutable)
    _,_,new_mod=locate(result,name)
    new_refs=refs_for_component(result,a,b)
    expected_refs=refs.copy();expected_refs[ref_index]=new_hash
    if new_refs!=expected_refs:raise ERR('Texture reference readback mismatch')
    expected_rec=bytearray(record);struct.pack_into('<I',expected_rec,0x3c,new_hash)
    if bytes.fromhex(new_mod['materials'][0]['source_record_hex'])!=bytes(expected_rec):
        raise ERR('Material record readback mismatch')
    for key in ('positions','normals','colors','uv','faces','triangle_material','vertex_buffers'):
        if mod[key]!=new_mod[key]:raise ERR(f'Geometry field unexpectedly changed: {key}')
    allowed=set(range(mat_field,mat_field+4))|set(range(ref_field,ref_field+4))
    changed={i for i,(x,y) in enumerate(zip(chunk,result)) if x!=y}
    if len(result)!=len(chunk) or not changed.issubset(allowed):
        raise ERR('Unexpected changes outside exactly two allowed u32 fields')
    report={'component':name,'old_hash':f'{old:08X}','new_hash':f'{new_hash:08X}',
      'material_record_offset':mat_field,'dependency_reference_offset':ref_field,
      'dependency_slot_index':ref_index,'dependency_count':len(refs),
      'material_count':1,'native_chunk_size_preserved':len(result)==len(chunk),
      'changed_bytes':len(changed),'changed_byte_offsets':sorted(changed),
      'unchanged_other_objects_and_geometry':True,
      'sha256_before':hashlib.sha256(chunk).hexdigest(),
      'sha256_after':hashlib.sha256(result).hexdigest(),
      'retained_auxiliary_donor_dependencies':[f'{h:08X}' for h in new_refs if h!=new_hash],
      'offline_only':True,'runtime_tested':False,
      'unresolved':['shader appropriateness','auxiliary donor texture dependency','object identity',
                    'placement in sector','collision','navigation','stream offsets']}
    return result,report


def underc_redbuilding_binding(pc_chunk:bytes,wii_chunk:bytes,pc_tpk_payload:bytes,
                               pc_carrier='AXOU_PARKLAMPA_1B_00',
                               wii_source='XBU_REDBUILDING_1B_00'):
    # This convenience pipeline is intentionally restricted to the exact V21
    # offline RedBuilding *prototype*, not a user game stream. The lower-level
    # in-place writer is available separately for controlled research.
    expected_prototype_sha='64e45f29390db3f8b35332780423098e475c4bd3ffc7cda0d1018807729b5cdf'
    if hashlib.sha256(pc_chunk).hexdigest()!=expected_prototype_sha:
        raise ERR('Expected the verified V21 RedBuilding offline prototype; refusing unknown input')
    _,_,carrier_mod=locate(pc_chunk,pc_carrier)
    if (len(carrier_mod['positions']),len(carrier_mod['faces']))!=(400,260):
        raise ERR('Input is not the 400-vertex/260-face RedBuilding transplant')
    h=source_wii_one_texture(wii_chunk,wii_source)
    pack=strict_full_layout_v25(pc_tpk_payload)
    e=pack['entries'].get(h)
    if not e or e['name']!='ARC_REDBUILDING_01' or e['format']!='DXT1':
        raise ERR('Supplied PC TPK does not contain source RedBuilding original DXT1 texture')
    out,report=rebind_single_material(pc_chunk,pc_carrier,h)
    report['wii_component']=wii_source
    report['wii_source_hash_agrees_with_pc_tpk']=True
    report['pc_tpk_texture_name']=e['name']
    report['pc_tpk_texture_resolution']=[e['width'],e['height']]
    report['pc_tpk_mip_payload_bytes']=e['size']
    report['pc_tpk_entry_count']=pack['entry_count']
    return out,report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('carbon_pc_carrier_chunk',type=Path)
    p.add_argument('undercover_wii_scenery_chunk',type=Path)
    p.add_argument('carbon_pc_tpk_payload_with_redbuilding',type=Path)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--report',type=Path)
    a=p.parse_args()
    if a.out.resolve()==a.carbon_pc_carrier_chunk.resolve():
        raise SystemExit('Refusing to overwrite original chunk')
    out,report=underc_redbuilding_binding(a.carbon_pc_carrier_chunk.read_bytes(),
         a.undercover_wii_scenery_chunk.read_bytes(),a.carbon_pc_tpk_payload_with_redbuilding.read_bytes())
    a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_bytes(out)
    if a.report:a.report.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
