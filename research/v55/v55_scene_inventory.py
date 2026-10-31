#!/usr/bin/env python3
"""V55 read-only scenery ROOT inventory for user-supplied binary streams.

Looks for candidate little-endian 0x80034100 ROOTs and checks direct-child
chunk framing, but does NOT authenticate games, decode visibility, identify
Carbon PC's ABI, or write original archives. Only emits hashes/aggregate data.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import mmap
from pathlib import Path
import struct

ROOT = 0x80034100
ROOT_MAGIC = struct.pack('<I', ROOT)
SCENE, INSTANCE, PRECULLER, AUX = (0x34101, 0x34103, 0x34107, 0x3410D)
REQUIRED_WII_CANDIDATE = frozenset((SCENE, INSTANCE, PRECULLER, AUX))
KNOWN_WII_SHA = 'cb08ca728a9b76992aaaefe32b450565ef53246f090cfe296f77d96c5d272e7f'
DEFAULT_MAX_ROOT_BYTES = 64 * 1024 * 1024

class InventoryError(ValueError):
    pass


def digest_stream(path: Path, chunk_size: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(chunk_size), b''):
            h.update(chunk)
    return h.hexdigest()


def inspect_root(data: mmap.mmap, base: int, *, max_root_bytes: int = DEFAULT_MAX_ROOT_BYTES):
    """Return structural inventory, or None for malformed/nonconforming roots.

    Lengths in EA chunk framing here are payload lengths, as validated by the
    exact original Wii fixture. This scanner does not generalize other formats.
    """
    size = len(data)
    if base < 0 or base > size - 8:
        return None
    tag, length = struct.unpack_from('<II', data, base)
    if tag != ROOT or length < 16 or length > max_root_bytes - 8 or length > size - base - 8:
        return None
    end = base + 8 + length
    position = base + 8
    children = {}
    while position < end:
        if position > end - 8:
            return None
        child_tag, child_length = struct.unpack_from('<II', data, position)
        payload_start = position + 8
        if child_tag & 0x80000000 or child_tag in children or child_length > end - payload_start:
            return None
        children[child_tag] = (payload_start - base, child_length)
        position = payload_start + child_length
    # Require a scenery marker and at least one other child to reduce random hits.
    if SCENE not in children or len(children) < 2:
        return None
    # Only digest the bounded candidate root, not the whole source archive.
    root_hash = hashlib.sha256(data[base:end]).hexdigest()
    is_wii_candidate = REQUIRED_WII_CANDIDATE <= children.keys()
    candidate_rows = None
    candidate_blocks = None
    candidate_aux = None
    candidate_consistency = None
    if is_wii_candidate:
        inst_start, inst_bytes = children[INSTANCE]
        pad = (-inst_start) & 15
        candidate_consistency = (
            inst_bytes >= pad and (inst_bytes - pad) % 96 == 0
            and children[PRECULLER][1] > 0 and children[PRECULLER][1] % 128 == 0
            and children[AUX][1] % 32 == 0
        )
        if candidate_consistency:
            candidate_rows = (inst_bytes - pad) // 96
            candidate_blocks = children[PRECULLER][1] // 128
            candidate_aux = children[AUX][1] // 32
    return {
        'offset': base,
        'length_bytes': end - base,
        'sha256': root_hash,
        'source_class': 'known_exact_Wii_RedBuilding_ROOT' if root_hash == KNOWN_WII_SHA else 'unverified_candidate',
        'direct_child_count': len(children),
        'children': [
            {'id': f'0x{tag:05X}', 'offset_in_root': off, 'payload_bytes': n}
            for tag, (off, n) in sorted(children.items())
        ],
        'has_required_Wii_candidate_children': is_wii_candidate,
        'Wii_candidate_stride_consistent': candidate_consistency,
        'candidate_96_byte_instance_rows': candidate_rows,
        'candidate_128_byte_preculler_blocks': candidate_blocks,
        'candidate_32_byte_aux_rows': candidate_aux,
    }


def scan_stream(path: Path, *, expected_sha256: str | None = None,
                max_root_bytes: int = DEFAULT_MAX_ROOT_BYTES,
                max_roots: int = 10000) -> dict:
    if max_root_bytes < 32 or max_root_bytes > 1024 * 1024 * 1024:
        raise InventoryError('max_root_bytes outside 32..1GiB')
    if max_roots < 1 or max_roots > 100000:
        raise InventoryError('max_roots outside 1..100000')
    expected = expected_sha256.lower() if expected_sha256 is not None else None
    if expected is not None and (len(expected) != 64 or any(c not in '0123456789abcdef' for c in expected)):
        raise InventoryError('Expected stream SHA-256 malformed')
    stream_hash = digest_stream(path)
    if expected is not None and stream_hash != expected:
        raise InventoryError('Stream SHA-256 mismatch; refusing structural claims')
    size = path.stat().st_size
    hits = []
    if size >= 8:
        with path.open('rb') as f, mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as data:
            start = 0
            while (at := data.find(ROOT_MAGIC, start)) >= 0:
                root = inspect_root(data, at, max_root_bytes=max_root_bytes)
                if root is not None:
                    hits.append(root)
                    if len(hits) > max_roots:
                        raise InventoryError('Candidate ROOT limit reached; no partial report emitted')
                    # Do not reinterpret a child's bytes as an independent root.
                    start = at + root['length_bytes']
                else:
                    start = at + 1
    return {
        'stream_sha256': stream_hash,
        'stream_size_bytes': size,
        'integrity_hash_guard_applied': expected is not None,
        'source_identity_independently_authenticated': False,
        'root_count': len(hits),
        'roots': hits,
    }


def inventory(paths: list[Path], expected_hashes: list[str] | None = None, **kwargs) -> dict:
    if not paths:
        raise InventoryError('Provide one or more stream paths')
    if expected_hashes is not None and len(paths) != len(expected_hashes):
        raise InventoryError('Provide one expected hash for every supplied archive')
    streams = [scan_stream(p, expected_sha256=expected_hashes[i] if expected_hashes is not None else None,
                           **kwargs) for i, p in enumerate(paths)]
    # No original game payloads, scene coordinates or bytes enter this report.
    for i, s in enumerate(streams):
        s['stream_index'] = i
    roots = [r['sha256'] for s in streams for r in s['roots']]
    counts = Counter(roots)
    return {
        'schema': 'v55-read-only-scenery-root-corpus-inventory-v1',
        'streams': streams,
        'total_root_occurrences': len(roots),
        'distinct_root_sha256s': len(counts),
        'repeated_root_digests': sum(n > 1 for n in counts.values()),
        'candidate_Wii_layout_roots': sum(r['Wii_candidate_stride_consistent'] is True
                                         for s in streams for r in s['roots']),
        'independent_original_scenes_authenticated': False,
        'layout_correspondence_not_semantic_proof': True,
        'Carbon_PC_serialized_layout_verified': False,
        'in_game_verified': False,
        'safe_to_install': False,
        'read_only': True,
        'notes': [
            'Different bytes/hashes do not authenticate source or establish independent original game scenes.',
            'Candidate rows and masks are Wii-layout hypotheses, not decoded culling semantics.',
            'This scanner recognizes only little-endian root and child framing observed in the pinned Wii fixture.',
            'A real Carbon PC archive requires independent schema/loader validation before compatibility claims.',
        ],
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stream', required=True, type=Path, action='append', help='Input BUN/stream, repeatable')
    p.add_argument('--expected-stream-sha256', action='append', default=[],
                   help='Trusted independent archive SHA-256; one per --stream, if used')
    p.add_argument('--report', required=True, type=Path, help='New JSON report, never overwrites')
    p.add_argument('--max-root-bytes', type=int, default=DEFAULT_MAX_ROOT_BYTES)
    p.add_argument('--max-roots', type=int, default=10000)
    a = p.parse_args()
    if a.expected_stream_sha256 and len(a.stream) != len(a.expected_stream_sha256):
        p.error('Expected hashes must cover every stream')
    if a.report.exists() or a.report.resolve() in {x.resolve() for x in a.stream}:
        p.error('Report exists or overlaps input; refusing overwrite')
    result = inventory(a.stream, a.expected_stream_sha256 or None,
                       max_root_bytes=a.max_root_bytes, max_roots=a.max_roots)
    a.report.parent.mkdir(parents=True, exist_ok=True)
    with a.report.open('x', encoding='utf-8') as f:
        json.dump(result, f, indent=2, sort_keys=True)
        f.write('\n')
    print(f'V55 read-only inventory: {result["total_root_occurrences"]} candidates, '
          f'{result["distinct_root_sha256s"]} distinct SHA-256s; report: {a.report}')
    print('No game files changed. No original scene authenticated by this scan alone.')

if __name__ == '__main__':
    main()
