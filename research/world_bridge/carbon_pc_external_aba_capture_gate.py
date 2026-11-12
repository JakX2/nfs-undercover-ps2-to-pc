#!/usr/bin/env python3
"""Original-free Carbon PC A/B/A external-resource filesystem evidence gate.

A = baseline launch, B = one owner-original XNFSModFiles resource enabled,
A = restore/disabled launch. An existing, independently known normal Carbon
file is used as a positive ProcMon capture sentinel in all three runs.

All claims are about FILE I/O visible in the supplied CSVs, not whether
the ASI, engine registration or on-screen content worked. No Carbon process
is launched, altered, hooked or contacted by this module.
"""
import argparse
import csv
import io
import json
import ntpath
import os
from pathlib import Path

from carbon_pc_external_resource_read_gate import (
    MAX_CSV_BYTES, MAX_EVENTS, REQUIRED_FIELDS, _windows_bundle_path,
)
from carbon_pc_original_loader_control_chain import (
    MAX_SOURCE_BYTES, _owner_file, _stamp, _windows_root,
    audit_carbon_original_external_control, audit_owner_carbon_control_files,
)

def _capture_probe(text, external_path, sentinel_path):
    """Find exact-path same-PID successful open+read pairs, per source run.

    Return ONLY aggregate counts/flags. PID sets never leave this function.
    Reads before a matching CreateFile do not qualify, and events of other
    processes, paths or unsuccessful operations are ignored.
    """
    if not isinstance(text, str) or len(text.encode('utf-8')) > MAX_CSV_BYTES:
        raise ValueError('Missing, malformed or oversized ProcMon CSV')
    external = _windows_bundle_path(external_path)
    sentinel = _windows_bundle_path(sentinel_path)
    if sentinel == external:
        raise ValueError('Capture calibration source must differ from external resource')
    reader = csv.DictReader(io.StringIO(text, newline=''))
    if (not reader.fieldnames or len(set(reader.fieldnames)) != len(reader.fieldnames)
            or any(field not in reader.fieldnames for field in REQUIRED_FIELDS)):
        raise ValueError('Missing or duplicate required ProcMon columns')
    states = {}
    target_events = 0
    valid_rows = 0
    try:
        for row in reader:
            valid_rows += 1
            if valid_rows > MAX_EVENTS:
                raise ValueError('Too many ProcMon events')
            if (row.get('Process Name') or '').strip().casefold() != 'nfsc.exe':
                continue
            op = (row.get('Operation') or '').strip().casefold()
            if op not in ('createfile', 'readfile'):
                continue
            pid = (row.get('PID') or '').strip()
            if not pid.isascii() or not pid.isdecimal() or int(pid) <= 0:
                continue
            if (row.get('Result') or '').strip().casefold() != 'success':
                continue
            try:
                path = _windows_bundle_path(row.get('Path') or '')
            except ValueError:
                continue
            if path != external and path != sentinel:
                continue
            role = 'external' if path == external else 'sentinel'
            if role == 'external':
                target_events += 1
            state = states.setdefault(int(pid), {
                'external_open': False, 'external_read': False,
                'sentinel_open': False, 'sentinel_read': False
            })
            if op == 'createfile':
                state[role + '_open'] = True
            elif state[role + '_open']:
                state[role + '_read'] = True
    except (csv.Error, UnicodeError) as error:
        raise ValueError('Invalid ProcMon CSV structure') from error
    sentinel_pids = {pid for pid, v in states.items() if v['sentinel_read']}
    external_pids = {pid for pid, v in states.items() if v['external_read']}
    return {
        'sentinel_open_read_same_pid': bool(sentinel_pids),
        'external_open_read_same_pid': bool(external_pids),
        'external_open_or_read_event_observed': bool(target_events),
        'external_successful_target_events': target_events,
        'external_read_and_sentinel_same_pid': bool(sentinel_pids & external_pids),
    }


