#!/usr/bin/env python3
"""Read-only, original-archive-backed model hash and instance-link audit.

Pure in-memory 4-byte name-hash slot promotion is validated against unmodified
Carbon PC/PS2/Wii controls. No source files are changed and no game assets are
exported. Reconstructed MW names are terminology only, not Carbon PC ABI proof.
"""
import argparse
import json
from pathlib import Path
import struct

from rb_scenery_graph_census import read_rb
from track_bundle_probe import SplitZip

INFO_ID = 0x34102
INSTANCE_ID = 0x34103
INFO_SIZE = 72
INSTANCE_SIZE = 96
INSTANCE_INFO_INDEX_OFFSET = 0x54
FIRST_HASH_OFFSET = 0x18
SECOND_HASH_OFFSET = 0x1c
THIRD_HASH_OFFSET = 0x20
HASH_SLOTS = 4
INSTANCE_PREFIX = b'\x11' * 4


def parse_info_records(blob):
    """Return 72-byte candidates, rejecting empty/misaligned records."""
    if not blob or len(blob) % INFO_SIZE:
        raise ValueError('Scenery info bytes are not complete 72-byte records')
    return tuple(blob[i:i+INFO_SIZE] for i in range(0, len(blob), INFO_SIZE))


def validate_instance_links(instances, info_blob):
    """Decode candidate signed 16-bit info indexes at 0x54 in 96-byte entries."""
    ninfos = len(parse_info_records(info_blob))
    if (len(instances) < 4 or instances[:4] != INSTANCE_PREFIX or
            (len(instances) - 4) % INSTANCE_SIZE):
        raise ValueError('Scenery instances do not have the expected 96-byte structure')
    indices = []
    for position in range(4, len(instances), INSTANCE_SIZE):
        value = struct.unpack_from('<h', instances, position + INSTANCE_INFO_INDEX_OFFSET)[0]
        if not 0 <= value < ninfos:
            raise ValueError('Scenery instance references an invalid info index')
        indices.append(value)
    if not indices:
        raise ValueError('Empty instance table')
    return tuple(indices)


def promote_model_hash0(console_info):
    """Copy candidate detail slot 1 to empty slot 0, in RAM only.

    The field match is empirical for these archives. Nonzero source slot 0,
    empty source slot 1, or truncated input cause fail-closed refusal.
    """
    records = parse_info_records(console_info)
    output = bytearray(console_info)
    for i, row in enumerate(records):
        first, second = struct.unpack_from('<II', row, FIRST_HASH_OFFSET)
        if first != 0 or second == 0:
            raise ValueError('Source is not a supported empty-slot0 console info record')
        struct.pack_into('<I', output, i*INFO_SIZE+FIRST_HASH_OFFSET, second)
    return bytes(output)


def summarize_scene(scene):
    c = scene['children']
    rows = parse_info_records(c[INFO_ID])
    indices = validate_instance_links(c[INSTANCE_ID], c[INFO_ID])
    slots = [struct.unpack_from('<4I', r, FIRST_HASH_OFFSET) for r in rows]
    return {'info_records': len(rows), 'instances': len(indices),
            'valid_instance_to_info_links': len(indices),
            'links_equal_to_instance_ordinals': sum(i == v for i,v in enumerate(indices)),
            'distinct_info_targets': len(set(indices)),
            'first_model_hash_nonzero': sum(h[0] != 0 for h in slots),
            'first_equal_second': sum(h[0] == h[1] for h in slots),
            'second_equal_third': sum(h[1] == h[2] for h in slots),
            'fourth_model_hash_nonzero': sum(h[3] != 0 for h in slots)}


def summarize_sources(scenes):
    summed = [summarize_scene(s) for s in scenes.values()]
    keys = list(summed[0])
    return {'validated_scene_roots': len(summed),
            **{k: sum(r[k] for r in summed) for k in keys}}


def compare_pc_to_console(pc_scenes, console_scenes):
    overlap = pc_scenes.keys() & console_scenes.keys()
    count_equal = 0
    exact_before, exact_after, count_after = 0, 0, 0
    infos_matched = 0
    for section in overlap:
        target = pc_scenes[section]['children'][INFO_ID]
        donor = console_scenes[section]['children'][INFO_ID]
        if len(target) != len(donor):
            continue
        count_equal += 1
        exact_before += target == donor
        promoted = promote_model_hash0(donor)
        if target == promoted:
            exact_after += 1
            count_after += len(promoted)//INFO_SIZE
        infos_matched += len(promoted)//INFO_SIZE
    return {'shared_scenery_roots':len(overlap),
            'same_number_of_info_records':count_equal,
            'exact_info_payloads_without_promotion':exact_before,
            'exact_info_payloads_after_slot0_copy':exact_after,
            'exact_info_records_after_slot0_copy':count_after,
            'all_records_in_equal_size_scenes':infos_matched}


def analyze(pc_volumes, carbon_ps2, carbon_wii_volumes, uc_ps2, uc_wii):
    archives = {
        'carbon_pc': (SplitZip(pc_volumes), 'L5'),
        'carbon_ps2': (Path(carbon_ps2), 'L5'),
        'carbon_wii': (SplitZip(carbon_wii_volumes), 'L5'),
        'undercover_ps2': (Path(uc_ps2), 'L2'),
        'undercover_wii': (Path(uc_wii), 'L2'),
    }
    scenes = {name: read_rb(archive, stem)[0]
              for name,(archive,stem) in archives.items()}
    sources = {name: summarize_sources(data) for name,data in scenes.items()}
    for label in ('carbon_ps2', 'carbon_wii', 'undercover_ps2', 'undercover_wii'):
        for scene in scenes[label].values():
            promote_model_hash0(scene['children'][INFO_ID])
    return {
        'sources': sources,
        'controls': {
            'carbon_pc_vs_carbon_ps2':compare_pc_to_console(scenes['carbon_pc'], scenes['carbon_ps2']),
            'carbon_pc_vs_carbon_wii':compare_pc_to_console(scenes['carbon_pc'], scenes['carbon_wii']),
        },
        'scope':('RB scenery roots only; slot0 promotion is a pure in-memory '
                 '4-byte model-hash candidate and not a game-file writer. '
                 'No Carbon PC runtime model resolution, texture, geometry, '
                 'collision or converted Undercover scene validated.'),
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--pc-volumes',nargs='+',type=Path,required=True)
    p.add_argument('--carbon-ps2-zip',type=Path,required=True)
    p.add_argument('--carbon-wii-volumes',nargs='+',type=Path,required=True)
    p.add_argument('--undercover-ps2-zip',type=Path,required=True)
    p.add_argument('--undercover-wii-zip',type=Path,required=True)
    a=p.parse_args()
    print(json.dumps(analyze(a.pc_volumes,a.carbon_ps2_zip,a.carbon_wii_volumes,
                             a.undercover_ps2_zip,a.undercover_wii_zip),indent=2))

if __name__=='__main__':main()
