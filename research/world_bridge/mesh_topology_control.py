#!/usr/bin/env python3
"""Read-only mesh count and strip-table controls for original Carbon/Undercover.

All geometry is parsed in RAM. Only aggregate statistics are printed; never
export asset payloads or imply that PS2 VIF/DMA data is already converted.
"""
import argparse
from collections import Counter
import json
import math
from pathlib import Path
import struct
import zipfile

from geometry_hash_control import (GEOM, SOLID_ROOT, SOLID_PLATFORM,
    PLATFORM_PC, PLATFORM_PS2, MAX_REGION, MAX_SECTION,
    read_chunks, parse_geometry_root, parse_solid)
from rb_scenery_graph_census import read_rb
from track_bundle_probe import SplitZip
from visibility_stream_join import read_small

PS2_STRIPS = 0x134A01
PS2_STRIP_DATA = 0x134A02
PC_MESH = 0x134B02
PC_TRI_INDICES = 0x134B03
PC_VERTEX = 0x134B01
PC_MATERIAL = 0x134C02
FILLER = b'\x11'*4
MAX_SOLIDS_IN_SECTION = 8192


def filler_size(blob):
    offset = 0
    while offset + 4 <= len(blob) and blob[offset:offset+4] == FILLER:
        offset += 4
    if offset > 12:
        raise ValueError('Excessive or ambiguous chunk alignment filler')
    return offset


def parse_ps2_mesh(platform_children):
    """Verify a 16-byte PS2 strip table, VIF byte-budget, and polygon counts."""
    if [c for c,_ in platform_children] != [PLATFORM_PS2, PS2_STRIPS, PS2_STRIP_DATA]:
        raise ValueError('Unexpected PS2 mesh platform child sequence')
    info, entries, data = [b for _,b in platform_children]
    p = filler_size(info)
    if p+12 > len(info):
        raise ValueError('Truncated PS2 platform info')
    version, nstrips, nbytes = struct.unpack_from('<III', info, p)
    if version != 0x20 or not 0 < nstrips <= 65535 or nbytes <= 0:
        raise ValueError('Unsupported PS2 platform info version/counts')
    entry_prefix, data_prefix = filler_size(entries), filler_size(data)
    if entry_prefix != 4 or data_prefix != 8:
        raise ValueError('Unexpected PS2 strip chunk alignment')
    if len(entries) != 4 + 16*nstrips or len(data) != 8 + nbytes:
        raise ValueError('PS2 strip count or strip-data byte count mismatch')
    polygons = 0
    strip_vertices = 0
    for i in range(nstrips):
        flags, nverts, npolys, density, qoff, nz, nt, qsize, group, tex, light = struct.unpack_from(
            '<HBBfHbbBBbb', entries, 4+16*i)
        if flags or not math.isfinite(density) or nverts < npolys+2 or qoff*16 + qsize*16 > nbytes:
            raise ValueError('Invalid PS2 strip descriptor or data range')
        polygons += npolys
        strip_vertices += nverts
    return {'strip_entries':nstrips, 'strip_polygon_count':polygons,
            'strip_vertices_declared':strip_vertices, 'strip_data_bytes':nbytes,
            'strip_ranges_bounded':True}


