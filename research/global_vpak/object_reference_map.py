#!/usr/bin/env python3
"""Read-only NpxE object-range and NrtP source-domain validation.

Run with 3 local GLOBAL.zip paths. No proprietary names or object bytes are emitted.
The pointer-domain interpretation is an inference from data invariants, not a
verified Carbon runtime loading algorithm or executable patch.
"""
import argparse
import bisect
import json
import struct
from pathlib import Path


def align8(value):
    return (value + 7) & ~7


def pointer_groups(block):
    """NrtP rows split by the observed two group markers, with an all-zero tail."""
    if len(block) < 32 or block[:4] != b'NrtP' or len(block) % 16:
        raise ValueError('Invalid NrtP block')
    if struct.unpack_from('<I', block, 4)[0] != len(block):
        raise ValueError('NrtP size mismatch')
    rows = []
    cursor = 8
    while cursor + 12 <= len(block):
        row = struct.unpack_from('<3I', block, cursor)
        if row == (0, 0, 0):
            if any(block[cursor:]):
                raise ValueError('Nonzero NrtP padding')
            break
        rows.append(row)
        cursor += 12
    else:
        raise ValueError('Missing NrtP zero terminator')
    if not rows or rows[0] != (0, 0x10002, 0):
        raise ValueError('Missing NrtP group A marker')
    dividers = [i for i, row in enumerate(rows) if row == (0, 2, 0)]
    if len(dividers) != 1 or dividers[0] == 0:
        raise ValueError('Missing or duplicated NrtP group B marker')
    cut = dividers[0]
    a, b = rows[1:cut], rows[cut + 1:]
    if any(kind != 0x10003 or off % 4 for off, kind, dest in a + b):
        raise ValueError('Bad NrtP relocation kind or alignment')
    return a, b


