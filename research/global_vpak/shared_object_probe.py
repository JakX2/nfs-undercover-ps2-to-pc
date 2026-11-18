#!/usr/bin/env python3
"""Read-only, resource-name-scoped NpxE object identity and reference comparison.

Only aggregates are emitted: no original names (except hard-coded three shared
resource keys), object bytes, object identifiers, or asset-derived hashes.
NpxE word3 is an empirical identity candidate, not a decoded hash algorithm.
"""
import argparse
import bisect
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import struct

from audit import read_selected_members
from chunk_layout import parse_chunks
from object_reference_map import inspect_record, pointer_groups

SHARED_KEYS = ('gpcore', 'race_bin_challenge', 'race_bin_quickrace')


def resource_name(npe):
    """Strict paired .vlt/.bin name extraction from verified NpeD layout."""
    if len(npe) < 32 or npe[:4] != b'NpeD' or struct.unpack_from('<I', npe, 4)[0] != len(npe):
        raise ValueError('Invalid NpeD header')
    count, h1, h2, reserved, n = struct.unpack_from('<5I', npe, 8)
    if count != 2 or reserved or n < 6 or 28 + 2*n > len(npe):
        raise ValueError('Invalid NpeD name metadata')
    a = npe[28:28+n]
    b = npe[28+n:28+2*n]
    if not (a.endswith(b'.vlt\0') and b.endswith(b'.bin\0') and a[:-5] == b[:-5]):
        raise ValueError('Mismatched NpeD names')
    if not a[:-5] or any(ch < 32 or ch > 126 for ch in a[:-5]) or any(npe[28+2*n:]):
        raise ValueError('Invalid NpeD basename or padding')
    return a[:-5].decode('ascii')


def project_record(record):
    """Describe validated objects by local layout and target *content*, in RAM."""
    inspect_record(record)
    text = record['text']
    chunks = record['chunks']
    strings_end = struct.unpack_from('<I', text, 4)[0]
    aux = b''.join(chunks[tag] for tag in ('sreV', 'NpeD', 'NrtS', 'NtaD'))
    entries = list(struct.iter_unpack('<4I', chunks['NpxE'][16:]))
    starts = [entry[2] for entry in entries]
    _, group_b = pointer_groups(chunks['NrtP'])
    refs = defaultdict(list)
    for source, _kind, target in group_b:
        index = bisect.bisect_right(starts, source) - 1
        if not 0 <= index < len(entries):
            raise ValueError('Group B source outside NpxE index')
        relative = source - starts[index]
        if target < strings_end:
            end = text.find(b'\0', target, strings_end)
            if end < 0:
                raise ValueError('Unterminated NrtP named target')
            dest = ('string', text[target:end])
        else:
            dest = ('structured', target - strings_end)
        refs[index].append((relative, dest))
    objects = {}
    all_hashes = Counter()
    for index, (_constant, size, offset, identity) in enumerate(entries):
        payload_hash = hashlib.sha256(aux[offset:offset+size]).digest()
        all_hashes[payload_hash] += 1
        target_list = sorted(refs[index])
        layout = (size, tuple((off, kind) for off, (kind, _value) in target_list))
        names = tuple((off, value) for off, (kind, value) in target_list if kind == 'string')
        structured = tuple((off, value) for off, (kind, value) in target_list if kind == 'structured')
        if identity:
            if identity in objects:
                raise ValueError('Duplicate nonzero NpxE word3 within one resource')
            objects[identity] = (index, payload_hash, layout, names, structured)
        elif index != len(entries)-1:
            raise ValueError('Zero NpxE word3 before terminal entry')
    return {'count': len(entries), 'by_id': objects, 'payload_hash_multiset': all_hashes}


def compare(a, b):
    common = a['by_id'].keys() & b['by_id'].keys()
    result = {
        'left_objects': a['count'], 'right_objects': b['count'],
        'shared_nonzero_word3': len(common),
        'same_index_when_word3_shared': 0,
        'identical_payload_when_word3_shared': 0,
        'same_reference_layout_when_word3_shared': 0,
        'same_named_targets_when_word3_shared': 0,
        'same_named_targets_and_layout_when_word3_shared': 0,
        'same_structured_target_offsets_when_word3_shared': 0,
        'shared_word3_with_structured_targets': 0,
        'same_structured_offsets_for_shared_word3_with_structured_targets': 0,
        'identical_payload_multiset_count_ignoring_word3': sum((a['payload_hash_multiset'] & b['payload_hash_multiset']).values()),
    }
    for key in common:
        left, right = a['by_id'][key], b['by_id'][key]
        index1, payload1, layout1, names1, structured1 = left
        index2, payload2, layout2, names2, structured2 = right
        result['same_index_when_word3_shared'] += index1 == index2
        result['identical_payload_when_word3_shared'] += payload1 == payload2
        result['same_reference_layout_when_word3_shared'] += layout1 == layout2
        result['same_named_targets_when_word3_shared'] += names1 == names2
        result['same_named_targets_and_layout_when_word3_shared'] += names1 == names2 and layout1 == layout2
        result['same_structured_target_offsets_when_word3_shared'] += structured1 == structured2
        has_structured = bool(structured1 or structured2)
        result['shared_word3_with_structured_targets'] += has_structured
        result['same_structured_offsets_for_shared_word3_with_structured_targets'] += has_structured and structured1 == structured2
    return result


def load_sources(pc_zip, carbon_zip, uc_zip):
    inputs = [
        ('carbon_pc_backup', pc_zip, 'GAMEPLAY.BAK'),
        ('carbon_pc_active', pc_zip, 'GAMEPLAY.BIN'),
        ('carbon_ps2', carbon_zip, 'GAMEPLAY.BIN'),
        ('undercover_ps2', uc_zip, 'GAMEPLAY.BIN'),
    ]
    result = {}
    for label, path, member in inputs:
        archive, _ = read_selected_members(path)
        if member not in archive:
            raise ValueError(f'Missing {member} in {label}')
        matches = {}
        for record in parse_chunks(archive[member]):
            key = resource_name(record['chunks']['NpeD'])
            if key in SHARED_KEYS:
                if key in matches:
                    raise ValueError('Duplicate target resource')
                matches[key] = project_record(record)
        if set(matches) != set(SHARED_KEYS):
            raise ValueError(f'Missing named resource in {label}')
        result[label] = matches
    return result


def audit(pc_zip, carbon_zip, uc_zip):
    sources = load_sources(pc_zip, carbon_zip, uc_zip)
    report = {}
    for resource in SHARED_KEYS:
        report[resource] = {
            'carbon_pc_backup_vs_carbon_ps2': compare(sources['carbon_pc_backup'][resource], sources['carbon_ps2'][resource]),
            'undercover_ps2_vs_carbon_ps2': compare(sources['undercover_ps2'][resource], sources['carbon_ps2'][resource]),
            'carbon_pc_active_vs_backup': compare(sources['carbon_pc_active'][resource], sources['carbon_pc_backup'][resource]),
        }
    report['limitations'] = ('Nonzero NpxE word3 is an identity candidate only; raw object equality excludes NrtP target tables. '
                             'Structured target offsets can move even when payload bytes match. Not a port or verified loader.')
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('carbon_pc_zip', 'carbon_ps2_zip', 'undercover_ps2_zip'):
        p.add_argument(name, type=Path)
    args = p.parse_args()
    print(json.dumps(audit(args.carbon_pc_zip, args.carbon_ps2_zip, args.undercover_ps2_zip), indent=2))


if __name__ == '__main__':
    main()
