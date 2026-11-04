#!/usr/bin/env python3
"""Read-only four-pack Undercover PS2 -> PC-shaped geometry registry preflight.

Preserves original geometry-pack boundaries, model occurrence order, local
material/texture index tables and duplicate model identities across packs.
The resulting geometry roots exist ONLY in RAM. Game loader registration,
texture registration, scene registration, collisions and rendering are UNSOLVED.
Original source bytes, raw hashes and model identifiers never enter reports.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import struct
import zipfile

from undercover_pc_geometry_bridge import (
    _chunk, _hash, convert_decoded_ps2_model, GEOM_ROOT, GEOM_HEADER,
    GEOM_HEADER_DATA, GEOM_INDEX, GEOM_EMPTY, SOLID_ROOT,
    SOLID_HEADER, SOLID_TEXTURE_TABLE, SOLID_PLATFORM, MAX_OUTPUT, MAX_ZIP)

MAX_PACKS = 16
MAX_MODELS = 8192
MAX_STREAM = 128 * 1024 * 1024
MAX_PC_ARCHIVE = 1024 * 1024 * 1024
MAX_SECTION_BYTES = 32 * 1024 * 1024


def source_partition_roots(section_bytes):
    """Return original source geometry packs in original stream/solid order.

    In-memory results contain original proprietary data. They must not be
    serialized, logged, committed or included in a source-only artifact.
    """
    from geometry_hash_control import (
        GEOM, SOLID_ROOT as SRC_SOLID, PLATFORM_PS2,
        parse_geometry_root, parse_solid, read_chunks)
    from texture_binding_control import parse_solid_texture_table
    from mesh_topology_control import parse_ps2_mesh
    if (type(section_bytes) is not bytes or
            not 16 <= len(section_bytes) <= MAX_SECTION_BYTES):
        raise ValueError('Invalid original PS2 section length')
    packs = []
    at = 0
    needle = struct.pack('<I', GEOM)
    seen_ranges = []
    while True:
        at = section_bytes.find(needle, at)
        if at < 0:
            break
        start = at
        at += 4
        if start % 4 or start + 8 > len(section_bytes):
            continue
        n = struct.unpack_from('<I', section_bytes, start + 4)[0]
        if n > len(section_bytes) - start - 8:
            continue
        frame = section_bytes[start:start + 8 + n]
        try:
            parsed = parse_geometry_root(frame)
        except ValueError:
            continue
        if parsed['platform'] != PLATFORM_PS2:
            raise ValueError('Source geometry is not PS2 platform')
        if len(packs) >= MAX_PACKS:
            raise ValueError('Excessive source geometry pack count')
        if any(start < b and a < start + len(frame) for a, b in seen_ranges):
            raise ValueError('Overlapping original geometry roots')
        seen_ranges.append((start, start + len(frame)))
        pack = []
        for kind, solid in list(read_chunks(frame, 16, len(frame)))[1:]:
            if kind != SRC_SOLID:
                raise ValueError('Unexpected original geometry child')
            identity, platform, _, _ = parse_solid(solid)
            if platform != PLATFORM_PS2:
                raise ValueError('Mixed source platforms')
            chunks = list(read_chunks(solid, 0, len(solid)))
            if [k for k, _ in chunks][:2] != [SOLID_HEADER, SOLID_TEXTURE_TABLE]:
                raise ValueError('Missing original source material table')
            header, raw_table = chunks[0][1], chunks[1][1]
            texture_hashes = parse_solid_texture_table(header, raw_table)
            platform_children = list(read_chunks(chunks[-1][1], 0, len(chunks[-1][1])))
            parse_ps2_mesh(platform_children)
            pack.append((identity, header, tuple(texture_hashes), platform_children))
        if not pack or set(k for k, *_ in pack) != set(parsed['hashes']):
            raise ValueError('Pack identities differ from original source index')
        if len(pack) != len(parsed['hashes']):
            raise ValueError('Duplicate model identity inside original pack')
        if sum(len(p) for p in packs) + len(pack) > MAX_MODELS:
            raise ValueError('Too many original eSolid occurrences')
        packs.append(tuple(pack))
        at = start + len(frame)
    if not packs:
        raise ValueError('No source indexed geometry pack')
    return tuple(packs)


def merge_pc_pack_candidates(candidate_roots):
    """Wrap complete *single-model* PC candidate roots into ONE indexed pack.

    Preserves eSolid children byte-for-byte and their source ordering. A PC
    index is sorted by identity, not by source resource occurrence order.
    Duplicate identities are accepted only ACROSS independent packs.
    """
    from geometry_hash_control import parse_geometry_root, parse_solid, read_chunks, PLATFORM_PC
    if not isinstance(candidate_roots, (tuple, list)) or not 1 <= len(candidate_roots) <= MAX_MODELS:
        raise ValueError('Invalid candidate pack size')
    ordered_ids = []
    original_solids = []
    for root in candidate_roots:
        if not isinstance(root, bytes) or len(root) > MAX_OUTPUT:
            raise ValueError('Unsafe candidate root payload')
        info = parse_geometry_root(root)
        if info['platform'] != PLATFORM_PC or info['solid_count'] != 1:
            raise ValueError('Candidate must contain exactly one PC eSolid')
        children = list(read_chunks(root, 16, len(root)))
        if [x for x, _ in children] != [GEOM_HEADER, SOLID_ROOT]:
            raise ValueError('Unexpected candidate framing')
        solid = children[1][1]
        identity, platform, _, _ = parse_solid(solid)
        if platform != PLATFORM_PC or set(info['hashes']) != {identity}:
            raise ValueError('Candidate indexed identity differs from eSolid')
        ordered_ids.append(identity)
        original_solids.append(_chunk(SOLID_ROOT, solid))
    if len(set(ordered_ids)) != len(ordered_ids):
        raise ValueError('Duplicate model identity within one destination pack')
    index = b''.join(struct.pack('<II', h, 0) for h in sorted(ordered_ids))
    header = _chunk(GEOM_HEADER,
                    _chunk(GEOM_HEADER_DATA, bytes(144)) +
                    _chunk(GEOM_INDEX, index) +
                    _chunk(GEOM_EMPTY, b''))
    merged = _chunk(GEOM_ROOT, bytes(8) + header + b''.join(original_solids))
    if len(merged) > MAX_OUTPUT:
        raise ValueError('Combined destination geometry pack exceeds 32 MiB')
    check = parse_geometry_root(merged)
    if (check['platform'] != PLATFORM_PC or
            check['solid_count'] != len(ordered_ids) or
            set(check['hashes']) != set(ordered_ids)):
        raise ValueError('Combined native PC pack failed source reader')
    rebuilt = [_chunk(k, payload) for k, payload in list(read_chunks(merged, 16, len(merged)))[1:]]
    if rebuilt != original_solids:
        raise ValueError('Combined pack reordered or modified eSolids')
    return merged, {'pc_pack_solid_occurrences': len(ordered_ids),
                    'pc_pack_candidate_bytes': len(merged),
                    'source_order_preserved': True,
                    'pc_index_sorted': True,
                    'native_pc_pack_parser_valid': True}


def material_registry_coverage(packs, original_registered_hashes, used_indices=None):
    """Count material identities *without* returning private texture hashes.

    An RB-local Carbon texture ID match only means a potentially matching
    identity exists in the selected original PC texture packs. It is not
    registration in the actual game loader, nor proof of shader/sampler match.
    """
    if not isinstance(packs, (tuple,list)) or not packs:
        raise ValueError('Missing original source partitions')
    if not isinstance(original_registered_hashes, (set, frozenset)):
        raise ValueError('Registered texture identities must be a private set')
    registered = {_hash(h) for h in original_registered_hashes}
    tables, occurrences, all_materials = [], [], set()
    if used_indices is not None and len(used_indices) != len(packs):
        raise ValueError('Source used-material index partition count differs')
    for pidx, pack in enumerate(packs):
        if not pack:
            raise ValueError('Empty original geometry partition')
        if used_indices is not None and len(used_indices[pidx]) != len(pack):
            raise ValueError('Used-index model count differs')
        for midx, row in enumerate(pack):
            if len(row) < 3:
                raise ValueError('Invalid source eSolid tuple')
            table = row[2]
            if not isinstance(table, (tuple,list)) or not 1 <= len(table) <= 127:
                raise ValueError('Unsafe original material table length')
            texture_hashes = tuple(_hash(h) for h in table)
            tables.append(texture_hashes)
            all_materials.update(texture_hashes)
            ids = range(len(texture_hashes)) if used_indices is None else used_indices[pidx][midx]
            if not isinstance(ids, (tuple,list,range,set,frozenset)):
                raise ValueError('Invalid used material indices')
            if any(type(i) is not int or not 0 <= i < len(texture_hashes) for i in ids):
                raise ValueError('Material mesh references invalid source texture index')
            occurrences.extend(texture_hashes[i] for i in sorted(set(ids)))
    used = set(occurrences)
    matches = used & registered
    return {
        'original_material_table_entries': sum(len(t) for t in tables),
        'original_distinct_material_texture_ids': len(all_materials),
        'used_material_identity_occurrences': len(occurrences),
        'used_distinct_material_texture_ids': len(used),
        'used_identity_occurrences_found_in_carbon_rb': sum(h in registered for h in occurrences),
        'used_distinct_identities_found_in_carbon_rb': len(matches),
        'used_distinct_identities_absent_from_carbon_rb': len(used - registered),
        'rb_local_material_identity_coverage_complete': used <= registered,
        'new_texture_registration_or_fallback_still_required': not used <= registered,
    }


def scene_detail_registry_coverage(packs, scene_detail_identities):
    """Assess *candidate* primary-detail scene-to-model lookup, aggregates only.

    Source scenery info LOD slots and loader rules are unverified. Repeated
    identities across separate pack occurrences remain deliberately ambiguous.
    """
    if not isinstance(scene_detail_identities, (list,tuple)):
        raise ValueError('Scenery references must preserve source info-row occurrences')
    pack_hashes = [[_hash(row[0]) for row in pack] for pack in packs]
    if not pack_hashes or any(not p for p in pack_hashes):
        raise ValueError('Missing source pack identities')
    counts = Counter(h for pack in pack_hashes for h in pack)
    references = [_hash(h) for h in scene_detail_identities]
    resolved = sum(h in counts for h in references)
    ambiguous = sum(counts[h] > 1 for h in references)
    return {
        'source_scene_detail_reference_occurrences':len(references),
        'source_scene_distinct_detail_references':len(set(references)),
        'source_scene_detail_references_backed_by_pack_model':resolved,
        'source_scene_detail_references_missing_local_pack_model':len(references)-resolved,
        'source_scene_detail_references_with_multiple_pack_occurrences':ambiguous,
        'source_model_hashes_repeated_across_independent_packs':sum(v>1 for v in counts.values()),
        'all_source_scene_detail_references_locally_resolved':resolved==len(references),
        'loader_model_occurrence_disambiguation_unverified':bool(ambiguous),
    }


def reconcile_cross_section_scene_registry(source_pack_map, scene_reference_map):
    """Distinguish section-local absence from unresolved global scene identity.

    This is a static identity-presence test for Undercover's two RB sections;
    source LOD selection, runtime resource lifetime, streaming/visibility and
    how the loader disambiguates multiple pack occurrences remain unverified.
    """
    if (not isinstance(source_pack_map, dict) or
            not isinstance(scene_reference_map, dict) or
            set(source_pack_map) != {241, 3401} or
            set(scene_reference_map) != {241, 3401}):
        raise ValueError('Expected both original Undercover RB source sections')
    models = {}
    for section in (241, 3401):
        groups = source_pack_map[section]
        if not isinstance(groups, (tuple, list)) or not groups or any(not group for group in groups):
            raise ValueError('Missing original scene model packs')
        models[section] = {_hash(record[0]) for group in groups for record in group}
    union = models[241] | models[3401]
    per_section = {}
    references_by_section = {}
    for section in (241, 3401):
        src = scene_reference_map[section]
        if not isinstance(src, (tuple, list)) or not src:
            raise ValueError('Missing or empty source scenery-info references')
        refs = [_hash(value) for value in src]
        other = 3401 if section == 241 else 241
        local = models[section]
        references_by_section[section] = refs
        per_section[str(section)] = {
            'source_scenery_info_references': len(refs),
            'locally_resolvable': sum(h in local for h in refs),
            'other_section_only_resolvable': sum(h not in local and h in models[other] for h in refs),
            'unresolved_across_both_source_sections': sum(h not in union for h in refs),
        }
        if sum(per_section[str(section)][k] for k in (
                'locally_resolvable', 'other_section_only_resolvable',
                'unresolved_across_both_source_sections')) != len(refs):
            raise ValueError('Cross-section model reference counts inconsistent')
    return {
        'distinct_source_model_identities_across_both_sections':len(union),
        'distinct_model_identities_shared_by_both_source_sections':len(models[241] & models[3401]),
        'total_source_scenery_info_references':sum(len(v) for v in references_by_section.values()),
        'per_section':per_section,
        'all_source_scene_model_hashes_accounted_for_by_either_section':
            all(not v['unresolved_across_both_source_sections'] for v in per_section.values()),
        'source_model_identity_presence_not_engine_registration':True,
    }


def reconcile_cross_section_material_registry(source_pack_map, carbon_rb_texture_ids):
    """Count distinct USED texture identity blockers over both source sections.

    This intentionally treats the two Undercover geometry sections as one
    private donor model pool, avoiding double counting source texture IDs
    shared across the source sections. No texture hashes are reported.
    """
    from triangle_corner_uv_control import ps2_geometry_attributes
    if not isinstance(source_pack_map, dict) or set(source_pack_map) != {241, 3401}:
        raise ValueError('Expected both original source geometry sections')
    if not isinstance(carbon_rb_texture_ids, (set, frozenset)):
        raise ValueError('Carbon texture registry identities require a set')
    carbon = {_hash(h) for h in carbon_rb_texture_ids}
    source_used = {}
    for section in (241, 3401):
        groups = source_pack_map[section]
        if not isinstance(groups, (tuple, list)) or not groups:
            raise ValueError('Missing geometry for texture identity join')
        used = set()
        for group in groups:
            if not group:
                raise ValueError('Empty source geometry pack')
            for model in group:
                if len(model) != 4:
                    raise ValueError('Bad source material/geometry tuple')
                _, _, table, platform = model
                if not isinstance(table, (tuple,list)) or not 1 <= len(table) <= 127:
                    raise ValueError('Bad source material table')
                keys = tuple(_hash(h) for h in table)
                _,_,faces,labels = ps2_geometry_attributes(platform)
                if not faces or len(faces) != len(labels):
                    raise ValueError('Missing triangle material labels')
                if any(type(label) is not int or not 0 <= label < len(keys) for label in labels):
                    raise ValueError('Source used material index out of bounds')
                used.update(keys[i] for i in set(labels))
        source_used[section] = used
    union = source_used[241] | source_used[3401]
    return {
        'used_distinct_source_material_texture_ids_combined':len(union),
        'used_distinct_source_material_texture_ids_shared_sections':
            len(source_used[241] & source_used[3401]),
        'used_distinct_source_material_texture_ids_only_section_241':
            len(source_used[241] - source_used[3401]),
        'used_distinct_source_material_texture_ids_only_section_3401':
            len(source_used[3401] - source_used[241]),
        'combined_used_material_ids_present_in_carbon_rb_texture_indexes':len(union & carbon),
        'combined_used_material_ids_absent_from_carbon_rb_texture_indexes':len(union - carbon),
        'additional_identity_registration_or_remap_required_for_rb_only':not union <= carbon,
    }


def reconcile_original_undercover_texture_presence(source_pack_map, original_texture_sections):
    """Compare source-used material IDs with original Undercover RB image IDs.

    One eSolid material identity can refer to a global/RA resource rather than
    the two source RB texture packs. Absence is therefore RB-local, not proof
    the original game lacks that texture somewhere else.
    """
    from triangle_corner_uv_control import ps2_geometry_attributes
    from texture_metadata_pixel_bridge import parse_pack
    if (not isinstance(source_pack_map, dict) or set(source_pack_map) != {241,3401} or
            not isinstance(original_texture_sections, dict) or
            set(original_texture_sections) != {241,3401}):
        raise ValueError('Expected both original Undercover source sections and image indexes')
    available = {}
    used = {}
    per_section = {}
    for section in (241,3401):
        source = original_texture_sections[section]
        if not isinstance(source, bytes):
            raise ValueError('Original PS2 texture section must remain private bytes')
        records = parse_pack(source, 'ps2')['records']
        indexed = {_hash(h) for h in records}
        if not indexed:
            raise ValueError('No original PS2 texture index records')
        available[section] = indexed
        seen = set()
        groups = source_pack_map[section]
        if not isinstance(groups, (tuple,list)) or not groups or any(not g for g in groups):
            raise ValueError('Missing PS2 source geometry material groups')
        for group in groups:
            for row in group:
                if len(row) != 4:
                    raise ValueError('Wrong original eSolid record')
                _,_,table,platform = row
                if not isinstance(table,(tuple,list)) or not 1<=len(table)<=127:
                    raise ValueError('Invalid original material table')
                hashes = tuple(_hash(h) for h in table)
                _,_,faces,labels = ps2_geometry_attributes(platform)
                if not faces or len(faces)!=len(labels):
                    raise ValueError('Missing original used material labels')
                if any(type(k) is not int or not 0<=k<len(hashes) for k in labels):
                    raise ValueError('Invalid original used material label')
                seen.update(hashes[k] for k in set(labels))
        used[section] = seen
        per_section[str(section)] = {
            'local_source_texture_index_records':len(indexed),
            'locally_used_distinct_material_texture_ids':len(seen),
            'locally_used_ids_with_texture_in_same_source_rb_section':len(seen & indexed),
            'locally_used_ids_not_in_same_source_rb_texture_index':len(seen - indexed),
        }
    union_used = used[241] | used[3401]
    union_images = available[241] | available[3401]
    return {
        'per_section':per_section,
        'distinct_source_used_material_texture_ids_combined':len(union_used),
        'distinct_undercover_rb_image_texture_ids_combined':len(union_images),
        'distinct_undercover_rb_image_ids_shared_across_sections':len(available[241] & available[3401]),
        'combined_used_material_ids_with_undercover_rb_image':len(union_used & union_images),
        'combined_used_material_ids_absent_from_both_undercover_rb_image_indexes':len(union_used - union_images),
        'material_to_source_pixel_image_registry_complete_in_rb':union_used <= union_images,
        'other_source_pack_or_global_registration_may_resolve_absences':True,
    }


def convert_four_pack_section(source_packs, registered_pc_texture_ids, scene_detail_ids=()):
    """Build all PC-shaped pack candidates privately, return aggregates only.

    All candidates live in RAM; no output section, stream, registry or assets
    are written. Per-source-model native readback is performed by the existing
    independent Undercover geometry bridge before any multi-model merging.
    """
    from triangle_corner_uv_control import ps2_geometry_attributes
    if not isinstance(source_packs, (tuple,list)) or len(source_packs) != 4:
        raise ValueError('Expected exactly four source geometry pack partitions')
    packed = []
    totals = Counter()
    used_indices = []
    identities = []
    for group in source_packs:
        if not group:
            raise ValueError('Empty original source geometry pack')
        single_roots = []
        used_for_group = []
        for identity, header, table, platform in group:
            xyz,uv,faces,labels = ps2_geometry_attributes(platform)
            single, info = convert_decoded_ps2_model(identity, table, xyz,uv,faces,labels,header)
            single_roots.append(single)
            used_for_group.append(tuple(sorted(set(labels))))
            for field in ('source_vertex_occurrences','source_triangles','generated_pc_meshes',
                          'generated_pc_vertex_occurrences','generated_pc_triangles',
                          'degenerate_geometric_faces_preserved',
                          'candidate_normal_fallback_vertices'):
                totals[field] += info[field]
        merged, status = merge_pc_pack_candidates(single_roots)
        if status['pc_pack_solid_occurrences'] != len(group):
            raise ValueError('PC pack candidate lost an original model occurrence')
        packed.append(merged)
        used_indices.append(tuple(used_for_group))
        identities.append(tuple(identity for identity, *_ in group))
        totals['pc_pack_candidate_bytes'] += len(merged)
        totals['source_model_occurrences'] += len(group)
    if len(packed) != len(source_packs):
        raise ValueError('Lost original pack partition')
    per_pack = [len(group) for group in source_packs]
    registrable = material_registry_coverage(source_packs, registered_pc_texture_ids, used_indices)
    spatial = scene_detail_registry_coverage(source_packs, scene_detail_ids)
    return {'scope':'OFFLINE_PC_SHAPED_FOUR_PACKS_NOT_RETAIL_REGISTERED',
            'original_geometry_pack_count':len(source_packs),
            'pc_candidate_pack_count':len(packed),
            'source_models_per_pack':per_pack,
            'source_model_occurrences':totals['source_model_occurrences'],
            'distinct_source_model_identities':len(set(h for group in identities for h in group)),
            'cross_pack_duplicate_model_identity_count':
                sum(v>1 for v in Counter(h for group in identities for h in group).values()),
            'original_pack_order_and_resource_order_retained':True,
            'all_pc_packs_pass_native_source_parser':True,
            **dict(sorted(totals.items())),
            'material_texture_identity_preflight':registrable,
            'scene_primary_model_identity_preflight':spatial,
            'runtime_loader_registration':'UNVERIFIED',
            'actual_pc_texture_resources_created':False,
            'game_data_written':False}


def _read_owner_zip_section(path, section):
    """CRC-verified private Undercover RB stream extraction into RAM only."""
    from visibility_stream_join import read_small
    rows, _, _ = read_small(path, 'L2', 'RB')
    if section not in rows:
        raise ValueError('Missing source RB section table row')
    off, length = struct.unpack_from('<II', rows[section], 0x14)
    if length < 8 or length > MAX_SECTION_BYTES:
        raise ValueError('Original source section size unsafe')
    with zipfile.ZipFile(path) as z:
        info = z.getinfo('TRACKS/STREAML2RB.BUN')
        if not 0 < info.file_size <= MAX_STREAM or off + length > info.file_size:
            raise ValueError('Source section outside original owner stream')
        stream = z.read(info)  # Python ZIP validates compressed member CRC32
    return stream[off:off + length]


def _read_owner_pc_registered_hashes(volumes):
    """CRC-check original Carbon PC split-ZIP RB texture identity indexes.

    Split ZIP volumes are read in disk order by the repository's established
    read-only PKZIP multi-volume reader. Neither source bytes nor source hash
    inventories are returned in the published aggregate JSON.
    """
    from texture_metadata_pixel_bridge import parse_pack
    from private_carbon_dxt1_stream_stage import section_span
    from track_bundle_probe import SplitZip
    if not isinstance(volumes, (list, tuple)) or len(volumes) < 2:
        raise ValueError('Provide original Carbon PC split ZIP volumes in disk order')
    archive = SplitZip(volumes)
    small = 'TRACKS/L5RB.BUN'
    large = 'TRACKS/STREAML5RB.BUN'
    bundle = archive.read(small, limit=8 * 1024 * 1024)
    if archive.entries[large][4] > MAX_STREAM:
        raise ValueError('Carbon PC RB source stream exceeds inspection limit')
    stream = archive.read(large, limit=MAX_STREAM)
    registered = set()
    counts = []
    for section in (141,142):
        off, size = section_span(bundle, len(stream), section)
        records = parse_pack(stream[off:off+size], 'pc')['records']
        counts.append(len(records))
        registered.update(records)
    return registered, counts


def _source_scene_detail_hashes(original_section):
    """Candidate source scene-info +0x1C hashes, not runtime scene registry.

    Scenery root and graph are independently validated first by existing
    parse routines, preventing arbitrary 4-byte signature hits from being
    promoted as source scene info.
    """
    from z0_tree_graph_probe import scene_children, inspect_scene
    signature = struct.pack('<I', 0x80034100)
    at = 0
    candidates = []
    while True:
        at = original_section.find(signature, at)
        if at < 0:
            break
        start = at
        at += 4
        if start % 4:
            continue
        try:
            info = inspect_scene(original_section[start:])
            children, length = scene_children(original_section[start:])
        except ValueError:
            continue
        raw = children[0x34102]
        if not raw or len(raw) % 72:
            raise ValueError('Invalid scenery info stride')
        # PS2 source candidate primary detail model is info slot +0x1C.
        ids = tuple(struct.unpack_from('<I', raw, i + 0x1C)[0]
                    for i in range(0, len(raw), 72))
        if any(h == 0 for h in ids):
            raise ValueError('Zero primary source model hash')
        candidates.append(ids)
        at = start + length
    if len(candidates) != 1:
        raise ValueError('Expected one original scene root within this section')
    return candidates[0]


def audit_original_four_pack_registry(undercover_zip, carbon_pc_volumes):
    """Return safe aggregate audit of both source sections; no file writes."""
    def safe_file(path, limit):
        p = Path(path).absolute()
        if any(x.is_symlink() for x in (p,*p.parents)) or not p.is_file():
            raise ValueError('Missing or symlinked original owner archive')
        if not 0 < p.stat().st_size <= limit:
            raise ValueError('Missing/oversized private original archive')
        return p
    uc_path=safe_file(undercover_zip, MAX_ZIP)
    if (not isinstance(carbon_pc_volumes,(tuple,list)) or
            not 2 <= len(carbon_pc_volumes) <= 16):
        raise ValueError('Supply the original split Carbon PC archive volumes')
    pc_paths = tuple(safe_file(p, MAX_PC_ARCHIVE) for p in carbon_pc_volumes)
    if len(set(pc_paths)) != len(pc_paths) or uc_path in pc_paths:
        raise ValueError('Original game archives must be different files')
    def digest(path):
        h=hashlib.sha256()
        with path.open('rb') as f:
            while data:=f.read(1024*1024):h.update(data)
        return (path.stat().st_size,path.stat().st_mtime_ns,h.digest())
    source_states={p:digest(p) for p in (uc_path,*pc_paths)}
    registered, pc_counts = _read_owner_pc_registered_hashes(pc_paths)
    sections = {}
    all_source_packs = {}
    all_scene_detail = {}
    all_texture_sections = {}
    for number in (241,3401):
        source = _read_owner_zip_section(uc_path, number)
        groups = source_partition_roots(source)
        all_texture_sections[number] = source
        detail = _source_scene_detail_hashes(source)
        all_source_packs[number] = groups
        all_scene_detail[number] = detail
        sections[str(number)]=convert_four_pack_section(groups,registered,detail)
    if any(digest(p) != state for p,state in source_states.items()):
        raise ValueError('Original owner archive was modified during read-only audit')
    source_scene_cross_section = reconcile_cross_section_scene_registry(
        all_source_packs, all_scene_detail)
    source_material_cross_section = reconcile_cross_section_material_registry(
        all_source_packs, registered)
    source_texture_coverage = reconcile_original_undercover_texture_presence(
        all_source_packs, all_texture_sections)
    return {'scope':'PRIVATE_ORIGINAL_ARCHIVE_FOUR_PACK_PARSER_GATE_ONLY',
            'undercover_sections':sections,
            'cross_section_source_scene_registry':source_scene_cross_section,
            'cross_section_source_material_registry':source_material_cross_section,
            'undercover_source_rb_texture_image_presence':source_texture_coverage,
            'original_carbon_rb_texture_records':sum(pc_counts),
            'original_carbon_rb_distinct_texture_identities':len(registered),
            'originals_unchanged':True,
            'private_original_game_assets_published':False,
            'retail_pc_geometry_registration':'NOT_TESTED'}


def main():
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--undercover-ps2-zip',type=Path,required=True)
    cli.add_argument('--carbon-pc-volumes',type=Path,nargs='+',required=True,
                     help='Owner-original Carbon PC TRACKS.z01 ... TRACKS.zip volumes in order')
    args=cli.parse_args()
    print(json.dumps(audit_original_four_pack_registry(
        args.undercover_ps2_zip,args.carbon_pc_volumes),indent=2))


if __name__=='__main__':main()
