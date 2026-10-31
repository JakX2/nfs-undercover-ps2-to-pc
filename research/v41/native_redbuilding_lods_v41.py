#!/usr/bin/env python3
"""V41 OFFLINE ONLY: source-verified RedBuilding 1B/1C/1Z in a PC native library.

Reuses the *exact* V33 original 1B native sample as a 36-byte single-material
layout donor for the two lower Wii LODs. Never patches a BUN or game install.
Unknown shader semantics, streaming registration, collision and gameplay remain.
"""
from __future__ import annotations
import argparse, hashlib, json, struct
from pathlib import Path
from carbon_pc_identity_v27 import (ROOT,CATALOGUE,CATALOGUE_INFO,ID_DIRECTORY,COMPONENT,
    HEADER,root_parts,root_header_for_component,rewrite_name_hash,bin_hash,chunks)
from carbon_pc_scenery_v19 import parse_component
from carbon_pc_bounds_v21 import rebuild,inspect
from carbon_scenery_transform_v21 import transplant_matrix,locate_header
from undercover_native_prototype_v20 import transplant,wii_to_pc_buffers
from wii_gx_v17_2 import read_model as read_wii,subchunks
from scenery_lod_bridge_v40 import (first_instance_of_name,choose_pc_info_lod,
                                      strict_require_complete)

WII_SHA='b72dd15bb57a298d02c216236701bc5345f2b7eb54d6eb2143ec55a83cb2115b'
DONOR_SHA='082c8b0cfb8acc4352c9cb643368d2d5fc7bfb4f9aa16dd983a746d3881e7793'
ORIGINAL_1B='XBU_REDBUILDING_1B_00'
LODS=('1B','1C','1Z')
TEXTURE_HASH=0x2CAB30BD

class LODError(ValueError): pass

def sha(data):return hashlib.sha256(data).hexdigest()
def modelname(lod):return f'XBU_REDBUILDING_{lod}_00'

def chunk_pack(kind,payload):
    if len(payload)>0xffffffff:raise LODError('Chunk too large')
    return struct.pack('<II',kind,len(payload))+payload

def get_source_model(source,name):
    models,errors=read_wii(source,name)
    if errors or len(models)!=1:raise LODError(f'Original Wii model unavailable or unsupported: {name}: {errors}')
    return models[0]

def get_wii_component_ref(source,name):
    matching=[]
    for a,b in subchunks(source,8,len(source),COMPONENT):
        from carbon_scenery_transform_v21 import _header
        h=_header(source,a,b)
        if h['name']!=name:continue
        refs=list(subchunks(source,a,b,0x134012))
        if len(refs)!=1:raise LODError('Original Wii component has unsupported reference table')
        s,e=refs[0]
        if (e-s)!=8:raise LODError('Original Wii component is not single-texture')
        tex,unknown=struct.unpack_from('<II',source,s)
        if unknown!=0:raise LODError('Unexpected Wii dependency flags')
        matching.append(tex)
    if len(matching)!=1:raise LODError('Ambiguous original Wii component')
    return matching[0]

def validate_face_attributes(wii_model,pc_model):
    """Check all source corners after float32 quantization, including colors/UV.

    The Wii->PC source exporter deduplicates (position,color,UV index) tuples,
    and may duplicate positions at seams. The original face order and winding
    must survive. Normals are NOT source-verifiable (V20 estimated them).
    """
    expected_vbytes,expected_indices,nverts,nfaces=wii_to_pc_buffers(wii_model)
    if len(pc_model['positions'])!=nverts or len(pc_model['faces'])!=nfaces:
        raise LODError('PC vertex/triangle count mismatch')
    expected=[(struct.unpack_from('<3f',expected_vbytes,p),
               tuple(expected_vbytes[p+24:p+28]),
               struct.unpack_from('<2f',expected_vbytes,p+28))
              for p in range(0,len(expected_vbytes),36)]
    for i,(xyz,color,uv) in enumerate(expected):
        if pc_model['positions'][i]!=xyz or pc_model['colors'][i]!=color or pc_model['uv'][i]!=uv:
            raise LODError(f'Source corner attributes changed at native PC vertex {i}')
    native_faces=[tri for tri in struct.iter_unpack('<3H',expected_indices)]
    if pc_model['faces']!=native_faces:
        raise LODError('Source triangle connectivity / winding changed')
    return {'positions':len(wii_model['positions']),'source_faces':nfaces,
            'native_vertices':nverts,'source_color_entries':len(wii_model['colors']),
            'source_uv_entries':len(wii_model['uv_raw']),
            'normal_source':'not verified: V20 area-weighted normals'}

