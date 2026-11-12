#!/usr/bin/env python3
"""Read-only Undercover PC-shaped geometry -> candidate PC DXT5 image binding gate.

This is an offline identity join. It establishes that source-derived PC-shaped
mesh material slots point to records in a separate, parser-valid PC-shaped
texture candidate. It NEVER registers those identities with Carbon's engine,
installs a game file, invents missing image records, or proves rendering.

Original texture/model hashes, source names, proprietary geometry/pixels and
local file paths remain private. JSON reports expose only aggregate counts.
"""
import argparse
from collections import Counter
import json
import struct
import zipfile

from geometry_hash_control import (PLATFORM_PC, SOLID_ROOT,
    parse_geometry_root, parse_solid, read_chunks)
from pc_native_vertex_control import inspect_pc_solid
from texture_binding_control import parse_solid_texture_table
from texture_metadata_pixel_bridge import parse_pack
from texture_pixel_base_alignment import aligned_pixel_array
from undercover_pc_geometry_bridge import convert_decoded_ps2_model, _hash
from undercover_pc_partition_registry_gate import (
    source_partition_roots, merge_pc_pack_candidates)
from undercover_pc_dxt5_new_identity_candidate import (
    build_private_dxt5_candidate, audit_registration_coverage)
from undercover_ra_texture_presence_gate import (
    _owner_archive, _fingerprint, _member_bytes, parse_stream_section_rows,
    MAX_SMALL_BUN, MAX_RB_STREAM)
from triangle_corner_uv_control import ps2_geometry_attributes

SECTIONS = (241, 3401)
MAX_PACKS_PER_SECTION = 4
MAX_PC_PACK = 32 * 1024 * 1024


def _private_identity_set(ids):
    if (not isinstance(ids, (set, frozenset)) or not ids or
            any(type(x) is not int or not 0 < x <= 0xffffffff for x in ids)):
        raise ValueError('Invalid private source image identity set')
    return set(ids)



def _native_mesh_material_triangle_budget(platform_chunks, texture_count, native):
    """Independent 144-byte PC mesh row budget; full PC reader runs first.

    Do not infer a local texture hash from material-name strings. The exact
    0x18 4-byte index word and 0x60/0x64/0x7c triangle ranges must agree.
    """
    meshes = [b for cid, b in platform_chunks if cid == 0x00134b02]
    if (len(meshes) != 1 or not 0 < texture_count <= 127 or
            type(native.get('mesh_records')) is not int):
        raise ValueError('Missing validated native PC mesh rows')
    blob = meshes[0]
    count = native['mesh_records']
    if blob[:4] != b'\x11'*4 or len(blob) != 4+144*count:
        raise ValueError('PC mesh record stride/prefix inconsistent with native reader')
    budget = Counter()
    expected_index = 0
    for i in range(count):
        row = blob[4+144*i:4+144*(i+1)]
        packed_material = struct.unpack_from('<I', row, 0x18)[0]
        local_index = packed_material & 0xff
        if (packed_material != local_index*0x01010101 or
                local_index >= texture_count):
            raise ValueError('PC material index is invalid or inconsistently replicated')
        triangles, begin = struct.unpack_from('<II', row, 0x60)
        # +0x60 triangle count, +0x64 index first, +0x7c index length.
        length = struct.unpack_from('<I', row, 0x7c)[0]
        if not triangles or begin != expected_index or length != triangles*3:
            raise ValueError('PC material mesh triangle/index record is inconsistent')
        expected_index += length
        budget[local_index] += triangles
    if expected_index != 3*native['triangle_count'] or sum(budget.values()) != native['triangle_count']:
        raise ValueError('Native PC triangle/material budget mismatch')
    return budget


