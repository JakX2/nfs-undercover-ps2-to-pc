#!/usr/bin/env python3
"""Read-only texture-table and polygon-texture budget audit for Carbon and UC.

The source-backed checks link solid texture hash tables, PC per-mesh material
slots and PS2 per-strip texture numbers. No texture pixels, materials, model
hash lists, or game bytes are printed or exported. Face-by-face material
assignment and texture package availability are separate, unproven gates.
"""
import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import struct
import zipfile

from geometry_hash_control import (GEOM, SOLID_ROOT, PLATFORM_PC, PLATFORM_PS2,
                                   MAX_REGION, parse_geometry_root, parse_solid,
                                   read_chunks)
from mesh_topology_control import (PC_MESH, PS2_STRIPS, parse_pc_mesh,
                                   parse_ps2_mesh, filler_size)
from rb_scenery_graph_census import read_rb
from track_bundle_probe import SplitZip
from visibility_stream_join import read_small

HEADER_ID = 0x00134011
TEXTURE_TABLE_ID = 0x00134012
PLATFORM_GROUP_ID = 0x80134100
MAX_SECTION_BYTES = 32 * 1024 * 1024


def parse_solid_texture_table(header, table):
    """Use source-validated eSolid header +0x19 count and 8-byte table rows.

    The 32-bit pointer slot is zero in the serialized source versions tested.
    Duplicated texture hash entries are preserved instead of being collapsed.
    """
    pad = filler_size(header)
    if pad + 26 > len(header) or struct.unpack_from('<I', header, pad+12)[0] not in (0x16, 0x800016):
        raise ValueError('Unsupported or truncated eSolid header')
    count = header[pad+25]
    if not 0 < count <= 127 or len(table) != 8*count:
        raise ValueError('Solid texture count/table byte length mismatch')
    rows = tuple(struct.iter_unpack('<II', table))
    if any(h == 0 or ptr != 0 for h,ptr in rows):
        raise ValueError('Zero texture hash or unexpected serialized table pointer')
    return tuple(h for h,_ in rows)


def pc_material_budget(platform, texture_count):
    """Candidate PC mesh +0x18 low-byte texture index, +0x60 triangle count."""
    validated = parse_pc_mesh(platform)
    mesh = next(b for cid,b in platform if cid == PC_MESH)
    pad = filler_size(mesh)
    if len(mesh) != pad + 144*validated['pc_mesh_records']:
        raise ValueError('Incorrect native mesh count')
    counts = Counter()
    anomalous_replicas = 0
    for i in range(validated['pc_mesh_records']):
        row = mesh[pad+144*i:pad+144*(i+1)]
        texture_index = row[0x18]
        if texture_index >= texture_count:
            raise ValueError('PC mesh references out-of-range texture table index')
        tris = struct.unpack_from('<I', row, 0x60)[0]
        counts[texture_index] += tris
        anomalous_replicas += struct.unpack_from('<I',row,0x18)[0] != texture_index * 0x01010101
    if validated['pc_triangle_indices'] % 3 or sum(counts.values()) != validated['pc_triangle_indices']//3:
        raise ValueError('PC material triangle budget differs from native index count')
    return {'per_texture':counts,
            'meshes':validated['pc_mesh_records'],
            'triangles':validated['pc_triangle_indices']//3,
            'unusual_packed_texture_words':anomalous_replicas}


def ps2_material_budget(platform, texture_count):
    """Candidate signed int8 texture number at PS2 strip descriptor +0x0E."""
    validated = parse_ps2_mesh(platform)
    entry = next(b for cid,b in platform if cid == PS2_STRIPS)
    if len(entry) != 4 + 16*validated['strip_entries']:
        raise ValueError('Unexpected PS2 strip descriptor array')
    budgets = Counter()
    groups = defaultdict(set)
    for i in range(validated['strip_entries']):
        row = struct.unpack_from('<HBBfHbbBBbb', entry, 4+16*i)
        npoly, group, texture_index = row[2], row[-3], row[-2]
        if not 0 <= texture_index < texture_count:
            raise ValueError('PS2 strip references out-of-range solid texture index')
        budgets[texture_index] += npoly
        groups[group].add(texture_index)
    if any(len(textures) != 1 for textures in groups.values()):
        raise ValueError('PS2 polygon group references multiple textures')
    return {'per_texture':budgets, 'strips':validated['strip_entries'],
            'triangles':sum(budgets.values()), 'polygon_groups':len(groups)}


def parse_solid_material(solid, expected_platform):
    parts = list(read_chunks(solid, 0, len(solid)))
    if [k for k,_ in parts] not in ([HEADER_ID,TEXTURE_TABLE_ID,PLATFORM_GROUP_ID],
                                      [HEADER_ID,TEXTURE_TABLE_ID,0x0013401A,PLATFORM_GROUP_ID]):
        raise ValueError('Unexpected solid header/texture/platform chunk order')
    model_hash, platform_id, _, _ = parse_solid(solid)
    if platform_id != expected_platform:
        raise ValueError('Source solid has wrong platform format')
    table = parse_solid_texture_table(parts[0][1], parts[1][1])
    platform = list(read_chunks(parts[-1][1], 0, len(parts[-1][1])))
    layout = (pc_material_budget(platform,len(table)) if expected_platform == PLATFORM_PC
              else ps2_material_budget(platform,len(table)))
    return model_hash, {'texture_table':table, **layout}