def audit_carbon_external_aba(
        manifest_bytes, original_resource_bytes,
        baseline_csv, control_csv, restore_csv,
        windows_game_root, windows_external_path, windows_sentinel_path,
        kind):
    """Pure input audit of three separately captured original-file runs.

    Caller controls provenance and capture chronology; THIS cannot
    independently attest that the external loader was disabled/re-enabled
    in those respective runs or that no other mods were installed.
    """
    game_root = _windows_root(windows_game_root)
    external = _windows_bundle_path(windows_external_path)
    sentinel = _windows_bundle_path(windows_sentinel_path)
    for path in (external, sentinel):
        try:
            relative = ntpath.relpath(path, game_root)
        except ValueError as exc:
            raise ValueError('Control files must be on the game drive') from exc
        if relative == '..' or relative.startswith('..\\') or relative == '.':
            raise ValueError('Control files must belong to test game root')
    if not baseline_csv or not control_csv or not restore_csv:
        raise ValueError('All three ProcMon captures are required')

    # The prior gate validates the complete bounded original PC BUN chunk
    # sequence, the single exact manifest entry, and the CONTROL capture.
    bound = audit_carbon_original_external_control(
        manifest_bytes, original_resource_bytes, control_csv,
        game_root, external, kind)
    a = _capture_probe(baseline_csv, external, sentinel)
    b = _capture_probe(control_csv, external, sentinel)
    restored = _capture_probe(restore_csv, external, sentinel)
    calibrated = all(row['sentinel_open_read_same_pid']
                     for row in (a, b, restored))
    isolated = not a['external_open_or_read_event_observed'] and not (
        restored['external_open_or_read_event_observed'])
    matching_pid = b['external_read_and_sentinel_same_pid']
    bound_read = bound['same_pid_ordered_open_read_observed']
    full = bound['entire_original_file_read_by_one_process_observed']
    if not calibrated:
        status = 'INCONCLUSIVE_CAPTURE_CALIBRATION_MISSING'
    elif not isolated:
        status = 'INCONCLUSIVE_EXTERNAL_TARGET_NOT_ISOLATED_TO_CONTROL'
    elif matching_pid and bound_read:
        status = 'ISOLATED_EXTERNAL_FILE_READ_OBSERVED_NOT_REGISTRATION'
    elif b['external_open_or_read_event_observed']:
        status = 'INCONCLUSIVE_CONTROL_TARGET_ACCESS_WITHOUT_CALIBRATED_READ'
    else:
        status = 'INCONCLUSIVE_NO_CONTROL_FILE_READ'

    return {
        'scope': 'OWNER_CAPTURED_CARBON_A_B_A_FILE_IO_NOT_RUNTIME_LOADING',
        'baseline_calibrated': a['sentinel_open_read_same_pid'],
        'control_calibrated': b['sentinel_open_read_same_pid'],
        'restore_calibrated': restored['sentinel_open_read_same_pid'],
        'all_captures_calibrated': calibrated,
        'baseline_external_file_events_observed': a['external_open_or_read_event_observed'],
        'control_external_file_events_observed': b['external_open_or_read_event_observed'],
        'restore_external_file_events_observed': restored['external_open_or_read_event_observed'],
        'external_access_isolated_to_control_capture': isolated,
        'control_external_and_sentinel_same_pid': matching_pid,
        'control_same_pid_open_read_observed': bound_read,
        'control_full_external_file_read_observed': full,
        'control_external_file_bytes_covered': bound['read_bytes_covered_by_one_process'],
        'original_file_bytes': bound['original_file_bytes'],
        'original_source_native_pc_chunk_framing_valid': bound['source_complete_chunk_framing_verified'],
        'manifest_matches_exact_control_file': bound['single_loader_manifest_entry_verified'],
        'evidence_level': status,
        'owner_run_order_or_loader_toggle_verified': False,
        'carbon_asi_loaded_verified': False,
        'carbon_engine_resource_registration_verified': False,
        'carbon_in_game_rendering_verified': False,
        'undercover_asset_loaded_verified': False,
        'files_modified': False,
        'limitations': ('A/B/A file-read differences are captured filesystem '
                        'observations, not an attestation of game configuration '
                        'or original loader execution. Calibrating each ProcMon '
                        'capture with a normally accessed stock file reduces '
                        'empty-capture errors but cannot rule out file-specific '
                        'filters, caching, PID reuse or mapped I/O. A complete '
                        'read does not imply asset registration or rendering.'),
    }


