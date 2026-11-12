#!/usr/bin/env python3
"""Offline source-backed Carbon PC scene model-reference closure (V22).

A V21 in-memory scene rebind preserves Carbon PC's native 72-byte
scenery-info records and 96-byte scenery-instance references, changing
only two model-hash fields. That alone does not establish that the
remaining scenery models are backed by source Carbon geometry.

This audits ALL four candidate model-hash fields in each referenced
info record, checks original native Carbon PC eSolid roots and the
single converted Undercover V20 model, and refuses to overclaim a
complete global Carbon resource registry or any in-game rendering.

No original resource hashes, model names, positions or binary payloads
are ever included in the report. No files are written or loaded in game.
"""
import struct

from carbon_pc_bun_chunk_stream_gate import MAX_BUN_BYTES
from carbon_pc_first_model_stream_assembly import build_private_pc_first_model_stream
from carbon_pc_native_postscene_layout_gate import (
    _children, scene_profile, SCENE_CHILDREN, MAX_SCENE,
)
from carbon_pc_resource_namespace_gate import _roots
from geometry_hash_control import parse_geometry_root, PLATFORM_PC
from scenery_model_hash_bridge import (
    INFO_ID, INSTANCE_ID, INFO_SIZE, FIRST_HASH_OFFSET,
    validate_instance_links,
)

MAX_NATIVE_GEOMETRY_BYTES = 32 * 1024 * 1024


