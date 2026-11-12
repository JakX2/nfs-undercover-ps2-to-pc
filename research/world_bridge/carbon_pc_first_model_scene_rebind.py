#!/usr/bin/env python3
"""Source-backed PC scenery-info *one slot* model rebind, in memory only.

Carbon PC original RB scenery root: 0x80034100, with 0x34102 72-byte
info records and 0x34103 96-byte instance records. Existing empirical
Carbon PC sections use primary detail hash 0x18 == secondary hash 0x1c.
Rebind these exact two fields of ONE already referenced original scene
info record to the single indexed eSolid ID in a V20 texture-first private
.pcchunk candidate. Preserve original placement, instance indices,
auxiliary records, other model references and all unknown bytes exactly.

This is NOT a complete Carbon streaming section: no 0x372xx control,
visibility, global model registration, collision or renderer ABI is made.
Original game files remain private and are never changed by this module.
"""
import argparse
import json
from pathlib import Path
import struct

from carbon_pc_bun_chunk_stream_gate import (
    MAX_BUN_BYTES, inspect_carbon_pc_chunk_stream,
)
from carbon_pc_first_model_stream_assembly import (
    build_private_pc_first_model_stream,
)
from carbon_pc_native_postscene_layout_gate import (
    MAX_SCENE, SCENE, SCENE_CHILDREN, _children, scene_profile,
)
from carbon_pc_resource_namespace_gate import _model_and_materials
from scenery_model_hash_bridge import (
    FIRST_HASH_OFFSET, INFO_ID, INFO_SIZE, INSTANCE_ID,
    SECOND_HASH_OFFSET, validate_instance_links,
)


def rebind_one_pc_scene_model(scene_root, private_pcchunk, info_index):
    """Return private patched original scene bytes and a redacted audit.

    Input scene must be a complete original-format Carbon PC root.
    Input candidate is validated against the actual strict V20
    texture-before-geometry first-model resource assembly, not just its
    model-name/hash value. Full unknown scene data is byte-preserved.
    """
    if (type(scene_root) is not bytes or not 80 <= len(scene_root) <= MAX_SCENE
            or type(private_pcchunk) is not bytes
            or not 80 <= len(private_pcchunk) <= MAX_BUN_BYTES
            or type(info_index) is not int or info_index < 0):
        raise ValueError('Invalid original scene/candidate/index dimensions')

    original_profile = scene_profile(scene_root, 'pc')
    if struct.unpack_from('<I', private_pcchunk)[0] != 0xB3300000:
        raise ValueError('Expected V20 PC texture-first candidate')
    tex_end = struct.unpack_from('<I', private_pcchunk, 4)[0] + 8
    if not 40 <= tex_end <= len(private_pcchunk) - 40:
        raise ValueError('Incomplete private V20 candidate root')
    # Exact two roots and their indexed material closure are validated
    # by the same tested V20 builder. This also refuses old V19 order.
    rebuilt, _ = build_private_pc_first_model_stream(
        private_pcchunk[tex_end:], private_pcchunk[:tex_end])
    if rebuilt != private_pcchunk:
        raise ValueError('Candidate byte layout changed during parsing')
    inventory = inspect_carbon_pc_chunk_stream(private_pcchunk, 'either')
    if (inventory['top_level_frames'] != 2 or
            inventory['native_pc_geometry_roots'] != 1 or
            inventory['native_pc_texture_roots'] != 1):
        raise ValueError('Expected a single complete two-root PC candidate')
    candidate_ids, _ = _model_and_materials(private_pcchunk[tex_end:])
    if len(candidate_ids) != 1:
        raise ValueError('One indexed model required')
    new_hash = next(iter(candidate_ids))

    children = _children(scene_root, 8, len(scene_root))
    if tuple(tag for tag, _, _ in children) != SCENE_CHILDREN:
        raise ValueError('Unexpected Carbon PC scenery children')
    ranges = {tag: (start, end) for tag, start, end in children}
    ia, ib = ranges[INFO_ID]
    index_count = (ib - ia) // INFO_SIZE
    if info_index >= index_count:
        raise ValueError('Scenery info index outside original table')
    xa, xb = ranges[INSTANCE_ID]
    references = validate_instance_links(scene_root[xa:xb], scene_root[ia:ib])
    count = references.count(info_index)
    if not count:
        raise ValueError('Selected Carbon scene info has no instance reference')

    hashes = tuple(struct.unpack_from('<II', scene_root, ia + i*INFO_SIZE +
                                      FIRST_HASH_OFFSET)
                   for i in range(index_count))
    at = ia + info_index*INFO_SIZE + FIRST_HASH_OFFSET
    old_hash, old_second = hashes[info_index]
    if old_hash == new_hash or old_hash != old_second:
        raise ValueError('Selected Carbon original detail hash cannot be rebound')
    # Prevent shadowing an existing Carbon scenery-info model in the SAME
    # source section. This does not prove global game resource uniqueness.
    if any(new_hash in pair for i, pair in enumerate(hashes) if i != info_index):
        raise ValueError('Candidate model identity conflicts with another scene info')

    patched = bytearray(scene_root)
    struct.pack_into('<II', patched, at, new_hash, new_hash)
    patched = bytes(patched)

    # Establish strict eight-byte write budget. Do not modify other hash
    # slots, placements, instance links, flags or source opaque bytes.
    if (patched[:at] != scene_root[:at] or
            patched[at+8:] != scene_root[at+8:] or
            len(patched) != len(scene_root)):
        raise ValueError('PC scene patch changed bytes outside two hash fields')
    modified_profile = scene_profile(patched, 'pc')
    if (modified_profile != original_profile or
            struct.unpack_from('<II', patched, at) != (new_hash, new_hash)):
        raise ValueError('Patched Carbon scene no longer matches source profile')
    ib2 = ranges[INFO_ID][1]
    xa2, xb2 = ranges[INSTANCE_ID]
    if (validate_instance_links(patched[xa2:xb2], patched[ia:ib2]) !=
            references):
        raise ValueError('Original Carbon scenery instance link changed')

    unmodified_ids = {a for i, (a, b) in enumerate(hashes)
                      if i != info_index}
    return patched, {
        'scope': 'PRIVATE_PC_SCENE_ONE_INFO_MODEL_REBIND_NOT_RUNTIME',
        'original_scene_root_validated_as_pc': True,
        'private_v20_two_root_candidate_reparsed': True,
        'scene_info_records': index_count,
        'scene_instance_records': len(references),
        'selected_info_instances_preserved': count,
        'scene_info_entries_rebound': 1,
        'hash_fields_rebound': 2,
        'changed_byte_window_bytes': 8,
        'all_original_scene_bytes_outside_two_fields_preserved': True,
        'original_instance_indices_unchanged': True,
        'other_scene_model_ids_still_referenced': len(unmodified_ids),
        'all_other_native_model_references_resolved': False,
        'native_pc_scenery_root_reparsed': True,
        'native_pc_postscene_controls_generated': False,
        'native_carbon_stream_sector_complete': False,
        'owner_original_carbon_asset_provenance_verified': False,
        'pc_external_loader_registration_verified': False,
        'undercover_model_rendered_in_game': False,
        'private_ids_coordinates_and_scene_bytes_disclosed': False,
        'game_files_modified': False,
    }


