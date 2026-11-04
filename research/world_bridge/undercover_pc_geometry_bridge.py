#!/usr/bin/env python3
"""Source-only PS2 Undercover scenery -> experimental Carbon-PC-shaped eSolid.

The source geometry comes from the existing validated PS2 VIF/texture-material
readers. The output is a *new private file* only with explicit opt-in. Generated
PC mesh chunks and complete index/solid/root framing are checked by the
existing Carbon PC readers. Unknown runtime/renderer flags and normals remain
unverified; no stock Carbon game archive or installation is modified.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
import math
import os
from pathlib import Path
import struct

GEOM_ROOT = 0x80134000
GEOM_HEADER = 0x80134001
SOLID_ROOT = 0x80134010
SOLID_HEADER = 0x00134011
SOLID_TEXTURE_TABLE = 0x00134012
SOLID_PLATFORM = 0x80134100
GEOM_HEADER_DATA = 0x00134002
GEOM_INDEX = 0x00134003
GEOM_EMPTY = 0x80134008
MAX_FACE_COUNT = 150_000
MAX_SOURCE_VERTICES = 500_000
MAX_MESHES = 512
MAX_OUTPUT = 32 * 1024 * 1024
MAX_ZIP = 1024 * 1024 * 1024


def _chunk(cid, body):
    if type(cid) is not int or not 0 <= cid <= 0xffffffff or not isinstance(body, bytes):
        raise ValueError('Invalid candidate chunk')
    if len(body) > MAX_OUTPUT:
        raise ValueError('Candidate chunk exceeds 32 MiB')
    return struct.pack('<II', cid, len(body)) + body


def _hash(value):
    if type(value) is not int or not 0 < value <= 0xffffffff:
        raise ValueError('Invalid source identity')
    return value


def _vec(values, count, kind):
    if not isinstance(values, (list,tuple)) or len(values) != count:
        raise ValueError('Invalid '+kind+' vector')
    if any(type(x) not in (int,float) or not math.isfinite(x) or abs(x)>1e8 for x in values):
        raise ValueError('Nonfinite or excessive '+kind+' coordinate')
    return tuple(float(x) for x in values)


def _cross(a,b,c):
    x=(b[0]-a[0],b[1]-a[1],b[2]-a[2]);y=(c[0]-a[0],c[1]-a[1],c[2]-a[2])
    return (x[1]*y[2]-x[2]*y[1],x[2]*y[0]-x[0]*y[2],x[0]*y[1]-x[1]*y[0])


def _norm(v):
    m=math.sqrt(sum(c*c for c in v))
    return tuple(c/m for c in v) if m>1e-20 else None


def mesh_specs_from_ps2(xyz, uv, faces, labels, texture_hashes):
    """Group PS2 face corners per local material, preserving full face multiset.

    The normal is a deterministic area-weighted *candidate*, not decoded PS2
    normal data. Original winding from the bounded VIF ADC candidate is kept.
    """
    if (not isinstance(xyz,(tuple,list)) or not 3<=len(xyz)<=MAX_SOURCE_VERTICES or
            not isinstance(uv,(tuple,list)) or len(uv)!=len(xyz) or
            not isinstance(faces,(tuple,list)) or not 1<=len(faces)<=MAX_FACE_COUNT or
            not isinstance(labels,(tuple,list)) or len(labels)!=len(faces) or
            not isinstance(texture_hashes,(tuple,list)) or not 1<=len(texture_hashes)<=127):
        raise ValueError('Invalid PS2 source attribute collection')
    if any(_hash(h)==0 for h in texture_hashes):
        raise ValueError('Invalid source material hash')
    coordinates=[_vec(v,3,'XYZ') for v in xyz]
    texcoords=[_vec(v,2,'UV') for v in uv]
    by_label=defaultdict(list)
    for face,label in zip(faces,labels):
        if type(label) is not int or not 0<=label<len(texture_hashes):
            raise ValueError('Triangle references missing material table entry')
        if not isinstance(face,(tuple,list)) or len(face)!=3 or any(
                type(i) is not int or i<0 or i>=len(coordinates) for i in face):
            raise ValueError('Invalid original triangle index')
        if len(set(face))<3:
            raise ValueError('Degenerate repeated-index triangle')
        by_label[label].append(tuple(face))
    if len(by_label)>MAX_MESHES:
        raise ValueError('Too many grouped PC meshes')
    output=[]
    degenerate=0
    normal_fallbacks=0
    for label, source_faces in sorted(by_label.items()):
        vertex_map={}
        local_positions=[];local_uv=[];local_faces=[]
        for face in source_faces:
            target=[]
            for original in face:
                if original not in vertex_map:
                    vertex_map[original]=len(local_positions)
                    local_positions.append(coordinates[original])
                    local_uv.append(texcoords[original])
                target.append(vertex_map[original])
            local_faces.append(tuple(target))
        if len(local_positions)>65535:
            raise ValueError('Material mesh exceeds 16-bit local index limit')
        totals=[[0.0,0.0,0.0] for _ in local_positions]
        dominant=None
        for a,b,c in local_faces:
            cross=_cross(local_positions[a],local_positions[b],local_positions[c])
            if _norm(cross) is None:
                degenerate+=1
                continue
            if dominant is None:dominant=_norm(cross)
            for v in (a,b,c):
                for i in range(3):totals[v][i]+=cross[i]
        if dominant is None:
            raise ValueError('No nondegenerate face for a material mesh')
        normals=[]
        for v in totals:
            normal=_norm(v)
            if normal is None:
                normal=dominant
                normal_fallbacks+=1
            normals.append(normal)
        output.append({'positions':tuple(local_positions),
                       'normals':tuple(normals),
                       'uv':tuple(local_uv),
                       'triangles':tuple(local_faces),
                       'texture_index':label,
                       'material_name':f'UC_MATERIAL_{label:03d}'})
    stats={'source_vertex_occurrences':len(xyz),'source_triangles':len(faces),
           'generated_pc_meshes':len(output),
           'generated_pc_vertex_occurrences':sum(len(m['positions']) for m in output),
           'generated_pc_triangles':sum(len(m['triangles']) for m in output),
           'source_material_table_entries':len(texture_hashes),
           'area_weighted_normal_candidate':True,
           'degenerate_geometric_faces_preserved':degenerate,
           'candidate_normal_fallback_vertices':normal_fallbacks}
    return output,stats


def _new_header(model_hash, texture_count):
    """Parser-shaped fallback. Unknown retail header fields are NOT discovered."""
    header=bytearray(184)
    struct.pack_into('<I',header,12,0x16)
    struct.pack_into('<I',header,16,model_hash)
    header[25]=texture_count
    return bytes(header)


def pack_pc_geometry_root(model_hash, texture_hashes, pc_chunks, source_header=None):
    """Construct a complete indexed 0x80134000 candidate from PC mesh chunks.

    Source header bytes may be retained for offline tests, but whether their
    unknown source-platform fields work in Carbon's PC engine is UNPROVEN.
    """
    model_hash=_hash(model_hash)
    if not isinstance(texture_hashes,(tuple,list)) or not 1<=len(texture_hashes)<=127:
        raise ValueError('Invalid source texture table')
    table=tuple(_hash(x) for x in texture_hashes)
    if not isinstance(pc_chunks,(tuple,list)) or len(pc_chunks)<5:
        raise ValueError('Missing candidate PC native mesh chunks')
    expected={0x134900,0x134b01,0x134b02,0x134b03,0x134c02}
    if any(not isinstance(pair,tuple) or len(pair)!=2 or pair[0] not in expected or
           not isinstance(pair[1],bytes) for pair in pc_chunks):
        raise ValueError('Invalid native PC platform child')
    if [p[0] for p in pc_chunks[:3]] != [0x134900,0x134b02,0x134b03]:
        raise ValueError('Incorrect PC platform header/index child sequence')
    if source_header is None:
        header=_new_header(model_hash,len(table))
    else:
        if not isinstance(source_header,bytes) or not 32<=len(source_header)<=4096:
            raise ValueError('Invalid original source eSolid header')
        pad=0
        while source_header[pad:pad+4]==b'\x11'*4 and pad<16:pad+=4
        if (pad not in (0,4,8,12) or pad+26>len(source_header) or
                struct.unpack_from('<I',source_header,pad+12)[0] not in (0x16,0x800016) or
                struct.unpack_from('<I',source_header,pad+16)[0]!=model_hash or
                source_header[pad+25]!=len(table)):
            raise ValueError('Original source header does not match source identity/table')
        header=source_header
    tex=_chunk(SOLID_TEXTURE_TABLE,b''.join(struct.pack('<II',h,0) for h in table))
    platform=_chunk(SOLID_PLATFORM,b''.join(_chunk(k,v) for k,v in pc_chunks))
    solid=_chunk(SOLID_ROOT,_chunk(SOLID_HEADER,header)+tex+platform)
    geom_header=_chunk(GEOM_HEADER,
                       _chunk(GEOM_HEADER_DATA,bytes(144))+
                       _chunk(GEOM_INDEX,struct.pack('<II',model_hash,0))+
                       _chunk(GEOM_EMPTY,b''))
    root=_chunk(GEOM_ROOT,bytes(8)+geom_header+solid)
    if len(root)>MAX_OUTPUT:
        raise ValueError('Built candidate exceeds source inspection limit')
    return root


def _sig(vecs,uvs,tri,label):
    """Cyclic orientation-preserving face signature after f32 serialization."""
    corners=[]
    for index in tri:
        flat=(*vecs[index],*uvs[index])
        corners.append(struct.pack('<5f',*flat))
    rotations=(tuple(corners[k:]+corners[:k]) for k in range(3))
    return (label,min(rotations))


def verify_ps2_to_pc_faces(source_xyz,source_uv,source_faces,source_labels,
                            pc_xyz,pc_uv,pc_faces,pc_labels):
    """Exact f32 face-corner + texture-local-label multiset witness."""
    if len(source_faces)!=len(pc_faces) or len(source_labels)!=len(source_faces) or len(pc_labels)!=len(pc_faces):
        raise ValueError('PS2/PC triangle counts do not match')
    left=Counter(_sig(source_xyz,source_uv,f,l) for f,l in zip(source_faces,source_labels))
    right=Counter(_sig(pc_xyz,pc_uv,f,l) for f,l in zip(pc_faces,pc_labels))
    if left!=right:
        raise ValueError('PC roundtrip changed PS2 triangle/UV/material corner multiset')
    return {'source_faces':len(source_faces),'pc_faces':len(pc_faces),
            'all_f32_xyz_uv_texture_corner_faces_preserved':True,
            'orientation_preserved_up_to_cyclic_rotation':True}


def convert_decoded_ps2_model(model_hash,texture_hashes,xyz,uv,faces,labels,
                              source_header=None):
    """Produce candidate full root and compare native PC readback with PS2 faces."""
    # Imports are local so the core material grouping/normal math can be
    # audited and tested independently without original game readers.
    from synthetic_pc_mesh_writer import make_pc_chunks
    from geometry_hash_control import parse_geometry_root,read_chunks,parse_solid,PLATFORM_PC
    from pc_native_vertex_control import inspect_pc_solid
    from triangle_corner_uv_control import pc_geometry_attributes
    mesh_specs,stats=mesh_specs_from_ps2(xyz,uv,faces,labels,texture_hashes)
    children=make_pc_chunks(mesh_specs)
    blob=pack_pc_geometry_root(model_hash,texture_hashes,children,source_header)
    envelope=parse_geometry_root(blob)
    if envelope['hashes']!=frozenset({model_hash}) or envelope['platform']!=PLATFORM_PC:
        raise ValueError('Full PC candidate root failed native geometry identity checks')
    solid=next(v for cid,v in read_chunks(blob,16,len(blob)) if cid==SOLID_ROOT)
    info=parse_solid(solid)
    if info[0]!=model_hash or info[1]!=PLATFORM_PC:
        raise ValueError('Native PC candidate eSolid failed source identity check')
    platform=next(v for cid,v in read_chunks(solid,0,len(solid)) if cid==SOLID_PLATFORM)
    parsed=list(read_chunks(platform,0,len(platform)))
    check=inspect_pc_solid(parsed)
    pc_xyz,pc_uv,pc_faces,pc_labels=pc_geometry_attributes(parsed)
    face_check=verify_ps2_to_pc_faces(xyz,uv,faces,labels,pc_xyz,pc_uv,pc_faces,pc_labels)
    if check['mesh_records']!=stats['generated_pc_meshes'] or check['triangle_count']!=len(faces):
        raise ValueError('Native PC readback mesh/triangle totals disagree with source')
    return blob, {**stats,**face_check,
                  'pc_root_bytes':len(blob),
                  'native_pc_parser_roundtrip':True,
                  'retail_pc_loader_compatibility':'UNVERIFIED'}


def _source_geometry_occurrences(uc_zip,section):
    """Validate every source eSolid in pack order, preserving repeated hashes.

    Undercover's section 241 can contain multiple occurrences of one model
    identity across independent geometry packs. A hash->solid dict is lossy.
    This collection intentionally stays private in memory.
    """
    import zipfile
    from geometry_hash_control import (GEOM,SOLID_ROOT,PLATFORM_PS2,
       parse_geometry_root,parse_solid,read_chunks)
    from texture_binding_control import parse_solid_texture_table
    from visibility_stream_join import read_small
    from mesh_topology_control import parse_ps2_mesh
    rows,_,_=read_small(Path(uc_zip),'L2','RB')
    if section not in rows:raise ValueError('Requested source section absent from verified bundle')
    offset,length=struct.unpack_from('<II',rows[section],0x14)
    with zipfile.ZipFile(uc_zip) as z:
        info=z.getinfo('TRACKS/STREAML2RB.BUN')
        if (not 0<info.file_size<=128*1024*1024 or
                length>MAX_OUTPUT or offset+length>info.file_size):
            raise ValueError('Original PS2 stream section outside safety bounds')
        data=z.read(info)[offset:offset+length]  # zipfile checks member CRC
    found=[]
    cursor=0
    pack_count=0
    while True:
        at=data.find(struct.pack('<I',GEOM),cursor)
        if at<0:break
        cursor=at+4
        if at%4 or at+8>len(data):continue
        size=struct.unpack_from('<I',data,at+4)[0]
        if size>len(data)-at-8:continue
        frame=data[at:at+8+size]
        try:root=parse_geometry_root(frame)
        except ValueError:continue
        if root['platform']!=PLATFORM_PS2:
            raise ValueError('Source model pack unexpectedly has non-PS2 platform')
        pack_count+=1
        if pack_count>16:raise ValueError('Too many validated source geometry packs')
        names=set()
        for cid,raw in list(read_chunks(frame,16,len(frame)))[1:]:
            if cid!=SOLID_ROOT:raise ValueError('Non-solid in validated original source geometry')
            name,platform,_,_=parse_solid(raw)
            if platform!=PLATFORM_PS2 or name in names:
                raise ValueError('Duplicated source hash within one pack or wrong platform')
            names.add(name)
            chunks=list(read_chunks(raw,0,len(raw)))
            if [cid for cid,_ in chunks][:2]!=[SOLID_HEADER,SOLID_TEXTURE_TABLE]:
                raise ValueError('Unexpected original source eSolid header/material framing')
            header,table=chunks[0][1],chunks[1][1]
            table_hashes=parse_solid_texture_table(header,table)
            pchildren=list(read_chunks(chunks[-1][1],0,len(chunks[-1][1])))
            parse_ps2_mesh(pchildren)
            found.append((name,header,table_hashes,pchildren))
        if names!=root['hashes']:
            raise ValueError('Original pack index does not match contained source eSolids')
        cursor=at+8+size
    if not found:raise ValueError('No source-indexed geometry models in selected section')
    return found,pack_count


def audit_original_undercover(uc_zip,section=241,model_ordinal=0,private_output=None,write_private=False):
    """Owner-only source audit; default does not create any file."""
    if type(section) is not int or section not in (241,3401):
        raise ValueError('Unsupported original Undercover section')
    if type(model_ordinal) is not int or model_ordinal<0:
        raise ValueError('Invalid source model ordinal')
    if type(write_private) is not bool or (write_private!=(private_output is not None)):
        raise ValueError('Private writing requires both explicit opt-in and a target')
    path=Path(uc_zip).absolute()
    if any(p.is_symlink() for p in (path,*path.parents)) or not path.is_file() or not 0<path.stat().st_size<=MAX_ZIP:
        raise ValueError('Original owner archive missing, symlinked or excessive')
    # Check the original immutable archive before and after all work.
    def fingerprint():
        h=hashlib.sha256()
        with path.open('rb') as f:
            while v:=f.read(1024*1024):h.update(v)
        return path.stat().st_size,path.stat().st_mtime_ns,h.digest()
    snapshot=fingerprint()
    from triangle_corner_uv_control import ps2_geometry_attributes
    occurrences,source_packs=_source_geometry_occurrences(path,section)
    if model_ordinal>=len(occurrences):
        raise ValueError('Original model occurrence ordinal out of range')
    model_hash,header,table,platform=occurrences[model_ordinal]
    xyz,uv,faces,labels=ps2_geometry_attributes(platform)
    root,stats=convert_decoded_ps2_model(model_hash,table,xyz,uv,faces,labels,header)
    if fingerprint()!=snapshot:
        raise ValueError('Original source ZIP changed during geometry conversion')
    if write_private:
        target=Path(private_output).absolute()
        if (not target.name.startswith('PRIVATE_') or target.suffix.lower()!='.bin' or
                any(p.is_symlink() for p in (target,*target.parents)) or
                not target.parent.is_dir() or target.parent.name.casefold()=='tracks' or
                target.exists() or target.resolve()==path):
            raise ValueError('Private output must be new PRIVATE_*.bin outside game TRACKS')
        fd=os.open(target,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        try:
            with os.fdopen(fd,'wb') as out:
                out.write(root);out.flush();os.fsync(out.fileno())
        except BaseException:
            target.unlink(missing_ok=True)
            raise
    return {'scope':'PRIVATE_PS2_TO_PC_PARSER_VALIDATED_NOT_ENGINE_TESTED',
            'undercover_source_section':section,'source_model_ordinal':model_ordinal,
            'source_model_occurrences_available':len(occurrences),
            'source_model_identities_unique':len(set(x[0] for x in occurrences)),
            'validated_source_geometry_packs':source_packs,
            **stats,'private_file_created':write_private}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--undercover-ps2-zip',type=Path,required=True)
    p.add_argument('--section',type=int,choices=(241,3401),default=241)
    p.add_argument('--model-ordinal',type=int,default=0)
    p.add_argument('--private-output',type=Path)
    p.add_argument('--write-private',action='store_true')
    a=p.parse_args()
    print(json.dumps(audit_original_undercover(a.undercover_ps2_zip,a.section,
                  a.model_ordinal,a.private_output,a.write_private),indent=2))

if __name__=='__main__':main()
