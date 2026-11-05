#!/usr/bin/env python3
"""Read-only original Undercover PS2 RA/RB texture-image presence gate.

Checks whether texture identities *used by RB scenery geometry* occur in fully
validated original RA/RB texture-image indexes. No hashes, names, coordinates,
source paths, original pixels or game files are written or printed. This is
an archive-local image INDEX test, never engine registration or rendering.
"""
import argparse
from bisect import bisect_right
import hashlib
import json
import os
from pathlib import Path
import struct
import zipfile

from texture_metadata_pixel_bridge import parse_pack
from texture_pixel_base_alignment import aligned_pixel_array

CHUNK_TABLE = 0x00034110
TEXTURE_ROOT = 0xB3300000
CHUNK_ROW_BYTES = 92
MAX_SMALL_BUN = 8 * 1024 * 1024
MAX_RA_STREAM = 512 * 1024 * 1024
MAX_RB_STREAM = 128 * 1024 * 1024
MAX_PACK = 32 * 1024 * 1024
MAX_SECTIONS = 4096
MAX_ROOTS = 8192
MAX_ZIP = 1024 * 1024 * 1024
SOURCE_SECTIONS = (241, 3401)
SOURCE_ARCHIVE_ENTRIES = (
    'TRACKS/L2RA.BUN', 'TRACKS/STREAML2RA.BUN',
    'TRACKS/L2RB.BUN', 'TRACKS/STREAML2RB.BUN',
    'TRACKS/LOC2DYNTEX.BIN',
)


def _owner_archive(path):
    p = Path(path).absolute()
    if any(q.is_symlink() for q in (p, *p.parents)):
        raise ValueError('Symlinked original archive path is not permitted')
    if not p.is_file() or not 0 < p.stat().st_size <= MAX_ZIP:
        raise ValueError('Original Undercover archive is missing or oversized')
    return p.resolve(strict=True)


def _fingerprint(path):
    stat = path.stat()
    h = hashlib.sha256()
    with path.open('rb') as src:
        while data := src.read(1024 * 1024):
            h.update(data)
    return (stat.st_size, stat.st_mtime_ns, h.digest())


def _member_bytes(archive, name, max_bytes, allow_empty=False):
    info = archive.getinfo(name)
    if info.is_dir() or info.flag_bits & 1 or info.file_size > max_bytes or (not allow_empty and not info.file_size):
        raise ValueError('Unsafe original ZIP member for private audit')
    # zipfile.read verifies member length and CRC32, including streamed deflate.
    blob = archive.read(info)
    if len(blob) != info.file_size:
        raise ValueError('Short original ZIP member read')
    return blob


def parse_stream_section_rows(bundle, stream_length):
    """Validate the entire original 92-byte 0x34110 section table.

    Return ordered, disjoint stream intervals and an ID -> (start, end) map.
    Internal section positions are private and must never be logged.
    """
    if (type(bundle) is not bytes or not 8 <= len(bundle) <= MAX_SMALL_BUN or
            type(stream_length) is not int or not 0 < stream_length <= MAX_RA_STREAM):
        raise ValueError('Unsafe source bundle or stream length')
    cursor, payload = 0, None
    while cursor < len(bundle):
        if cursor + 8 > len(bundle):
            raise ValueError('Truncated original BUN chunk')
        kind, length = struct.unpack_from('<II', bundle, cursor)
        stop = cursor + 8 + length
        if stop > len(bundle):
            raise ValueError('Original BUN chunk exceeds file bounds')
        if kind == CHUNK_TABLE:
            if payload is not None:
                raise ValueError('Multiple original streaming section tables')
            payload = bundle[cursor + 8:stop]
        cursor = stop
    if payload is None or not payload or len(payload) % CHUNK_ROW_BYTES:
        raise ValueError('Missing or malformed original streaming section rows')
    count = len(payload) // CHUNK_ROW_BYTES
    if count > MAX_SECTIONS:
        raise ValueError('Too many original stream sections')
    positions = {}
    ranges = []
    for at in range(0, len(payload), CHUNK_ROW_BYTES):
        number = struct.unpack_from('<h', payload, at + 8)[0]
        offset, length = struct.unpack_from('<II', payload, at + 20)
        if (number in positions or offset % 2048 or
                length < 8 or length > MAX_PACK or offset + length > stream_length):
            raise ValueError('Duplicate, misaligned or out-of-bounds original stream row')
        positions[number] = (offset, offset + length)
        ranges.append((offset, offset + length, number))
    ranges.sort()
    if any(b > c for (_, b, _), (c, _, _) in zip(ranges, ranges[1:])):
        raise ValueError('Original streaming sections overlap')
    return tuple(ranges), positions


