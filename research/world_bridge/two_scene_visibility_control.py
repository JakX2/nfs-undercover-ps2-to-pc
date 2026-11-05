#!/usr/bin/env python3
"""Read-only two-scene Carbon PC/PS2 world linkage control.

Only source-pinned, structurally validated RB scene roots are eligible. Require
matching PS2/PC scenery tree+instance bytes; ensure the same signed section ID
is a drivable visibility target in both variants; validate 96-byte instance to
72-byte info indexes; reproduce exact PC info bytes with console hash0<-hash1.
No geometry pack, texture or runtime model resolution is assumed or claimed.
"""
import argparse
import json
from pathlib import Path

from rb_scenery_graph_census import read_rb
from scenery_model_hash_bridge import (
    INFO_ID, INSTANCE_ID, INFO_SIZE, parse_info_records,
    promote_model_hash0, validate_instance_links,
)
from track_bundle_probe import SplitZip
from visibility_stream_join import read_small

TREE_ID = 0x34105
Z0_ID = 2600


def visible_targets(drivable_rows):
    return {ref for record in drivable_rows.values() for ref in record['refs']}


def select_controls(pc_scenes, ps2_scenes, pc_rows, ps2_rows,
                    pc_targets, ps2_targets, count=2):
    """Select independently anchored PC/PS2 controls; fail on contradictions.

    Input scenes must originate from the bounded, validated RB scene parser.
    A qualifying non-Z0 scene is present in both streaming tables and in both
    visibility target graphs, has exactly matching tree and instance chunks,
    and an exact PS2-to-PC one-field info table reconstruction.
    """
    if type(count) is not int or not 2 <= count <= 32:
        raise ValueError('Choose between two and 32 distinct control scenes')
    shared = set(pc_scenes) & set(ps2_scenes)
    selected = []
    for section in sorted(shared):
        if section == Z0_ID or section not in pc_rows or section not in ps2_rows:
            continue
        if section not in pc_targets or section not in ps2_targets:
            continue
        pc = pc_scenes[section]['children']
        ps2 = ps2_scenes[section]['children']
        if pc[INSTANCE_ID] != ps2[INSTANCE_ID] or pc[TREE_ID] != ps2[TREE_ID]:
            continue
        pc_info, ps2_info = pc[INFO_ID], ps2[INFO_ID]
        if len(pc_info) != len(ps2_info):
            continue
        pc_links = validate_instance_links(pc[INSTANCE_ID], pc_info)
        ps2_links = validate_instance_links(ps2[INSTANCE_ID], ps2_info)
        if pc_links != ps2_links:
            raise ValueError('Equal instance bytes have inconsistent info indexes')
        # Fail closed if candidate controls differ in any field besides the
        # validated four-byte model hash slot, rather than skipping anomalies.
        expected_pc = promote_model_hash0(ps2_info)
        if pc_info != expected_pc:
            raise ValueError('Candidate Carbon scene differs beyond hash-slot promotion')
        info_records = parse_info_records(pc_info)
        if not info_records or any(int.from_bytes(r[24:28], 'little') == 0 for r in info_records):
            raise ValueError('Candidate PC scene has an empty first model-hash slot')
        selected.append({'section_id': section,
                         'scenery_instances': len(pc_links),
                         'model_info_records': len(info_records),
                         'distinct_info_references': len(set(pc_links)),
                         'same_tree_and_instance_payloads': True,
                         'in_pc_and_ps2_visibility_targets': True,
                         'pc_info_exact_after_hash_slot_promotion': True})
    if len(selected) < count:
        raise ValueError('Fewer than two independently linked scene controls')
    return {'qualifying_controls': len(selected),
            'selected_controls': selected[:count],
            'unselected_qualifying_controls': len(selected)-count,
            'total_selected_instances': sum(row['scenery_instances'] for row in selected[:count]),
            'total_selected_info_records': sum(row['model_info_records'] for row in selected[:count])}


def analyze(pc_volumes, carbon_ps2_zip, control_count=2):
    pc = SplitZip(pc_volumes)
    ps2 = Path(carbon_ps2_zip)
    pc_scenes, _ = read_rb(pc, 'L5')
    ps2_scenes, _ = read_rb(ps2, 'L5')
    pc_rows, _pc_boundaries, pc_drivable = read_small(pc, 'L5', 'RB')
    ps2_rows, _ps2_boundaries, ps2_drivable = read_small(ps2, 'L5', 'RB')
    return {
        'control': select_controls(pc_scenes, ps2_scenes, pc_rows, ps2_rows,
                                   visible_targets(pc_drivable),
                                   visible_targets(ps2_drivable), control_count),
        'scope': ('Original Carbon PC vs Carbon PS2 RB controls only. '
                  'Numeric stream/visibility IDs and matched scenery-instance, '
                  'tree and per-info model-hash metadata; no source geometry '
                  'resource lookup, Carbon PC runtime or Undercover import verified.'),
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--pc-volumes', nargs='+', type=Path, required=True)
    p.add_argument('--carbon-ps2-zip', type=Path, required=True)
    p.add_argument('--control-count', type=int, default=2)
    a = p.parse_args()
    print(json.dumps(analyze(a.pc_volumes, a.carbon_ps2_zip, a.control_count), indent=2))


if __name__ == '__main__':
    main()
