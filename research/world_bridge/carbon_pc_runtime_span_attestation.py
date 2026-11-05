#!/usr/bin/env python3
"""Read-only, source-private Carbon PC stream-load evidence gate.

Compares pristine, staged and installed STREAML5RB.BUN bytes, obtains the
selected existing DXT1/DXT5 image span from the pristine Carbon L5RB.BUN,
and checks a user-captured ProcMon CSV for exact-file same-PID open+reads.

Never copies, installs, modifies, hashes publicly, or prints original game
textures, resource hashes, usernames, file paths, PIDs or image payloads.
A positive result proves filesystem access, NOT Carbon texture rendering.
"""
import argparse
import csv
import hashlib
import io
import json
import ntpath
from pathlib import Path
import re

from pc_texture_header_overlay_gate import _source_image_span
from private_carbon_dxt1_stream_stage import section_span
from texture_metadata_pixel_bridge import MAX_SECTION, parse_pack
from texture_pixel_base_alignment import aligned_pixel_array

MAX_STREAM = 2 * 1024 * 1024 * 1024
MAX_BUNDLE = 8 * 1024 * 1024
MAX_CSV_BYTES = 24 * 1024 * 1024
MAX_EVENTS = 200_000
READ_SIZE = 1024 * 1024
REQUIRED_FIELDS = ('Process Name', 'PID', 'Operation', 'Path', 'Result', 'Detail')
NUMBER = r'(?:0[xX][0-9a-fA-F]+|(?:[0-9]{1,3}(?:,[0-9]{3})+|[0-9]+))'
OFFLEN = re.compile(r'\bOffset:\s*('+NUMBER+r')\s*,\s*Length:\s*('+NUMBER+r')(?=,\s|\s|$)', re.I)


def _safe_file(path, maximum):
    path = Path(path)
    if path.is_symlink() or not path.is_file() or not 0 < path.stat().st_size <= maximum:
        raise ValueError('Missing, symlinked, empty, or oversized private input')
    return path


def _normalized_windows_file(path):
    if not isinstance(path, str) or not path or '\0' in path:
        raise ValueError('Malformed Windows file path')
    p = path.replace('/', '\\')
    if p.startswith('\\\\?\\'):
        p = p[4:]
    p = ntpath.normcase(ntpath.normpath(p))
    drive, tail = ntpath.splitdrive(p)
    if not drive or not tail.startswith('\\') or not p.endswith(r'\tracks\streaml5rb.bun'):
        raise ValueError('Expected an absolute TRACKS\\STREAML5RB.BUN Windows path')
    # Equality is exact after case/separator normalization, NOT a suffix match.
    return p


def _read_span(detail):
    if not isinstance(detail, str):
        return None
    m = OFFLEN.search(detail)
    if not m:
        return None
    try:
        offset, size = (int(v.replace(',', ''), 0 if v.lower().startswith('0x') else 10)
                        for v in m.groups())
    except ValueError:
        return None
    if offset < 0 or size <= 0 or offset + size > MAX_STREAM:
        return None
    return offset, offset + size


def _interval_coverage(intervals, left, right):
    covered = 0
    end = left
    for a, b in sorted(intervals):
        lo, hi = max(left, a), min(right, b)
        if lo >= hi:
            continue
        lo = max(end, lo)
        if lo < hi:
            covered += hi - lo
            end = hi
    return covered


