#!/usr/bin/env python3
"""V10: select and verify ONE source-backed Undercover scenery model offline.

The selected PS2 model must be referenced by a validated original scenery-info
record, occur once in the selected source section, and have EVERY entry of its
local material texture table backed by validated original RB image records.
The conversion and private DXT5 image candidate exist only in memory.
No owner game bytes, image identities, model hashes, coordinates or filenames
are printed, written, installed or published. Retail Carbon load is unproven.
"""
import argparse
from collections import Counter
import json
import struct
import zipfile


SOURCE_SECTIONS = (241, 3401)
MAX_TRIANGLES = 150_000


def rank_candidates(packs, image_ids, scene_refs, section,
                    min_triangles=4, max_triangles=2048, budget_fn=None):
    """Return private candidates, ordered by a predeclared score.

    Candidate dictionaries contain private identities. Never print them or
    include them in a JSON report. Counts contain no private identities.
    A local texture table is fully backed even if some entries are unused;
    this intentionally imposes a stronger requirement than face-only closure.
    """
    if type(section) is not int or section not in SOURCE_SECTIONS:
        raise ValueError('Unsupported Undercover source section')
    if (type(min_triangles) is not int or type(max_triangles) is not int or
            not 1 <= min_triangles <= max_triangles <= MAX_TRIANGLES):
        raise ValueError('Unsafe candidate triangle range')
    if (not isinstance(packs, (tuple, list)) or len(packs) != 4 or
            any(not isinstance(group, (tuple, list)) or not group for group in packs)):
        raise ValueError('Expected four original source geometry packs')
    if (not isinstance(image_ids, (set, frozenset)) or not image_ids or
            any(type(h) is not int or not 0 < h <= 0xffffffff for h in image_ids)):
        raise ValueError('Invalid original source image index')
    if (not isinstance(scene_refs, (tuple, list)) or not scene_refs or
            any(type(h) is not int or not 0 < h <= 0xffffffff for h in scene_refs)):
        raise ValueError('Invalid original scene references')
    if budget_fn is None:
        from texture_binding_control import ps2_material_budget
        budget_fn = ps2_material_budget

    occurrences = Counter()
    for group in packs:
        for entry in group:
            if not isinstance(entry, (tuple, list)) or len(entry) != 4:
                raise ValueError('Malformed original PS2 eSolid row')
            identity, header, table, platform = entry
            if (type(identity) is not int or not 0 < identity <= 0xffffffff or
                    not isinstance(header, bytes) or
                    not isinstance(table, (tuple, list)) or not 1 <= len(table) <= 127 or
                    any(type(h) is not int or not 0 < h <= 0xffffffff for h in table) or
                    not isinstance(platform, (tuple, list))):
                raise ValueError('Malformed original PS2 model or texture table')
            occurrences[identity] += 1

    references = Counter(scene_refs)
    counts = Counter()
    candidates = []
    for pack_ordinal, group in enumerate(packs):
        for model_ordinal, (identity, header, table, platform) in enumerate(group):
            counts['indexed_model_occurrences'] += 1
            if identity not in references:
                counts['not_primary_scenery_referenced'] += 1
                continue
            counts['primary_scenery_referenced'] += 1
            if occurrences[identity] != 1:
                counts['ambiguous_local_model_occurrences'] += 1
                continue
            if not set(table) <= image_ids:
                counts['unbacked_full_material_tables'] += 1
                continue
            counts['fully_image_backed_full_material_tables'] += 1
            budget = budget_fn(platform, len(table))
            if not isinstance(budget, dict) or not isinstance(budget.get('per_texture'), (dict, Counter)):
                raise ValueError('Invalid source PS2 strip material budget')
            material_counts = budget['per_texture']
            if (any(type(i) is not int or not 0 <= i < len(table) or
                    type(n) is not int or n < 0 for i, n in material_counts.items())):
                raise ValueError('Malformed source PS2 strip material index or budget')
            triangles = sum(material_counts.values())
            if (not 0 < triangles <= MAX_TRIANGLES or
                    type(budget.get('triangles')) is not int or
                    triangles != budget['triangles']):
                raise ValueError('Source PS2 strip triangle totals disagree')
            if not min_triangles <= triangles <= max_triangles:
                counts['outside_candidate_triangle_window'] += 1
                continue
            if not any(material_counts.values()):
                raise ValueError('No used material on selected source model')
            counts['eligible_candidate_models'] += 1
            candidates.append({
                'identity': identity, 'header': header, 'table': tuple(table),
                'platform': tuple(platform), 'section': section,
                'pack_ordinal': pack_ordinal, 'model_ordinal': model_ordinal,
                'triangles': triangles,
                'scene_reference_count': references[identity],
                'source_material_budget': dict(material_counts),
            })
    candidates.sort(key=lambda r: (
        r['triangles'], len(set(r['table'])), -r['scene_reference_count'],
        r['pack_ordinal'], r['model_ordinal']))
    counts['geometry_packs'] = len(packs)
    counts['source_scenery_info_references'] = len(scene_refs)
    return tuple(candidates), dict(counts)


