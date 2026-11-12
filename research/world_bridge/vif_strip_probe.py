#!/usr/bin/env python3
"""Read-only VIF strip packet audit on selected original PS2 world sections.

This does not emit vertices, UVs, model hashes or texture identities. A decoded
triangle *count* is not a verified Carbon PC rendering/topology conversion.
PS2 VIF encoding and the candidate ADC mask logic are cross-checked against
https://github.com/pablonolascoo/nfs-mw-2005-ps2-port (MIT-licensed research).
"""
import argparse
from collections import Counter
import json
import math
from pathlib import Path
import struct
import zipfile

from geometry_hash_control import GEOM, SOLID_ROOT, PLATFORM_PS2, MAX_REGION, read_chunks, parse_geometry_root
from mesh_topology_control import parse_ps2_mesh, PS2_STRIPS, PS2_STRIP_DATA
from rb_scenery_graph_census import read_rb
from visibility_stream_join import read_small

MAX_PACKET = 4096
MAX_OPS = 512
NAMES = {0x00:'NOP',0x01:'STCYCL',0x02:'OFFSET',0x03:'BASE',0x04:'ITOP',
         0x05:'STMOD',0x06:'MSKPATH3',0x07:'MARK',0x10:'FLUSHE',0x11:'FLUSH',
         0x13:'FLUSHA',0x14:'MSCAL',0x15:'MSCALF',0x17:'MSCNT',0x20:'STMASK',
         0x30:'STROW',0x31:'STCOL',0x4a:'MPG',0x50:'DIRECT',0x51:'DIRECTHL'}


