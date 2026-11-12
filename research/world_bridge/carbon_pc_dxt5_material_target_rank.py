#!/usr/bin/env python3
"""Read-only Carbon PC DXT5 existing-slot material and scene-use ranking.

This is a *candidate visibility prioritizer*, NOT a visibility or rendering
proof. Original texture/model identity hashes and asset bytes stay private;
only section numbers, safe DXT5 ordinals and aggregate model/triangle/instance
counts are reported. No game-file writer or install logic is present.

Original section payloads are parsed using the separately regression-tested
texture/geometry/eSolid/scenery validators in this directory.
"""
import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import struct

from texture_metadata_pixel_bridge import parse_pack
from texture_pixel_base_alignment import aligned_pixel_array

MAX_PROFILES = 8192
MAX_SCENE_LINKS = 32768
MAX_TEXTURES = 32768
DXT5 = 38


def _u32(value, *, allow_zero=False):
    return type(value) is int and (0 <= value <= 0xffffffff if allow_zero else 0 < value <= 0xffffffff)


def validate_profiles(profiles):
    """Accept validated per-solid material evidence, preserving occurrences.

    Each entry is (model_identity, {texture_table, per_texture}), as returned
    by texture_binding_control.parse_solid_material / source_materials.
    We never interpret an out-of-section texture reference as missing globally.
    """
    if not isinstance(profiles, (tuple, list)) or not 0 < len(profiles) <= MAX_PROFILES:
        raise ValueError('Missing or excessive original PC solid occurrences')
    result = []
    for item in profiles:
        if not isinstance(item, (tuple, list)) or len(item) != 2:
            raise ValueError('Malformed model occurrence')
        model, info = item
        if not _u32(model) or not isinstance(info, dict):
            raise ValueError('Invalid model identity or material profile')
        table = info.get('texture_table')
        triangles = info.get('per_texture')
        if (not isinstance(table, (tuple, list)) or not 0 < len(table) <= 127 or
                any(not _u32(h) for h in table) or
                not hasattr(triangles, 'items') or not triangles):
            raise ValueError('Invalid original eSolid texture table or triangle budget')
        checked = {}
        for slot, count in triangles.items():
            if (type(slot) is not int or not 0 <= slot < len(table) or
                    type(count) is not int or not 0 < count <= 10000000):
                raise ValueError('Invalid PC mesh texture index/triangle budget')
            checked[slot] = count
        result.append((model, tuple(table), checked))
    return tuple(result)


def validate_links(links):
    """Each scenery instance is (primary LOD hash, unique candidate LOD hashes).

    A single scenery instance must not be counted repeatedly when several LOD
    hash slots contain the same value. Accept hash 0 for an unused LOD slot.
    """
    if not isinstance(links, (tuple, list)) or not 0 < len(links) <= MAX_SCENE_LINKS:
        raise ValueError('Missing or excessive instance-to-info links')
    out = []
    for row in links:
        if (not isinstance(row, (tuple, list)) or len(row) != 2 or
                not _u32(row[0]) or not isinstance(row[1], (tuple, list, set, frozenset)) or
                not 1 <= len(row[1]) <= 4 or any(not _u32(x, allow_zero=True) for x in row[1]) or
                row[0] not in row[1]):
            raise ValueError('Invalid candidate model LOD hashes for scenery instance')
        out.append((row[0], frozenset(x for x in row[1] if x)))
    return tuple(out)


