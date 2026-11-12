#!/usr/bin/env python3
"""Source-only code for private Carbon PC scenery coordinate scout.

Source-scene AABB coordinates are experimental *object-location cues*, not
verified road positions, navigable waypoints, camera poses or engine units.
No owner original coordinate or identity is emitted to stdout. An explicitly
requested CSV is private user data and MUST NOT be committed or distributed.
"""
import argparse
import csv
import io
import json
import math
import os
from pathlib import Path
import struct

from carbon_pc_dxt5_spatial_smoke_target import (
    _clusters, instance_bounds, validate_tree_bounds, spatial_slot_profile,
)

MAX_RECORDS = 1024
CSV_FIELDS = (
    'source_section','dxt5_slot','experimental_group',
    'source_instance_ordinal','group_size',
    *(f'group_center_{a}' for a in 'xyz'),
    *(f'group_min_{a}' for a in 'xyz'),
    *(f'group_max_{a}' for a in 'xyz'),
    *(f'instance_min_{a}' for a in 'xyz'),
    *(f'instance_max_{a}' for a in 'xyz'),
)


def scout_components(texture_records, material_profiles, primary_model_hashes,
                     instance_bytes, tree_bytes, *, section=142, slot=16,
                     cluster_distance=12.0):
    """Return a public aggregate and caller-private CSV rows, without file I/O."""
    public = spatial_slot_profile(
        texture_records, material_profiles, primary_model_hashes,
        instance_bytes, tree_bytes, section=section, slot=slot,
        cluster_distance=cluster_distance,
    )
    boxes = instance_bounds(instance_bytes)
    validate_tree_bounds(tree_bytes, boxes)
    targets = sorted(h for h, meta in texture_records.items() if meta.get('codec') == 38)
    chosen_hash = targets[slot]
    models = set()
    for model, record in material_profiles:
        table, by_index = record['texture_table'], record['per_texture']
        if any(table[index] == chosen_hash and count > 0
               for index, count in by_index.items()):
            models.add(model)
    chosen = [(i, box) for i, (model, box) in enumerate(zip(primary_model_hashes, boxes))
              if model in models]
    if not chosen or len(chosen) > MAX_RECORDS or len(chosen) != public['source_primary_scenery_instances']:
        raise ValueError('Candidate scene-to-geometry counts disagree')
    centers = [tuple((lo[a] + hi[a])/2 for a in range(3)) for _, (lo, hi) in chosen]
    clusters = _clusters(centers, cluster_distance)
    # Order stable under input permutation of the instance rows: centroid lexicographic.
    ranked = []
    for group in clusters:
        c = tuple(sum(centers[j][axis] for j in group)/len(group) for axis in range(3))
        ranked.append((c, group))
    ranked.sort(key=lambda x: x[0])
    rows = []
    for group_number, (center, group) in enumerate(ranked, 1):
        subset = [chosen[j] for j in group]
        low = tuple(min(b[0][a] for _, b in subset) for a in range(3))
        high = tuple(max(b[1][a] for _, b in subset) for a in range(3))
        for orig_index, box in sorted(subset):
            lo, hi = box
            rows.append({
                'source_section': section, 'dxt5_slot': slot,
                'experimental_group': group_number,
                'source_instance_ordinal': orig_index,
                'group_size': len(group),
                **{f'group_center_{ax}': center[a] for a, ax in enumerate('xyz')},
                **{f'group_min_{ax}': low[a] for a, ax in enumerate('xyz')},
                **{f'group_max_{ax}': high[a] for a, ax in enumerate('xyz')},
                **{f'instance_min_{ax}': lo[a] for a, ax in enumerate('xyz')},
                **{f'instance_max_{ax}': hi[a] for a, ax in enumerate('xyz')},
            })
    if len(rows) != len(chosen):
        raise ValueError('Private scout must include each matching instance exactly once')
    return public, tuple(rows)


def scout_original_pc_section(raw_section, *, section=142, slot=16,
                              cluster_distance=12.0):
    """Parse original in-memory Carbon scene through prior validated controls."""
    if not isinstance(raw_section, bytes) or not 40 <= len(raw_section) <= 32*1024*1024:
        raise ValueError('Unsafe original Carbon section bytes')
    from texture_metadata_pixel_bridge import parse_pack
    from texture_pixel_base_alignment import aligned_pixel_array
    from carbon_pc_dxt5_material_target_rank import source_material_profiles
    from z0_tree_graph_probe import scene_children, inspect_scene, MAX_Z0_FRAME
    from scenery_model_hash_bridge import parse_info_records, validate_instance_links
    records = parse_pack(raw_section, 'pc')['records']
    aligned_pixel_array(raw_section, records)
    profiles = source_material_profiles(raw_section)
    marker = struct.pack('<I', 0x80034100)
    found=[]; pos=0
    while True:
        pos = raw_section.find(marker,pos)
        if pos < 0: break
        at=pos;pos+=4
        if at%4:continue
        try:
            chunk=raw_section[at:at+MAX_Z0_FRAME+8]
            children,n=scene_children(chunk)
            inspect_scene(chunk[:n])
        except ValueError:
            continue
        found.append(children)
        if len(found)>1:raise ValueError('Multiple original scene roots')
        pos=at+n
    if len(found)!=1:raise ValueError('Missing validated original Carbon scene root')
    scene=found[0]
    infos=parse_info_records(scene[0x34102])
    refs=validate_instance_links(scene[0x34103], scene[0x34102])
    primary=tuple(struct.unpack_from('<I',infos[index],0x18)[0] for index in refs)
    return scout_components(records,profiles,primary,scene[0x34103],scene[0x34105],
                            section=section,slot=slot,cluster_distance=cluster_distance)


