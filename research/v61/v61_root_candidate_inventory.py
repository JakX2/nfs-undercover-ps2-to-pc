#!/usr/bin/env python3
"""V61: hash-guarded read-only discovery of possible 0x80034100 ROOT frames.

Complements V43's top-level chunk walker and V60's offset-supplied index audit.
A byte-pattern match, even when its direct-child TLV framing parses, is NOT
source authentication, a Carbon loader proof, or permission to patch a BUN.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import mmap
from pathlib import Path
import re
import struct

ROOT = 0x80034100
SCENE = 0x34101
INSTANCE = 0x34103
MAX_ROOT_BYTES = 64 * 1024 * 1024
MAX_CHILDREN = 4096
MAX_CANDIDATES = 10000
MAX_ANCHOR_SHORTLIST = 64
SHA64 = re.compile(r'^[a-fA-F0-9]{64}$')


class InventoryError(ValueError):
    pass


def checked_int(value, label, low=0, high=None):
    if type(value) is not int or value < low or (high is not None and value > high):
        raise InventoryError(f'{label}: invalid integer or out of bounds')
    return value


def validate_sha(value):
    if not isinstance(value, str) or not SHA64.fullmatch(value):
        raise InventoryError('expected_file_sha256 must be 64 hex digits')
    return value.lower()


def endian_format(value):
    if value == 'little':
        return '<'
    if value == 'big':
        return '>'
    raise InventoryError('endian must be little or big')


def file_sha256(handle):
    """Hash an open file descriptor once, without loading it into memory."""
    h = hashlib.sha256()
    handle.seek(0)
    for buf in iter(lambda: handle.read(4 * 1024 * 1024), b''):
        h.update(buf)
    return h.hexdigest()


def direct_child_inventory(data, start, end, e):
    """Strict *candidate* direct-TLV parse; never a native Carbon schema claim.

    The stream might have a different format. Such roots must be classified as
    framed-but-unparsed, not automatically declared corrupt.
    """
    at = start + 8
    children = []
    seen = set()
    while at < end:
        if at + 8 > end or len(children) >= MAX_CHILDREN:
            return None
        tag, size = struct.unpack_from(e + 'II', data, at)
        at += 8
        if tag & 0x80000000 or tag in seen or size > end - at:
            return None
        seen.add(tag)
        children.append((tag, size, at - start))
        at += size
    if not children or at != end:
        return None
    return children


def _sha_range(data, start, end):
    # memoryview avoids copying a complete large scenery root.
    view = memoryview(data)[start:end]
    try:
        return hashlib.sha256(view).hexdigest()
    finally:
        view.release()


def scan_frames(data, *, endian='little', start_offset=0, stop_offset=None,
                max_candidates=2048):
    """Inspect bounded byte-pattern hits; search window limits ROOT *starts*.

    A framed root may extend past stop_offset as long as the whole root is in
    the authenticated file. Scan completeness is always explicitly reported.
    """
    e = endian_format(endian)
    n = len(data)
    checked_int(start_offset, 'start_offset', high=n)
    if stop_offset is None:
        stop_offset = n
    checked_int(stop_offset, 'stop_offset', low=start_offset, high=n)
    checked_int(max_candidates, 'max_candidates', low=1, high=MAX_CANDIDATES)
    marker = struct.pack(e + 'I', ROOT)
    results = []
    marker_hits = 0
    bad_frame = 0
    bad_tlv = 0
    at = start_offset
    truncated = False
    # bytes.find(end=...) requires the *whole marker* to fit. Search an
    # expanded end, then filter by marker start, so a narrow one-byte start
    # window still includes a marker that begins within it.
    search_end = min(n, stop_offset + len(marker) - 1)
    while (pos := data.find(marker, at, search_end)) != -1:
        if pos >= stop_offset:
            break
        marker_hits += 1
        at = pos + 1  # Do not skip embedded or overlapping candidates.
        if pos + 8 > n:
            bad_frame += 1
            continue
        size = struct.unpack_from(e + 'I', data, pos + 4)[0]
        if size < 8 or size > MAX_ROOT_BYTES - 8 or size > n - pos - 8:
            bad_frame += 1
            continue
        end = pos + 8 + size
        children = direct_child_inventory(data, pos, end, e)
        if children is None:
            bad_tlv += 1
            # We do not promote a frame with unknown children into a V60 anchor.
            # A different real PC chunk grammar is still possible.
            continue
        tags = {tag: length for tag, length, _ in children}
        scene_like = SCENE in tags and INSTANCE in tags and tags[SCENE] >= 4
        if len(results) >= max_candidates:
            truncated = True
            break
        results.append({
            'offset': pos,
            'end_exclusive': end,
            'root_bytes': 8 + size,
            'root_sha256': _sha_range(data, pos, end),
            'classification': 'scenery_direct_TLV_candidate' if scene_like
                              else 'other_direct_TLV_candidate',
            'child_count': len(children),
            'children': [{'id': f'0x{tag:05X}', 'bytes': length,
                          'payload_offset_in_root': payload_at}
                         for tag, length, payload_at in children],
        })
    distinct = {}
    for item in results:
        distinct.setdefault(item['root_sha256'], []).append(item['offset'])
    # All anchored source objects must be different byte-for-byte, not merely
    # repeated copies at new positions. Do not invent source authenticity.
    shortlisted = set()
    anchors = []
    for item in results:
        if item['classification'] != 'scenery_direct_TLV_candidate':
            continue
        if item['root_sha256'] in shortlisted:
            continue
        if len(anchors) >= MAX_ANCHOR_SHORTLIST:
            break
        shortlisted.add(item['root_sha256'])
        anchors.append({'label': f'candidate_{len(anchors) + 1:03d}',
                        'offset': item['offset'],
                        'expected_root_sha256': item['root_sha256']})
    # Report overlapping candidates, rather than silently counting both as
    # independent disjoint scenery roots.
    ordered = sorted(results, key=lambda x: (x['offset'], x['end_exclusive']))
    overlapping = []
    furthest_end = -1
    furthest_at = None
    for item in ordered:
        if item['offset'] < furthest_end:
            overlapping.append({'offset': item['offset'],
                                'overlaps_offset': furthest_at})
        if item['end_exclusive'] > furthest_end:
            furthest_end = item['end_exclusive']
            furthest_at = item['offset']
    return {
        'schema': 'v61-readonly-embedded-root-inventory-v1',
        'endian_hypothesis': endian,
        'file_length_bytes': n,
        'search_start_inclusive': start_offset,
        'search_stop_exclusive': stop_offset,
        'candidate_limit': max_candidates,
        'scan_complete_within_window': not truncated,
        'marker_hits_examined': marker_hits,
        'rejected_invalid_frame': bad_frame,
        'rejected_unparsed_direct_TLV': bad_tlv,
        'valid_candidate_root_count': len(results),
        'scenery_direct_TLV_candidate_count': sum(x['classification'] == 'scenery_direct_TLV_candidate' for x in results),
        'distinct_candidate_root_byte_hashes': len(distinct),
        'repeated_identical_candidate_roots': [
            {'root_sha256': h, 'offsets': offsets}
            for h, offsets in sorted(distinct.items()) if len(offsets) > 1
        ],
        'overlapping_root_candidates': overlapping,
        'candidate_roots': results,
        'v60_anchor_shortlist_unverified_provenance': anchors,
        'source_provenance_authenticated_by_file_hash_alone': False,
        'carbon_PC_root_or_master_schema_proven': False,
        'native_loader_or_relocations_verified': False,
        'safe_to_install': False,
        'read_only': True,
        'interpretation': ('Framed direct-TLV candidates only; root offsets and fingerprints are '
                           'not proof of original Carbon source or loader ownership. '
                           'A rejected TLV grammar does not prove a Carbon chunk is invalid.'),
    }


def audit_file(path: Path, *, expected_sha256: str, endian: str,
               start_offset: int = 0, stop_offset: int | None = None,
               max_candidates: int = 2048):
    expected = validate_sha(expected_sha256)
    endian_format(endian)
    if not path.is_file():
        raise InventoryError('source file absent')
    with path.open('rb') as f:
        stat_before = path.stat()
        actual = file_sha256(f)
        if actual != expected:
            raise InventoryError('whole-file SHA-256 mismatch')
        f.seek(0)
        if stat_before.st_size == 0:
            report = scan_frames(b'', endian=endian, start_offset=start_offset,
                                 stop_offset=stop_offset, max_candidates=max_candidates)
        else:
            with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mapped:
                report = scan_frames(mapped, endian=endian, start_offset=start_offset,
                                     stop_offset=stop_offset, max_candidates=max_candidates)
        stat_after = path.stat()
        if (stat_after.st_size != stat_before.st_size or
            stat_after.st_mtime_ns != stat_before.st_mtime_ns):
            raise InventoryError('source size/timestamp changed during read')
    report['source_file_sha256'] = actual
    return report


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--source', required=True, type=Path)
    ap.add_argument('--expected-file-sha256', required=True)
    ap.add_argument('--endian', required=True, choices=['little', 'big'])
    ap.add_argument('--start-offset', type=lambda x: int(x, 0), default=0)
    ap.add_argument('--stop-offset', type=lambda x: int(x, 0))
    ap.add_argument('--max-candidates', type=int, default=2048)
    ap.add_argument('--report', required=True, type=Path)
    a = ap.parse_args()
    if a.report.resolve() == a.source.resolve() or a.report.exists():
        ap.error('refusing to overwrite source or existing report')
    result = audit_file(a.source, expected_sha256=a.expected_file_sha256, endian=a.endian,
                        start_offset=a.start_offset, stop_offset=a.stop_offset,
                        max_candidates=a.max_candidates)
    a.report.parent.mkdir(parents=True, exist_ok=True)
    with a.report.open('x', encoding='utf-8') as out:
        json.dump(result, out, indent=2, sort_keys=True)
        out.write('\n')
    print(f"V61 read-only: {result['valid_candidate_root_count']} candidate roots, "
          f"{result['scenery_direct_TLV_candidate_count']} scenery-shaped; "
          f"report: {a.report}")


if __name__ == '__main__':
    main()