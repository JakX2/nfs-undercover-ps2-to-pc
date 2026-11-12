#!/usr/bin/env python3
"""Owner-local read-only external Carbon PC resource filesystem evidence.

This gate checks whether NFSC.exe was observed opening and reading an
owner-original, independently verified Carbon PC geometry/texture root.
It DOES NOT prove external-loader ABI, asset registration, or rendering.
No path, PID, asset name, hash, original bytes or image pixel is output.
No executable is patched, executed, or injected by this tool.
"""
import argparse
import csv
import io
import json
import ntpath
from pathlib import Path
import struct

from carbon_pc_runtime_span_attestation import (
    MAX_CSV_BYTES, MAX_EVENTS, REQUIRED_FIELDS, _read_span,
    _interval_coverage,
)
from carbon_pc_resource_namespace_gate import read_private_carbon_roots
from geometry_hash_control import parse_geometry_root, PLATFORM_PC
from texture_metadata_pixel_bridge import parse_pack

MAX_SOURCE_BYTES = 32 * 1024 * 1024


def _windows_bundle_path(value):
    """Strict absolute DOS-drive path, case-insensitive, never suffix match."""
    if not isinstance(value, str) or not value or any(ord(c) < 32 for c in value):
        raise ValueError('Invalid private Windows Carbon resource path')
    path = value.replace('/', '\\')
    if path.startswith('\\\\?\\'):
        path = path[4:]
    drive, rest = ntpath.splitdrive(path)
    if (len(drive) != 2 or not drive[0].isascii() or
            not drive[0].isalpha() or drive[1] != ':' or
            not rest.startswith('\\') or rest == '\\'):
        raise ValueError('Expected an absolute Windows drive resource path')
    normalized = ntpath.normcase(ntpath.normpath(path))
    if normalized.endswith('\\') or ntpath.basename(normalized) in ('', '.', '..'):
        raise ValueError('Expected a regular Windows resource filename')
    if not normalized.lower().endswith(('.bun', '.bin')):
        raise ValueError('Expected an extracted Carbon resource .bun/.bin file')
    return normalized


def _verify_native_resource(source, kind):
    """Validate ORIGINAL Carbon PC resource framing, never resource identity."""
    if type(source) is not bytes or not 40 <= len(source) <= MAX_SOURCE_BYTES:
        raise ValueError('Invalid bounded original Carbon PC resource bytes')
    if kind == 'geometry':
        parsed = parse_geometry_root(source)
        if parsed['platform'] != PLATFORM_PC or not parsed['solid_count']:
            raise ValueError('Not indexed PC native geometry')
        return {'resource_kind': 'native_pc_geometry',
                'source_resource_records': parsed['solid_count']}
    if kind == 'texture':
        if 8 + struct.unpack_from('<I', source, 4)[0] != len(source):
            raise ValueError('Trailing or incomplete original PC texture root')
        parsed = parse_pack(source, 'pc')
        return {'resource_kind': 'native_pc_texture',
                'source_resource_records': len(parsed['records'])}
    raise ValueError('Invalid PC reference kind')


