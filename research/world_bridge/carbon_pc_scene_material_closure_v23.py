#!/usr/bin/env python3
"""V23: original-source backed PC scenery eSolid -> texture closure.

Resolve *each referenced eSolid's own complete material table* against
indexed original Carbon PC texture roots and the converted Undercover
DXT5 textures. Do not mistake a global union of textures for proof
that specific scenery/LOD model identities are backed.

Offline source-only evidence, never a Carbon resource-manager, render,
post-scene-control or global registry claim. No private IDs or pixels
appear in returned reports.
"""
import struct

from carbon_pc_bun_chunk_stream_gate import MAX_BUN_BYTES
from carbon_pc_first_model_stream_assembly import build_private_pc_first_model_stream
from carbon_pc_scene_model_closure_v22 import audit_pc_scene_model_closure
from carbon_pc_native_postscene_layout_gate import _children, SCENE_CHILDREN, MAX_SCENE
from carbon_pc_resource_namespace_gate import _roots, _texture_ids
from geometry_hash_control import (
    PLATFORM_PC, SOLID_ROOT, parse_geometry_root, parse_solid, read_chunks,
)
from scenery_model_hash_bridge import (
    INFO_ID, INFO_SIZE, INSTANCE_ID, FIRST_HASH_OFFSET, validate_instance_links,
)
from texture_binding_control import parse_solid_texture_table

MAX_PRIVATE_ROOT = 32 * 1024 * 1024


def _pc_model_materials(root):
    """Native indexed PC eSolid identities mapped to complete material tables."""
    if type(root) is not bytes or not 40 <= len(root) <= MAX_PRIVATE_ROOT:
        raise ValueError('Native PC eSolid root outside private inspection bound')
    metadata = parse_geometry_root(root)
    if metadata['platform'] != PLATFORM_PC:
        raise ValueError('Native geometry must contain PC platform eSolids')
    materials = {}
    for tag, solid in read_chunks(root, 16, len(root)):
        if tag != SOLID_ROOT:
            continue
        model, platform, _, _ = parse_solid(solid)
        if platform != PLATFORM_PC or model in materials:
            raise ValueError('Invalid or duplicate source model header')
        children = list(read_chunks(solid, 0, len(solid)))
        if len(children) < 3:
            raise ValueError('Incomplete source eSolid texture table')
        table = parse_solid_texture_table(children[0][1], children[1][1])
        if not table:
            raise ValueError('PC model has no material identities')
        materials[model] = frozenset(table)
    if set(materials) != set(metadata['hashes']):
        raise ValueError('Native eSolid model index differs from parsed material tables')
    return materials


