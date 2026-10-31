#!/usr/bin/env python3
"""Strict NFS Carbon PC native world-scenery mesh reader (0x80134000).

Validated against named Carbon Wii models, not a Carbon PC writer.
0x134B02 stores 144-byte material records; known PC vertex formats are
0x224000/0x224012: stride 52 and 0x4000: stride 36. Indexed triangles
are explicit in 0x134B03 as unsigned little-endian 16-bit triangle lists.
0x134B01 can hold multiple adjacent material runs with matching stride.
Unknown formats and ambiguous buffer grouping are intentionally rejected.
"""
from __future__ import annotations
import argparse,collections,json,math,mmap,re,struct
from pathlib import Path
from wii_gx_v17_2 import subchunks

GEOM=0x80134000
PC_FORMAT_STRIDES={0x224000:52,0x224012:52,0x4000:36}
class UnsupportedPC(ValueError):pass


def exact(block,a,b,kind):
    found=list(subchunks(block,a,b,kind))
    if len(found)!=1:raise UnsupportedPC(f'Expected one {kind:#x}, got {len(found)}')
    return block[slice(*found[0])]


def padded(raw,record_bytes,kind):
    """Strip only 0x11 padding based on a known exact record size."""
    pad=len(raw)%record_bytes
    if pad>15 or pad%4 or raw[:pad]!=b'\x11'*pad:
        raise UnsupportedPC(f'{kind} bad padding/size: {len(raw)}, remainder {pad}')
    return raw[pad:],pad


def parse_component(block,a,b):
    head=exact(block,a,b,0x134011)
    m=re.search(rb'[A-Z][A-Z0-9_]{6,}',head)
    if not m:raise UnsupportedPC('No component name')
    name=m.group().decode('ascii')
    meta=exact(block,a,b,0x134900)
    mats_blob=exact(block,a,b,0x134b02)
    index_blob=exact(block,a,b,0x134b03)
    vranges=list(subchunks(block,a,b,0x134b01))
    if not vranges:raise UnsupportedPC('No 0x134b01 vertex buffers')
    matdata,pad=padded(mats_blob,144,'material entries')
    if not matdata:raise UnsupportedPC('No material entries')
    materials=[]
    for i in range(0,len(matdata),144):
        x=matdata[i:i+144]
        nv=struct.unpack_from('<I',x,0x40)[0]
        nf=struct.unpack_from('<I',x,0x60)[0]
        first=struct.unpack_from('<I',x,0x64)[0]
        ni=struct.unpack_from('<I',x,0x7c)[0]
        fmt=struct.unpack_from('<I',x,0x38)[0]
        if fmt not in PC_FORMAT_STRIDES:raise UnsupportedPC(f'Unknown vertex layout {fmt:#x}')
        if not 1<=nv<65536 or not 1<=nf<65536 or ni!=3*nf:
            raise UnsupportedPC('Material vertex/triangle counts invalid')
        materials.append(dict(vertices=nv,triangles=nf,first_index=first,num_indices=ni,
            vertex_format=fmt,stride=PC_FORMAT_STRIDES[fmt],source_record_hex=x.hex()))
    expected_indices=sum(m['num_indices'] for m in materials)
    index_pad_candidates=[]
    extra=len(index_blob)-expected_indices*2
    for lead in range(max(0,extra-15),min(15,extra)+1):
        tail=extra-lead
        if lead%2==0 and tail%2==0 and index_blob[:lead]==b'\x11'*lead and (not tail or index_blob[-tail:]==b'\x00'*tail):
            index_pad_candidates.append((lead,tail))
    if len(index_pad_candidates)!=1:
        raise UnsupportedPC(f'Index buffer padding/count unexpected: {len(index_blob)}, expected {expected_indices*2}')
    index_pad,index_tail=index_pad_candidates[0]
    indices=struct.unpack_from('<'+str(expected_indices)+'H',index_blob,index_pad)
    ix_cursor=0
    for m in materials:
        if m['first_index']!=ix_cursor:raise UnsupportedPC('Material index offsets noncontiguous')
        ix_cursor+=m['num_indices']

    # Each 0x134b01 contains the exact vertices of one or more contiguous
    # material entries, all with the same byte stride. Split only if unique.
    raw_buffers=[block[slice(*r)] for r in vranges]
    assignments=[]
    def solve(vi,mi,acc):
        if vi==len(raw_buffers) and mi==len(materials):
            assignments.append(acc);return
        if vi>=len(raw_buffers) or mi>=len(materials) or len(assignments)>1:return
        raw=raw_buffers[vi]
        total=0
        s=materials[mi]['stride']
        for j in range(mi,len(materials)):
            if materials[j]['stride']!=s:break
            total+=materials[j]['vertices']
            size=total*s
            pad=len(raw)-size
            if 0<=pad<=15 and pad%4==0 and raw[:pad]==b'\x11'*pad:
                solve(vi+1,j+1,acc+[(mi,j+1,pad,s,total)])
    solve(0,0,[])
    if len(assignments)!=1:
        raise UnsupportedPC(f'Vertex buffer segmentation not uniquely established ({len(assignments)} ways)')
    assignment=assignments[0]
    vertices=[]; normals=[]; colors=[]; uv=[];buffer_summaries=[]; faces=[]; triangle_material=[]
    material_buffer=[]
    offset=0; cursor=0
    for vi,(mi,mj,pad,stride,nv) in enumerate(assignment):
        raw=raw_buffers[vi][pad:]
        if len(raw)!=nv*stride:raise UnsupportedPC('Unexpected vertex count')
        group_vertices=[]
        for j in range(nv):
            off=j*stride
            v=struct.unpack_from('<3f',raw,off)
            n=struct.unpack_from('<3f',raw,off+12)
            rgba=struct.unpack_from('<4B',raw,off+24)
            tex=struct.unpack_from('<2f',raw,off+28)
            if not all(math.isfinite(x) and abs(x)<1e6 for x in (*v,*n,*tex)):
                raise UnsupportedPC('Invalid PC vertex float')
            group_vertices.append(v)
            vertices.append(v);normals.append(n);colors.append(rgba);uv.append(tex)
        prefix=0
        for m_id in range(mi,mj):
            m=materials[m_id]
            start=m['first_index'];end=start+m['num_indices'];local=indices[start:end]
            if len(local)!=3*m['triangles'] or any(i<prefix or i>=prefix+m['vertices'] for i in local):
                raise UnsupportedPC(f'Material {m_id} index outside its own vertex interval')
            m['vertex_buffer']=vi
            m['vertex_offset_in_buffer']=prefix
            m['vertex_offset_global']=offset+prefix
            for t in range(0,len(local),3):
                faces.append(tuple(offset+x for x in local[t:t+3]))
                triangle_material.append(m_id)
            prefix+=m['vertices']
        if prefix!=nv:raise UnsupportedPC('Buffer vertex count inconsistent')
        buffer_summaries.append({'vertices':nv,'stride':stride,'padding':pad,'material_ids':list(range(mi,mj))})
        offset+=nv
    if len(faces)!=sum(m['triangles'] for m in materials):raise UnsupportedPC('Incorrect triangle sum')
    if any(len(set(f))<3 for f in faces):raise UnsupportedPC('Source PC degenerate triangle')
    return dict(name=name,positions=vertices,normals=normals,colors=colors,uv=uv,faces=faces,
        triangle_material=triangle_material,materials=materials,vertex_buffers=buffer_summaries,
        index_padding=index_pad,index_tail_padding=index_tail,material_padding=len(mats_blob)-len(matdata),
        header_bytes=len(head),meta_bytes=len(meta))


