#!/usr/bin/env python3
"""Read-only NrtP two-section table validator for GAMEPLAY VPAK records.

Section names denote observed marker values, not proven pointer semantics.
No game data or per-entry offsets are exported by the CLI.
"""
import argparse
import json
import struct
from pathlib import Path

from audit import read_selected_members
from chunk_layout import parse_chunks


GROUP_HEADER_A = (0, 0x00010002, 0)
GROUP_HEADER_B = (0, 0x00000002, 0)
ENTRY_KIND = 0x00010003
ZERO_ROW = (0, 0, 0)


def parse_pointer_sections(data, first_region_length):
    """Parse 12-byte triples from NrtP offset +8 up to all-zero trailing padding.

    Only values in the first marker section are empirically bounded against the
    record's separate pre-auxiliary text region. Other fields remain uninterpreted.
    """
    if len(data) < 32 or data[:4] != b'NrtP' or len(data) % 16:
        raise ValueError('Truncated or unaligned NrtP block')
    (size,) = struct.unpack_from('<I', data, 4)
    if size != len(data):
        raise ValueError('Mismatched NrtP size')
    if first_region_length < 0:
        raise ValueError('Invalid first-region size')
    rows = []
    stop = None
    for position in range(8, len(data) - 11, 12):
        row = struct.unpack_from('<3I', data, position)
        if row == ZERO_ROW:
            stop = position
            break
        rows.append(row)
    if stop is None or len(data) - stop not in (12, 16, 20, 24) or any(data[stop:]):
        raise ValueError('Missing zero sentinel or nonzero NrtP padding')
    if not rows or rows[0] != GROUP_HEADER_A:
        raise ValueError('Missing initial NrtP section marker')
    group_b_indices = [i for i, row in enumerate(rows) if row == GROUP_HEADER_B]
    if len(group_b_indices) != 1 or group_b_indices[0] == 0:
        raise ValueError('Missing or duplicated second NrtP section marker')
    split = group_b_indices[0]
    first, second = rows[1:split], rows[split + 1:]
    for section, entries in enumerate((first, second)):
        for source_offset, kind, target_value in entries:
            if kind != ENTRY_KIND or source_offset % 4:
                raise ValueError('Bad NrtP entry kind or source alignment')
            if section == 0 and target_value >= first_region_length:
                raise ValueError('First-section NrtP target outside text region')
    return first, second


def inspect_pointer_sections(records):
    summary = {
        'records': len(records),
        'initial_marker_count': 0,
        'second_marker_count': 0,
        'first_section_entries': 0,
        'second_section_entries': 0,
        'first_section_targets_after_erts': 0,
        'first_section_sources_beyond_ntad': 0,
        'second_section_sources_beyond_ntad': 0,
        'second_section_targets_beyond_ntad': 0,
    }
    for record in records:
        chunks = record['chunks']
        first, second = parse_pointer_sections(chunks['NrtP'], len(record['text']))
        summary['initial_marker_count'] += 1
        summary['second_marker_count'] += 1
        summary['first_section_entries'] += len(first)
        summary['second_section_entries'] += len(second)
        erts_end = struct.unpack_from('<I', record['text'], 4)[0]
        ntad_len = len(chunks['NtaD'])
        summary['first_section_targets_after_erts'] += sum(target >= erts_end for _, _, target in first)
        summary['first_section_sources_beyond_ntad'] += sum(src + 4 > ntad_len for src, _, _ in first)
        summary['second_section_sources_beyond_ntad'] += sum(src + 4 > ntad_len for src, _, _ in second)
        summary['second_section_targets_beyond_ntad'] += sum(target + 4 > ntad_len for _, _, target in second)
    return summary


def analyze(pc_zip, carbon_ps2_zip, undercover_ps2_zip):
    archives = [read_selected_members(path)[0] for path in (pc_zip, carbon_ps2_zip, undercover_ps2_zip)]
    results = {}
    for label, archive, member in (
        ('carbon_pc_active', archives[0], 'GAMEPLAY.BIN'),
        ('carbon_pc_backup', archives[0], 'GAMEPLAY.BAK'),
        ('carbon_ps2', archives[1], 'GAMEPLAY.BIN'),
        ('undercover_ps2', archives[2], 'GAMEPLAY.BIN'),
    ):
        if member not in archive:
            raise ValueError(f'Missing {label}/{member}')
        results[label] = inspect_pointer_sections(parse_chunks(archive[member]))
    results['limits'] = ('NrtP markers and bounded first-section targets only. '
                         'NtaD offset bases, pointer relocation semantics and event coordinates remain unknown.')
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for field in ('carbon_pc_zip', 'carbon_ps2_zip', 'undercover_ps2_zip'):
        parser.add_argument(field, type=Path)
    args = parser.parse_args()
    print(json.dumps(analyze(args.carbon_pc_zip, args.carbon_ps2_zip, args.undercover_ps2_zip), indent=2))


if __name__ == '__main__':
    main()
