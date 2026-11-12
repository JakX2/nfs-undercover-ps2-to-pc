#!/usr/bin/env python3
"""Read-only five-platform cross-reference of visibility, streams and RB scenes.

Joins *candidate* signed section IDs between original 0x34110 streaming rows,
0x34152 boundaries, 0x34153 drivable visibility records and validated RB
0x80034100 scenery roots. Produces only aggregate counts and a short list of
changed row identifiers. An unmatched ID is not automatically an invalid link:
LOD/overlay/permanent loading and other file classes are not yet decoded.
No game content is written, converted, or emitted.
"""
import argparse
import json
from pathlib import Path
import zipfile

from rb_scenery_graph_census import read_rb
from scenery_visibility_anchor import find_unique_chunk
from section_identity_anchor import parse_rows
from track_bundle_probe import SplitZip
from visibility_edge_bridge import (BOUNDARY_ID, DRIVABLE_ID,
                                    parse_boundaries, parse_drivable_sections,
                                    visibility_children)

MAX_BUNDLE = 8 * 1024 * 1024


def coverage(stream_rows, boundary_rows, drivable_rows, scene_ids=()):
    """Compare bounded IDs, not location, semantics, or runtime graph validity."""
    streams = set(stream_rows)
    boundaries = set(boundary_rows)
    drivable = set(drivable_rows)
    scenes = set(scene_ids)
    if scenes - streams:
        raise ValueError('Validated scene has no parent streaming row')
    refs = [ref for row in drivable_rows.values() for ref in row['refs']]
    if any(not 0 < ref < 32768 for ref in refs):
        raise ValueError('Invalid visibility target ID')
    targets = set(refs)
    return {
        'stream_rows': len(streams),
        'boundary_rows': len(boundaries),
        'drivable_rows': len(drivable),
        'visibility_reference_occurrences': len(refs),
        'visibility_unique_targets': len(targets),
        'drivable_ids_in_stream_rows': len(drivable & streams),
        'drivable_ids_in_boundaries': len(drivable & boundaries),
        'boundary_ids_in_stream_rows': len(boundaries & streams),
        'boundary_ids_in_visibility_targets': len(boundaries & targets),
        'drivable_ids_in_visibility_targets': len(drivable & targets),
        'visibility_unique_targets_in_stream_rows': len(targets & streams),
        'visibility_unique_targets_outside_stream_rows': len(targets - streams),
        'visibility_unique_targets_in_boundaries': len(targets & boundaries),
        'validated_scene_roots': len(scenes),
        'scene_roots_in_visibility_targets': len(scenes & targets),
        'scene_roots_not_in_visibility_targets': len(scenes - targets),
        'scene_roots_in_boundaries': len(scenes & boundaries),
        'scene_roots_in_drivable_records': len(scenes & drivable),
    }


def is_subsequence(candidate, parent):
    """True if candidate's order is preserved within parent, no false padding."""
    iterator = iter(parent)
    return all(any(x == wanted for x in iterator) for wanted in candidate)


def compare_drivable(left, right):
    """Examine changes without assuming that either platform is canonical."""
    shared = sorted(left.keys() & right.keys())
    changed = [sec for sec in shared if left[sec] != right[sec]]
    added_only = []
    extra_left = extra_right = 0
    for sec in changed:
        a = left[sec]['refs']
        b = right[sec]['refs']
        extra_left += len(set(a) - set(b))
        extra_right += len(set(b) - set(a))
        if (len(a) > len(b) and is_subsequence(b, a)
                and left[sec]['capacity'] - right[sec]['capacity'] == len(a) - len(b)
                and left[sec]['most'] - right[sec]['most'] == len(a) - len(b)):
            added_only.append(sec)
    all_left = {n for r in left.values() for n in r['refs']}
    all_right = {n for r in right.values() for n in r['refs']}
    return {
        'shared_drivable_section_ids': len(shared),
        'rows_only_left': len(left) - len(shared),
        'rows_only_right': len(right) - len(shared),
        'different_row_count': len(changed),
        'different_row_ids': changed[:32],
        'different_row_id_list_truncated': len(changed) > 32,
        'changed_rows_with_left_only_order_preserving_insertions': len(added_only),
        'left_only_reference_occurrences_in_changed_rows': extra_left,
        'right_only_reference_occurrences_in_changed_rows': extra_right,
        'same_global_target_id_set': all_left == all_right,
    }