def _private_file(path, suffix, upper_bound):
    p = Path(path).absolute()
    if (p.suffix.casefold() != suffix or
            any(part.is_symlink() for part in (p, *p.parents)) or
            not p.is_file() or not 80 <= p.stat().st_size <= upper_bound):
        raise ValueError('Unsafe or missing owner-private source file')
    return p


def _snapshot(path):
    s = path.stat()
    return s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns


def inspect_private_scene_and_candidate(scene_path, candidate_path, info_index):
    """Owner-local read-only CLI: emits *only* aggregate data, no edited file."""
    scene = _private_file(scene_path, '.pcscene', MAX_SCENE)
    candidate = _private_file(candidate_path, '.pcchunk', MAX_BUN_BYTES)
    if scene == candidate or scene.samefile(candidate):
        raise ValueError('Scene and candidate source files must differ')
    before = (_snapshot(scene), _snapshot(candidate))
    output, audit = rebind_one_pc_scene_model(
        scene.read_bytes(), candidate.read_bytes(), info_index)
    if before != (_snapshot(scene), _snapshot(candidate)):
        raise ValueError('Private source changed during read-only audit')
    # The edited scene remains in memory only. Do not print its contents.
    if len(output) != scene.stat().st_size:
        raise ValueError('Unexpected private scene length change')
    return audit


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--carbon-pc-scene-root', required=True,
                        help='owner-private extracted native PC scenery root in .pcscene')
    parser.add_argument('--private-candidate', required=True,
                        help='owner-local V20 texture-first .pcchunk candidate')
    parser.add_argument('--info-index', type=int, required=True,
                        help='existing Carbon scene info row ordinal to rebind')
    args = parser.parse_args()
    print(json.dumps(inspect_private_scene_and_candidate(
        args.carbon_pc_scene_root, args.private_candidate,
        args.info_index), indent=2))


if __name__ == '__main__':
    main()