def make_library(donor_root:bytes,wii_root:bytes):
    if sha(donor_root)!=DONOR_SHA:raise LODError('Source must be the exact verified V33 1B standalone PC root')
    if sha(wii_root)!=WII_SHA:raise LODError('Source must be the exact verified original Wii RedBuilding 3-LOD root')
    donor=root_parts(donor_root)
    if len(donor['entries'])!=1 or donor['entries'][0]['name']!=ORIGINAL_1B:
        raise LODError('Unexpected Carbon PC donor catalogue')
    if not (donor['index']==[bin_hash(ORIGINAL_1B)] and len(donor['children'])==3
            and [t for t,_,_ in donor['children']]==[0,CATALOGUE,COMPONENT]):
        raise LODError('Unrecognized native catalogue template')
    original_component=donor['entries'][0]['bytes']
    converted=[];models=[];details={}
    for lod in LODS:
        name=modelname(lod);src=get_source_model(wii_root,name)
        if get_wii_component_ref(wii_root,name)!=TEXTURE_HASH:
            raise LODError(f'Original Wii texture hash differs for {name}')
        if lod=='1B':
            root=donor_root
        else:
            root,transplant_result=transplant(donor_root,ORIGINAL_1B,wii_root,source_name=name)
            root,_=rebuild(root,ORIGINAL_1B,allow_invalid_source=True)
            root,_=transplant_matrix(root,ORIGINAL_1B,wii_root,name)
        before=root_parts(root)
        if len(before['entries'])!=1:raise LODError('Transplant altered catalogue cardinality')
        # Edit exact component identity instead of renaming untracked strings.
        component=before['entries'][0]['bytes']
        if lod!='1B':component=rewrite_name_hash(component,name,bin_hash(name))
        if root_header_for_component(component)!={'name':name,'id':bin_hash(name)}:
            raise LODError('Native component ID/name mismatch')
        mod=parse_component(component,8,len(component))
        attrs=validate_face_attributes(src,mod)
        # The bounds rebuilt from source geometry must be native-verified.
        single=chunk_pack(ROOT,b''.join(donor_root[s:e] for k,s,e in donor['children'] if k!=COMPONENT)+component)
        bounds=inspect(single,name)
        if not bounds['header_equals_material_union'] or not bounds['header_vertex_extrema_plus_0_01']:
            raise LODError('Native Carbon PC bounding boxes invalid')
        _,_,original_header=locate_header(wii_root,name)
        _,_,dest_header=locate_header(single,name)
        if original_header['matrix_bytes']!=dest_header['matrix_bytes']:
            raise LODError('Wii original object-local matrix not preserved')
        from carbon_texture_refs_v21 import refs_for_component
        ref=refs_for_component(component,8,len(component))
        if TEXTURE_HASH not in ref:raise LODError('Native material lost Undercover texture dependency')
        # Material +0x3C was source verified only in V26 direct-material case.
        if len(mod['materials'])!=1 or struct.unpack_from('<I',bytes.fromhex(mod['materials'][0]['source_record_hex']),0x3c)[0]!=TEXTURE_HASH:
            raise LODError('Native direct-texture material binding did not survive transplant')
        details[name]={**attrs,'hash':f'{bin_hash(name):08X}',
                       'source_texture_hash':f'{TEXTURE_HASH:08X}',
                       'pc_material_reference_hashes':[f'{v:08X}' for v in ref],
                       'bounds_match_pc_rule':True,'original_wii_matrix_preserved':True,
                       'component_bytes':len(component),'component_sha256':sha(component)}
        converted.append(component);models.append(src)
    # Retain Carbon PC group section id, library name, platform flags.
    cat=donor['catdata']
    ids=sorted(bin_hash(modelname(x)) for x in LODS)
    byid={root_header_for_component(b)['id']:b for b in converted}
    newcat=b''
    for kind,s,e in donor['catparts']:
        if kind==CATALOGUE_INFO:
            original_info=cat[s+8:e]
            info=bytearray(original_info)
            struct.pack_into('<I',info,0x0c,len(ids))
            newcat+=chunk_pack(kind,info)
        elif kind==ID_DIRECTORY:
            newcat+=chunk_pack(kind,b''.join(struct.pack('<II',h,0) for h in ids))
        else:newcat+=cat[s:e]
    body=b''
    for kind,s,e in donor['children']:
        if kind==CATALOGUE:body+=chunk_pack(kind,newcat)
        elif kind==COMPONENT:
            for h in ids:body+=byid[h]
        else:body+=donor_root[s:e]
    result=chunk_pack(ROOT,body)
    final=root_parts(result)
    if final['index']!=ids or len(final['entries'])!=3:
        raise LODError('New native PC catalogue readback failed')
    if any(final['entries'][i]['bytes']!=byid[ids[i]] for i in range(3)):
        raise LODError('Native component changed in final group')
    if final['info'][:12]!=donor['info'][:12] or final['info'][16:]!=donor['info'][16:]:
        raise LODError('PC-specific catalogue metadata modified unexpectedly')
    if struct.unpack_from('<I',final['info'],0x48)[0]!=0x3058 or struct.unpack_from('<I',final['info'],0x70)[0]!=0x80:
        raise LODError('Target library section/platform fields invalid')
    return result,{'stage':'OFFLINE, NOT INSTALLED OR TESTED IN CARBON','native_root_size':len(result),
                   'model_ids':[f'{h:08X}' for h in ids], 'source_wii_group_sha256':WII_SHA,
                   'source_pc_v33_donor_sha256':DONOR_SHA,
                   'library_name':final['info'][16:72].split(b'\0',1)[0].decode('ascii'),
                   'native_pc_section_id':f'{struct.unpack_from("<I",final["info"],0x48)[0]:08X}',
                   'native_root_sha256':sha(result),'lods':details,'unresolved':[
                    'PC streaming section insert/ownership', 'PC shader rendering compatibility',
                    'source-texture inclusion in a correctly registered PC TPK',
                    'scenery-instance sector insertion','collision / navigation','in-game execution']}