def audit_candidate_material_bindings(geometry_packs, pc_dxt5_root,
                                      original_source_image_ids=None,
                                      require_complete=False):
    """Validate eight PC geometry packs against one PC DXT5 identity index.

    geometry_packs is a PRIVATE mapping of section => four complete PC-shaped
    geometry pack bytes. Original source IDs can independently bind provenance
    by requiring exact set equality with the generated PC candidate index.
    No private identity, model name or material index is returned.
    """
    if (type(require_complete) is not bool or not isinstance(geometry_packs, dict) or
            set(geometry_packs) != set(SECTIONS)):
        raise ValueError('Expected source section keys and a boolean strictness flag')
    if type(pc_dxt5_root) is not bytes or not 40 <= len(pc_dxt5_root) <= MAX_PC_PACK:
        raise ValueError('Invalid private PC DXT5 candidate root')
    images = parse_pack(pc_dxt5_root, 'pc')['records']
    aligned_pixel_array(pc_dxt5_root, images)
    if not images or any(rec['codec'] != 38 for rec in images.values()):
        raise ValueError('Candidate contains non-DXT5 or no images')
    available = set(images)
    if original_source_image_ids is not None:
        source = _private_identity_set(original_source_image_ids)
        if source != available:
            raise ValueError('PC image identities do not exactly match private original source index')
    totals = Counter()
    used = set()
    unavailable = set()
    model_occurrences = Counter()
    per_section = {}
    for section in SECTIONS:
        roots = geometry_packs[section]
        if (not isinstance(roots, (list, tuple)) or
                len(roots) != MAX_PACKS_PER_SECTION):
            raise ValueError('Must preserve four independent PC geometry packs per source section')
        section_stats = Counter()
        pack_counts = []
        for root in roots:
            if type(root) is not bytes or not 24 <= len(root) <= MAX_PC_PACK:
                raise ValueError('Invalid private PC geometry pack bytes')
            envelope = parse_geometry_root(root)
            if envelope['platform'] != PLATFORM_PC or not envelope['solid_count']:
                raise ValueError('Expected a nonempty PC geometry pack')
            children = list(read_chunks(root, 16, len(root)))
            if len(children)-1 != envelope['solid_count']:
                raise ValueError('Geometry index does not cover eSolids')
            pack_stats = Counter()
            for kind, solid in children[1:]:
                if kind != SOLID_ROOT:
                    raise ValueError('Unexpected PC geometry resource child')
                identity, platform, _, _ = parse_solid(solid)
                if platform != PLATFORM_PC or identity not in envelope['hashes']:
                    raise ValueError('PC geometry model identity failed source index validation')
                model_occurrences[identity] += 1
                fields = list(read_chunks(solid, 0, len(solid)))
                if len(fields) not in (3, 4):
                    raise ValueError('Unexpected PC eSolid child structure')
                header = fields[0][1]
                tex_table = fields[1][1]
                table = parse_solid_texture_table(header, tex_table)
                platform_chunks = list(read_chunks(fields[-1][1], 0, len(fields[-1][1])))
                native = inspect_pc_solid(platform_chunks)
                budget = _native_mesh_material_triangle_budget(platform_chunks, len(table), native)
                pack_stats['model_occurrences'] += 1
                for local_index, tris in budget.items():
                    if type(local_index) is not int or not 0 <= local_index < len(table) or tris <= 0:
                        raise ValueError('Invalid used PC mesh material index/triangle count')
                    image_identity = table[local_index]
                    used.add(image_identity)
                    pack_stats['material_meshes'] += 1
                    pack_stats['triangles'] += tris
                    if image_identity in available:
                        pack_stats['source_index_backed_material_meshes'] += 1
                        pack_stats['source_index_backed_triangles'] += tris
                    else:
                        unavailable.add(image_identity)
                        pack_stats['unresolved_material_meshes'] += 1
                        pack_stats['unresolved_triangles'] += tris
            if pack_stats['model_occurrences'] != envelope['solid_count']:
                raise ValueError('PC pack material accounting lost a model')
            if pack_stats['source_index_backed_triangles'] + pack_stats['unresolved_triangles'] != pack_stats['triangles']:
                raise ValueError('Image binding triangle accounting is incomplete')
            pack_counts.append({
                'material_image_identity_binding_complete': not pack_stats['unresolved_triangles'],
                'model_occurrences': pack_stats['model_occurrences'],
                'material_meshes': pack_stats['material_meshes'],
                'triangles': pack_stats['triangles'],
                'source_index_backed_triangles': pack_stats['source_index_backed_triangles'],
                'unresolved_triangles': pack_stats['unresolved_triangles'],
            })
            section_stats.update(pack_stats)
        if section_stats['source_index_backed_triangles'] + section_stats['unresolved_triangles'] != section_stats['triangles']:
            raise ValueError('Section material-to-image accounting mismatch')
        per_section[str(section)] = {
            'source_geometry_pack_count': len(roots),
            'fully_image_bound_geometry_packs': sum(k['material_image_identity_binding_complete'] for k in pack_counts),
            'triangles_in_fully_image_bound_packs': sum(k['triangles'] for k in pack_counts if k['material_image_identity_binding_complete']),
            'per_pack': pack_counts,
            'model_occurrences': section_stats['model_occurrences'],
            'material_meshes': section_stats['material_meshes'],
            'triangles': section_stats['triangles'],
            'triangles_with_candidate_dxt5_identity': section_stats['source_index_backed_triangles'],
            'triangles_without_candidate_dxt5_identity': section_stats['unresolved_triangles'],
            'material_meshes_without_candidate_dxt5_identity': section_stats['unresolved_material_meshes'],
        }
        totals.update(section_stats)
    if not totals['triangles'] or not used:
        raise ValueError('No source-derived PC geometry triangles audited')
    complete_pack_counts = [part for section in per_section.values() for part in section['per_pack']
                            if part['material_image_identity_binding_complete']]
    resolved = used & available
    if not unavailable == used - available:
        raise ValueError('Candidate material identity classification is inconsistent')
    complete = not unavailable
    if require_complete and not complete:
        raise ValueError('Unresolved source material image identities: complete PC registration refused')
    return {
        'scope': 'OFFLINE_PC_SHAPED_IDENTITY_BINDING_NOT_RETAIL_ENGINE_REGISTRATION',
        'pc_candidate_dxt5_image_identity_count': len(available),
        'candidate_ids_exactly_equal_to_validated_source_image_ids': original_source_image_ids is not None,
        'source_sections': [241, 3401],
        'pc_geometry_pack_count': 8,
        'fully_image_bound_geometry_pack_count': len(complete_pack_counts),
        'triangles_in_fully_image_bound_geometry_packs': sum(k['triangles'] for k in complete_pack_counts),
        'triangles_in_partially_bound_geometry_packs': (
            totals['triangles']-sum(k['triangles'] for k in complete_pack_counts)),
        'pc_model_occurrences': totals['model_occurrences'],
        'distinct_pc_model_identities': len(model_occurrences),
        'repeated_model_identities_across_source_packs_or_sections': sum(v > 1 for v in model_occurrences.values()),
        'pc_material_meshes': totals['material_meshes'],
        'pc_total_triangles': totals['triangles'],
        'pc_triangles_with_candidate_dxt5_identity': totals['source_index_backed_triangles'],
        'pc_triangles_without_candidate_dxt5_identity': totals['unresolved_triangles'],
        'pc_material_meshes_with_candidate_dxt5_identity': totals['source_index_backed_material_meshes'],
        'pc_material_meshes_without_candidate_dxt5_identity': totals['unresolved_material_meshes'],
        'source_material_identities_used': len(used),
        'source_material_identities_with_candidate_image': len(resolved),
        'source_material_identities_without_candidate_image': len(unavailable),
        'offline_material_image_identity_coverage_complete': complete,
        'all_pc_mesh_ranges_and_local_material_indexes_validated': True,
        'no_missing_textures_fabricated': True,
        'safe_for_game_install': False,
        'engine_registration': 'UNVERIFIED',
        'per_source_section': per_section,
    }