def source_materials(archive, stem, section_ids, platform):
    """Preserve repeated model hashes as separate occurrences, never overwrite."""
    scenes,_ = read_rb(archive, stem)
    rows,_,_ = read_small(archive, stem, 'RB')
    member = f'TRACKS/STREAM{stem}RB.BUN'
    if isinstance(archive,SplitZip):
        if archive.entries[member][4] > MAX_REGION:
            raise ValueError('RB stream exceeds safety limit')
        stream=archive.read(member,limit=MAX_REGION)
    else:
        with zipfile.ZipFile(archive) as z:
            if z.getinfo(member).file_size > MAX_REGION:
                raise ValueError('RB stream exceeds safety limit')
            stream=z.read(member)
    material_groups={}
    for section in section_ids:
        if section not in rows or section not in scenes:
            raise ValueError('Missing verified scene root or streaming section')
        offset,size=struct.unpack_from('<II',rows[section],0x14)
        if size>MAX_SECTION_BYTES or offset+size>len(stream):
            raise ValueError('Section outside allowed stream bounds')
        area=stream[offset:offset+size]
        found=[]
        cursor=0
        while True:
            at=area.find(struct.pack('<I',GEOM),cursor)
            if at<0:break
            cursor=at+4
            if at%4 or at+8>len(area):continue
            length=struct.unpack_from('<I',area,at+4)[0]
            if length>len(area)-at-8:continue
            root=area[at:at+8+length]
            try:
                index=parse_geometry_root(root)
            except ValueError:
                continue
            actual=set()
            for tag,solid in list(read_chunks(root,16,len(root)))[1:]:
                if tag != SOLID_ROOT:raise ValueError('Unexpected geometry child')
                h,profile=parse_solid_material(solid,platform)
                if h in actual:raise ValueError('Duplicate name hash in one geometry pack')
                actual.add(h)
                found.append((h,profile))
            if actual != index['hashes']:
                raise ValueError('Solid resource hash disagrees with geometry pack index')
            cursor=at+8+length
        if not found:
            raise ValueError('No source-validated solid material records')
        material_groups[section]=found
    return material_groups


def compare_carbon(pc_scenes, ps2_scenes):
    totals=Counter()
    mismatches=[]
    for sec in sorted(pc_scenes):
        if sec not in ps2_scenes:raise ValueError('Missing paired scene')
        left=pc_scenes[sec];right=ps2_scenes[sec]
        if len({h for h,_ in left})!=len(left) or len({h for h,_ in right})!=len(right):
            raise ValueError('Repeated model identity in paired Carbon control')
        pc={h:p for h,p in left};ps={h:p for h,p in right}
        if set(pc)!=set(ps):raise ValueError('PC/PS2 control index hash sets differ')
        for h in pc:
            a,b=pc[h],ps[h]
            if a['texture_table'] != b['texture_table']:
                raise ValueError('Same-hash Carbon PC/PS2 texture tables differ')
            if set(a['per_texture']) != set(b['per_texture']):
                raise ValueError('Same-hash Carbon PC/PS2 texture index sets differ')
            delta=a['triangles']-b['triangles']
            texture_delta={t:a['per_texture'][t]-b['per_texture'][t]
                           for t in a['per_texture']}
            if any(texture_delta.values()):
                mismatches.append(sorted(v for v in texture_delta.values() if v))
            totals['models_with_exact_texture_hash_table']+=1
            totals['models_with_equal_per_texture_triangle_budgets']+=not any(texture_delta.values())
            totals['pc_meshes']+=a['meshes']
            totals['ps2_strips']+=b['strips']
            totals['pc_triangles']+=a['triangles']
            totals['ps2_triangles']+=b['triangles']
            totals['pc_meshes_with_unusual_texture_word']+=a['unusual_packed_texture_words']
    return {**dict(totals), 'models_with_texture_count_mismatch':len(mismatches),
            'nonzero_per_texture_triangle_differences':sorted(v for row in mismatches for v in row)}


def summarize_undercover(scenes):
    totals=Counter()
    by_hash=defaultdict(set)
    for solid_occurrences in scenes.values():
        for namehash,profile in solid_occurrences:
            by_hash[namehash].add(profile['texture_table'])
            totals['solid_occurrences']+=1
            totals['texture_table_entry_occurrences']+=len(profile['texture_table'])
            totals['ps2_strips_with_valid_texture_numbers']+=profile['strips']
            totals['triangles']+=profile['triangles']
            totals['polygon_groups']+=profile['polygon_groups']
    return {**dict(totals), 'distinct_solid_hashes':len(by_hash),
            'model_hashes_with_more_than_one_texture_table':sum(len(tables)>1 for tables in by_hash.values())}


def analyze(pc_volumes,carbon_ps2_zip,undercover_ps2_zip):
    carbon_pc=source_materials(SplitZip(pc_volumes),'L5',(141,142),PLATFORM_PC)
    carbon_ps2=source_materials(Path(carbon_ps2_zip),'L5',(141,142),PLATFORM_PS2)
    uc_ps2=source_materials(Path(undercover_ps2_zip),'L2',(241,3401),PLATFORM_PS2)
    return {'carbon_pc_vs_ps2':compare_carbon(carbon_pc,carbon_ps2),
            'undercover_ps2':summarize_undercover(uc_ps2),
            'limitations':('Read-only texture table hashes and texture-index triangle budgets. '
                           'No per-face material bijection, texture pixel/resource availability, '
                           'UV sampler wrap mode, native PC writer or game runtime test.')}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--pc-volumes',nargs='+',type=Path,required=True)
    p.add_argument('--carbon-ps2-zip',type=Path,required=True)
    p.add_argument('--undercover-ps2-zip',type=Path,required=True)
    a=p.parse_args()
    print(json.dumps(analyze(a.pc_volumes,a.carbon_ps2_zip,a.undercover_ps2_zip),indent=2))

if __name__=='__main__':main()