def parse_pc_mesh(platform_children):
    """Check PC mesh/index records and count possible vertex record layouts.

    36/52 divisibility is only a format candidate; this does not decode vertex
    coordinates, normals, UVs, material bindings, or resource lifetime.
    """
    if not platform_children or platform_children[0][0] != PLATFORM_PC:
        raise ValueError('Missing PC platform info chunk')
    kinds = [cid for cid,_ in platform_children]
    if (kinds.count(PC_MESH) != 1 or kinds.count(PC_TRI_INDICES) != 1 or
        PC_VERTEX not in kinds or PC_MATERIAL not in kinds or
        any(cid not in (PLATFORM_PC, PC_MESH, PC_TRI_INDICES, PC_VERTEX, PC_MATERIAL) for cid in kinds)):
        raise ValueError('Missing or unrecognized PC mesh chunks')
    info = platform_children[0][1]
    p = filler_size(info)
    if p+48 > len(info):
        raise ValueError('Truncated PC platform info')
    version = struct.unpack_from('<I', info, p+8)[0]
    flags = struct.unpack_from('<I', info, p+12)[0]
    meshes = struct.unpack_from('<I', info, p+16)[0]
    index_count = struct.unpack_from('<I', info, p+44)[0]
    if version != 0x12 or not 0 < meshes <= 8192 or not 0 < index_count <= 10000000:
        raise ValueError('Unsupported PC platform version or mesh/index count')
    if index_count % 3:
        raise ValueError('PC index count is not a multiple of three')
    if kinds.count(PC_MATERIAL) != meshes:
        raise ValueError('PC material-name chunk count differs from mesh records')
    mesh = next(blob for cid,blob in platform_children if cid==PC_MESH)
    indices = next(blob for cid,blob in platform_children if cid==PC_TRI_INDICES)
    if filler_size(mesh)!=4 or len(mesh)!=4+144*meshes:
        raise ValueError('PC mesh-entry count/144-byte stride mismatch')
    expected_index_bytes=(2*index_count+3)//4*4
    if filler_size(indices)!=8 or len(indices)!=8+expected_index_bytes:
        raise ValueError('PC index count/16-bit padded size mismatch')
    vertex_buffers=[b for cid,b in platform_children if cid==PC_VERTEX]
    possible=Counter()
    for blob in vertex_buffers:
        p=filler_size(blob)
        usable=len(blob)-p
        if usable <= 0:
            raise ValueError('Empty PC vertex buffer')
        fits36=(usable % 36 == 0)
        fits52=(usable % 52 == 0)
        if not (fits36 or fits52):
            raise ValueError('PC vertex buffer has neither 36 nor 52-byte candidate stride')
        possible['ambiguous' if fits36 and fits52 else ('36_only' if fits36 else '52_only')] += 1
    return {'pc_mesh_records':meshes,'pc_triangle_indices':index_count,
            'pc_triangle_count':index_count//3, 'pc_vertex_chunks':len(vertex_buffers),
            'candidate_vertex_chunk_classes':dict(possible),
            'pc_material_chunks':kinds.count(PC_MATERIAL),
            'platform_flag_word':flags}


def inspect_solid(solid):
    h, platform, _, _ = parse_solid(solid)
    chunks = list(read_chunks(solid, 0, len(solid), count_limit=5))
    children = list(read_chunks(chunks[-1][1],0,len(chunks[-1][1])))
    info = parse_pc_mesh(children) if platform==PLATFORM_PC else parse_ps2_mesh(children)
    return h, platform, info


def scan_geometry_pack_solids(section):
    """Locate complete indexed packs; reject duplicate local hash identities."""
    if len(section)>MAX_SECTION:
        raise ValueError('Stream section exceeds inspection bound')
    signature=struct.pack('<I',GEOM)
    result={}
    packs=0
    cursor=0
    while True:
        at=section.find(signature,cursor)
        if at<0:break
        cursor=at+4
        if at%4 or at+8>len(section):continue
        length=struct.unpack_from('<I',section,at+4)[0]
        if length>len(section)-at-8:continue
        frame=section[at:at+8+length]
        try:
            index=parse_geometry_root(frame)
        except ValueError:
            continue
        children=list(read_chunks(frame,16,len(frame)))
        solids=[data for cid,data in children[1:] if cid==SOLID_ROOT]
        indexed=set()
        for solid in solids:
            h,platform,stats=inspect_solid(solid)
            if h in indexed or h not in index['hashes']:
                raise ValueError('Duplicate or unindexed solid within a geometry pack')
            indexed.add(h)
            # Same hash in another pack may be legitimate; individual pack is
            # still validated, and the caller counts duplicated occurrences.
            result.setdefault(h, []).append((platform,stats))
            if sum(map(len,result.values()))>MAX_SOLIDS_IN_SECTION:
                raise ValueError('Too many solid resources in one section')
        if indexed!=index['hashes']:
            raise ValueError('Indexed models differ from complete validated solids')
        packs+=1
        if packs>16:
            raise ValueError('Too many geometry packs in one scene section')
        cursor=at+8+length
    if not packs:
        raise ValueError('No valid geometry pack')
    return packs,result