def _convert_owner_geometry_section(source_packs):
    """Private owner-memory PS2 → four candidate PC packs, no disk writes."""
    if not isinstance(source_packs, (list, tuple)) or len(source_packs) != 4:
        raise ValueError('Original Undercover source does not have four geometry packs')
    roots = []
    used = set()
    source_faces = 0
    for original_pack in source_packs:
        models = []
        for identity, header, table, platform in original_pack:
            xyz, uv, faces, labels = ps2_geometry_attributes(platform)
            if not faces or len(labels) != len(faces):
                raise ValueError('Original PS2 material-face decode is incomplete')
            if any(type(k) is not int or not 0 <= k < len(table) for k in labels):
                raise ValueError('Original source face has invalid material index')
            used.update(table[k] for k in set(labels))
            root, info = convert_decoded_ps2_model(identity, table, xyz, uv, faces, labels, header)
            if info['source_triangles'] != len(faces):
                raise ValueError('Original PS2 face count lost during conversion')
            source_faces += len(faces)
            models.append(root)
        combined, status = merge_pc_pack_candidates(models)
        if status['pc_pack_solid_occurrences'] != len(original_pack):
            raise ValueError('Merged candidate eSolid count differs from original')
        roots.append(combined)
    return tuple(roots), used, source_faces