def analyze_trace(csv_text, expected_windows_path, image_start, image_length):
    """Require an exact target path, same PID, ordered success open/read events.

    The returned summary contains no private path, PID, timestamp or byte data.
    ProcMon may miss memory-mapped access or have gaps if filtering was used.
    """
    if not isinstance(csv_text, str) or len(csv_text.encode('utf-8')) > MAX_CSV_BYTES:
        raise ValueError('Unsafe ProcMon CSV')
    target = _normalized_windows_file(expected_windows_path)
    if (type(image_start) is not int or type(image_length) is not int or
            image_start < 0 or image_length <= 0 or image_start + image_length > MAX_STREAM):
        raise ValueError('Unsafe image span')
    reader = csv.DictReader(io.StringIO(csv_text, newline=''))
    if not reader.fieldnames or any(f not in reader.fieldnames for f in REQUIRED_FIELDS):
        raise ValueError('Missing required ProcMon columns')
    state = {}
    totals = {'rows': 0, 'nfsc_target_events': 0, 'failed_target_events': 0,
              'successful_target_open_events': 0, 'successful_target_read_events': 0,
              'read_events_with_valid_offsets': 0, 'read_events_overlapping_image': 0}
    try:
        for row in reader:
            totals['rows'] += 1
            if totals['rows'] > MAX_EVENTS:
                raise ValueError('ProcMon event limit exceeded')
            if (row.get('Process Name', '').strip().casefold() != 'nfsc.exe' or
                    not row.get('Path')):
                continue
            try:
                path = _normalized_windows_file(row['Path'])
            except ValueError:
                continue
            if path != target:
                continue
            op = (row.get('Operation') or '').strip().casefold()
            if op not in ('createfile', 'readfile'):
                continue
            raw_pid = (row.get('PID') or '').strip()
            if not raw_pid.isascii() or not raw_pid.isdecimal() or int(raw_pid) <= 0:
                continue
            pid = int(raw_pid)
            totals['nfsc_target_events'] += 1
            if (row.get('Result') or '').strip().casefold() != 'success':
                totals['failed_target_events'] += 1
                continue
            st = state.setdefault(pid, {'opened': False, 'reads_after_open': 0,
                                        'overlap': [], 'hits': 0})
            if op == 'createfile':
                st['opened'] = True
                totals['successful_target_open_events'] += 1
                continue
            totals['successful_target_read_events'] += 1
            if not st['opened']:
                continue
            st['reads_after_open'] += 1
            span = _read_span(row.get('Detail'))
            if span is None:
                continue
            totals['read_events_with_valid_offsets'] += 1
            l, r = span
            if l < image_start + image_length and image_start < r:
                st['hits'] += 1
                totals['read_events_overlapping_image'] += 1
                st['overlap'].append((l, r))
    except (csv.Error, UnicodeError) as exc:
        raise ValueError('Malformed ProcMon CSV') from exc
    matched = [x for x in state.values() if x['opened'] and x['reads_after_open']]
    best = max((_interval_coverage(x['overlap'], image_start, image_start + image_length)
                for x in matched), default=0)
    if best == image_length:
        level = 'full_image_span_read_observed_not_rendering'
    elif best:
        level = 'some_image_bytes_read_observed_not_rendering'
    elif matched:
        level = 'exact_stream_open_and_read_without_proven_image_overlap'
    elif any(x['opened'] for x in state.values()):
        level = 'exact_stream_open_only'
    else:
        level = 'no_positive_exact_stream_open'
    return {**totals,
            'same_pid_ordered_open_read_observed': bool(matched),
            'matched_image_bytes_covered_for_one_process': best,
            'image_span_bytes': image_length,
            'evidence_level': level,
            'limitations': ('A ProcMon ReadFile intersection proves disk range access only. '
                           'It does not prove an installed copy was in place when read, '
                           'texture registration, alpha blending or on-screen rendering. '
                           'Memory-mapped/cache paths, PID reuse and capture filtering may hide or misattribute reads.')}


def existing_image_span(bundle, pristine_stream, section_id, codec, ordinal):
    """Use original Carbon table and metadata; no caller-provided raw offsets."""
    if codec not in ('DXT1', 'DXT5') or type(ordinal) is not int or ordinal < 0:
        raise ValueError('Only existing DXT1/DXT5 slots by nonnegative ordinal')
    bun = _safe_file(bundle, MAX_BUNDLE).read_bytes()
    stream = _safe_file(pristine_stream, MAX_STREAM)
    offset, length = section_span(bun, stream.stat().st_size, section_id)
    if length > MAX_SECTION:
        raise ValueError('Unsafe section size')
    with stream.open('rb') as handle:
        handle.seek(offset)
        section = handle.read(length)
    if len(section) != length:
        raise ValueError('Truncated original PC section')
    records = parse_pack(section, 'pc')['records']
    aligned_pixel_array(section, records)
    target = 34 if codec == 'DXT1' else 38
    slots = sorted(h for h, meta in records.items() if meta['codec'] == target)
    if ordinal >= len(slots):
        raise ValueError('Requested PC texture slot does not exist')
    left, right = _source_image_span(section, records[slots[ordinal]])
    if not 0 <= left < right <= len(section):
        raise ValueError('Source texture span exceeds verified section')
    return offset + left, right - left


