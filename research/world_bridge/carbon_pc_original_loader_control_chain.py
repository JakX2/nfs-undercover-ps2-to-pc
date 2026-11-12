#!/usr/bin/env python3
"""Read-only, owner-local Carbon external loader KNOWN-ORIGINAL control chain.

Binds one XNFSModFiles.txt entry, its original PC-shaped Carbon resource
and an owner-captured ProcMon CSV to the SAME absolute Windows path.
Does NOT install a mod, launch NFSC.exe, read a process, or claim that
Carbon registered/rendered the original file or any Undercover scenery.

Only derived nonprivate counts and evidence flags are printed.
"""
import argparse
import json
import ntpath
import os
from pathlib import Path

from carbon_pc_xnfsmodfiles_manifest_gate import (
    MAX_CONFIG_BYTES, parse_one_carbon_control,
)
from carbon_pc_external_resource_read_gate import (
    MAX_CSV_BYTES, MAX_SOURCE_BYTES, _verify_native_resource,
    _windows_bundle_path, audit_external_resource_trace,
)
from carbon_pc_resource_namespace_gate import read_private_carbon_roots


def _windows_root(value):
    if not isinstance(value, str) or not value or any(ord(c) < 32 for c in value):
        raise ValueError('Expected an absolute Carbon PC Windows game root')
    p = value.replace('/', '\\')
    drive, tail = ntpath.splitdrive(p)
    if (len(drive) != 2 or not drive[0].isascii() or
            not drive[0].isalpha() or drive[1] != ':' or
            not tail.startswith('\\')):
        raise ValueError('Expected a Windows Carbon game root with a drive')
    normalized = ntpath.normcase(ntpath.normpath(p))
    if normalized == ntpath.normcase(drive + '\\'):
        raise ValueError('Carbon test game root must not be a drive root')
    return normalized


def audit_carbon_original_external_control(
        manifest_bytes, original_resource_bytes, procmon_text,
        windows_game_root, windows_resource_path, kind):
    """Correlate configuration, actual owner source bytes and same-file I/O.

    Pure in-memory original-free function, suitable for synthetic CI.
    A passing FILE_READ status is STILL NOT proof of engine registration,
    loader execution, successful rendering or original resource provenance.
    """
    game = _windows_root(windows_game_root)
    resource = _windows_bundle_path(windows_resource_path)
    if type(original_resource_bytes) is not bytes:
        raise ValueError('Original Carbon PC resource must be immutable bytes')
    if kind not in ('geometry', 'texture'):
        raise ValueError('Explicit native Carbon PC resource kind required')

    try:
        relative = ntpath.relpath(resource, game)
    except ValueError as exc:
        raise ValueError('External resource on different Windows drive') from exc
    if relative.startswith('..\\') or relative in ('.', '..'):
        raise ValueError('External resource is outside Carbon PC game root')
    # The original loader expects a relative path from its active working
    # directory, not the system drive or a configurable external root.
    manifest = parse_one_carbon_control(manifest_bytes, relative)
    original = _verify_native_resource(original_resource_bytes, kind)
    io = audit_external_resource_trace(
        procmon_text, resource, len(original_resource_bytes), kind)

    observed = io['same_pid_ordered_open_read_observed']
    full = io['entire_file_read_by_one_process_observed']
    if full:
        level = 'EXACT_ORIGINAL_PC_FILE_READ_FULL_NOT_REGISTRATION'
    elif observed:
        level = 'EXACT_ORIGINAL_PC_FILE_READ_PARTIAL_OR_UNKNOWN_NOT_REGISTRATION'
    elif io['successful_target_open_events'] > 0:
        level = 'ORIGINAL_PC_FILE_OPEN_OBSERVED_NO_READ'
    else:
        level = 'NO_POSITIVE_ORIGINAL_PC_FILE_IO_EVIDENCE'
    # Never forward the original path, file bytes, resource names or
    # PID. Both component reports already return redacted scalars.
    return {
        'scope': 'OFFLINE_SOURCE_BOUND_CARBON_CONTROL_NOT_RUNTIME_REGISTRATION',
        'source_compatible_with_native_pc_parser': True,
        'source_kind': original['resource_kind'],
        'source_resource_records': original['source_resource_records'],
        'single_loader_manifest_entry_verified': True,
        'loader_stage': manifest['loader_stage'],
        'loader_resource_type': manifest['resource_file_type'],
        'configured_path_matches_original_file': True,
        'capture_exact_filename_match': True,
        'same_pid_ordered_open_read_observed': observed,
        'entire_original_file_read_by_one_process_observed': full,
        'read_bytes_covered_by_one_process': io['verified_file_bytes_read_for_one_process'],
        'original_file_bytes': len(original_resource_bytes),
        'control_evidence': level,
        'original_retail_provenance_verified': False,
        'xnfsmodfiles_asi_loaded_verified': False,
        'resource_create_begin_loading_invoked_verified': False,
        'native_carbon_resource_registered_verified': False,
        'in_game_visual_change_verified': False,
        'undercover_model_loaded_verified': False,
        'files_modified': False,
        'limitations': ('This audit establishes source structure, a single '
                        'matching config path and captured disk I/O only. '
                        'ProcMon may miss cached/mapped operations or be '
                        'captured outside the relevant session. Neither '
                        'file read nor filename match establishes engine '
                        'resource registration, on-screen rendering, '
                        'or ownership/provenance of a source file.'),
    }


