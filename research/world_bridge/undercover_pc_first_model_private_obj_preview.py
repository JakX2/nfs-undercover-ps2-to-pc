#!/usr/bin/env python3
"""V11 source-only, owner-private Undercover PS2 -> PC-shaped mesh -> OBJ witness.

Default is READ ONLY. Optional explicit local .obj export is not a Carbon patch.
The original model identity, geometry, texture pixels and names are never logged.
"""
import argparse
import json
import math
from pathlib import Path
import zipfile

MAX_VERTICES = 250_000
MAX_FACES = 150_000
MAX_OBJ = 16 * 1024 * 1024


def private_obj_text(xyz, uv, faces, labels):
    """Standard OBJ made from PC-native parser readback, no original identifiers."""
    if (not isinstance(xyz, (tuple, list)) or not isinstance(uv, (tuple, list)) or
            not isinstance(faces, (tuple, list)) or not isinstance(labels, (tuple, list)) or
            not 3 <= len(xyz) <= MAX_VERTICES or len(uv) != len(xyz) or
            not 1 <= len(faces) <= MAX_FACES or len(labels) != len(faces)):
        raise ValueError('Invalid private PC model vertex/face collection')
    parts = ['# PRIVATE ORIGINAL-OWNER OFFLINE MODEL PREVIEW',
             '# Not a Carbon resource bundle or game installation',
             'o UC_PS2_PC_Shaped_Preview']
    for position, texcoord in zip(xyz, uv):
        if (not isinstance(position, (tuple, list)) or len(position) != 3 or
                not isinstance(texcoord, (tuple, list)) or len(texcoord) != 2 or
                any(type(x) not in (int, float) or not math.isfinite(x) or abs(x) > 1e8
                    for x in (*position, *texcoord))):
            raise ValueError('Nonfinite or malformed PC vertex/UV')
        parts.append('v ' + ' '.join(format(x, '.9g') for x in position))
    for _, texcoord in zip(xyz, uv):
        parts.append('vt ' + ' '.join(format(x, '.9g') for x in texcoord))
    last_material = None
    for face, label in zip(faces, labels):
        if (not isinstance(face, (tuple, list)) or len(face) != 3 or
                any(type(i) is not int or i < 0 or i >= len(xyz) for i in face) or
                len(set(face)) != 3 or type(label) is not int or not 0 <= label <= 126):
            raise ValueError('Invalid PC face/material index')
        if label != last_material:
            parts.append(f'usemtl UC_MATERIAL_{label:03d}')
            last_material = label
        parts.append('f ' + ' '.join(f'{i + 1}/{i + 1}' for i in face))
    obj = '\n'.join(parts) + '\n'
    if len(obj.encode('utf-8')) > MAX_OBJ:
        raise ValueError('Private OBJ exceeds bounded export size')
    return obj


def write_private_obj(path, contents):
    """Only explicit path, no overwrite, no original game installation dirs."""
    p = Path(path).absolute()
    if (not isinstance(contents, str) or not contents.startswith('# PRIVATE ORIGINAL-OWNER') or
            len(contents.encode('utf-8')) > MAX_OBJ or p.suffix.lower() != '.obj'):
        raise ValueError('Invalid private OBJ export')
    if any(q.is_symlink() for q in (p, *p.parents)):
        raise ValueError('Private output or parent is symlinked')
    if any(s.casefold() in ('carbonpc', 'carbonps2', 'ucps2', 'tracks') for s in p.parts):
        raise ValueError('Private preview must be outside extracted game directories')
    if not p.parent.is_dir() or p.exists():
        raise ValueError('Private output parent missing or existing output (no overwrite)')
    with p.open('x', encoding='utf-8', newline='\n') as out:
        out.write(contents)
    return True