def _private_text(path):
    file = _owner_file(path, MAX_CSV_BYTES)
    before = _stamp(file)
    text = file.read_text(encoding='utf-8-sig')
    if before != _stamp(file) or len(text.encode('utf-8')) > MAX_CSV_BYTES:
        raise ValueError('ProcMon CSV changed or exceeds capture bound')
    return text


def audit_owner_aba_files(
        game_directory, manifest_path, original_resource_path,
        sentinel_game_file, baseline_csv, control_csv, restore_csv, kind,
        *, windows_root_override_for_tests=None):
    """Owner-local files only: no writing, file creation or game actions."""
    root = Path(game_directory).absolute()
    # Stock TRACKS stream files can be far larger than 32 MiB. The
    # sentinel is stat-checked ONLY; no content is loaded into memory.
    sentinel_file = _owner_file(sentinel_game_file, 2 * 1024 * 1024 * 1024)
    if any(p.is_symlink() for p in (root, *root.parents)) or not root.is_dir():
        raise ValueError('Carbon game root missing or symlinked')
    try:
        relative_sentinel = sentinel_file.relative_to(root)
    except ValueError as exc:
        raise ValueError('Stock sentinel must reside inside Carbon test game') from exc
    if (len(relative_sentinel.parts) < 2 or
            relative_sentinel.name.lower().split('.')[-1] not in ('bun', 'bin')):
        raise ValueError('Select a known-stock native Carbon .BUN/.BIN sentinel')
    paths = [Path(x).absolute() for x in
             (manifest_path, original_resource_path, sentinel_game_file,
              baseline_csv, control_csv, restore_csv)]
    if len(set(paths)) != len(paths):
        raise ValueError('All owner-private original files and captures must be distinct')
    before = [_stamp(_owner_file(p, MAX_CSV_BYTES if index >= 3 else
                                 (2 * 1024 * 1024 * 1024 if index == 2
                                  else MAX_SOURCE_BYTES)))
              for index, p in enumerate(paths)]
    control = _private_text(paths[4])
    # Reuse entire V16 validated manifest/external-file selection logic.
    # Do not imply this is a runtime loading test.
    audit_owner_carbon_control_files(
        root, manifest_path, original_resource_path, control_csv, kind,
        windows_root_override_for_tests=windows_root_override_for_tests)
    from carbon_pc_resource_namespace_gate import read_private_carbon_roots
    resource = read_private_carbon_roots((original_resource_path,))[0]
    manifest = _owner_file(manifest_path, 4096).read_bytes()
    baseline = _private_text(paths[3])
    restore = _private_text(paths[5])
    if before != [_stamp(p) for p in paths]:
        raise ValueError('Owner source/capture changed during audit')

    if windows_root_override_for_tests is not None:
        win_root = windows_root_override_for_tests
    elif os.name == 'nt':
        win_root = str(root)
    else:
        raise ValueError('Owner-file A/B/A audit requires Windows')
    relative_resource = Path(original_resource_path).absolute().relative_to(root)
    external = ntpath.join(win_root, *relative_resource.parts)
    sentinel = ntpath.join(win_root, *relative_sentinel.parts)
    return audit_carbon_external_aba(
        manifest, resource, baseline, control, restore,
        win_root, external, sentinel, kind)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--carbon-game-dir', required=True)
    parser.add_argument('--xnfs-manifest', required=True)
    parser.add_argument('--original-carbon-bun', required=True)
    parser.add_argument('--stock-sentinel-bun', required=True)
    parser.add_argument('--baseline-csv', required=True)
    parser.add_argument('--control-csv', required=True)
    parser.add_argument('--restore-csv', required=True)
    parser.add_argument('--kind', choices=('geometry', 'texture'), required=True)
    args = parser.parse_args()
    print(json.dumps(audit_owner_aba_files(
        args.carbon_game_dir, args.xnfs_manifest, args.original_carbon_bun,
        args.stock_sentinel_bun, args.baseline_csv, args.control_csv,
        args.restore_csv, args.kind), indent=2))


if __name__ == '__main__':
    main()