def verify_single_model(candidate, source_section, mip_levels=4,
                        pc_header_profile='preserve_source'):
    """Convert ONE selected model and its complete texture table in memory.

    The original PS2 strip material triangle budget must equal the generated
    native PC mesh/material budget for every used local texture index.
    """
    if not isinstance(candidate, dict) or not all(k in candidate for k in (
            'identity', 'header', 'table', 'platform', 'section', 'pack_ordinal',
            'model_ordinal', 'triangles', 'source_material_budget',
            'scene_reference_count')):
        raise ValueError('No validated private model candidate selected')
    if type(source_section) is not bytes:
        raise ValueError('Original source section must be immutable bytes')
    if type(mip_levels) is not int or not 1 <= mip_levels <= 16:
        raise ValueError('Invalid candidate mip policy')
    from triangle_corner_uv_control import ps2_geometry_attributes
    from undercover_pc_geometry_bridge import convert_decoded_ps2_model
    from undercover_pc_dxt5_new_identity_candidate import build_private_dxt5_candidate
    from geometry_hash_control import (
        parse_geometry_root, parse_solid, read_chunks, PLATFORM_PC, SOLID_ROOT)
    from pc_native_vertex_control import inspect_pc_solid
    from texture_binding_control import parse_solid_texture_table
    from undercover_pc_material_image_binding_gate import (
        _native_mesh_material_triangle_budget)
    from texture_metadata_pixel_bridge import parse_pack
    from texture_pixel_base_alignment import aligned_pixel_array

    identity, table = candidate['identity'], candidate['table']
    xyz, uv, faces, labels = ps2_geometry_attributes(candidate['platform'])
    if (not faces or len(faces) != len(labels) or
            len(faces) != candidate['triangles'] or
            any(type(n) is not int or not 0 <= n < len(table) for n in labels)):
        raise ValueError('PS2 VIF material/face results contradict preselected strip budget')
    face_budget = Counter(labels)
    if dict(face_budget) != {i: n for i, n in candidate['source_material_budget'].items() if n}:
        raise ValueError('PS2 VIF face labels contradict source strip material budget')

    geometry, geo_report = convert_decoded_ps2_model(
        identity, table, xyz, uv, faces, labels, candidate['header'],
        pc_header_profile=pc_header_profile)
    root = parse_geometry_root(geometry)
    if (root['platform'] != PLATFORM_PC or root['solid_count'] != 1 or
            root['hashes'] != frozenset({identity})):
        raise ValueError('Selected PC geometry identity/index mismatch')
    solid_parts = list(read_chunks(geometry, 16, len(geometry)))
    solids = [body for tag, body in solid_parts if tag == SOLID_ROOT]
    if len(solids) != 1:
        raise ValueError('PC root must contain exactly one selected eSolid')
    solid = solids[0]
    if parse_solid(solid)[:2] != (identity, PLATFORM_PC):
        raise ValueError('PC eSolid header differs from original source identity')
    children = list(read_chunks(solid, 0, len(solid)))
    solid_table = parse_solid_texture_table(children[0][1], children[1][1])
    if solid_table != table:
        raise ValueError('PC eSolid texture-table order/hash changed')
    pc_platform = list(read_chunks(children[-1][1], 0, len(children[-1][1])))
    native = inspect_pc_solid(pc_platform)
    pc_budget = _native_mesh_material_triangle_budget(pc_platform, len(table), native)
    if dict(pc_budget) != dict(face_budget):
        raise ValueError('PC mesh material budgets differ from original PS2 strips')

    images, texture_report = build_private_dxt5_candidate(
        source_section, used_material_ids=set(table), mip_levels=mip_levels)
    records = parse_pack(images, 'pc')['records']
    aligned_pixel_array(images, records)
    if (set(records) != set(table) or
            not texture_report['complete_material_identity_coverage'] or
            texture_report['partial_ordinal_batch'] or
            any(meta['codec'] != 38 for meta in records.values())):
        raise ValueError('Incomplete or invalid selected PC DXT5 material image index')
    if (geo_report['pc_faces'] != candidate['triangles'] or
            geo_report['generated_pc_triangles'] != candidate['triangles'] or
            not geo_report['all_f32_xyz_uv_texture_corner_faces_preserved']):
        raise ValueError('Candidate native PC geometry face/UV readback incomplete')
    return {
        'scope': 'PRIVATE_OFFLINE_SINGLE_UNDERCOVER_MODEL_CANDIDATE_NOT_REGISTERED',
        'source_section': candidate['section'],
        'original_pack_ordinal_zero_based': candidate['pack_ordinal'],
        'original_model_ordinal_zero_based': candidate['model_ordinal'],
        'source_scene_info_references_to_selected_model': candidate['scene_reference_count'],
        'original_triangle_count': candidate['triangles'],
        'generated_pc_triangle_count': geo_report['pc_faces'],
        'local_material_table_entries': len(table),
        'distinct_required_image_identities': len(set(table)),
        'pc_dxt5_image_records': len(records),
        'pc_candidate_geometry_bytes_in_memory': len(geometry),
        'pc_candidate_texture_bytes_in_memory': len(images),
        'native_geometry_and_material_budget_passed': True,
        'pc_esolid_header_profile': pc_header_profile,
        'all_source_table_image_identities_backed': True,
        'source_model_hash_preserved_without_publication': True,
        'candidate_header_and_sampler_abi': 'UNVERIFIED',
        'native_scene_registration': 'UNVERIFIED',
        'game_rendering_verified': False,
        'safe_for_game_install': False,
        'game_files_written': False,
    }