def inspect_record(record):
    """Identify bounded NtaD spans and associate every group B reference.

    Input shape matches chunk_layout.parse_chunks(): {'text': bytes, 'chunks':
    {'sreV': bytes, 'NpeD': bytes, 'NrtS': bytes, 'NtaD': bytes,
     'NpxE': bytes, 'NrtP': bytes}}.
    """
    text = record['text']
    chunks = record['chunks']
    required = ('sreV', 'NpeD', 'NrtS', 'NtaD', 'NpxE', 'NrtP')
    if any(tag not in chunks for tag in required):
        raise ValueError('Missing one or more required chunks')
    if len(text) < 8 or text[:4] != b'ErtS':
        raise ValueError('Missing ErtS')
    string_end = struct.unpack_from('<I', text, 4)[0]
    if not 8 <= string_end <= len(text):
        raise ValueError('Bad ErtS bounds')
    prefix = b''.join(chunks[k] for k in ('sreV', 'NpeD', 'NrtS'))
    data = chunks['NtaD']
    if data[:4] != b'NtaD' or struct.unpack_from('<I', data, 4)[0] != len(data):
        raise ValueError('Invalid NtaD header')
    aux_data = prefix + data
    data_start = len(prefix) + 8
    exports = chunks['NpxE']
    if len(exports) < 32 or exports[:4] != b'NpxE' or len(exports) % 16:
        raise ValueError('Invalid NpxE')
    if struct.unpack_from('<I', exports, 4)[0] != len(exports):
        raise ValueError('NpxE size mismatch')
    count = struct.unpack_from('<I', exports, 8)[0]
    if count < 1 or len(exports) != 16 + count * 16:
        raise ValueError('NpxE count mismatch')
    entries = list(struct.iter_unpack('<4I', exports[16:]))
    begins = []
    for index, (word0, length, offset, marker) in enumerate(entries):
        if word0 != 0x8E112EB7 or not length or length % 4 or offset % 8:
            raise ValueError('Invalid NpxE entry signature or alignment')
        if not data_start <= offset < offset + length <= len(aux_data):
            raise ValueError('NpxE object outside NtaD')
        if (index == count - 1) != (marker == 0):
            raise ValueError('NpxE terminal marker placement')
        if index == 0 and offset != data_start:
            raise ValueError('First NpxE object does not start after NtaD header')
        if index:
            prev_offset, prev_len = begins[-1]
            if offset != align8(prev_offset + prev_len):
                raise ValueError('Broken NpxE object chain')
            if any(aux_data[prev_offset + prev_len:offset]):
                raise ValueError('Nonzero inter-object padding')
        begins.append((offset, length))
    tail = begins[-1][0] + begins[-1][1]
    if any(aux_data[tail:]):
        raise ValueError('Nonzero NtaD trailing padding')

    group_a, group_b = pointer_groups(chunks['NrtP'])
    stats = {'objects': count, 'terminal_nonempty_objects': 1,
             'group_a': len(group_a), 'group_b': len(group_b),
             'group_a_string_targets': 0, 'group_a_post_string_self_next': 0,
             'group_b_string_targets': 0, 'group_b_post_string_targets': 0,
             'objects_with_group_b_references': 0, 'object_padding_bytes': len(aux_data) - data_start - sum(length for _, length in begins)}
    a_sources = set()
    for source, _, target in group_a:
        if source in a_sources:
            raise ValueError('Repeated group A source slot')
        a_sources.add(source)
        if not (string_end <= source and source + 4 <= len(text) and
                8 <= target < len(text) and text[source:source + 4] == b'\0' * 4):
            raise ValueError('Group A pointer site or target out of text bounds/nonzero')
        if target < string_end:
            if text[target - 1] != 0:
                raise ValueError('Group A string target not NUL-delimited')
            stats['group_a_string_targets'] += 1
        else:
            if target != source + 4:
                raise ValueError('Unsupported group A post-ErtS target')
            stats['group_a_post_string_self_next'] += 1

    offsets = [off for off, _ in begins]
    objects_used = set()
    b_sources = set()
    for source, _, target in group_b:
        if source in b_sources:
            raise ValueError('Repeated group B source slot')
        b_sources.add(source)
        if not (data_start <= source and source + 4 <= len(aux_data) and
                8 <= target < len(text) and aux_data[source:source + 4] == b'\0' * 4):
            raise ValueError('Group B source site or target out of bounds/nonzero')
        obj = bisect.bisect_right(offsets, source) - 1
        if obj < 0 or source + 4 > begins[obj][0] + begins[obj][1]:
            raise ValueError('Group B source does not belong to any NpxE object')
        objects_used.add(obj)
        if target < string_end:
            if text[target - 1] != 0:
                raise ValueError('Group B string target not NUL-delimited')
            stats['group_b_string_targets'] += 1
        else:
            stats['group_b_post_string_targets'] += 1
    stats['objects_with_group_b_references'] = len(objects_used)
    if len(objects_used) != count:
        raise ValueError('One or more NpxE object ranges has no group B references')
    return stats


def audit_records(records):
    result = {'records': 0}
    for record in records:
        stats = inspect_record(record)
        result['records'] += 1
        for key, value in stats.items():
            result[key] = result.get(key, 0) + value
    return result


def analyze(carbon_pc, carbon_ps2, undercover_ps2):
    from audit import read_selected_members
    from chunk_layout import parse_chunks
    pc, _ = read_selected_members(carbon_pc)
    carbon, _ = read_selected_members(carbon_ps2)
    uc, _ = read_selected_members(undercover_ps2)
    result = {}
    for files, member, label in (
        (pc, 'GAMEPLAY.BIN', 'carbon_pc_active'),
        (pc, 'GAMEPLAY.BAK', 'carbon_pc_backup'),
        (carbon, 'GAMEPLAY.BIN', 'carbon_ps2'),
        (uc, 'GAMEPLAY.BIN', 'undercover_ps2'),
    ):
        if member not in files:
            raise ValueError(f'Missing source: {label}/{member}')
        result[label] = audit_records(parse_chunks(files[member]))
    result['limits'] = ('Read-only structural evidence for NpxE object spans and NrtP '
                        'source/target domains; object fields, relocations in memory, '
                        'and PC loader compatibility remain unverified.')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('carbon_pc_zip', type=Path)
    parser.add_argument('carbon_ps2_zip', type=Path)
    parser.add_argument('undercover_ps2_zip', type=Path)
    args = parser.parse_args()
    print(json.dumps(analyze(args.carbon_pc_zip, args.carbon_ps2_zip, args.undercover_ps2_zip), indent=2))


if __name__ == '__main__':
    main()