def compare_stream_inventory(left_rows, right_rows, left_drivable, right_drivable):
    """Count platform-specific stream rows, explicitly including visibility targets."""
    left = set(left_rows)
    right = set(right_rows)
    a_targets = {x for r in left_drivable.values() for x in r['refs']}
    b_targets = {x for r in right_drivable.values() for x in r['refs']}
    only_left, only_right = left - right, right - left
    return {
        'shared_stream_section_ids': len(left & right),
        'only_left_stream_ids': len(only_left),
        'only_right_stream_ids': len(only_right),
        'left_only_stream_ids_in_left_visibility_targets': len(only_left & a_targets),
        'right_only_stream_ids_in_right_visibility_targets': len(only_right & b_targets),
        'same_global_visibility_target_id_set': a_targets == b_targets,
    }


def read_small(source, stem, region):
    member = f'TRACKS/{stem}{region}.BUN'
    streamed = f'TRACKS/STREAM{stem}{region}.BUN'
    if isinstance(source, SplitZip):
        bun = source.read(member, limit=MAX_BUNDLE)
        stream_size = source.entries[streamed][4]
    else:
        with zipfile.ZipFile(source) as archive:
            if archive.getinfo(member).file_size > MAX_BUNDLE:
                raise ValueError('Small bundle exceeds 8 MiB bound')
            bun = archive.read(member)
            stream_size = archive.getinfo(streamed).file_size
    rows = parse_rows(find_unique_chunk(bun, 0x34110)[8:], stream_size)
    vis = visibility_children(bun)
    return (rows, parse_boundaries(vis[BOUNDARY_ID]),
            parse_drivable_sections(vis[DRIVABLE_ID]))


def analyze(pc_volumes, carbon_ps2_zip, carbon_wii_volumes, uc_ps2_zip, uc_wii_zip):
    sources = {
        'carbon_pc': (SplitZip(pc_volumes), 'L5'),
        'carbon_ps2': (Path(carbon_ps2_zip), 'L5'),
        'carbon_wii': (SplitZip(carbon_wii_volumes), 'L5'),
        'undercover_ps2': (Path(uc_ps2_zip), 'L2'),
        'undercover_wii': (Path(uc_wii_zip), 'L2'),
    }
    result = {}
    drivable = {}
    streams_by_source = {}
    for label, (archive, stem) in sources.items():
        for region in ('RA', 'RB'):
            streams, boundaries, records = read_small(archive, stem, region)
            validated_scenes = set()
            if region == 'RB':
                validated_scenes = set(read_rb(archive, stem)[0])
            result[f'{label}_{region}'] = coverage(
                streams, boundaries, records, validated_scenes)
            drivable[label, region] = records
            streams_by_source[label, region] = streams
    comparisons = {}
    stream_comparisons = {}
    pairs = (('carbon_pc', 'carbon_ps2'), ('carbon_pc', 'carbon_wii'),
             ('carbon_wii', 'carbon_ps2'), ('undercover_wii', 'undercover_ps2'))
    for left, right in pairs:
        for region in ('RA', 'RB'):
            comparisons[f'{left}_vs_{right}_{region}'] = compare_drivable(
                drivable[left, region], drivable[right, region])
            stream_comparisons[f'{left}_vs_{right}_{region}'] = compare_stream_inventory(
                streams_by_source[left, region], streams_by_source[right, region],
                drivable[left, region], drivable[right, region])
    return {
        'sources': result, 'drivable_record_comparisons': comparisons,
        'stream_inventory_comparisons': stream_comparisons,
        'limitations': (
            'Cross references compare numeric candidate section IDs only, not '
            'semantically resolved PC runtime pointers. RB scenery roots are '
            'the bounded validated finds from the prior scanner. RA scene '
            'roots are not scanned. Visibility IDs absent from one streaming '
            'table may legitimately refer to other resource classes or load '
            'paths. Z0 and other unlisted scene roots are not proven unused. '
            'No collision, textures, gameplay, or playable PC map is shown.'),
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--pc-volumes', nargs='+', type=Path, required=True)
    p.add_argument('--carbon-ps2-zip', type=Path, required=True)
    p.add_argument('--carbon-wii-volumes', nargs='+', type=Path, required=True)
    p.add_argument('--undercover-ps2-zip', type=Path, required=True)
    p.add_argument('--undercover-wii-zip', type=Path, required=True)
    a = p.parse_args()
    print(json.dumps(analyze(a.pc_volumes, a.carbon_ps2_zip, a.carbon_wii_volumes,
                             a.undercover_ps2_zip, a.undercover_wii_zip), indent=2))


if __name__ == '__main__':
    main()