def validated_texture_ids(root):
    """Use original repository parser and aligned PS2 pixel range validator."""
    if type(root) is not bytes or not 40 <= len(root) <= MAX_PACK:
        raise ValueError('Unsafe texture root frame')
    kind, length = struct.unpack_from('<II', root)
    if kind != TEXTURE_ROOT or length + 8 != len(root):
        raise ValueError('Not an exactly framed original PS2 texture root')
    parsed = parse_pack(root, 'ps2')
    aligned_pixel_array(root, parsed['records'])
    if not parsed['records']:
        raise ValueError('Empty validated PS2 image index')
    return frozenset(parsed['records'])


def enumerate_ra_texture_indexes(stream, ordered_rows):
    """Inspect all RA bytes, classify verified index roots by row membership.

    A texture-root marker alone never counts. Only full PS2 metadata and 128B
    aligned image/palette spans are accepted. Roots outside a declared stream
    row are retained as *unbound private evidence*, not registered resources.
    """
    if type(stream) is not bytes or not 0 < len(stream) <= MAX_RA_STREAM:
        raise ValueError('Unsafe original RA stream')
    if not isinstance(ordered_rows, (list, tuple)) or not ordered_rows:
        raise ValueError('Missing original RA row bounds')
    starts = []
    previous_end = 0
    for start, end, section in ordered_rows:
        if (type(start) is not int or type(end) is not int or
                type(section) is not int or start < previous_end or
                not start < end <= len(stream)):
            raise ValueError('Invalid RA row ordering or bounds')
        starts.append(start)
        previous_end = end
    search = 0
    candidates = 0
    accepted = 0
    bounded = 0
    out_of_row = 0
    bounded_ids, all_root_ids = set(), set()
    root_intervals = []
    signature = struct.pack('<I', TEXTURE_ROOT)
    while True:
        at = stream.find(signature, search)
        if at < 0:
            break
        search = at + 4
        candidates += 1
        if at % 4 or at + 8 > len(stream):
            continue
        n = struct.unpack_from('<I', stream, at + 4)[0]
        if n < 32 or n > MAX_PACK - 8 or at + 8 + n > len(stream):
            continue
        try:
            private_ids = validated_texture_ids(stream[at:at + 8 + n])
        except (ValueError, struct.error):
            # A mere four-byte signature is not a trusted resource frame.
            continue
        end = at + 8 + n
        if root_intervals and at < root_intervals[-1][1]:
            raise ValueError('Overlapping fully validated RA texture roots')
        root_intervals.append((at, end))
        accepted += 1
        if accepted > MAX_ROOTS:
            raise ValueError('Excessive original RA texture root count')
        all_root_ids.update(private_ids)
        row = bisect_right(starts, at) - 1
        if row >= 0 and at >= ordered_rows[row][0] and end <= ordered_rows[row][1]:
            bounded += 1
            bounded_ids.update(private_ids)
        else:
            out_of_row += 1
        search = end
    return {'all_validated_ra_ids':frozenset(all_root_ids),
            'declared_section_ra_ids':frozenset(bounded_ids),
            'candidate_markers_examined':candidates,
            'fully_validated_image_roots':accepted,
            'roots_contained_in_declared_ra_stream_rows':bounded,
            'roots_not_contained_in_declared_stream_rows':out_of_row,
            'distinct_validated_image_identities':len(all_root_ids),
            'distinct_section_contained_image_identities':len(bounded_ids)}


