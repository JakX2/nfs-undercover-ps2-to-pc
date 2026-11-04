#!/usr/bin/env python3
"""Fail-closed, *private-only* staged copy for a Carbon PC existing DXT1 slot.

This tool does not patch the game installation, split ZIP, executable, or any
input file. It reads an owner's EXTRACTED L5RB.BUN and STREAML5RB.BUN, chooses
one already-present DXT1 slot by its ordinal (never prints the source hash),
and optionally creates a NEW uncompressed stream copy beside a chosen path.

Output may contain the owner's copyrighted game data. Never commit, publish,
attach, or redistribute it. Offline parser acceptance is NOT runtime proof.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import struct
import tempfile

from pc_texture_header_overlay_gate import overlay_existing_dxt1, _source_image_span
from texture_metadata_pixel_bridge import MAX_SECTION, parse_pack
from texture_pixel_base_alignment import aligned_pixel_array

SECTION_TABLE = 0x34110
ROW_BYTES = 92
MAX_BUNDLE = 8 * 1024 * 1024
MAX_STREAM = 2 * 1024 * 1024 * 1024
READ_SIZE = 1024 * 1024
ALLOWED_SECTIONS = (141, 142)


def section_span(bundle, stream_size, section_id):
    """Validate original 0x34110 rows and return one existing stream range."""
    if (not isinstance(bundle, bytes) or not 8 <= len(bundle) <= MAX_BUNDLE or
            type(stream_size) is not int or not 0 < stream_size <= MAX_STREAM or
            type(section_id) is not int or section_id not in ALLOWED_SECTIONS):
        raise ValueError('Unsafe bundle, stream size or target section')
    signature = struct.pack('<I', SECTION_TABLE)
    positions = []
    cursor = 0
    while True:
        pos = bundle.find(signature, cursor)
        if pos < 0:
            break
        positions.append(pos)
        cursor = pos + len(signature)
    if len(positions) != 1:
        raise ValueError('Missing or ambiguous 0x34110 section table')
    pos = positions[0]
    if pos + 8 > len(bundle):
        raise ValueError('Truncated section-table chunk')
    size = struct.unpack_from('<I', bundle, pos + 4)[0]
    if size < ROW_BYTES or size % ROW_BYTES or pos + 8 + size > len(bundle):
        raise ValueError('Invalid 0x34110 row table bounds')
    found = None
    seen = set()
    nonempty = []
    for at in range(pos + 8, pos + 8 + size, ROW_BYTES):
        identity = struct.unpack_from('<h', bundle, at + 8)[0]
        off, length = struct.unpack_from('<II', bundle, at + 0x14)
        if identity in seen:
            raise ValueError('Duplicate streaming section number')
        seen.add(identity)
        if length:
            if off + length > stream_size:
                raise ValueError('Section row exceeds the supplied stream')
            nonempty.append((off, off + length, identity))
        if identity == section_id:
            if length < 8 or length > MAX_SECTION or off % 2048:
                raise ValueError('Unsafe selected section span')
            found = (off, length)
    if found is None:
        raise ValueError('Requested section is absent')
    start, size = found
    # Another nonempty row must not alias the bytes the private tool will edit.
    for left, right, identity in nonempty:
        if identity != section_id and left < start + size and start < right:
            raise ValueError('Selected section overlaps another stream section')
    return start, size


def _read_regular(path, maximum):
    path = Path(path)
    if path.is_symlink() or not path.is_file() or path.stat().st_size > maximum:
        raise ValueError('Missing, symlinked or oversized source file')
    return path


def _rgb(hex_rgb):
    if (not isinstance(hex_rgb, str) or len(hex_rgb) != 6 or
            any(c not in '0123456789abcdefABCDEF' for c in hex_rgb)):
        raise ValueError('Expected exactly six RGB hexadecimal digits')
    return bytes.fromhex(hex_rgb)


def make_plan(bundle, stream_size, section, section_id, dxt1_slot=0, solid_rgb='FF00FF'):
    """Return private in-memory modification plan; never include source identity.

    *section* must be the original bytes from the validated section-table row.
    Only one existing, image-length-preserving DXT1 span may change.
    """
    offset, size = section_span(bundle, stream_size, section_id)
    if not isinstance(section, bytes) or len(section) != size:
        raise ValueError('Section does not equal selected table-row length')
    if type(dxt1_slot) is not int or dxt1_slot < 0:
        raise ValueError('Invalid DXT1 ordinal')
    parsed = parse_pack(section, 'pc')['records']
    aligned_pixel_array(section, parsed)
    candidates = sorted(h for h, meta in parsed.items() if meta['codec'] == 34)
    if dxt1_slot >= len(candidates):
        raise ValueError('Selected DXT1 ordinal does not exist')
    identity = candidates[dxt1_slot]
    meta = parsed[identity]
    rgb = _rgb(solid_rgb)
    rgba = bytes((*rgb, 255)) * (meta['width'] * meta['height'])
    patched, result = overlay_existing_dxt1(section, identity, rgba)
    left, right = _source_image_span(section, meta)
    if (len(patched) != len(section) or patched[:left] != section[:left] or
            patched[right:] != section[right:] or
            len(patched[left:right]) != meta['image_bytes'] or
            patched[left:right] == section[left:right]):
        raise ValueError('Overlay failed exact, nonempty byte-span isolation')
    # Strict local reversal, proving original exact bytes are available in RAM.
    reverted = bytearray(patched)
    reverted[left:right] = section[left:right]
    if bytes(reverted) != section:
        raise ValueError('In-memory reversal failed')
    return {
        'section_start': offset,
        'section_bytes': size,
        'change_start': offset + left,
        'original_image': section[left:right],
        'replacement_image': patched[left:right],
        'candidate_dxt1_slots': len(candidates),
        'original_texture_count': len(parsed),
        'mip_levels': meta['mip_levels'],
        'changed_bytes': result['changed_image_bytes'],
    }


def _digest_file(path):
    sha = hashlib.sha256()
    with open(path, 'rb') as fp:
        while block := fp.read(READ_SIZE):
            sha.update(block)
    return sha.digest()


def _verify_output(source_path, test_path, change_start, original, replacement):
    """Verify an entire staged stream, not just the edited image slice."""
    size = source_path.stat().st_size
    if test_path.stat().st_size != size or len(original) != len(replacement):
        raise ValueError('Private staged output changed stream length')
    changed = 0
    pos = 0
    with source_path.open('rb') as old, test_path.open('rb') as new:
        while a := old.read(READ_SIZE):
            b = new.read(len(a))
            if len(a) != len(b):
                raise ValueError('Private staged output truncated')
            stop = pos + len(a)
            low = max(pos, change_start)
            high = min(stop, change_start + len(replacement))
            if low < high:
                start = low - change_start
                end = high - change_start
                if (a[low-pos:high-pos] != original[start:end] or
                        b[low-pos:high-pos] != replacement[start:end]):
                    raise ValueError('Wrong DXT1 source/target bytes')
                changed += sum(x != y for x, y in zip(a[low-pos:high-pos], b[low-pos:high-pos]))
                if a[:low-pos] != b[:low-pos] or a[high-pos:] != b[high-pos:]:
                    raise ValueError('Staged file changed data outside the image span')
            elif a != b:
                raise ValueError('Staged file changed unrelated game bytes')
            pos = stop
        if new.read(1) or pos != size:
            raise ValueError('Staged output has trailing bytes')
    if changed == 0:
        raise ValueError('No image bytes changed in staged output')
    return changed


def stage_private_copy(bundle_path, stream_path, section_id, dxt1_slot=0,
                       solid_rgb='FF00FF', private_output=None, write_private_copy=False):
    """Dry-run by default. Explicit write creates a NEW file, never overwrites.

    The input source is never opened in write mode; a temporary file is linked
    into its final private output path only after full byte-isolation checks.
    """
    bundle_path = _read_regular(bundle_path, MAX_BUNDLE)
    stream_path = _read_regular(stream_path, MAX_STREAM)
    size = stream_path.stat().st_size
    with bundle_path.open('rb') as fp:
        bundle = fp.read(MAX_BUNDLE + 1)
    offset, length = section_span(bundle, size, section_id)
    with stream_path.open('rb') as fp:
        fp.seek(offset)
        section = fp.read(length)
    if len(section) != length:
        raise ValueError('Missing selected section bytes')
    plan = make_plan(bundle, size, section, section_id, dxt1_slot, solid_rgb)
    report = {
        'verdict': 'OFFLINE_ONLY_NOT_RUNTIME_VALIDATED',
        'section_id': section_id,
        'dxt1_slots_in_source_section': plan['candidate_dxt1_slots'],
        'changed_image_bytes': plan['changed_bytes'],
        'image_span_bytes': len(plan['replacement_image']),
        'mip_levels': plan['mip_levels'],
        'same_size_and_nonimage_bytes_preserved': True,
        'input_files_left_unchanged': True,
        'private_copy_created': False,
    }
    if not write_private_copy:
        if private_output is not None:
            raise ValueError('Output path requires explicit --write-private-copy')
        return report
    if private_output is None:
        raise ValueError('Explicit private output path is required')
    output = Path(private_output)
    if not output.parent.is_dir() or output.exists() or output.is_symlink():
        raise ValueError('Output must not already exist; parent directory must exist')
    if output.resolve() in (bundle_path.resolve(), stream_path.resolve()):
        raise ValueError('Cannot write over source files')
    initial_stats = (stream_path.stat().st_size, stream_path.stat().st_mtime_ns)
    original_digest = _digest_file(stream_path)
    tmp = None
    try:
        fd, tmp = tempfile.mkstemp(prefix='.private-carbon-test-', suffix='.tmp', dir=output.parent)
        with os.fdopen(fd, 'w+b') as dest, stream_path.open('rb') as source:
            while block := source.read(READ_SIZE):
                dest.write(block)
            dest.seek(plan['change_start'])
            dest.write(plan['replacement_image'])
            dest.flush()
            os.fsync(dest.fileno())
        changed = _verify_output(stream_path, Path(tmp), plan['change_start'],
                                 plan['original_image'], plan['replacement_image'])
        if (changed != plan['changed_bytes'] or
                original_digest != _digest_file(stream_path) or
                initial_stats != (stream_path.stat().st_size, stream_path.stat().st_mtime_ns)):
            raise ValueError('Source stream changed while staging private copy')
        # Atomic, no-overwrite promotion. Both paths reside on same filesystem.
        os.link(tmp, output)
        report['private_copy_created'] = True
        return report
    finally:
        if tmp is not None:
            try:
                os.unlink(tmp)
            except FileNotFoundError:
                pass


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--bundle', type=Path, required=True, help='Private extracted L5RB.BUN')
    p.add_argument('--stream', type=Path, required=True, help='Private extracted STREAML5RB.BUN')
    p.add_argument('--section-id', type=int, choices=ALLOWED_SECTIONS, required=True)
    p.add_argument('--dxt1-slot', type=int, default=0, help='Zero-based ordinal among existing DXT1 slots')
    p.add_argument('--solid-rgb', default='FF00FF', help='Synthetic diagnostic solid RGB, 6 hex digits')
    p.add_argument('--private-output', type=Path, help='New uncompressed STREAML5RB.BUN test COPY path')
    p.add_argument('--write-private-copy', action='store_true', help='Opt in to creating private output')
    args = p.parse_args()
    report = stage_private_copy(args.bundle, args.stream, args.section_id, args.dxt1_slot,
                                args.solid_rgb, args.private_output, args.write_private_copy)
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