def rank_material_targets(texture_records, material_profiles, scenery_links,
                          donor_records=None, *, section_id=142):
    """Rank Carbon PC DXT5 ordinals using validated material/scenery references.

    No original hashes leave the result; ordinal order is identical to the
    existing DXT5 donor-stage tool's sorted texture-hash enumeration.
    """
    if type(section_id) is not int or section_id not in (141, 142):
        raise ValueError('Unsupported Carbon secondary-area section')
    if not isinstance(texture_records, dict) or not 0 < len(texture_records) <= MAX_TEXTURES:
        raise ValueError('Missing bounded original Carbon PC texture index')
    for h, meta in texture_records.items():
        if (not _u32(h) or not isinstance(meta, dict) or
                type(meta.get('codec')) is not int or meta['codec'] not in (34, 36, 38) or
                type(meta.get('width')) is not int or type(meta.get('height')) is not int or
                meta['width'] <= 0 or meta['height'] <= 0 or
                type(meta.get('mip_levels')) is not int or not 1 <= meta['mip_levels'] <= 16):
            raise ValueError('Invalid native PC texture index record')
    profiles = validate_profiles(material_profiles)
    links = validate_links(scenery_links)
    donor_dimensions = defaultdict(list)
    if donor_records is not None:
        if not isinstance(donor_records, dict) or not 0 < len(donor_records) <= MAX_TEXTURES:
            raise ValueError('Malformed optional donor metadata')
        for donor_ordinal, (key, meta) in enumerate(sorted(donor_records.items())):
            if (not _u32(key) or not isinstance(meta, dict) or
                    meta.get('codec') not in (4, 8) or
                    type(meta.get('width')) is not int or type(meta.get('height')) is not int or
                    meta['width'] <= 0 or meta['height'] <= 0):
                raise ValueError('Invalid donor texture dimensions or indexed depth')
            donor_dimensions[(meta['width'], meta['height'])].append(donor_ordinal)
    used = defaultdict(lambda: {'models': set(), 'triangle_count': 0, 'solid_occurrences': 0})
    out_of_local_index = set()
    for model, table, triangles in profiles:
        for idx, tri in triangles.items():
            h = table[idx]
            if h not in texture_records:
                out_of_local_index.add(h)
                continue
            row = used[h]
            row['models'].add(model)
            row['triangle_count'] += tri
            row['solid_occurrences'] += 1
    targets = []
    for ordinal, (identity, meta) in enumerate(sorted(
            ((h, m) for h, m in texture_records.items() if m['codec'] == DXT5),
            key=lambda item: item[0])):
        row = used[identity]
        models = row['models']
        primaries = sum(primary in models for primary, candidates in links)
        any_lod = sum(bool(candidates & models) for primary, candidates in links)
        compatible_ordinals = donor_dimensions[(meta['width'], meta['height'])] if donor_records is not None else None
        count = len(compatible_ordinals) if compatible_ordinals is not None else None
        targets.append({'carbon_section': section_id,
                        'pc_dxt5_slot': ordinal,
                        'width': meta['width'], 'height': meta['height'],
                        'mip_levels': meta['mip_levels'],
                        'distinct_models': len(models),
                        'material_solid_occurrences': row['solid_occurrences'],
                        'material_triangles': row['triangle_count'],
                        'primary_lod_instance_refs': primaries,
                        'any_lod_instance_refs': any_lod,
                        'dimension_compatible_donor_count': count,
                        'dimension_compatible_donor_ordinals': compatible_ordinals})
    # A ranked candidate is NOT a visible texture; use dimensions to choose a
    # source donor and material/instance counts only as offline prioritization.
    targets.sort(key=lambda row: (
        -(row['primary_lod_instance_refs'] > 0),
        -row['primary_lod_instance_refs'],
        -row['distinct_models'],
        -row['material_triangles'],
        row['pc_dxt5_slot']))
    return {'section': section_id,
            'source_pc_texture_records': len(texture_records),
            'candidate_dxt5_slots': len(targets),
            'source_solid_occurrences': len(profiles),
            'source_scene_instances': len(links),
            'scene_backed_dxt5_slots': sum(x['primary_lod_instance_refs'] > 0 for x in targets),
            'material_backed_dxt5_slots': sum(x['material_triangles'] > 0 for x in targets),
            'solid_texture_hashes_outside_local_pc_index': len(out_of_local_index),
            'ranked_targets': targets,
            'verdict': 'STATIC_MATERIAL_AND_SCENERY_CANDIDATE_NOT_RUNTIME_VISIBILITY'}


def source_material_profiles(pc_section):
    """Reuse verified indexed-geometry and per-mesh PC material parsers."""
    from geometry_hash_control import (GEOM, SOLID_ROOT, PLATFORM_PC,
                                       parse_geometry_root, read_chunks)
    from texture_binding_control import parse_solid_material
    if not isinstance(pc_section, bytes) or len(pc_section) > 32 * 1024 * 1024:
        raise ValueError('Unsafe owner-supplied PC section')
    signature = struct.pack('<I', GEOM)
    profiles = []
    count = 0
    cursor = 0
    while True:
        at = pc_section.find(signature, cursor)
        if at < 0: break
        cursor = at + 4
        if at % 4 or at + 8 > len(pc_section): continue
        length = struct.unpack_from('<I', pc_section, at+4)[0]
        if length > len(pc_section)-at-8: continue
        root = pc_section[at:at+8+length]
        try:
            index = parse_geometry_root(root)
        except ValueError:
            continue
        if index['platform'] != PLATFORM_PC:
            raise ValueError('Mixed or unsupported source geometry platform')
        children = list(read_chunks(root, 16, len(root)))
        got = set()
        for tag, payload in children[1:]:
            if tag != SOLID_ROOT:
                raise ValueError('Unexpected validated geometry child')
            h, profile = parse_solid_material(payload, PLATFORM_PC)
            if h in got or h not in index['hashes']:
                raise ValueError('Unindexed or repeated geometry model identity')
            got.add(h)
            profiles.append((h, profile))
        if got != index['hashes']:
            raise ValueError('Geometry pack model index mismatch')
        count += 1
        if count > 16:
            raise ValueError('Too many geometry packs')
        cursor = at + 8 + length
    if not count:
        raise ValueError('No indexed PC geometry in selected texture section')
    return profiles


