#!/usr/bin/env python3
"""Validate GAMEPLAY NpeD paired resource keys; compare named records.

Read-only and stdlib-only. Requires local game archives; does not extract assets.
Hashes are reported as raw 32-bit identifiers, not as a verified hash algorithm.
"""
import argparse
import json
import struct
from pathlib import Path

from audit import read_selected_members
from chunk_layout import parse_chunks


def parse_resource_key(chunk):
    """Decode a strictly bounded NpeD pair of NUL-terminated ASCII names."""
    if len(chunk) < 32 or chunk[:4] != b'NpeD':
        raise ValueError('Missing or truncated NpeD')
    size, count, hash_a, hash_b, reserved, name_length = struct.unpack_from('<6I', chunk, 4)
    if size != len(chunk) or size % 16 != 0 or count != 2 or reserved != 0:
        raise ValueError('Invalid NpeD header')
    if not (5 <= name_length <= (size - 28) // 2):
        raise ValueError('Invalid NpeD filename size')
    if size != (28 + 2 * name_length + 15) // 16 * 16:
        raise ValueError('Unexpected NpeD padding length')
    a = chunk[28:28 + name_length]
    b = chunk[28 + name_length:28 + 2 * name_length]
    tail = chunk[28 + 2 * name_length:]
    if not (a.endswith(b'.vlt\0') and b.endswith(b'.bin\0')):
        raise ValueError('Expected .vlt and .bin resource pair')
    if any(tail) or any(byte < 32 or byte > 126 for byte in a[:-1] + b[:-1]):
        raise ValueError('Non-ASCII name or nonzero NpeD padding')
    base_a = a[:-5]
    base_b = b[:-5]
    if not base_a or base_a != base_b or b'\0' in base_a:
        raise ValueError('Mismatched or empty NpeD basename')
    return {'base': base_a.decode('ascii'), 'hash_pair': (hash_a, hash_b)}


def index_resources(records):
    """Reject duplicate resource basenames before matching indexes."""
    seen = {}
    for index, record in enumerate(records):
        key = parse_resource_key(record['chunks']['NpeD'])
        if key['base'] in seen:
            raise ValueError('Duplicate NpeD resource key')
        seen[key['base']] = {'index': index, 'hash_pair': key['hash_pair'],
                             'npxe_entries': (len(record['chunks']['NpxE']) - 16) // 16}
    return seen


def compare_resources(left, right):
    both = sorted(set(left) & set(right))
    details = both if len(both) <= 10 else []  # avoid dumping large source-name inventories
    return {'shared_resource_pairs': len(both),
            'same_index_pairs': sum(left[name]['index'] == right[name]['index'] for name in both),
            'matching_hash_pairs': sum(left[name]['hash_pair'] == right[name]['hash_pair'] for name in both),
            'shared': [{'name': name, 'left_index': left[name]['index'],
                        'right_index': right[name]['index'],
                        'hash_pair_matches': left[name]['hash_pair'] == right[name]['hash_pair'],
                        'left_npxe_entries': left[name]['npxe_entries'],
                        'right_npxe_entries': right[name]['npxe_entries']} for name in details]}


def analyze(pc_path, ps2_path, uc_path):
    blobs = [read_selected_members(path)[0] for path in (pc_path, ps2_path, uc_path)]
    source = {}
    for label, archive, member in (
        ('carbon_pc_active', blobs[0], 'GAMEPLAY.BIN'),
        ('carbon_pc_backup', blobs[0], 'GAMEPLAY.BAK'),
        ('carbon_ps2', blobs[1], 'GAMEPLAY.BIN'),
        ('undercover_ps2', blobs[2], 'GAMEPLAY.BIN'),
    ):
        if member not in archive:
            raise ValueError(f'Missing {label}/{member}')
        source[label] = index_resources(parse_chunks(archive[member]))
    return {'resource_counts': {name: len(keys) for name, keys in source.items()},
            'pc_backup_vs_carbon_ps2': compare_resources(source['carbon_pc_backup'], source['carbon_ps2']),
            'carbon_ps2_vs_undercover_ps2': compare_resources(source['carbon_ps2'], source['undercover_ps2']),
            'limits': 'Resource-name/hash matches only; VLT record payloads and runtime compatibility are not established.'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for field in ('carbon_pc_zip', 'carbon_ps2_zip', 'undercover_ps2_zip'):
        p.add_argument(field, type=Path)
    a = p.parse_args()
    print(json.dumps(analyze(a.carbon_pc_zip, a.carbon_ps2_zip, a.undercover_ps2_zip), indent=2))


if __name__ == '__main__':
    main()