def read_model(block,only_component=None):
    if len(block)<8 or struct.unpack_from('<I',block)[0]!=GEOM:raise ValueError('Not a Carbon PC 0x80134000 chunk')
    models=[];errors=[]
    for a,b in subchunks(block,8,len(block),0x80134010):
        h=list(subchunks(block,a,b,0x134011))
        hit=re.search(rb'[A-Z][A-Z0-9_]{6,}',block[slice(*h[0])]) if h else None
        name=hit.group().decode('ascii') if hit else 'UNNAMED'
        if only_component and name.upper()!=only_component.upper():continue
        try:models.append(parse_component(block,a,b))
        except (UnsupportedPC,struct.error) as e:errors.append({'name':name,'error':str(e)})
    return models,errors


def inspect_stream(path,limit=None):
    tally=collections.Counter();formats=collections.Counter();errs=collections.Counter();examples=[]
    with open(path,'rb') as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as mm:
        p=0;scans=0
        while p+8<=len(mm):
            typ,length=struct.unpack_from('<II',mm,p)
            if p+8+length>len(mm):raise ValueError('Top-level stream chunk invalid')
            if typ==GEOM:
                scans+=1
                if limit is not None and scans>limit:break
                models,errors=read_model(mm[p:p+length+8])
                tally['full' if models and not errors else 'partial' if models else 'unsupported']+=1
                tally['models']+=len(models);tally['triangles']+=sum(len(m['faces']) for m in models)
                for mod in models:
                    for mat in mod['materials']:formats[hex(mat['vertex_format'])]+=1
                for error in errors:errs[error['error']]+=1
                if models and len(examples)<10:examples.append({'offset':p,'name':models[0]['name'],'triangles':len(models[0]['faces'])})
            p+=8+length
    return {'geometry_containers':min(scans,limit or scans),'counts':dict(tally),'layout_codes':dict(formats),'unsupported':dict(errs.most_common(20)),'examples':examples}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('carbon_pc_stream');p.add_argument('--limit',type=int);p.add_argument('--output',default='CARBON_PC_AUDIT_V19.json');a=p.parse_args()
    out=inspect_stream(a.carbon_pc_stream,a.limit);Path(a.output).write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