def audit_pc_scene_material_closure(
        rebound_scene_root, private_pcchunk, selected_info_index,
        native_carbon_geometry_roots, native_carbon_texture_roots):
    """Check supplied original geometry+textures for all PC scene LOD slots.

    Missing materials can be elsewhere in Carbon's global resources; this
    is local coverage only. Duplicate native texture IDs or collisions
    with new candidate texture IDs are conservatively blocked until
    a source-backed overriding/alias policy is implemented.
    """
    if (type(rebound_scene_root) is not bytes or
            not 80 <= len(rebound_scene_root) <= MAX_SCENE or
            type(private_pcchunk) is not bytes or
            not 80 <= len(private_pcchunk) <= MAX_BUN_BYTES or
            type(selected_info_index) is not int or selected_info_index < 0):
        raise ValueError('Invalid private scene, candidate or source index')
    native_geo = _roots(native_carbon_geometry_roots, 'geometry')
    native_tex = _roots(native_carbon_texture_roots, 'texture')
    model_report = audit_pc_scene_model_closure(
        rebound_scene_root, private_pcchunk, selected_info_index, native_geo)

    # The original-first PC scenery candidate always contains exactly
    # the DXT5 root before the indexed eSolid root (V20).
    boundary = struct.unpack_from('<I', private_pcchunk, 4)[0] + 8
    if not 40 <= boundary <= len(private_pcchunk) - 40:
        raise ValueError('PC candidate texture root is incomplete')
    candidate_tex, candidate_geo = (
        private_pcchunk[:boundary], private_pcchunk[boundary:])
    rebuilt, _ = build_private_pc_first_model_stream(
        candidate_geo, candidate_tex)
    if rebuilt != private_pcchunk:
        raise ValueError('Candidate PC material source stream disagrees')
    candidate_models = _pc_model_materials(candidate_geo)
    if len(candidate_models) != 1:
        raise ValueError('Expected one converted Undercover PC model')
    converted_id = next(iter(candidate_models))
    converted_images = _texture_ids(candidate_tex)
    if candidate_models[converted_id] != converted_images:
        raise ValueError('Converted model does not have exact DXT image closure')

    # Read *actual per-model* texture identities, not just a geometry
    # pack-wide union. Duplicated eSolid IDs across packs are ambiguous.
    original_models = {}
    duplicate_models = set()
    for root in native_geo:
        for model, images in _pc_model_materials(root).items():
            if model in original_models:
                duplicate_models.add(model)
            original_models[model] = images

    native_images = set()
    duplicate_images = set()
    for root in native_tex:
        if type(root) is not bytes or not 40 <= len(root) <= MAX_PRIVATE_ROOT:
            raise ValueError('Native PC texture root outside private inspection bound')
        texture_ids = _texture_ids(root)
        duplicate_images.update(native_images & texture_ids)
        native_images.update(texture_ids)

    children = _children(rebound_scene_root, 8, len(rebound_scene_root))
    if tuple(tag for tag, _, _ in children) != SCENE_CHILDREN:
        raise ValueError('Invalid native PC scenery child order')
    offsets = {tag: (start, end) for tag, start, end in children}
    ia, ib = offsets[INFO_ID]
    xa, xb = offsets[INSTANCE_ID]
    links = validate_instance_links(
        rebound_scene_root[xa:xb], rebound_scene_root[ia:ib])
    scene_rows = [
        struct.unpack_from('<4I', rebound_scene_root,
                           ia + i*INFO_SIZE + FIRST_HASH_OFFSET)
        for i in range((ib-ia)//INFO_SIZE)
    ]
    active_rows = frozenset(links)
    referenced_models = frozenset(
        model for i in active_rows for model in scene_rows[i] if model)
    all_scene_models = frozenset(
        model for row in scene_rows for model in row if model)
    if converted_id not in referenced_models:
        raise ValueError('Converted model is not referenced by active scene')

    # Unbacked model references are accounted for by the V22 gate; no
    # material table can safely be inferred for those missing models.
    supplied_models = {**original_models, **candidate_models}
    active_known = referenced_models & supplied_models.keys()
    all_known = all_scene_models & supplied_models.keys()
    referenced_materials = set().union(
        *(supplied_models[m] for m in active_known))
    all_materials = set().union(
        *(supplied_models[m] for m in all_known))
    native_referenced_materials = set().union(
        *(original_models[m] for m in referenced_models & original_models.keys()))
    all_available_images = native_images | converted_images
    missing_referenced_images = referenced_materials - all_available_images
    missing_any_images = all_materials - all_available_images
    candidate_image_collision = native_images & converted_images
    model_conflict = (model_report['local_model_reference_gate'] ==
                      'BLOCKED_COLLISION_OR_AMBIGUOUS_NATIVE_MODEL_ID')

    if model_conflict or duplicate_models or duplicate_images or candidate_image_collision:
        status = 'BLOCKED_AMBIGUOUS_MODEL_OR_TEXTURE_IDENTITY'
    elif (model_report['local_model_reference_gate'] !=
          'COMPLETE_FOR_SUPPLIED_SCENE_AND_GEOMETRY_NOT_RUNTIME_PROOF' or
          missing_referenced_images or missing_any_images):
        status = 'INCOMPLETE_LOCAL_PC_MODEL_OR_MATERIAL_REFERENCES'
    else:
        status = 'COMPLETE_FOR_SUPPLIED_PC_SCENE_RESOURCES_NOT_RUNTIME_PROOF'

    return {
        'scope': 'V23_OFFLINE_PC_SCENE_MODEL_MATERIAL_IMAGE_CLOSURE_ONLY',
        'v22_local_scene_model_closure': model_report['local_model_reference_gate'],
        'native_pc_geometry_roots_supplied': len(native_geo),
        'native_pc_texture_roots_supplied': len(native_tex),
        'referenced_distinct_scene_models': len(referenced_models),
        'referenced_models_backed_in_supplied_geometry': len(active_known),
        'all_scene_models_backed_in_supplied_geometry': len(all_known),
        'referenced_native_model_material_identities': len(native_referenced_materials),
        'referenced_distinct_material_identities_from_backed_models': len(referenced_materials),
        'all_scene_distinct_material_identities_from_backed_models': len(all_materials),
        'native_distinct_texture_identities_supplied': len(native_images),
        'converted_distinct_DXT5_texture_identities': len(converted_images),
        'referenced_material_identities_backed_by_native_textures':
            len(referenced_materials & native_images),
        'referenced_material_identities_backed_by_candidate_DXT5':
            len(referenced_materials & converted_images),
        'referenced_material_identities_unresolved_in_supplied_textures':
            len(missing_referenced_images),
        'all_scene_material_identities_unresolved_in_supplied_textures':
            len(missing_any_images),
        'native_texture_identities_repeated_across_roots': len(duplicate_images),
        'native_model_identities_repeated_across_roots': len(duplicate_models),
        'candidate_texture_identities_colliding_with_native': len(candidate_image_collision),
        'all_active_scene_model_materials_have_supplied_images':
            not missing_referenced_images and len(active_known) == len(referenced_models),
        'all_scene_info_model_materials_have_supplied_images':
            not missing_any_images and len(all_known) == len(all_scene_models),
        'local_material_closure_gate': status,
        'entire_carbon_global_texture_registry_examined': False,
        'postscene_372xx_texture_dependencies_verified': False,
        'native_carbon_sector_complete': False,
        'carbon_loader_registered_resources_verified': False,
        'undercover_model_rendered_inside_carbon_verified': False,
        'stock_game_files_modified': False,
        'private_model_texture_ids_names_pixels_disclosed': False,
        'limitations': (
            'Only explicitly supplied native Carbon geometry and texture '
            'roots are examined. Unresolved models cannot have their own '
            'material tables evaluated. Image ID presence does not prove '
            'correct pixels, palette sampling, streaming cache availability, '
            'runtime resource registration, visibility or drawing; original '
            'Carbon post-scene 0x372xx semantics are not reconstructed.'
        ),
    }