def _fingerprint(path):
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        while block := handle.read(READ_SIZE):
            digest.update(block)
    return digest.digest()


def verify_private_copy(pristine, staged, installed, image_start, image_length):
    """Ensure staged differs from pristine ONLY in image span; installed==stage.

    Read-only checks happen *after* capture; temporal consistency is unproven.
    Never return contents, full paths, digests, hashes or selected identity.
    """
    files = [_safe_file(p, MAX_STREAM) for p in (pristine, staged, installed)]
    if type(image_start) is not int or type(image_length) is not int or image_start < 0 or image_length <= 0:
        raise ValueError('Invalid image span')
    size = files[0].stat().st_size
    if any(p.stat().st_size != size for p in files) or image_start + image_length > size:
        raise ValueError('Original, staged or installed sizes/spans differ')
    if len({p.resolve() for p in files}) != 3:
        raise ValueError('Inputs must be three different files')
    inodes = [(p.stat().st_dev, p.stat().st_ino) for p in files]
    if all(ino > 0 for _, ino in inodes) and len(set(inodes)) != 3:
        raise ValueError('Hard-linked game files are not an isolated test')
    changed = 0
    pos = 0
    with files[0].open('rb') as clean, files[1].open('rb') as mod:
        while a := clean.read(READ_SIZE):
            b = mod.read(len(a))
            if len(b) != len(a):
                raise ValueError('Truncated staged copy')
            if a != b:
                lo = max(0, image_start - pos)
                hi = min(len(a), image_start + image_length - pos)
                if lo >= hi:
                    raise ValueError('Staged copy modifies bytes outside the texture span')
                if a[:lo] != b[:lo] or a[hi:] != b[hi:]:
                    raise ValueError('Staged copy modifies bytes outside the texture span')
                changed += sum(x != y for x, y in zip(a[lo:hi], b[lo:hi]))
            pos += len(a)
        if mod.read(1) or pos != size or changed == 0:
            raise ValueError('No valid isolated staged image modification')
    # Digest is an internal equality check, never exposed.
    if _fingerprint(files[1]) != _fingerprint(files[2]):
        raise ValueError('Installed stream does not match private staged copy')
    return {'pristine_staged_sizes_match': True,
            'stage_edits_confined_to_one_original_image': True,
            'changed_image_bytes': changed,
            'installed_stream_currently_matches_stage': True,
            'hashes_and_paths_not_disclosed': True}


def attest(bundle, pristine, staged, installed, procmon_csv, section_id,
           codec, ordinal, observed_windows_path=None):
    start, length = existing_image_span(bundle, pristine, section_id, codec, ordinal)
    proof = verify_private_copy(pristine, staged, installed, start, length)
    csv_path = _safe_file(procmon_csv, MAX_CSV_BYTES)
    if observed_windows_path is None:
        # On Windows the actual installed path is available from Path.resolve().
        observed_windows_path = str(Path(installed).resolve())
    trace = analyze_trace(csv_path.read_text(encoding='utf-8-sig'),
                          observed_windows_path, start, length)
    return {'scope': 'READ_ONLY_POST_CAPTURE_ATTESTATION_NOT_RUNTIME_RENDERING',
            'codec': codec, 'section_id': section_id, 'ordinal': ordinal,
            'copy_integrity': proof, 'procmon': trace}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--carbon-bun', type=Path, required=True,
                   help='Private original extracted TRACKS/L5RB.BUN')
    p.add_argument('--pristine-stream', type=Path, required=True)
    p.add_argument('--staged-stream', type=Path, required=True)
    p.add_argument('--installed-stream', type=Path, required=True,
                   help='Current local installed TRACKS/STREAML5RB.BUN, READ ONLY')
    p.add_argument('--procmon-csv', type=Path, required=True)
    p.add_argument('--section', type=int, choices=(141, 142), required=True)
    p.add_argument('--codec', choices=('DXT1', 'DXT5'), required=True)
    p.add_argument('--slot', type=int, required=True)
    args = p.parse_args()
    print(json.dumps(attest(args.carbon_bun, args.pristine_stream,
         args.staged_stream, args.installed_stream, args.procmon_csv,
         args.section, args.codec, args.slot), indent=2))


if __name__ == '__main__':
    main()
