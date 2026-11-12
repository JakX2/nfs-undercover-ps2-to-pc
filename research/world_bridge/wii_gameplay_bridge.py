#!/usr/bin/env python3
"""Read-only VPAK gameplay comparison across Wii, PS2 and Carbon PC.

Wii .7z archives must be extracted privately first; no source asset is emitted.
Header index fields are little endian on all platforms. Wii record chunk tags
are reversed and their length/entry fields use big endian.
"""
import argparse
import json
import struct
import zipfile
from pathlib import Path

TAGS = ('sreV', 'NpeD', 'NrtS', 'NtaD', 'NpxE', 'NrtP')


def parse_gameplay(data, wii=False):
    if len(data) < 16 or data[:4] != b'VPAK':
        raise ValueError('Missing VPAK header')
    count, index_end, _unknown = struct.unpack_from('<III', data, 4)
    if not 0 < count <= 4096 or not 16 + 20 * count <= index_end <= len(data):
        raise ValueError('Invalid VPAK index')
    indices = [struct.unpack_from('<5I', data, 16 + 20 * i) for i in range(count)]
    result = []
    fmt = '>' if wii else '<'
    previous_end = index_end
    for i, index in enumerate(indices):
        _cum, text_size, aux_size, text_start, aux_start = index
        following = indices[i + 1][3] if i + 1 < count else len(data)
        if not (previous_end <= text_start <= aux_start <= following <= len(data)
                and 8 <= text_size <= aux_start - text_start
                and 128 <= aux_size <= following - aux_start):
            raise ValueError(f'Invalid record bounds at index {i}')
        text = data[text_start:aux_start]
        if text[:4] != (b'StrE' if wii else b'ErtS'):
            raise ValueError(f'Invalid record string header at index {i}')
        (pool_end,) = struct.unpack_from(fmt + 'I', text, 4)
        if not 8 <= pool_end <= text_size:
            raise ValueError(f'Invalid ErtS pool size at index {i}')
        pos, chunks = aux_start, {}
        for tag in TAGS:
            if pos + 8 > aux_start + aux_size:
                raise ValueError(f'Truncated chunk at index {i}')
            magic, length = struct.unpack_from(fmt + '4sI', data, pos)
            expected = tag.encode('ascii')[::-1] if wii else tag.encode('ascii')
            if magic != expected or length < 16 or length % 16 or pos + length > aux_start + aux_size:
                raise ValueError(f'Invalid {tag} chunk at index {i}')
            chunks[tag] = data[pos:pos+length]
            pos += length
        if pos != aux_start + aux_size:
            raise ValueError(f'Unparsed auxiliary bytes at index {i}')
        npxe = chunks['NpxE']
        export_count = struct.unpack_from(fmt + 'I', npxe, 8)[0]
        if len(npxe) != 16 + export_count * 16:
            raise ValueError(f'Invalid NpxE entry count at index {i}')
        entries = tuple(struct.iter_unpack(fmt + '4I', npxe[16:]))
        pointer_rows = []
        ptr = chunks['NrtP']
        for offset in range(8, len(ptr) - 11, 12):
            source, kind, dest = struct.unpack_from(fmt + '3I', ptr, offset)
            if (source, kind, dest) == (0, 0, 0):
                if any(ptr[offset:]):
                    raise ValueError(f'Nonzero NrtP padding at index {i}')
                break
            # The middle field is a pair of 16-bit values, not a single
            # endian-independent 32-bit enumeration.
            if wii:
                kind = ((kind & 0xffff) << 16) | (kind >> 16)
            if kind not in (0x00010002, 0x00010003, 2):
                raise ValueError(f'Unknown NrtP marker at index {i}')
            pointer_rows.append((source, kind, dest))
        else:
            raise ValueError(f'Missing NrtP terminator at index {i}')
        name_tail = chunks['NpeD'][28:].rstrip(b'\0')
        result.append({'index': index, 'pool': text[8:pool_end],
                       'name_tail': name_tail, 'exports': entries,
                       'references': tuple(pointer_rows)})
        previous_end = pos
    return result


def compare_records(left, right):
    n = min(len(left), len(right))
    result = {'left_records': len(left), 'right_records': len(right),
              'compared_records': n}
    fields = ('index', 'pool', 'name_tail', 'exports', 'references')
    for field in fields:
        equal = [i for i in range(n) if left[i][field] == right[i][field]]
        result[f'{field}_matching_records'] = len(equal)
        result[f'{field}_different_indices'] = [i for i in range(n) if i not in set(equal)]
    result['shared_export_entries_numerically_equal'] = sum(
        a == b for i in range(n) for a, b in zip(left[i]['exports'], right[i]['exports']))
    result['left_export_entries'] = sum(len(r['exports']) for r in left)
    result['right_export_entries'] = sum(len(r['exports']) for r in right)
    return result


def read_zip_member(path, member):
    with zipfile.ZipFile(path) as z:
        choices = [n for n in z.namelist() if n.casefold() == member.casefold()]
        if len(choices) != 1:
            raise ValueError(f'Expected one {member} in {path}')
        return z.read(choices[0])


def analyze(uc_wii, carbon_wii, uc_ps2_zip, carbon_ps2_zip, carbon_pc_zip):
    records = {
        'uc_wii': parse_gameplay(Path(uc_wii).read_bytes(), True),
        'carbon_wii': parse_gameplay(Path(carbon_wii).read_bytes(), True),
        'uc_ps2': parse_gameplay(read_zip_member(uc_ps2_zip, 'GLOBAL/GAMEPLAY.BIN')),
        'carbon_ps2': parse_gameplay(read_zip_member(carbon_ps2_zip, 'GLOBAL/GAMEPLAY.BIN')),
        'carbon_pc_backup': parse_gameplay(read_zip_member(carbon_pc_zip, 'GLOBAL/GAMEPLAY.BAK')),
    }
    return {
        'undercover_wii_vs_ps2': compare_records(records['uc_wii'], records['uc_ps2']),
        'carbon_wii_vs_ps2': compare_records(records['carbon_wii'], records['carbon_ps2']),
        'carbon_wii_vs_pc_backup': compare_records(records['carbon_wii'], records['carbon_pc_backup']),
        'limits': ('Numeric table equality is not proof of payload byte equality, '
                   'loader ABI compatibility, gameplay semantics or a working port.'),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for arg in ('uc_wii_gameplay', 'carbon_wii_gameplay', 'uc_ps2_global_zip',
                'carbon_ps2_global_zip', 'carbon_pc_global_zip'):
        parser.add_argument(arg, type=Path)
    a = parser.parse_args()
    print(json.dumps(analyze(a.uc_wii_gameplay, a.carbon_wii_gameplay,
                             a.uc_ps2_global_zip, a.carbon_ps2_global_zip,
                             a.carbon_pc_global_zip), indent=2))


if __name__ == '__main__':
    main()