def audit_private_owner_archive(path, require_complete=False):
    """Read-only, complete original archive audit with no source identifiers in output."""
    if type(require_complete) is not bool:
        raise ValueError('Invalid complete coverage flag')
    original = _owner_archive(path)
    snapshot = _fingerprint(original)
    with zipfile.ZipFile(original) as zipf:
        bun = _member_bytes(zipf, 'TRACKS/L2RB.BUN', MAX_SMALL_BUN)
        stream = _member_bytes(zipf, 'TRACKS/STREAML2RB.BUN', MAX_RB_STREAM)
    _, rows = parse_stream_section_rows(bun, len(stream))
    if not set(SECTIONS) <= set(rows):
        raise ValueError('Original RB source section table is incomplete')
    sources = {sec: stream[slice(*rows[sec])] for sec in SECTIONS}
    source_packs = {sec: source_partition_roots(sources[sec]) for sec in SECTIONS}
    pc_packs = {}
    used = set()
    total_source_faces = 0
    for sec in SECTIONS:
        pc_packs[sec], local_used, nfaces = _convert_owner_geometry_section(source_packs[sec])
        total_source_faces += nfaces
        used.update(local_used)
    donor_images = {sec: set(parse_pack(sources[sec], 'ps2')['records']) for sec in SECTIONS}
    source_images = donor_images[241] | donor_images[3401]
    if not source_images or not source_images <= used:
        raise ValueError('Original indexed donor images do not match used material records')
    blob, candidate = build_private_dxt5_candidate(sources[3401], used_material_ids=used,
                                                     mip_levels=4)
    report = audit_candidate_material_bindings(pc_packs, blob, source_images,
                                               require_complete=require_complete)
    if (report['pc_total_triangles'] != total_source_faces or
            report['pc_candidate_dxt5_image_identity_count'] != candidate['pc_candidate_texture_identities'] or
            report['source_material_identities_used'] != len(used)):
        raise ValueError('Owner original source-to-candidate counts disagree')
    coverage = audit_registration_coverage(used, sources)
    if (coverage['used_identities_with_source_images'] !=
            report['source_material_identities_with_candidate_image'] or
            coverage['used_identities_without_source_images'] !=
            report['source_material_identities_without_candidate_image']):
        raise ValueError('Independent source material-to-image index coverage disagrees')
    if _fingerprint(original) != snapshot:
        raise ValueError('Original owner archive changed during private audit')
    return {'geometry_to_image_binding': report,
            'original_source_image_coverage': coverage,
            'pc_candidate_texture_section_bytes': len(blob),
            'original_source_archive_sha256_unchanged': True,
            'original_rb_members_zip_crc_verified': True,
            'no_install_or_game_file_output': True,
            'source_converted_geometry_is_parser_valid_only': True,
            'missing_source_texture_ids_not_included_in_output': True}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--undercover-ps2-tracks-zip', required=True)
    ap.add_argument('--require-complete', action='store_true',
                    help='Refuse to label candidate complete while any used material lacks image bytes')
    args = ap.parse_args()
    result = audit_private_owner_archive(args.undercover_ps2_tracks_zip,
                                          require_complete=args.require_complete)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