def source_scenery_links(pc_section):
    """Reuse full scenery graph, instance-index and info-row validators."""
    from z0_tree_graph_probe import scene_children, inspect_scene, MAX_Z0_FRAME
    from scenery_model_hash_bridge import parse_info_records, validate_instance_links
    signature = struct.pack('<I', 0x80034100)
    found = []
    cursor = 0
    while True:
        at = pc_section.find(signature, cursor)
        if at < 0: break
        cursor = at + 4
        if at % 4: continue
        try:
            block = pc_section[at:at + MAX_Z0_FRAME + 8]
            children, length = scene_children(block)
            inspect_scene(block[:length])
        except ValueError:
            continue
        found.append(children)
        if len(found) > 1:
            raise ValueError('Ambiguous local original scenery roots')
        cursor = at + length
    if len(found) != 1:
        raise ValueError('Missing exactly one validated local scenery root')
    c = found[0]
    rows = parse_info_records(c[0x34102])
    indices = validate_instance_links(c[0x34103], c[0x34102])
    links = []
    for i in indices:
        if type(i) is not int or not 0 <= i < len(rows):
            raise ValueError('Scenery instance info index outside validated records')
        slots = struct.unpack_from('<4I', rows[i], 0x18)
        if not slots[0]:
            raise ValueError('Original PC scenery lacks primary model identity')
        links.append((slots[0], tuple(slots)))
    return links


def analyze_extracted_sources(carbon_bun, carbon_stream, *, sections=(141, 142),
                              undercover_ps2_zip=None, undercover_section=241):
    """Read owner's loose original Carbon data, without writing any game bytes."""
    from private_carbon_dxt1_stream_stage import section_span
    from private_undercover_dxt5_archive_audit import _private_uc_section
    for path in (carbon_bun, carbon_stream):
        p = Path(path).absolute()
        if any(s.is_symlink() for s in (p, *p.parents)) or not p.is_file():
            raise ValueError('Missing owner source file or forbidden symlink')
    bun = Path(carbon_bun).read_bytes()
    stream_path = Path(carbon_stream)
    if len(bun) > 8 * 1024 * 1024 or not 0 < stream_path.stat().st_size <= 2 * 1024 * 1024 * 1024:
        raise ValueError('Source bundle or stream exceeds explicit bound')
    if not sections or len(set(sections)) != len(sections) or any(x not in (141, 142) for x in sections):
        raise ValueError('Invalid Carbon section selection')
    donors = None
    if undercover_ps2_zip is not None:
        if undercover_section not in (241, 3401):
            raise ValueError('Unsupported donor section')
        uc = _private_uc_section(undercover_ps2_zip, undercover_section)
        donors = parse_pack(uc, 'ps2')['records']
        aligned_pixel_array(uc, donors)
    reports = []
    with stream_path.open('rb') as handle:
        for sec in sections:
            off, size = section_span(bun, stream_path.stat().st_size, sec)
            handle.seek(off)
            block = handle.read(size)
            if len(block) != size:
                raise ValueError('Short original section read')
            pc = parse_pack(block, 'pc')['records']
            aligned_pixel_array(block, pc)
            profiles = source_material_profiles(block)
            links = source_scenery_links(block)
            reports.append(rank_material_targets(pc, profiles, links, donors, section_id=sec))
    return {'donor_section': undercover_section if donors is not None else None,
            'sections': reports,
            'no_source_assets_published': True,
            'runtime_rendering_verified': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--carbon-bun', type=Path, required=True)
    parser.add_argument('--carbon-stream', type=Path, required=True)
    parser.add_argument('--undercover-ps2-zip', type=Path)
    parser.add_argument('--undercover-section', type=int, choices=(241, 3401), default=241)
    parser.add_argument('--section', type=int, action='append', choices=(141, 142))
    parser.add_argument('--top', type=int, default=8)
    args = parser.parse_args()
    if not 1 <= args.top <= 34:
        parser.error('--top must be between 1 and 34')
    result = analyze_extracted_sources(args.carbon_bun, args.carbon_stream,
        sections=tuple(args.section) if args.section is not None else (141, 142),
        undercover_ps2_zip=args.undercover_ps2_zip,
        undercover_section=args.undercover_section)
    for item in result['sections']:
        item['ranked_targets'] = item['ranked_targets'][:args.top]
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