def _safe_export_destination(dst, sources=()):
    """Private CSV must be a brand-new regular file outside TRACKS/game/repo areas."""
    path=Path(dst).absolute()
    forbidden={'tracks','.github','research','world_bridge','need for speed carbon'}
    if (not path.name.startswith('PRIVATE_') or path.suffix.lower() != '.csv'
            or any(part.casefold() in forbidden for part in path.parts)
            or any(part.is_symlink() for part in (path,*path.parents))
            or not path.parent.is_dir() or path.exists()):
        raise ValueError('Unsafe private export location or filename')
    for source in sources:
        s=Path(source).absolute()
        if path==s or path in s.parents or s in path.parents:
            raise ValueError('Private export aliases or contains a source path')
    return path


def export_private_csv(destination, rows, *, sources=()):
    """Exclusive create, mode 0600; a caller-requested confidential coordinate CSV."""
    if not isinstance(rows,(tuple,list)) or not 1<=len(rows)<=MAX_RECORDS:
        raise ValueError('Unsafe or empty private scout rows')
    path=_safe_export_destination(destination,sources)
    fields=CSV_FIELDS
    if any(tuple(row)!=fields for row in rows):
        raise ValueError('Invalid scout CSV schema')
    ordinals=[row['source_instance_ordinal'] for row in rows]
    if (any(type(x) is not int or x < 0 for x in ordinals) or
            len(set(ordinals)) != len(ordinals)):
        raise ValueError('Duplicate or invalid source instance ordinal')
    out=io.StringIO(newline='')
    writer=csv.DictWriter(out,fieldnames=fields,lineterminator='\n')
    writer.writeheader()
    for row in rows:
        if any(not isinstance(v,(int,float)) or not math.isfinite(v) for v in row.values()):
            raise ValueError('Nonfinite scout coordinate or ordinal')
        writer.writerow(row)
    data=out.getvalue().encode('utf-8')
    if len(data)>2*1024*1024:raise ValueError('Oversized scout CSV')
    flags=os.O_WRONLY|os.O_CREAT|os.O_EXCL
    if hasattr(os,'O_NOFOLLOW'):flags|=os.O_NOFOLLOW
    fd=os.open(path,flags,0o600)
    try:
        with os.fdopen(fd,'wb') as f:
            f.write(data);f.flush();os.fsync(f.fileno())
    except BaseException:
        try:os.unlink(path)
        except OSError:pass
        raise
    return {'private_csv_created':True,'private_instance_rows':len(rows),
            'source_positions_printed':False}


def analyze_original_files(bun,stream,*,section=142,slot=16,cluster_distance=12.0,
                           private_csv=None):
    bun=Path(bun).absolute();stream=Path(stream).absolute()
    if (bun==stream or any(p.is_symlink() for p in (bun,stream,*bun.parents,*stream.parents))
            or not bun.is_file() or not stream.is_file() or not 0<bun.stat().st_size<=8*1024*1024
            or not 0<stream.stat().st_size<=2*1024*1024*1024):
        raise ValueError('Unsafe original Carbon input paths')
    from private_carbon_dxt1_stream_stage import section_span
    bundle=bun.read_bytes()
    at,length=section_span(bundle,stream.stat().st_size,section)
    with stream.open('rb') as f:
        f.seek(at);section_bytes=f.read(length)
    if len(section_bytes)!=length:raise ValueError('Short original Carbon section')
    public, rows=scout_original_pc_section(section_bytes,section=section,slot=slot,
                                          cluster_distance=cluster_distance)
    result={**public,'private_csv_created':False,
            'camera_or_road_waypoint_verified':False}
    if private_csv is not None:
        result.update(export_private_csv(private_csv,rows,sources=(bun,stream)))
    return result


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--carbon-bun',type=Path,required=True)
    ap.add_argument('--carbon-stream',type=Path,required=True)
    ap.add_argument('--section',type=int,choices=(141,142),default=142)
    ap.add_argument('--slot',type=int,default=16)
    ap.add_argument('--cluster-distance',type=float,default=12.0)
    ap.add_argument('--private-csv',type=Path,help='Opt-in private coordinate export; use PRIVATE_*.csv outside any game/repository folder')
    a=ap.parse_args()
    print(json.dumps(analyze_original_files(a.carbon_bun,a.carbon_stream,section=a.section,
                                           slot=a.slot,cluster_distance=a.cluster_distance,
                                           private_csv=a.private_csv),indent=2))

if __name__=='__main__':main()