def audit_external_resource_trace(csv_text, expected_windows_path,
                                  resource_length, kind):
    """Read a bounded ProcMon CSV, returning ONLY nonprivate aggregates.

    Ordered successful CreateFile and ReadFile must occur for one NFSC.exe
    process and an exact, normalized target path. ProcMon may omit mmap,
    caching, device-I/O or events filtered during capture; negative evidence
    is INCONCLUSIVE, not proof that Carbon never attempted to use the file.
    """
    target = _windows_bundle_path(expected_windows_path)
    if (type(resource_length) is not int or
            not 40 <= resource_length <= MAX_SOURCE_BYTES):
        raise ValueError('Invalid external Carbon source length')
    if kind not in ('geometry', 'texture'):
        raise ValueError('Unknown external Carbon PC resource kind')
    if not isinstance(csv_text, str) or len(csv_text.encode('utf-8')) > MAX_CSV_BYTES:
        raise ValueError('Invalid or oversized ProcMon capture')
    reader = csv.DictReader(io.StringIO(csv_text, newline=''))
    if not reader.fieldnames or any(f not in reader.fieldnames for f in REQUIRED_FIELDS):
        raise ValueError('Missing required ProcMon CSV columns')

    processes = {}
    totals = {'candidate_target_events': 0, 'failed_target_events': 0,
              'successful_target_open_events': 0,
              'successful_target_read_events': 0,
              'reads_with_valid_file_spans_after_open': 0}
    rows = 0
    try:
        for row in reader:
            rows += 1
            if rows > MAX_EVENTS:
                raise ValueError('Excessive ProcMon CSV events')
            if (row.get('Process Name') or '').strip().casefold() != 'nfsc.exe':
                continue
            try:
                path = _windows_bundle_path(row.get('Path') or '')
            except ValueError:
                continue
            if path != target:
                continue
            operation = (row.get('Operation') or '').strip().casefold()
            if operation not in ('createfile', 'readfile'):
                continue
            pid_text = (row.get('PID') or '').strip()
            if not pid_text.isascii() or not pid_text.isdecimal() or int(pid_text) <= 0:
                continue
            pid = int(pid_text)
            totals['candidate_target_events'] += 1
            if (row.get('Result') or '').strip().casefold() != 'success':
                totals['failed_target_events'] += 1
                continue
            entry = processes.setdefault(pid, {'opened': False, 'read': False, 'spans': []})
            if operation == 'createfile':
                entry['opened'] = True
                totals['successful_target_open_events'] += 1
            else:
                totals['successful_target_read_events'] += 1
                if not entry['opened']:
                    continue
                entry['read'] = True
                span = _read_span(row.get('Detail'))
                if span is not None and span[0] < span[1] <= resource_length:
                    entry['spans'].append(span)
                    totals['reads_with_valid_file_spans_after_open'] += 1
    except (csv.Error, UnicodeError) as exc:
        raise ValueError('Malformed ProcMon capture') from exc

    ordered = [p for p in processes.values() if p['opened'] and p['read']]
    coverage = max((_interval_coverage(p['spans'], 0, resource_length)
                    for p in ordered), default=0)
    if coverage == resource_length:
        status = 'FULL_FILE_READ_OBSERVED_NOT_ASSET_REGISTRATION'
    elif coverage > 0:
        status = 'PARTIAL_FILE_READ_OBSERVED_NOT_ASSET_REGISTRATION'
    elif ordered:
        status = 'EXACT_FILE_OPEN_READ_OFFSETS_UNVERIFIED'
    elif any(p['opened'] for p in processes.values()):
        status = 'EXACT_FILE_OPEN_ONLY'
    else:
        status = 'NO_POSITIVE_CAPTURED_FILE_EVIDENCE'

    return {
        'scope': 'ORIGINAL_CARBON_PC_EXTERNAL_FILE_IO_EVIDENCE_ONLY',
        'source_kind': 'native_pc_' + kind,
        'source_length_bytes': resource_length,
        **totals,
        'same_pid_ordered_open_read_observed': bool(ordered),
        'verified_file_bytes_read_for_one_process': coverage,
        'entire_file_read_by_one_process_observed': coverage == resource_length,
        'evidence_level': status,
        'carbon_external_loader_abi_verified': False,
        'carbon_asset_registration_verified': False,
        'carbon_in_game_rendering_verified': False,
        'undercover_resource_loading_verified': False,
        'limitations': ('Observed file I/O is not engine resource registration. '
                        'Missing ProcMon events may reflect filtering, caching, '
                        'memory mapping or missing capture. PID reuse and '
                        'capture timing are not independently attested.'),
    }


def audit_original_files(original_resource, kind, procmon_csv):
    """Windows owner-local read-only entrypoint with metadata checks.

    A standalone extracted Carbon PC root can act as an original-source
    control. Whether a particular third-party mod loader actually accepts
    this raw root is NOT asserted by the file parser.
    """
    if type(kind) is not str or kind not in ('geometry', 'texture'):
        raise ValueError('Explicit source kind required')
    resource_file = Path(original_resource).absolute()
    report_source = _verify_native_resource(
        read_private_carbon_roots((resource_file,))[0], kind)
    log_file = Path(procmon_csv).absolute()
    if any(p.is_symlink() for p in (log_file, *log_file.parents)):
        raise ValueError('Unsafe symlink ProcMon capture')
    if not log_file.is_file() or not 0 < log_file.stat().st_size <= MAX_CSV_BYTES:
        raise ValueError('Missing or unsafe ProcMon CSV')
    before = log_file.stat()
    text = log_file.read_text(encoding='utf-8-sig')
    after = log_file.stat()
    if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) != (
            after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns):
        raise ValueError('ProcMon capture changed while being inspected')
    result = audit_external_resource_trace(
        text, str(resource_file), resource_file.stat().st_size, kind)
    result.update(report_source)
    result['original_pc_resource_framing_verified'] = True
    result['local_files_modified'] = False
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native-carbon-root', required=True,
                        help='owner-local extracted ORIGINAL Carbon PC .bun/.bin root')
    parser.add_argument('--kind', required=True, choices=('geometry', 'texture'))
    parser.add_argument('--procmon-csv', required=True,
                        help='owner-captured ProcMon event export for NFSC.exe')
    args = parser.parse_args()
    print(json.dumps(audit_original_files(
        args.native_carbon_root, args.kind, args.procmon_csv), indent=2))


if __name__ == '__main__':
    main()