def _owner_file(path, limit):
    p = Path(path).absolute()
    if (any(v.is_symlink() for v in (p, *p.parents)) or
            not p.is_file() or not 0 < p.stat().st_size <= limit):
        raise ValueError('Missing or unsafe owner-private Carbon control file')
    return p


def _stamp(path):
    state = path.stat()
    return state.st_dev, state.st_ino, state.st_size, state.st_mtime_ns


def audit_owner_carbon_control_files(
        game_directory, manifest_path, original_resource_path, procmon_csv,
        kind, *, windows_root_override_for_tests=None):
    """Read private inputs without changes, bind them to the actual game root.

    On Windows, the game root is taken from a native local path. The
    override is for ORIGINAL-FREE CI fixtures on non-Windows hosts and
    does not create runtime evidence.
    """
    root = Path(game_directory).absolute()
    if any(p.is_symlink() for p in (root, *root.parents)) or not root.is_dir():
        raise ValueError('Invalid Carbon PC test game directory')
    manifest = _owner_file(manifest_path, MAX_CONFIG_BYTES)
    resource = _owner_file(original_resource_path, MAX_SOURCE_BYTES)
    capture = _owner_file(procmon_csv, MAX_CSV_BYTES)

    try:
        relative_manifest = manifest.relative_to(root)
        relative_resource = resource.relative_to(root)
    except ValueError as exc:
        raise ValueError('Manifest and source must be under Carbon PC test copy') from exc
    config_location = tuple(p.casefold() for p in relative_manifest.parts)
    if config_location not in (
            ('xnfsmodfiles.txt',), ('scripts', 'xnfsmodfiles.txt')):
        raise ValueError('Manifest must be in game root or scripts directory')
    if (len(relative_resource.parts) < 2 or
            relative_resource.parts[0].casefold() != 'mods' or
            not relative_resource.name.lower().endswith('.bun')):
        raise ValueError('Source must be one relative MODS/*.BUN original control')

    # The public loader probes working directory XNFSModFiles.txt first.
    # Do not permit a second, shadowing manifest to make the evidence
    # ambiguous about WHICH config the loader would have used.
    choices = (root / 'XNFSModFiles.txt',
               root / 'scripts' / 'XNFSModFiles.txt')
    existing = [p for p in choices if p.is_file() or p.is_symlink()]
    if len(existing) != 1 or existing[0] != manifest:
        raise ValueError('Ambiguous, shadowed or missing Carbon manifest')
    if len({manifest, resource, capture}) != 3:
        raise ValueError('Private evidence files must be distinct')

    before = [_stamp(p) for p in (manifest, resource, capture)]
    raw_manifest = manifest.read_bytes()
    # Reuse strict private resource input bounds and mutation checking.
    raw_resource = read_private_carbon_roots((resource,))[0]
    procmon_text = capture.read_text(encoding='utf-8-sig')
    after = [_stamp(p) for p in (manifest, resource, capture)]
    if before != after:
        raise ValueError('Owner-private control changed during audit')

    if windows_root_override_for_tests is not None:
        win_root = windows_root_override_for_tests
    elif os.name == 'nt':
        win_root = str(root)
    else:
        raise ValueError('Original local-file Carbon control requires Windows')
    windows_resource = ntpath.join(win_root, *relative_resource.parts)
    return audit_carbon_original_external_control(
        raw_manifest, raw_resource, procmon_text,
        win_root, windows_resource, kind)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--carbon-game-dir', required=True,
                        help='owner-private, separate backed-up Carbon PC test copy')
    parser.add_argument('--xnfs-manifest', required=True,
                        help='existing root or scripts/XNFSModFiles.txt')
    parser.add_argument('--original-carbon-bun', required=True,
                        help='known-good original PC root file under game MODS')
    parser.add_argument('--kind', choices=('geometry', 'texture'), required=True)
    parser.add_argument('--procmon-csv', required=True,
                        help='owner-captured NFSC.exe original file I/O events')
    args = parser.parse_args()
    print(json.dumps(audit_owner_carbon_control_files(
        args.carbon_game_dir, args.xnfs_manifest, args.original_carbon_bun,
        args.procmon_csv, args.kind), indent=2))


if __name__ == '__main__':
    main()