def decode_vif(data):
    """Decode VIF op boundaries and UNPACK metadata with exact input bounds."""
    if not data or len(data)>MAX_PACKET or len(data)%4:
        raise ValueError('VIF packet empty, excessive or not word-aligned')
    cursor=0
    cl=wl=1
    ops=[]
    while cursor<len(data):
        if len(ops)>=MAX_OPS:
            raise ValueError('Too many VIF operations')
        word=struct.unpack_from('<I',data,cursor)[0]
        imm, num, command=word&0xffff, (word>>16)&0xff, (word>>24)&0x7f
        interrupt=bool(word&0x80000000)
        pos=cursor
        cursor+=4
        if 0x60<=command<=0x7f:
            vn,vl=(command>>2)&3, command&3
            count=num or 256
            components=vn+1
            # V4-5 is a single packed 16-bit word, not four 16-bit values.
            if vn==3 and vl==3:
                bits, bytes_per_elem=5,2
            else:
                if vl==3:
                    raise ValueError('Unsupported reserved VIF unpack format')
                bits=32>>vl
                bytes_per_elem=components*bits//8
            if cl==0 or wl==0:
                raise ValueError('Undefined zero VIF STCYCL parameters')
            source_elems=(count if wl<=cl else ((count//wl)*cl+min(count%wl,cl)))
            size=(source_elems*bytes_per_elem+3)&~3
            if cursor+size>len(data):
                raise ValueError('VIF UNPACK overreads strip packet')
            ops.append({'kind':'UNPACK','address':imm&0x3ff,'count':count,
                        'components':components,'bits':bits,'unsigned':bool(imm&0x4000),
                        'tops':bool(imm&0x8000),'mask':bool(command&0x10),
                        'data':memoryview(data)[cursor:cursor+size],
                        'byte_size':size,'source_elements':source_elems,
                        'cycle_cl':cl,'cycle_wl':wl,'pos':pos,'interrupt':interrupt})
            cursor+=size
        else:
            if command not in NAMES:
                raise ValueError('Unrecognized VIF command')
            extra={0x20:4, 0x30:16, 0x31:16}.get(command,0)
            if command==0x4a:extra=(num or 256)*8
            if command in (0x50,0x51):extra=(imm or 65536)*16
            if cursor+extra>len(data):
                raise ValueError('VIF command payload exceeds strip packet')
            if command==0x01:
                cl,wl=imm&0xff,(imm>>8)&0xff
            ops.append({'kind':NAMES[command],'pos':pos,'imm':imm,'num':num,
                        'payload_bytes':extra,'interrupt':interrupt})
            cursor+=extra
    return ops


def unpack_rows(op):
    """Return untransformed numeric rows. VIF V4-5 and nontrivial cycles excluded."""
    if op['kind']!='UNPACK' or op['cycle_wl']!=op['cycle_cl']:
        raise ValueError('Cannot decode this cycled UNPACK into flat numeric rows')
    n,comps,bits=op['count'],op['components'],op['bits']
    if bits==5:
        raise ValueError('Packed V4-5 rows require a separate colors decoder')
    raw=op['data']
    stride=comps*bits//8
    if n*stride>len(raw):
        raise ValueError('UNPACK numeric payload truncated')
    if bits==32:
        fmt='<'+str(n*comps)+'I'
    elif bits==16:
        fmt='<'+str(n*comps)+('H' if op['unsigned'] else 'h')
    elif bits==8:
        fmt='<'+str(n*comps)+('B' if op['unsigned'] else 'b')
    else:
        raise ValueError('Unsupported numeric width')
    flat=struct.unpack_from(fmt,raw,0)
    return tuple(tuple(flat[i*comps:(i+1)*comps]) for i in range(n))


def adc_mask_from_words(words, nv, packs):
    """Candidate per-vertex triangle suppression mask from VIF control words.

    The bit assignments are empirically derived in public PS2 Most Wanted port
    research. Keep these semantics provisional until matched to PC topology.
    """
    if len(words)!=4 or packs!=(nv-1)//4 or not 3<=nv<=32:
        raise ValueError('Invalid VIF ADC control words')
    primary=words[1] if packs==7 else (words[2] if packs==3 else words[0])
    mask=[]
    for k in range(nv):
        if k<=14:
            bit=(primary>>(14-k))&1
        elif packs==3:
            bit=0
        elif packs==7:
            if k==15:
                a=(words[1]>>1)&1
                b=words[1]&1
                c=(words[2]>>17)&1
                d=(words[2]>>16)&1
                bit=int((b and not a) or (c and not d))
            else:
                bit=(words[2]>>(33-k))&1
        else:
            shift=4*packs+5-k
            if shift<0:
                raise ValueError('Invalid VIF ADC shift')
            bit=(words[2]>>shift)&1
        mask.append(bool(bit))
    return tuple(mask)


def candidate_positions(by_addr, nv, main_groups, extra_verts, scale, bbox):
    """Decode candidate XYZ VIF SOA lanes and reconstruct source world scale.

    For 16-bit coordinates infer an integer anchor from min/bbox. This anchor
    convention is provisional pending Carbon PC control vertex comparisons.
    """
    main=by_addr[5]
    rows=unpack_rows(main)
    verts=[]
    if main_groups:
        for g in range(main_groups):
            for lane in range(4):
                verts.append(tuple(rows[g*3+a][lane] for a in range(3)))
        if extra_verts:
            tail=unpack_rows(by_addr[5+main_groups*3])
            for lane in range(extra_verts):
                verts.append(tuple(tail[a][lane] for a in range(3)))
    else:
        for lane in range(extra_verts):
            verts.append(tuple(rows[a][lane] for a in range(3)))
    if len(verts)!=nv:
        raise ValueError('Position lanes do not match vertex count')
    if main['bits']==32:
        world=[tuple(struct.unpack('<f',struct.pack('<I',component))[0] for component in row) for row in verts]
    elif main['bits']==16:
        anchors=[round(bbox[0][a]-min(v[a] for v in verts)*scale) for a in range(3)]
        world=[tuple(v[a]*scale+anchors[a] for a in range(3)) for v in verts]
    else:
        raise ValueError('Unsupported position component size')
    if not all(math.isfinite(x) for row in world for x in row):
        raise ValueError('Nonfinite candidate vertex positions')
    actual_min=[min(v[a] for v in world) for a in range(3)]
    actual_max=[max(v[a] for v in world) for a in range(3)]
    max_error=max(abs(actual_min[a]-bbox[0][a]) for a in range(3))
    max_error=max(max_error,*(abs(actual_max[a]-bbox[1][a]) for a in range(3)))
    if max_error >= 0.1:
        raise ValueError('Candidate XYZ reconstruction misses source strip bounds')
    return {'max_bbox_error':max_error,'all_coordinates_finite':True,
            'decoded_position_vertices':len(world),'positions':tuple(world)}


def candidate_uvs(by_addr, vertex_count, main_groups, extra):
    """Decode candidate signed 16-bit ST coordinates as normalized UV pairs."""
    if 29 not in by_addr:
        raise ValueError('Missing VIF UV rows')
    rows=list(unpack_rows(by_addr[29]))
    if extra and main_groups:
        rows.extend(unpack_rows(by_addr[29+2*main_groups]))
    uv=[]
    for r in rows:
        if len(r)!=4:
            raise ValueError('Unexpected ST lane count')
        uv.extend(((r[0]/4096.0,r[1]/4096.0),(r[3]/4096.0,r[2]/4096.0)))
    if len(uv)<vertex_count:
        raise ValueError('UV lanes do not cover all vertices')
    return tuple(uv[:vertex_count])


def candidate_triangle_indices(adc):
    """PS2 ADC-suppressed strip to triangle-list *candidate* winding.

    Parity is reset on a transition into a suppressed vertex. The resulting
    index list is bounded but not proven equivalent to Carbon PC topology.
    """
    if len(adc)<3:
        raise ValueError('Too few strip vertices for triangles')
    triangles=[]
    parity_start=0
    for k,suppressed in enumerate(adc):
        if suppressed:
            if k==0 or (k and not adc[k-1]):
                parity_start=k
            continue
        if k<2:
            continue
        if (k-parity_start)&1:
            triangles.append((k-1,k-2,k))
        else:
            triangles.append((k-2,k-1,k))
    return tuple(triangles)


def decode_strip_header(packet, expected_nv, expected_polys):
    """Check VIF headers against a PS2 16-byte strip descriptor.

    Builds in-memory candidate XYZ, UV and ADC-filtered triangle lists. Their
    orientation and PC compatibility have not yet been independently verified.
    """
    ops=decode_vif(packet)
    by_addr={}
    for op in ops:
        if op['kind']=='UNPACK':
            if op['address'] in by_addr:
                raise ValueError('Repeated VIF destination address')
            by_addr[op['address']]=op
    for address in (0,1,2,5):
        if address not in by_addr:
            raise ValueError('Missing mandatory VIF header/position address')
    head=by_addr[0]
    if (head['bits'],head['components'],head['count'])!=(8,4,1):
        raise ValueError('Unexpected first VIF header type')
    h=unpack_rows(head)[0]
    nv,packs=h[0],h[1]
    if nv!=expected_nv or nv<3 or packs!=(nv-1)//4:
        raise ValueError('VIF header vertex count disagrees with strip descriptor')
    if not (0<=expected_polys<=nv-2):
        raise ValueError('Invalid expected triangle count')
    extra_verts=nv%4
    main_groups=nv//4 if extra_verts else (nv+3)//4
    pos=by_addr[5]
    main_lanes=4 if main_groups else extra_verts
    expected_main_rows=3*main_groups if main_groups else 3
    if pos['components']!=main_lanes or pos['bits'] not in (16,32) or pos['count']!=expected_main_rows:
        raise ValueError('Unexpected packed XYZ VIF position rows')
    tail_addr=5+3*main_groups
    if extra_verts and main_groups:
        tail=by_addr.get(tail_addr)
        if (not tail or tail['components']!=extra_verts or
            tail['count']!=3 or tail['bits']!=pos['bits']):
            raise ValueError('Incomplete partial XYZ VIF lanes')
    uv_count=0
    if 29 in by_addr:
        uv=by_addr[29]
        expected_main_uv=2*main_groups if main_groups else (nv+1)//2
        if uv['components']!=4 or uv['bits']!=16 or uv['count']!=expected_main_uv:
            raise ValueError('Unexpected VIF UV/ST main rows')
        uv_count=2*uv['count']
        if extra_verts and main_groups:
            # Extra ST rows cover the remaining partial vertex lanes.
            tail=by_addr.get(29+2*main_groups)
            needed_tail=(extra_verts+1)//2
            if not tail or tail['count']!=needed_tail or tail['bits']!=16 or tail['components']!=4:
                raise ValueError('Incomplete partial UV/ST lanes')
            uv_count+=2*needed_tail
        if uv_count<expected_nv:
            raise ValueError('Insufficient UV/ST candidates')
    colors=by_addr.get(45)
    if colors and (colors['count']!=nv or colors['bits']!=8 or colors['components']!=4):
        raise ValueError('Wrong VIF vertex-color count')
    # Address 1 is four raw u32 words. The second is an observed position scale.
    ctrl=by_addr[1]
    if (ctrl['components'],ctrl['bits'],ctrl['count'])!=(4,32,1):
        raise ValueError('Unexpected VIF control-word row')
    words=unpack_rows(ctrl)[0]
    scale=struct.unpack('<f',struct.pack('<I',words[1]))[0]
    if not math.isfinite(scale) or scale<=0:
        raise ValueError('Invalid VIF position scale')
    adc=adc_mask_from_words((words[0],words[2],words[3],0),nv,packs)
    actual_polygons=sum(not adc[k] for k in range(2,nv))
    if actual_polygons!=expected_polys:
        raise ValueError('ADC suppression does not reconstruct descriptor polygon count')
    # Address 2 contains two candidate bbox rows, 3 float32 coordinates each.
    box=by_addr[2]
    if (box['components'],box['bits'],box['count'])!=(3,32,2):
        raise ValueError('Unexpected VIF bbox row shape')
    bbox_bits=unpack_rows(box)
    box_f=tuple(tuple(struct.unpack('<f',struct.pack('<I',v))[0] for v in row) for row in bbox_bits)
    if not all(math.isfinite(v) for row in box_f for v in row):
        raise ValueError('Nonfinite VIF bbox values')
    spatial=candidate_positions(by_addr,nv,main_groups,extra_verts,scale,box_f)
    uvs=candidate_uvs(by_addr,nv,main_groups,extra_verts)
    triangles=candidate_triangle_indices(adc)
    if len(triangles)!=expected_polys or any(not 0<=index<nv for tri in triangles for index in tri):
        raise ValueError('Candidate triangle list has incorrect size/index range')
    return {'vertex_count':nv,'strip_polygon_count':expected_polys,
            'position_samples':spatial['positions'],'uv_samples':uvs,
            'triangle_index_candidates':triangles,
            'position_word_bits':pos['bits'],'partial_position_lanes':extra_verts,
            'uv_candidate_vertices':uv_count, 'has_vertex_colors':bool(colors),
            'adc_polygon_count':actual_polygons,
            'suppressed_candidate_triangles':nv-2-actual_polygons,
            'vif_operations':len(ops),
            'unpack_operations':sum(x['kind']=='UNPACK' for x in ops),
            'bbox_finite':True,'scale_finite_positive':True,
            'decoded_position_vertices':spatial['decoded_position_vertices'],
            'max_bbox_error':spatial['max_bbox_error'],
            'all_coordinates_finite':spatial['all_coordinates_finite']}


def audit_solid(platform_children):
    sizes=parse_ps2_mesh(platform_children)
    entry_blob=platform_children[1][1]
    data=platform_children[2][1]
    accum=Counter()
    for i in range(sizes['strip_entries']):
        _,nv,npoly,_,qoff,_,_,qsize,_,_,_=struct.unpack_from('<HBBfHbbBBbb',entry_blob,4+16*i)
        if not qsize:
            raise ValueError('Empty PS2 VIF strip packet')
        start,end=8+16*qoff,8+16*(qoff+qsize)
        result=decode_strip_header(data[start:end],nv,npoly)
        accum['vif_strips']+=1
        accum['decoded_position_vertices']+=result['decoded_position_vertices']
        accum['bbox_max_error_ge_0_1']+=result['max_bbox_error']>=0.1
        accum['bbox_max_error_ge_0_01']+=result['max_bbox_error']>=0.01
        accum['bbox_max_error_ge_0_001']+=result['max_bbox_error']>=0.001
        accum['candidate_triangles']+=len(result['triangle_index_candidates'])
        accum['decoded_uv_vertices']+=len(result['uv_samples'])
        accum['declared_vertices']+=result['vertex_count']
        accum['declared_polygons']+=result['strip_polygon_count']
        accum['adc_polygons']+=result['adc_polygon_count']
        accum['suppressed_candidate_triangles']+=result['suppressed_candidate_triangles']
        accum['strips_with_st_uv']+=result['uv_candidate_vertices']>0
        accum['strips_with_colors']+=result['has_vertex_colors']
        accum['strips_with_16bit_xyz']+=result['position_word_bits']==16
        accum['strips_with_32bit_xyz']+=result['position_word_bits']==32
        accum['unpack_operations']+=result['unpack_operations']
    return dict(accum)


def analyze(carbon_ps2_zip, uc_ps2_zip):
    sources={'carbon_ps2':(Path(carbon_ps2_zip),'L5',(141,142)),
             'undercover_ps2':(Path(uc_ps2_zip),'L2',(241,3401))}
    output={}
    for label,(archive,stem,sections) in sources.items():
        scenes,_=read_rb(archive,stem)
        rows,_,_=read_small(archive,stem,'RB')
        member=f'TRACKS/STREAM{stem}RB.BUN'
        with zipfile.ZipFile(archive) as z:
            if z.getinfo(member).file_size>MAX_REGION:
                raise ValueError('Secondary stream exceeds bound')
            world=z.read(member)
        result={}
        total=0
        for section in sections:
            if section not in scenes or section not in rows:
                raise ValueError('Missing prevalidated scene and stream table section')
            off,length=struct.unpack_from('<II',rows[section],0x14)
            blob=world[off:off+length]
            pos=0
            section_totals=Counter()
            packs=0
            while True:
                at=blob.find(struct.pack('<I',GEOM),pos)
                if at<0:break
                pos=at+4
                if at%4 or at+8>len(blob):continue
                clen=struct.unpack_from('<I',blob,at+4)[0]
                if clen>len(blob)-at-8:continue
                frame=blob[at:at+8+clen]
                try:
                    header=parse_geometry_root(frame)
                except ValueError:
                    continue
                root=list(read_chunks(frame,16,len(frame)))
                for cid,solid in root[1:]:
                    if cid!=SOLID_ROOT:raise ValueError('Unexpected non-solid in validated geometry pack')
                    kids=list(read_chunks(solid,0,len(solid)))
                    platform=list(read_chunks(kids[-1][1],0,len(kids[-1][1])))
                    if platform[0][0]!=PLATFORM_PS2:raise ValueError('Non-PS2 solid in PS2 source')
                    section_totals.update(audit_solid(platform))
                packs+=1
                pos=at+8+clen
            if packs==0:raise ValueError('No anchored PS2 geometry pack found')
            total+=section_totals['vif_strips']
            result[str(section)]={'geometry_packs':packs,**section_totals}
        output[label]=result
    return {'original_sections':output,
            'limits':('VIF opcode/UNPACK and candidate positions/UV row counts only. '
                      'Candidate XYZ and UV samples and ADC-filtered triangle lists are '
                      'decoded only in RAM and not exported. Coordinate anchors and '
                      'strip winding are not yet cross-validated against actual PC '
                      'vertex/index buffers. No material/texture binding, PC buffer output, '
                      'collision or in-game rendering demonstrated.')}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--carbon-ps2-zip',type=Path,required=True)
    p.add_argument('--undercover-ps2-zip',type=Path,required=True)
    a=p.parse_args()
    print(json.dumps(analyze(a.carbon_ps2_zip,a.undercover_ps2_zip),indent=2))

if __name__=='__main__':main()
