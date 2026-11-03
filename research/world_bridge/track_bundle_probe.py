#!/usr/bin/env python3
"""Read-only track-bundle probe: split Carbon PC ZIP vs Carbon/Undercover PS2.

Output is aggregate structure metadata only. No game bytes are emitted.
Requires the owner's locally supplied original archives and does not alter them.
"""
import argparse
import bisect
import hashlib
import json
from pathlib import Path
import struct
import zipfile
import zlib

MAX_BUNDLE = 8 * 1024 * 1024
PREFIX_BYTES = 4096


def chunk_inventory(data):
    items, position, counts = [], 0, {}
    while position < len(data):
        if position + 8 > len(data):
            raise ValueError('Truncated chunk header')
        cid, length = struct.unpack_from('<II', data, position)
        end = position + 8 + length
        if end > len(data):
            raise ValueError('Chunk payload out of bounds')
        index = counts.get(cid, 0)
        counts[cid] = index + 1
        items.append({'id': f'0x{cid:08x}', 'occurrence': index,
                      'bytes': length, 'digest': hashlib.sha256(data[position:end]).digest()})
        position = end
    return items


def compare_inventories(left, right):
    a = {(row['id'], row['occurrence']): row for row in left}
    b = {(row['id'], row['occurrence']): row for row in right}
    common = a.keys() & b.keys()
    identical = [key for key in common if a[key]['bytes'] == b[key]['bytes']
                 and a[key]['digest'] == b[key]['digest']]
    return {'left_chunks': len(left), 'right_chunks': len(right),
            'same_id_and_occurrence': len(common),
            'identical_chunks': len(identical),
            'identical_nonempty_chunks': sum(a[key]['bytes'] > 0 for key in identical),
            'same_chunks': sorted([{'id': key[0], 'occurrence': key[1], 'bytes': a[key]['bytes']}
                                   for key in identical], key=lambda row: (row['id'], row['occurrence']))}


def common_prefix_len(left, right):
    return next((index for index, (x, y) in enumerate(zip(left, right)) if x != y),
                min(len(left), len(right)))


class SplitZip:
    """Bounded, disk-relative PKZIP reader for .z01/.z02/.../.zip volumes.

    ZIP64, encryption and multi-volume central directories are not supported.
    This is a read-only probe, not a general-purpose ZIP implementation.
    """
    def __init__(self, paths):
        self.paths = [Path(x) for x in paths]
        if len(self.paths) < 2 or any(not p.is_file() for p in self.paths):
            raise ValueError('Provide existing split volumes, in disk order')
        if not self.paths[-1].name.lower().endswith('.zip'):
            raise ValueError('Final split volume must be .zip')
        self.starts = [0]
        for path in self.paths:
            self.starts.append(self.starts[-1] + path.stat().st_size)
        tail = self.paths[-1].read_bytes()
        eocd = tail.rfind(b'PK\x05\x06')
        if eocd < 0 or eocd + 22 > len(tail):
            raise ValueError('Missing ZIP end-of-central-directory')
        _, disk, central_disk, local_count, total, size, offset, comment = struct.unpack_from(
            '<4s4H2IH', tail, eocd)
        if (disk != len(self.paths)-1 or central_disk != disk or total != local_count or
            total >= 65535 or size == 0xffffffff or offset == 0xffffffff or
            eocd + 22 + comment != len(tail) or offset + size != eocd):
            raise ValueError('Unsupported split central directory layout')
        self.entries = {}
        pos = offset
        for _ in range(total):
            if pos + 46 > eocd:
                raise ValueError('Truncated central directory')
            row = struct.unpack_from('<4s6H3I5H2I', tail, pos)
            sig, _made, _need, flags, method, _time, _date, crc, csize, usize, nlen, xlen, clen, local_disk, _iattr, _eattr, local_offset = row
            if (sig != b'PK\x01\x02' or flags & 1 or method not in (0, 8)
                or csize == 0xffffffff or usize == 0xffffffff or local_disk >= len(self.paths)):
                raise ValueError('Unsupported ZIP entry')
            end = pos + 46 + nlen + xlen + clen
            if end > eocd:
                raise ValueError('Central-directory entry exceeds bounds')
            name = tail[pos+46:pos+46+nlen].decode('utf-8')
            if name in self.entries or name.startswith('/') or '..' in Path(name).parts:
                raise ValueError('Duplicate or unsafe ZIP path')
            self.entries[name] = (local_disk, local_offset, method, csize, usize, crc)
            pos = end
        if pos != eocd:
            raise ValueError('Unused central-directory bytes')

    def _read(self, offset, length):
        if length < 0 or offset < 0 or offset + length > self.starts[-1]:
            raise ValueError('Volume read out of bounds')
        fragments = []
        while length:
            disk = bisect.bisect_right(self.starts, offset)-1
            n = min(length, self.starts[disk+1] - offset)
            with self.paths[disk].open('rb') as stream:
                stream.seek(offset-self.starts[disk])
                block = stream.read(n)
            if len(block) != n:
                raise ValueError('Short split-volume read')
            fragments.append(block)
            length -= n
            offset += n
        return b''.join(fragments)

    def read(self, member, limit=MAX_BUNDLE, prefix=False):
        disk, local_offset, method, compressed, usize, crc = self.entries[member]
        if limit < 1:
            raise ValueError('Invalid decompression bound')
        off = self.starts[disk] + local_offset
        header = self._read(off, 30)
        sig, _need, flags, actual_method, _time, _date, _crc, _csize, _usize, nlen, xlen = struct.unpack(
            '<4s5H3I2H', header)
        if sig != b'PK\x03\x04' or flags & 1 or actual_method != method:
            raise ValueError('Invalid split ZIP local header')
        if not prefix and usize > limit:
            raise ValueError('Member exceeds safety limit')
        off += 30 + nlen + xlen
        result = bytearray()
        decoder = zlib.decompressobj(-15) if method == 8 else None
        remaining = compressed
        while remaining:
            take = min(65536, remaining)
            raw = self._read(off, take)
            off += take
            remaining -= take
            if decoder:
                # For prefix mode, cap output from each compressed input chunk.
                data = decoder.decompress(raw, limit-len(result)+1) if prefix else decoder.decompress(raw)
            else:
                data = raw
            result.extend(data)
            if prefix and len(result) >= limit:
                return bytes(result[:limit])
            if len(result) > limit:
                raise ValueError('Excessive decompressed output')
        if decoder:
            result.extend(decoder.flush())
            if not decoder.eof:
                raise ValueError('Truncated DEFLATE stream')
        if not prefix and (len(result) != usize or zlib.crc32(result) != crc):
            raise ValueError('ZIP member failed size/CRC checks')
        return bytes(result[:limit])