def reconcile_image_presence(used_by_section, rb_images_by_section, ra_summary):
    """Return only count-safe comparisons, never original texture identities."""
    if (not isinstance(used_by_section, dict) or
            not isinstance(rb_images_by_section, dict) or
            set(used_by_section) != set(SOURCE_SECTIONS) or
            set(rb_images_by_section) != set(SOURCE_SECTIONS)):
        raise ValueError('Expected both Undercover source geometry/image sections')
    def safe_set(raw, label):
        if not isinstance(raw, (set, frozenset)) or not raw:
            raise ValueError('Missing private '+label+' identity set')
        if any(type(k) is not int or not 0 < k <= 0xffffffff for k in raw):
            raise ValueError('Invalid original identity in private set')
        return set(raw)
    used = {s:safe_set(used_by_section[s], 'material') for s in SOURCE_SECTIONS}
    rb = {s:safe_set(rb_images_by_section[s], 'RB image') for s in SOURCE_SECTIONS}
    if not isinstance(ra_summary, dict):
        raise ValueError('Missing validated RA image summary')
    ra = safe_set(ra_summary['all_validated_ra_ids'],'RA image')
    bounded = safe_set(ra_summary['declared_section_ra_ids'], 'registered RA image')
    if not bounded <= ra:
        raise ValueError('Declared RA image identities exceed validated RA population')
    if ra_summary['fully_validated_image_roots'] != (ra_summary['roots_contained_in_declared_ra_stream_rows'] + ra_summary['roots_not_contained_in_declared_stream_rows']):
        raise ValueError('RA root classification counts disagree')
    used_all = used[241] | used[3401]
    rb_all = rb[241] | rb[3401]
    rb_missing = used_all - rb_all
    ra_matches = rb_missing & bounded
    gap_only = rb_missing & (ra - bounded)
    unresolved = rb_missing - ra
    return {'scope':'OFFLINE_UNDERCOVER_ORIGINAL_TRACKS_RA_RB_INDEX_PRESENCE_NOT_RUNTIME_REGISTRATION',
            'source_sections_examined':2,
            'distinct_used_undercover_rb_scenery_material_ids':len(used_all),
            'distinct_original_rb_image_ids':len(rb_all),
            'distinct_material_ids_absent_from_rb_image_indexes':len(rb_missing),
            'distinct_ra_image_ids_full_validated_stream':len(ra),
            'distinct_ra_image_ids_declared_section_rows':len(bounded),
            'missing_rb_ids_resolved_in_declared_ra_texture_roots':len(ra_matches),
            'missing_rb_ids_found_only_in_unassigned_ra_root_frames':len(gap_only),
            'missing_rb_ids_not_in_any_validated_ra_texture_root':len(unresolved),
            'all_used_ids_within_examined_ra_or_rb_image_indexes':len(unresolved)==0 and len(gap_only)==0,
            'per_undercover_rb_section':{str(s):{
                'distinct_used_material_ids':len(used[s]),
                'distinct_local_rb_image_ids':len(rb[s]),
                'used_material_ids_with_same_section_rb_image':len(used[s] & rb[s]),
                'used_material_ids_without_same_section_rb_image':len(used[s] - rb[s])
            } for s in SOURCE_SECTIONS},
            'ra_texture_root_checks':{k:ra_summary[k] for k in (
                'candidate_markers_examined', 'fully_validated_image_roots',
                'roots_contained_in_declared_ra_stream_rows',
                'roots_not_contained_in_declared_stream_rows')},
            'other_original_resource_archives_or_special_material_semantics_still_unchecked':True,
            'carbon_pc_runtime_registration':'NOT_TESTED',
            'source_identity_values_or_original_assets_published':False}