def audit_original(path, section=241, mip_levels=4,
                   min_triangles=4, max_triangles=2048,
                   pc_header_profile='preserve_source'):
    """Original owner's CRC-verified RB source archive; no file writes."""
    from undercover_ra_texture_presence_gate import (
        _owner_archive, _fingerprint, _member_bytes, parse_stream_section_rows,
        MAX_SMALL_BUN, MAX_RB_STREAM)
    from undercover_pc_partition_registry_gate import (
        source_partition_roots, _source_scene_detail_hashes)
    from texture_metadata_pixel_bridge import parse_pack
    from texture_pixel_base_alignment import aligned_pixel_array

    if type(section) is not int or section not in SOURCE_SECTIONS:
        raise ValueError('Unsupported original source section')
    original = _owner_archive(path)
    before = _fingerprint(original)
    with zipfile.ZipFile(original) as archive:
        bun = _member_bytes(archive, 'TRACKS/L2RB.BUN', MAX_SMALL_BUN)
        stream = _member_bytes(archive, 'TRACKS/STREAML2RB.BUN', MAX_RB_STREAM)
    _, rows = parse_stream_section_rows(bun, len(stream))
    if section not in rows:
        raise ValueError('Missing expected original source RB section')
    first, last = rows[section]
    data = stream[first:last]
    records = parse_pack(data, 'ps2')['records']
    aligned_pixel_array(data, records)
    packs = source_partition_roots(data)
    refs = _source_scene_detail_hashes(data)
    ranked, stats = rank_candidates(
        packs, frozenset(records), refs, section,
        min_triangles=min_triangles, max_triangles=max_triangles)
    if not ranked:
        raise ValueError('No primary-scene model passes strict full-table image closure')
    result = verify_single_model(ranked[0], data, mip_levels,
                                 pc_header_profile=pc_header_profile)
    if _fingerprint(original) != before:
        raise ValueError('Original owner archive changed during read-only inspection')
    result.update({
        'candidate_scan': stats,
        'candidate_rank': 1,
        'source_zip_members_crc_verified': True,
        'original_archive_unchanged': True,
        'private_model_and_image_bytes_not_exported': True,
    })
    return result


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--undercover-ps2-tracks-zip', required=True)
    ap.add_argument('--source-section', type=int, choices=SOURCE_SECTIONS, default=241)
    ap.add_argument('--mip-levels', type=int, default=4)
    ap.add_argument('--min-triangles', type=int, default=4)
    ap.add_argument('--max-triangles', type=int, default=2048)
    ap.add_argument('--pc-header-profile', choices=('preserve_source','carbon_native_control'),
                    default='preserve_source')
    args = ap.parse_args()
    print(json.dumps(audit_original(args.undercover_ps2_tracks_zip,
        section=args.source_section, mip_levels=args.mip_levels,
        min_triangles=args.min_triangles, max_triangles=args.max_triangles,
        pc_header_profile=args.pc_header_profile), indent=2))


if __name__ == '__main__':
    main()