def verify_scene_info(scene_chunk,library):
    row,instance=first_instance_of_name(scene_chunk,'XBu_RedBuilding_1b_00')
    ids={e['id'] for e in root_parts(library)['entries']}
    candidate,diagnostic=choose_pc_info_lod(row,ids)
    strict_require_complete(candidate,ids)
    if tuple(struct.unpack_from('<4I',candidate,0x18))!=(bin_hash(modelname('1B')),bin_hash(modelname('1B')),bin_hash(modelname('1C')),bin_hash(modelname('1Z'))):
        raise LODError('Candidate PC scenery-info LOD fields do not match original Wii LODs')
    if candidate[0x1c:]!=row[0x1c:] or candidate[:0x18]!=row[:0x18]:
        raise LODError('Candidate scene-info writer changed unknown fields')
    return candidate,instance,diagnostic

def run(donor,wii,scene):
    root,report=make_library(donor,wii)
    row,instance,info=verify_scene_info(scene,root)
    report['scenery_info_candidate']=info
    report['scenery_info_lod_references_all_resolve']=True
    report['original_wii_placed_instance_unchanged']=True
    report['scenery_info_preview_sha256']=sha(row)
    report['original_instance_sha256']=sha(instance)
    return root,row,instance,report

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--pc-v33',type=Path,required=True)
    ap.add_argument('--uc-wii-source',type=Path,required=True)
    ap.add_argument('--uc-wii-scene',type=Path,required=True)
    ap.add_argument('--output-dir',type=Path,required=True)
    args=ap.parse_args()
    if any(args.output_dir.resolve()==p.resolve() for p in [args.pc_v33,args.uc_wii_source,args.uc_wii_scene]):
        raise SystemExit('Output directory cannot replace source')
    root,row,instance,report=run(args.pc_v33.read_bytes(),args.uc_wii_source.read_bytes(),args.uc_wii_scene.read_bytes())
    args.output_dir.mkdir(parents=True,exist_ok=True)
    (args.output_dir/'RedBuilding_1B_1C_1Z_Native_PC_V41.chunk').write_bytes(root)
    (args.output_dir/'RedBuilding_1B_PC_InfoRow_PREVIEW_V41.bin').write_bytes(row)
    (args.output_dir/'RedBuilding_Source_Instance_UNCHANGED_V41.bin').write_bytes(instance)
    (args.output_dir/'V41_REPORT.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