def inspect_source(archive,stem,sections):
    scenes,_=read_rb(archive,stem)
    rows,_,_=read_small(archive,stem,'RB')
    member=f'TRACKS/STREAM{stem}RB.BUN'
    if isinstance(archive,SplitZip):raw=archive.read(member,limit=MAX_REGION)
    else:
        with zipfile.ZipFile(archive) as z:
            if z.getinfo(member).file_size>MAX_REGION:
                raise ValueError('World stream exceeds inspection bound')
            raw=z.read(member)
    reports={}
    solid_maps={}
    for sec in sections:
        if sec not in scenes or sec not in rows:
            raise ValueError('Missing source-authenticated streaming/scenery section')
        off,size=struct.unpack_from('<II',rows[sec],0x14)
        packs,solids=scan_geometry_pack_solids(raw[off:off+size])
        solid_maps[sec]=solids
        total=Counter()
        for occurrences in solids.values():
            for plat,stat in occurrences:
                total['solid_occurrences']+=1
                if plat==PLATFORM_PC:
                    for key in ('pc_mesh_records','pc_triangle_indices','pc_triangle_count','pc_vertex_chunks','pc_material_chunks'):
                        total[key]+=stat[key]
                    for key,n in stat['candidate_vertex_chunk_classes'].items():
                        total['candidate_vertex_'+key]+=n
                else:
                    for key in ('strip_entries','strip_polygon_count','strip_vertices_declared','strip_data_bytes'):
                        total[key]+=stat[key]
        reports[sec]={'geometry_packs':packs,'distinct_solids':len(solids),**dict(total)}
    return reports, solid_maps


def compare_topology(pc,ps2):
    if set(pc)!=set(ps2):
        raise ValueError('PC and PS2 geometry control hashes disagree')
    delta=Counter()
    for namehash in pc:
        if len(pc[namehash])!=1 or len(ps2[namehash])!=1:
            raise ValueError('Control hashes must each have exactly one solid')
        pcplat,pcstat=pc[namehash][0]
        psplat,psstat=ps2[namehash][0]
        if pcplat!=PLATFORM_PC or psplat!=PLATFORM_PS2:
            raise ValueError('Unexpected paired mesh platforms')
        delta[pcstat['pc_triangle_count']-psstat['strip_polygon_count']]+=1
    return {'paired_solid_hashes':len(pc),'same_polygon_count':delta[0],
            'different_polygon_count':len(pc)-delta[0],
            'pc_minus_ps2_triangle_delta_distribution':{str(k):v for k,v in sorted(delta.items())}}


def analyze(pc_volumes,carbon_ps2_zip,uc_ps2_zip):
    sources={
        'carbon_pc':(SplitZip(pc_volumes),'L5',(141,142)),
        'carbon_ps2':(Path(carbon_ps2_zip),'L5',(141,142)),
        'undercover_ps2':(Path(uc_ps2_zip),'L2',(241,3401)),
    }
    reports={};solid_maps={}
    for label,(archive,stem,secs) in sources.items():
        report,ids=inspect_source(archive,stem,secs)
        reports[label]={str(k):v for k,v in report.items()}
        solid_maps[label]=ids
    comparisons={str(sec):compare_topology(solid_maps['carbon_pc'][sec],solid_maps['carbon_ps2'][sec]) for sec in (141,142)}
    return {'section_summaries':reports,'carbon_pc_vs_ps2':comparisons,
            'limits':('Counts/strides and indexed model hashes only. PS2 strip entry polygons are not yet decoded to triangle indices. '
                      'Candidate 36/52 PC vertex record sizes are length divisibility, not decoded formats. '
                      'No texture material lookup, imported model render, collision, runtime injection or playable world.')}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--pc-volumes',type=Path,nargs='+',required=True)
    p.add_argument('--carbon-ps2-zip',type=Path,required=True)
    p.add_argument('--undercover-ps2-zip',type=Path,required=True)
    a=p.parse_args()
    print(json.dumps(analyze(a.pc_volumes,a.carbon_ps2_zip,a.undercover_ps2_zip),indent=2))

if __name__=='__main__':main()