def prefix_root(data):
    needle = struct.pack('<I', 0x80134000)
    offset = data.find(needle, 0, min(128, len(data)))
    if offset < 0 or offset+24 > len(data):
        return {'root_found_in_first_128_bytes': False}
    length = struct.unpack_from('<I', data, offset+4)[0]
    return {'root_found_in_first_128_bytes': True, 'root_offset': offset,
            'root_id': '0x80134000', 'root_declared_bytes': length,
            'first_child_candidate_at_plus_16': f"0x{struct.unpack_from('<I', data, offset+16)[0]:08x}"}


def analyze(volumes, carbon_ps2, undercover_ps2):
    pc = SplitZip(volumes)
    records, roots = {}, {}
    for label, source, stem in [
        ('carbon_pc', pc, 'L5'), ('carbon_ps2', carbon_ps2, 'L5'),
        ('undercover_ps2', undercover_ps2, 'L2')]:
        for sector in ('RA', 'RB'):
            member = f'TRACKS/{stem}{sector}.BUN'
            streamed = f'TRACKS/STREAM{stem}{sector}.BUN'
            if label == 'carbon_pc':
                data = source.read(member)
                prefix = source.read(streamed, PREFIX_BYTES, prefix=True)
            else:
                with zipfile.ZipFile(source) as z:
                    if z.getinfo(member).file_size > MAX_BUNDLE:
                        raise ValueError('PS2 bundle exceeds safety limit')
                    data = z.read(member)
                    with z.open(streamed) as handle:
                        prefix = handle.read(PREFIX_BYTES)
            records[label, sector] = (data, chunk_inventory(data))
            roots[label, sector] = prefix_root(prefix)
    comparisons = {}
    for label1, label2, sector in [
        ('carbon_pc', 'carbon_ps2', 'RA'),
        ('carbon_pc', 'carbon_ps2', 'RB'),
        ('carbon_ps2', 'undercover_ps2', 'RA'),
        ('carbon_ps2', 'undercover_ps2', 'RB')]:
        a, ai = records[label1,sector]
        b, bi = records[label2,sector]
        comparisons[f'{label1}_vs_{label2}_{sector}'] = {
            'identical_prefix_bytes': common_prefix_len(a,b),
            **compare_inventories(ai,bi)}
    return {
        'bundles': {f'{label}_{sector}': {'bytes': len(data), 'top_level_chunks': len(chunks)}
                    for (label,sector), (data,chunks) in records.items()},
        'stream_prefixes': {f'{label}_{sector}': value for (label,sector), value in roots.items()},
        'comparisons': comparisons,
        'limits': ('Top-level chunk hashes establish byte identity only. STREAM* '
                   'files were inspected only in the first 4096 uncompressed bytes. '
                   'The +16 child field is an unverified candidate. '
                   'No runtime world loading, navigation or collision has been demonstrated.')}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pc-volumes', nargs='+', type=Path, required=True)
    parser.add_argument('--carbon-ps2-zip', type=Path, required=True)
    parser.add_argument('--undercover-ps2-zip', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(analyze(args.pc_volumes, args.carbon_ps2_zip, args.undercover_ps2_zip),
                     indent=2))


if __name__ == '__main__':
    main()