def used_material_ids_from_original_rb(section):
    """Resolve USED indexes through existing source-backed geometry and VIF parsers.

    Strict source pack parsing preserves duplicated eSolid identities across
    independent packs. The private original material ID set never leaves RAM.
    """
    from undercover_pc_partition_registry_gate import source_partition_roots
    from mesh_topology_control import PS2_STRIPS, parse_ps2_mesh
    packs = source_partition_roots(section)
    if not packs:
        raise ValueError('No original PS2 geometry packs in source RB section')
    used = set()
    for group in packs:
        for _, _, hashes, children in group:
            parsed = parse_ps2_mesh(children)
            entries = next((raw for k,raw in children if k==PS2_STRIPS), None)
            if entries is None or len(entries) != 4 + 16*parsed['strip_entries']:
                raise ValueError('Missing validated source PS2 strip material table')
            for at in range(4, len(entries), 16):
                idx = struct.unpack_from('<b', entries, at + 14)[0]
                if idx < 0 or idx >= len(hashes):
                    raise ValueError('Source material reference outside eSolid texture table')
                used.add(hashes[idx])
    if not used:
        raise ValueError('Source scenery had no used material identities')
    return frozenset(used)


def audit_original_undercover_archive(path):
    """CRC-check owner original RA/RB data and compare only private identity sets."""
    archive_path = _owner_archive(path)
    before = _fingerprint(archive_path)
    with zipfile.ZipFile(archive_path) as z:
        source_ra_small = _member_bytes(z, SOURCE_ARCHIVE_ENTRIES[0], MAX_SMALL_BUN)
        source_ra = _member_bytes(z, SOURCE_ARCHIVE_ENTRIES[1], MAX_RA_STREAM)
        source_rb_small = _member_bytes(z, SOURCE_ARCHIVE_ENTRIES[2], MAX_SMALL_BUN)
        source_rb = _member_bytes(z, SOURCE_ARCHIVE_ENTRIES[3], MAX_RB_STREAM)
        dyn = _member_bytes(z, SOURCE_ARCHIVE_ENTRIES[4], MAX_SMALL_BUN, allow_empty=True)
    ra_rows, _ = parse_stream_section_rows(source_ra_small, len(source_ra))
    _, rb_by_id = parse_stream_section_rows(source_rb_small, len(source_rb))
    used, rb_images = {}, {}
    for number in SOURCE_SECTIONS:
        if number not in rb_by_id:
            raise ValueError('Required source RB section missing from table')
        a,b = rb_by_id[number]
        source = source_rb[a:b]
        used[number] = used_material_ids_from_original_rb(source)
        # Existing RB section begins with an independently verified PS2 pack.
        if struct.unpack_from('<I', source)[0] != TEXTURE_ROOT:
            raise ValueError('Source RB section does not begin with texture pack')
        root_size = struct.unpack_from('<I', source, 4)[0] + 8
        if root_size > len(source):
            raise ValueError('RB source texture root extends past section')
        rb_images[number] = validated_texture_ids(source[:root_size])
    ra_summary = enumerate_ra_texture_indexes(source_ra, ra_rows)
    result = reconcile_image_presence(used, rb_images, ra_summary)
    if _fingerprint(archive_path) != before:
        raise ValueError('Original owner archive changed during read-only inspection')
    result.update({'original_ra_stream_bytes':len(source_ra),
                   'original_ra_declared_stream_sections':len(ra_rows),
                   'original_rb_declared_stream_sections':len(rb_by_id),
                   'dynamic_texture_entry_zero_bytes':len(dyn)==0,
                   'owner_original_zip_crc_verified':True,
                   'owner_original_unchanged':True})
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--undercover-ps2-zip',type=Path,required=True)
    args=p.parse_args()
    print(json.dumps(audit_original_undercover_archive(args.undercover_ps2_zip),indent=2))


if __name__=='__main__':
    main()