def audit_pc_scene_model_closure(
        rebound_scene_root, private_pcchunk, selected_info_index,
        native_carbon_pc_geometry_roots):
    """Resolve referenced scenery detail slots in supplied PC geometry.

    A valid result means ONLY local source-reference closure for the
    geometry roots the caller provided. The PC streaming system can load
    models from elsewhere; unresolved references are reported as
    INCOMPLETE, not proof of a missing runtime resource.

    All referenced info rows are counted using 96-byte instance links.
    The four nonzero model slots at +0x18/+0x1C/+0x20/+0x24 are audited,
    not just the two hashes modified by the V21 rebind. Duplicate
    global/native model IDs across distinct supplied roots are treated
    as ambiguous, never silently assumed interchangeable.
    """
    if (type(rebound_scene_root) is not bytes or
            not 80 <= len(rebound_scene_root) <= MAX_SCENE or
            type(private_pcchunk) is not bytes or
            not 80 <= len(private_pcchunk) <= MAX_BUN_BYTES or
            type(selected_info_index) is not int or selected_info_index < 0):
        raise ValueError('Invalid private PC scene/Undercover candidate dimensions')
    scene_profile(rebound_scene_root, 'pc')

    # Require exactly the *current* V20 texture-first, DXT5-backed model.
    if struct.unpack_from('<I', private_pcchunk, 0)[0] != 0xB3300000:
        raise ValueError('V20 texture-first model stream required')
    boundary = struct.unpack_from('<I', private_pcchunk, 4)[0] + 8
    if not 40 <= boundary <= len(private_pcchunk) - 40:
        raise ValueError('Incomplete V20 texture root')
    texture, geometry = private_pcchunk[:boundary], private_pcchunk[boundary:]
    rebuilt, _ = build_private_pc_first_model_stream(geometry, texture)
    if rebuilt != private_pcchunk:
        raise ValueError('V20 candidate failed complete reassembly')
    models = parse_geometry_root(geometry)
    if models['platform'] != PLATFORM_PC or models['solid_count'] != 1:
        raise ValueError('Expected one PC indexed Undercover model')
    candidate = next(iter(models['hashes']))

    children = _children(rebound_scene_root, 8, len(rebound_scene_root))
    if tuple(tag for tag, _, _ in children) != SCENE_CHILDREN:
        raise ValueError('Unsupported original Carbon scene root children')
    offsets = {tag: (start, stop) for tag, start, stop in children}
    info_start, info_end = offsets[INFO_ID]
    inst_start, inst_end = offsets[INSTANCE_ID]
    info_table = rebound_scene_root[info_start:info_end]
    instance_links = validate_instance_links(
        rebound_scene_root[inst_start:inst_end], info_table)
    total_rows = len(info_table) // INFO_SIZE
    if selected_info_index >= total_rows:
        raise ValueError('Selected Carbon scenery info index outside table')
    if selected_info_index not in instance_links:
        raise ValueError('Rebound info row is not referenced by any instance')

    rows = [
        struct.unpack_from('<4I', info_table, i*INFO_SIZE+FIRST_HASH_OFFSET)
        for i in range(total_rows)
    ]
    if rows[selected_info_index][:2] != (candidate, candidate):
        raise ValueError('Selected scenery info row does not match converted model')
    if (rows[selected_info_index][2] == candidate or
            rows[selected_info_index][3] == candidate or
            any(candidate in row for i,row in enumerate(rows)
                if i != selected_info_index)):
        raise ValueError('Candidate model also appears in another scene LOD slot')

    active_indices = frozenset(instance_links)
    active_slots = [
        h for info_index in active_indices for h in rows[info_index] if h
    ]
    active_hashes = frozenset(active_slots)
    all_hashes = frozenset(
        h for slots in rows for h in slots if h)
    native_roots = _roots(native_carbon_pc_geometry_roots, 'geometry')
    native_ids = set()
    duplicates = set()
    for native_root in native_roots:
        if type(native_root) is not bytes or not 40 <= len(native_root) <= MAX_NATIVE_GEOMETRY_BYTES:
            raise ValueError('Unbounded original Carbon PC native geometry root')
        parsed = parse_geometry_root(native_root)
        if parsed['platform'] != PLATFORM_PC:
            raise ValueError('Original Carbon geometry root is not PC platform')
        duplicates.update(native_ids.intersection(parsed['hashes']))
        native_ids.update(parsed['hashes'])

    collision = candidate in native_ids
    # Candidate first/second LOD slots are identical, so the set of
    # active scene identities is not equal to the number of slot uses.
    all_supply = native_ids | {candidate}
    active_missing = active_hashes - all_supply
    inactive_missing = all_hashes - all_supply
    native_used = active_hashes & native_ids
    status = (
        'BLOCKED_COLLISION_OR_AMBIGUOUS_NATIVE_MODEL_ID'
        if collision or duplicates else
        'INCOMPLETE_REFERENCES_IN_SUPPLIED_NATIVE_GEOMETRY'
        if active_missing or inactive_missing else
        'COMPLETE_FOR_SUPPLIED_SCENE_AND_GEOMETRY_NOT_RUNTIME_PROOF'
    )
    return {
        'scope': 'V22_OFFLINE_CARBON_PC_SCENE_MODEL_REFERENCE_CLOSURE_ONLY',
        'source_pc_scene_profile_verified': True,
        'undercover_candidate_eSolid_and_DXT5_verified': True,
        'scenery_info_records': total_rows,
        'scenery_instance_records': len(instance_links),
        'referenced_info_records': len(active_indices),
        'unreferenced_info_records': total_rows - len(active_indices),
        'referenced_nonzero_model_slot_occurrences': len(active_slots),
        'referenced_distinct_model_identities': len(active_hashes),
        'all_scene_distinct_model_identities': len(all_hashes),
        'source_native_geometry_roots_supplied': len(native_roots),
        'source_native_distinct_indexed_models': len(native_ids),
        'source_native_repeated_model_identities': len(duplicates),
        'source_native_models_referenced_by_instances': len(native_used),
        'converted_undercover_model_referenced_by_instances': candidate in active_hashes,
        'converted_model_collision_with_native': collision,
        'referenced_model_identities_unresolved_in_supplied_roots': len(active_missing),
        'all_scene_model_identities_unresolved_in_supplied_roots': len(inactive_missing),
        'all_referenced_instance_model_slots_backed_in_supplied_roots':
            not active_missing,
        'all_scene_info_model_slots_backed_in_supplied_roots':
            not inactive_missing,
        'local_model_reference_gate': status,
        'all_carbon_global_model_resources_enumerated': False,
        'native_material_texture_closure_verified': False,
        'native_postscene_control_dependencies_verified': False,
        'native_carbon_stream_sector_complete': False,
        'external_loader_model_registration_verified': False,
        'undercover_object_rendered_in_game': False,
        'game_files_modified': False,
        'private_model_ids_original_names_coordinates_disclosed': False,
        'limitations': (
            'Only the original Carbon PC geometry roots explicitly supplied '
            'by the owner are included. Other resource types, streaming '
            'sections and globally cached Carbon models are NOT enumerated. '
            'A missing local model may exist elsewhere in the game; a '
            'complete offline set does not establish runtime registration, '
            'texture closure for original Carbon models, placement, '
            'visibility, collision, post-scene controls or rendering.'
        ),
    }