def audit_original_private_obj(archive_path, section=241, min_triangles=128,
                               max_triangles=1024, private_obj=None, write_private=False):
    if type(write_private) is not bool or (private_obj is not None) != write_private:
        raise ValueError('Private export requires --write-private-obj AND a destination')
    if (type(section) is not int or section not in (241, 3401) or
            type(min_triangles) is not int or type(max_triangles) is not int or
            not 1 <= min_triangles <= max_triangles <= MAX_FACES):
        raise ValueError('Unsafe private source section or model triangle window')
    if not Path(archive_path).is_file():
        raise ValueError('Owner original archive missing')
    from undercover_ra_texture_presence_gate import (
        _owner_archive, _fingerprint, _member_bytes,
        parse_stream_section_rows, MAX_SMALL_BUN, MAX_RB_STREAM)
    from undercover_pc_partition_registry_gate import source_partition_roots, _source_scene_detail_hashes
    from undercover_pc_first_model_gate import rank_candidates, verify_single_model
    from texture_metadata_pixel_bridge import parse_pack
    from texture_pixel_base_alignment import aligned_pixel_array
    from triangle_corner_uv_control import ps2_geometry_attributes, pc_geometry_attributes
    from undercover_pc_geometry_bridge import convert_decoded_ps2_model, verify_ps2_to_pc_faces
    from geometry_hash_control import read_chunks, SOLID_ROOT

    original = _owner_archive(archive_path)
    snapshot = _fingerprint(original)
    with zipfile.ZipFile(original) as z:
        bun = _member_bytes(z, 'TRACKS/L2RB.BUN', MAX_SMALL_BUN)
        stream = _member_bytes(z, 'TRACKS/STREAML2RB.BUN', MAX_RB_STREAM)
    _, rows = parse_stream_section_rows(bun, len(stream))
    if section not in rows:
        raise ValueError('Original source section missing')
    data = stream[slice(*rows[section])]
    texture = parse_pack(data, 'ps2')['records']
    aligned_pixel_array(data, texture)
    packs = source_partition_roots(data)
    scene_refs = _source_scene_detail_hashes(data)
    eligible, scan = rank_candidates(packs, set(texture), scene_refs, section,
                                     min_triangles=min_triangles, max_triangles=max_triangles)
    if not eligible:
        raise ValueError('No unambiguous fully image-backed source scenery model')
    chosen = eligible[0]
    bound = verify_single_model(chosen, data)
    original_xyz, original_uv, original_faces, original_labels = ps2_geometry_attributes(chosen['platform'])
    geometry, _ = convert_decoded_ps2_model(chosen['identity'], chosen['table'],
        original_xyz, original_uv, original_faces, original_labels, chosen['header'])
    solids = [payload for cid, payload in read_chunks(geometry, 16, len(geometry)) if cid == SOLID_ROOT]
    if len(solids) != 1:
        raise ValueError('Expected exactly one native PC eSolid')
    parts = list(read_chunks(solids[0], 0, len(solids[0])))
    platform = list(read_chunks(parts[-1][1], 0, len(parts[-1][1])))
    xyz, uv, faces, labels = pc_geometry_attributes(platform)
    verify_ps2_to_pc_faces(original_xyz, original_uv, original_faces, original_labels,
                           xyz, uv, faces, labels)
    preview = private_obj_text(xyz, uv, faces, labels)
    if _fingerprint(original) != snapshot:
        raise ValueError('Owner original archive changed during read-only conversion')
    wrote = False
    if write_private:
        wrote = write_private_obj(private_obj, preview)
    return {
        'scope': 'OFFLINE_OWNER_MODEL_PREVIEW_NOT_CARBON_ENGINE_REGISTRATION',
        'source_section': section,
        'pack_ordinal_zero_based': chosen['pack_ordinal'],
        'model_ordinal_zero_based': chosen['model_ordinal'],
        'source_triangles': len(original_faces),
        'pc_roundtrip_obj_triangles': len(faces),
        'pc_roundtrip_obj_vertex_samples': len(xyz),
        'pc_roundtrip_obj_material_groups': len(set(labels)),
        'original_source_scene_references': chosen['scene_reference_count'],
        'candidate_image_identities': bound['pc_dxt5_image_records'],
        'complete_material_index_coverage': bound['all_source_table_image_identities_backed'],
        'native_pc_triangle_uv_material_witness_passed': True,
        'owner_original_zip_unchanged': True,
        'private_obj_written': wrote,
        'private_obj_bytes': len(preview.encode('utf-8')) if wrote else None,
        'candidate_registration_unverified': True,
        'safe_to_install_in_carbon': False,
        'candidate_scan': scan,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--undercover-ps2-tracks-zip', required=True)
    p.add_argument('--source-section', type=int, choices=(241, 3401), default=241)
    p.add_argument('--min-triangles', type=int, default=128)
    p.add_argument('--max-triangles', type=int, default=1024)
    p.add_argument('--private-obj')
    p.add_argument('--write-private-obj', action='store_true')
    a = p.parse_args()
    result = audit_original_private_obj(a.undercover_ps2_tracks_zip, a.source_section,
        a.min_triangles, a.max_triangles, a.private_obj, a.write_private_obj)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
