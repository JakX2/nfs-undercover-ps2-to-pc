#!/usr/bin/env python3
"""Offline Carbon PC resource-identity gate for candidate Undercover assets.

Uses independently verified Carbon PC geometry/texture readers. No game
installation, ASI injection, asset export, or retail loader invocation.
The returned report deliberately omits every model/texture ID and name.
A passing result is a *local namespace preflight*, NOT rendering proof.
"""

from geometry_hash_control import (
    PLATFORM_PC, SOLID_ROOT, parse_geometry_root, parse_solid, read_chunks,
)
from texture_binding_control import parse_solid_texture_table
from texture_metadata_pixel_bridge import parse_pack

MAX_REFERENCE_ROOTS = 32


def _bytes(value, role):
    if type(value) is not bytes:
        raise ValueError(role + ' must be immutable bytes')
    return value


def _model_and_materials(root):
    """Inspect one indexed Carbon PC geometry root and ALL eSolid tables."""
    info = parse_geometry_root(_bytes(root, 'geometry root'))
    if info['platform'] != PLATFORM_PC:
        raise ValueError('Expected original PC-shaped geometry, not PS2')
    materials = set()
    solid_count = 0
    for tag, solid in read_chunks(root, 16, len(root)):
        if tag != SOLID_ROOT:
            continue
        identity, platform, _pad, _children = parse_solid(solid)
        if platform != PLATFORM_PC or identity not in info['hashes']:
            raise ValueError('Geometry eSolid disagrees with PC root index')
        parts = list(read_chunks(solid, 0, len(solid)))
        if len(parts) < 3:
            raise ValueError('Incomplete PC geometry eSolid')
        materials.update(parse_solid_texture_table(parts[0][1], parts[1][1]))
        solid_count += 1
    if solid_count != info['solid_count'] or not materials:
        raise ValueError('No complete PC eSolid/material table')
    return info['hashes'], frozenset(materials)


def _texture_ids(root):
    root = _bytes(root, 'texture root')
    if len(root) < 8:
        raise ValueError('Truncated PC texture root')
    # The PC texture parser validates structure, image ranges, IDs and codec.
    # Refuse trailing resource bytes that the lower-level reader tolerates.
    import struct
    if 8 + struct.unpack_from('<I', root, 4)[0] != len(root):
        raise ValueError('Trailing or truncated PC texture root')
    return frozenset(parse_pack(root, 'pc')['records'])


def _roots(roots, kind):
    if type(roots) not in (tuple, list) or not 1 <= len(roots) <= MAX_REFERENCE_ROOTS:
        raise ValueError('Required bounded owner-original Carbon PC ' + kind + ' roots')
    return roots


def audit_carbon_registration_namespace(
        candidate_geometry, candidate_textures,
        native_carbon_geometry_roots, native_carbon_texture_roots):
    """Compare complete in-memory candidate resources with host Carbon RB roots.

    Caller supplies owner-private validated PC roots, not arbitrary hash sets.
    All private identities remain in memory; report only aggregate counts.
    This audits the *supplied* native roots, not the entire game's global
    resource manager, streaming cache or runtime registration rules.
    """
    candidate_models, candidate_materials = _model_and_materials(candidate_geometry)
    candidate_images = _texture_ids(candidate_textures)

    carbon_models = set()
    carbon_images = set()
    native_materials = set()
    for root in _roots(native_carbon_geometry_roots, 'geometry'):
        models, materials = _model_and_materials(root)
        carbon_models.update(models)
        native_materials.update(materials)
    for root in _roots(native_carbon_texture_roots, 'texture'):
        carbon_images.update(_texture_ids(root))

    # Internal closure requires the converted model's every *table* entry,
    # not just textures referenced by its triangles, to resolve in a candidate
    # pack or in inspected original Carbon PC texture roots.
    not_resolved = candidate_materials - (candidate_images | carbon_images)
    model_collisions = candidate_models & carbon_models
    texture_collisions = candidate_images & carbon_images
    # Presence of a candidate texture with an existing Carbon hash may mean
    # replacement, NOT an identical image. Never silently mark that safe.
    fail_reasons = {
        'model_identity_collision': bool(model_collisions),
        'texture_identity_collision': bool(texture_collisions),
        'unresolved_candidate_materials': bool(not_resolved),
    }
    return {
        'scope': 'OFFLINE_SUPPLIED_CARBON_RB_ROOTS_ONLY_NOT_RUNTIME',
        'candidate_model_count': len(candidate_models),
        'candidate_texture_count': len(candidate_images),
        'candidate_distinct_material_id_count': len(candidate_materials),
        'native_model_count_in_supplied_roots': len(carbon_models),
        'native_texture_count_in_supplied_roots': len(carbon_images),
        'native_material_count_in_supplied_roots': len(native_materials),
        'candidate_models_colliding_with_native': len(model_collisions),
        'candidate_textures_colliding_with_native': len(texture_collisions),
        'candidate_materials_resolved_by_candidate': len(candidate_materials & candidate_images),
        'candidate_materials_resolved_by_native': len(candidate_materials & carbon_images),
        'candidate_materials_unresolved': len(not_resolved),
        'blockers': fail_reasons,
        'namespace_gate': (
            'ELIGIBLE_FOR_OWNER_LOCAL_EXPERIMENT_NOT_RUNTIME_PROOF'
            if not any(fail_reasons.values()) else 'BLOCKED'
        ),
        'full_carbon_registry_coverage_verified': False,
        'carbon_loader_abi_verified': False,
        'runtime_registration_verified': False,
        'in_game_rendering_verified': False,
    }


if __name__ == '__main__':
    raise SystemExit('Import and use audit_carbon_registration_namespace with '
                     'owner-local PC roots; no retail files are embedded.')
