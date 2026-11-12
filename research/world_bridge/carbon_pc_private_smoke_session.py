#!/usr/bin/env python3
"""Opt-in, local-only, reversible Carbon PC existing-texture-slot smoke session.

Default `preflight` only reads files. `prepare` creates a private backup and
manifest in a NEW directory, never touching the installed stream. `install` and
`restore` require explicit --apply --game-closed, reject a running NFSC.exe on
Windows, verify staged/pristine byte identity outside exactly one validated
original texture image span, and atomically replace only TRACKS/STREAML5RB.BUN.

Only for users who own a private Carbon PC installation. No network or game
process execution, no new texture hash registration, and no runtime proof.
Local manifest and backup contain private paths/original game bytes: NEVER SHARE.
"""

import argparse
import csv
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

MAX_STREAM = 2 * 1024 * 1024 * 1024
MAX_BUN = 8 * 1024 * 1024
COPY_BLOCK = 1024 * 1024
FORMAT = 'nfsuc-carbon-existing-slot-session-v1'
MANIFEST = 'session.json'
BACKUP = 'STREAML5RB.BUN.private-original-backup'
LOCK = '.session-in-use'


def _file(path, limit=None):
    if limit is None:
        limit = MAX_STREAM
    p = Path(path).absolute()
    # Reject both symlink targets and symlinked directories, not only final leaf.
    if any(c.is_symlink() for c in (p, *p.parents)):
        raise ValueError('Symlinks are not permitted in test input paths')
    if not p.is_file() or not 0 < p.stat().st_size <= limit:
        raise ValueError('Missing, empty, oversized or non-regular input file')
    return p.resolve(strict=True)


def _installed_path(path):
    p = _file(path)
    if p.name.casefold() != 'streaml5rb.bun' or p.parent.name.casefold() != 'tracks':
        raise ValueError('Installed target must be TRACKS/STREAML5RB.BUN')
    return p


def _digest(path):
    sha = hashlib.sha256()
    with path.open('rb') as fp:
        while block := fp.read(COPY_BLOCK):
            sha.update(block)
    return sha.hexdigest()


def _changed_within(pristine, staged, left, size):
    if type(left) is not int or type(size) is not int or left < 0 or size <= 0:
        raise ValueError('Invalid verified image span')
    n = pristine.stat().st_size
    if staged.stat().st_size != n or left + size > n:
        raise ValueError('Staged stream size or image bounds mismatch')
    altered = 0
    pos = 0
    with pristine.open('rb') as aa, staged.open('rb') as bb:
        while a := aa.read(COPY_BLOCK):
            b = bb.read(len(a))
            if len(b) != len(a):
                raise ValueError('Short staged read')
            if a != b:
                lo = max(0, left - pos)
                hi = min(len(a), left + size - pos)
                if lo >= hi or a[:lo] != b[:lo] or a[hi:] != b[hi:]:
                    raise ValueError('Changes outside the selected image span')
                altered += sum(x != y for x, y in zip(a[lo:hi], b[lo:hi]))
            pos += len(a)
        if bb.read(1) or pos != n or altered == 0:
            raise ValueError('Missing or incomplete isolated image replacement')
    return altered


def _span(bundle, pristine, section, codec, slot):
    # Delegate address calculations to the source-backed existing-slot gate.
    from carbon_pc_runtime_span_attestation import existing_image_span
    return existing_image_span(bundle, pristine, section, codec, slot)


def preflight(bundle, pristine, staged, installed, section, codec, slot):
    if type(section) is not int or section not in (141, 142):
        raise ValueError('Only original Carbon PC sections 141 and 142 supported')
    if codec not in ('DXT1', 'DXT5') or type(slot) is not int or slot < 0:
        raise ValueError('Invalid original PC codec/slot selection')
    bundle = _file(bundle, MAX_BUN)
    pristine, staged, installed = _file(pristine), _file(staged), _installed_path(installed)
    paths = [bundle, pristine, staged, installed]
    if len(set(paths)) != 4 or any(os.path.samefile(a, b) for i, a in enumerate(paths) for b in paths[i+1:]):
        raise ValueError('Original, stage, installed and bundle must be distinct files')
    if any(p.stat().st_size != pristine.stat().st_size for p in (staged, installed)):
        raise ValueError('Stream sizes differ')
    left, length = _span(bundle, pristine, section, codec, slot)
    changed = _changed_within(pristine, staged, left, length)
    originals = [_digest(p) for p in paths]
    if originals[1] != originals[3] or originals[1] == originals[2]:
        raise ValueError('Installed file is not pristine or stage is unchanged')
    return {'format': FORMAT, 'bundle': str(bundle), 'pristine': str(pristine),
            'staged': str(staged), 'installed': str(installed), 'section': section,
            'codec': codec, 'slot': slot, 'image_start': left,
            'image_length': length, 'changed_bytes': changed,
            'stream_length': pristine.stat().st_size,
            'bundle_sha256': originals[0], 'pristine_sha256': originals[1],
            'staged_sha256': originals[2]}


def _public_report(status, manifest, **extras):
    return {'gate': 'PRIVATE_EXISTING_SLOT_SMOKE_SESSION_NOT_RENDERING',
            'state': status, 'section': manifest['section'],
            'codec': manifest['codec'], 'slot': manifest['slot'],
            'changed_image_bytes': manifest['changed_bytes'],
            'image_span_bytes': manifest['image_length'],
            'original_stream_bytes': manifest['stream_length'],
            'private_paths_and_hashes_omitted': True, **extras}


def _create_manifest_exclusive(path, data):
    # Only used to create the initial manifest, never to update state.
    text = json.dumps(data, sort_keys=True, indent=2) + '\n'
    with path.open('x', encoding='utf-8') as fp:
        fp.write(text)
        fp.flush()
        os.fsync(fp.fileno())
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass


def prepare(session_dir, bundle, pristine, staged, installed, section, codec, slot):
    manifest = preflight(bundle, pristine, staged, installed, section, codec, slot)
    root = Path(session_dir).absolute()
    if any(p.is_symlink() for p in (root, *root.parents)):
        raise ValueError('Symlinked session directories are forbidden')
    game_root = Path(manifest['installed']).parent.parent
    if root == game_root or game_root in root.parents:
        raise ValueError('Private backup session must be outside the game directory')
    # Exclusive NEW directory: never overwrite backups from an earlier attempt.
    root.mkdir(mode=0o700, parents=False, exist_ok=False)
    backup = root / BACKUP
    try:
        with _file(manifest['installed']).open('rb') as src, backup.open('xb') as dst:
            shutil.copyfileobj(src, dst, COPY_BLOCK)
            dst.flush()
            os.fsync(dst.fileno())
        if _digest(backup) != manifest['pristine_sha256']:
            raise ValueError('New private backup differs from pristine stream')
        try:
            os.chmod(backup, 0o600)
        except OSError:
            pass
        _create_manifest_exclusive(root / MANIFEST, manifest)
    except BaseException:
        # Keep the directory and any copied bytes for manual examination; in
        # particular, we never modify or remove the installed original.
        raise
    return _public_report('backup_created_no_installation_change', manifest)


def _read_manifest(session_dir):
    root = Path(session_dir).absolute()
    if any(p.is_symlink() for p in (root, *root.parents)):
        raise ValueError('Symlinked session directory is forbidden')
    path = _file(root / MANIFEST, 16384)
    with path.open('r', encoding='utf-8') as fp:
        data = json.load(fp)
    required = ('format', 'bundle', 'pristine', 'staged', 'installed', 'section',
                'codec', 'slot', 'image_start', 'image_length', 'changed_bytes',
                'stream_length', 'bundle_sha256', 'pristine_sha256', 'staged_sha256')
    if not isinstance(data, dict) or set(data) != set(required) or data['format'] != FORMAT:
        raise ValueError('Unsupported or incomplete private session manifest')
    for k in ('section', 'slot', 'image_start', 'image_length', 'changed_bytes', 'stream_length'):
        if type(data[k]) is not int or data[k] < 0:
            raise ValueError('Invalid session numeric field')
    if data['section'] not in (141, 142) or data['codec'] not in ('DXT1', 'DXT5') or data['image_length'] <= 0:
        raise ValueError('Invalid session target')
    for k in ('bundle_sha256', 'pristine_sha256', 'staged_sha256'):
        if not isinstance(data[k], str) or len(data[k]) != 64 or any(c not in '0123456789abcdef' for c in data[k]):
            raise ValueError('Invalid session digest')
    for k in ('bundle', 'pristine', 'staged', 'installed'):
        if not isinstance(data[k], str) or not Path(data[k]).is_absolute():
            raise ValueError('Invalid session path')
    return root, data


def _validate_session_sources(root, manifest):
    bundle = _file(manifest['bundle'], MAX_BUN)
    clean = _file(manifest['pristine'])
    staged = _file(manifest['staged'])
    installed = _installed_path(manifest['installed'])
    backup = _file(root / BACKUP)
    paths = [bundle, clean, staged, installed, backup]
    if len(set(paths)) != 5 or any(os.path.samefile(a, b) for i, a in enumerate(paths) for b in paths[i+1:]):
        raise ValueError('Session files unexpectedly alias one another')
    expected_size = manifest['stream_length']
    if any(p.stat().st_size != expected_size for p in paths[1:]):
        raise ValueError('Private session file size changed')
    for p, key in ((bundle, 'bundle_sha256'), (clean, 'pristine_sha256'),
                   (staged, 'staged_sha256'), (backup, 'pristine_sha256')):
        if _digest(p) != manifest[key]:
            raise ValueError('A verified source or backup has changed')
    left, length = _span(bundle, clean, manifest['section'], manifest['codec'], manifest['slot'])
    if (left, length) != (manifest['image_start'], manifest['image_length']):
        raise ValueError('Source-derived original image span changed')
    if _changed_within(clean, staged, left, length) != manifest['changed_bytes']:
        raise ValueError('Staged image has changed outside its verified state')
    return installed, backup


def status(session_dir):
    root, manifest = _read_manifest(session_dir)
    installed, _ = _validate_session_sources(root, manifest)
    digest = _digest(installed)
    if digest == manifest['pristine_sha256']:
        state = 'original_installed'
    elif digest == manifest['staged_sha256']:
        state = 'stage_installed_not_rendering_proof'
    else:
        state = 'unexpected_installed_bytes_refuse_to_overwrite'
    return _public_report(state, manifest)


@contextmanager
def _lock(root):
    lock = root / LOCK
    created = False
    try:
        with lock.open('x', encoding='utf-8') as fp:
            fp.write('private-local-operation\n')
        created = True
        yield
    finally:
        # Never unlink another process's preexisting lock.
        if created:
            try:
                lock.unlink()
            except FileNotFoundError:
                pass


def _require_game_closed(ack):
    if not ack:
        raise ValueError('Explicit --game-closed acknowledgement required')
    if sys.platform != 'win32':
        raise ValueError('Install/restore is Windows-only; dry-run tests are portable')
    # Conservative additional check: fail closed if tasklist cannot determine state.
    try:
        p = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq NFSC.exe', '/FO', 'CSV', '/NH'],
                           capture_output=True, text=True, check=True, timeout=15)
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        raise ValueError('Cannot confirm NFSC.exe is closed') from exc
    lines = [x for x in p.stdout.splitlines() if x.strip()]
    for row in csv.reader(lines):
        if row and row[0].strip().casefold() == 'nfsc.exe':
            raise ValueError('NFSC.exe is running; close the game first')
        # tasklist prints a text notice when no matching task exists.
        if row and not row[0].strip().casefold().startswith('info:'):
            raise ValueError('Unrecognized process status; refusing to replace game file')
    if not lines:
        raise ValueError('Empty tasklist result; cannot prove game is closed')


def _atomic_copy_into(source, destination, expected_sha):
    """Copy to an exclusive same-dir temp, verify hash, then atomic replace."""
    handle, name = tempfile.mkstemp(prefix='.nfsuc-private-', suffix='.tmp', dir=destination.parent)
    temp = Path(name)
    try:
        with os.fdopen(handle, 'wb') as out, source.open('rb') as src:
            shutil.copyfileobj(src, out, COPY_BLOCK)
            out.flush()
            os.fsync(out.fileno())
        shutil.copystat(destination, temp)
        if _digest(temp) != expected_sha:
            raise ValueError('Temporary stream failed checksum validation')
        os.replace(temp, destination)
        if _digest(destination) != expected_sha:
            raise ValueError('Installed stream failed post-replacement checksum')
    finally:
        if temp.exists():
            temp.unlink()


def apply_session(session_dir, operation, confirmed=False, game_closed=False):
    if operation not in ('install', 'restore') or not confirmed:
        raise ValueError('A supported operation and explicit --apply are required')
    root, manifest = _read_manifest(session_dir)
    with _lock(root):
        installed, backup = _validate_session_sources(root, manifest)
        now = _digest(installed)
        original = manifest['pristine_sha256']
        staged = manifest['staged_sha256']
        if operation == 'install':
            if now != original:
                raise ValueError('Install requires unmodified original in installed target')
            _require_game_closed(game_closed)
            source, expected = _file(manifest['staged']), staged
            next_state = 'stage_installed_not_rendering_proof'
        else:
            if now not in (original, staged):
                raise ValueError('Refusing restore: unexpected installed stream modifications')
            if now == original:
                return _public_report('already_original_no_files_modified', manifest)
            _require_game_closed(game_closed)
            source, expected = backup, original
            next_state = 'restored_original_verified'
        _atomic_copy_into(source, installed, expected)
        return _public_report(next_state, manifest)


def evidence(session_dir, procmon_csv):
    root, manifest = _read_manifest(session_dir)
    _validate_session_sources(root, manifest)
    if _digest(_installed_path(manifest['installed'])) != manifest['staged_sha256']:
        raise ValueError('Evidence requires the stage currently installed, not an original/unknown stream')
    from carbon_pc_runtime_span_attestation import attest
    return attest(manifest['bundle'], manifest['pristine'], manifest['staged'],
                  manifest['installed'], procmon_csv, manifest['section'],
                  manifest['codec'], manifest['slot'])


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='command', required=True)
    for command in ('preflight', 'prepare'):
        s = sub.add_parser(command, help='Read-only check or create backup session; never install')
        for arg in ('carbon-bun', 'pristine-stream', 'staged-stream', 'installed-stream'):
            s.add_argument('--' + arg, type=Path, required=True)
        s.add_argument('--section', type=int, choices=(141, 142), required=True)
        s.add_argument('--codec', choices=('DXT1', 'DXT5'), required=True)
        s.add_argument('--slot', type=int, required=True)
        if command == 'prepare':
            s.add_argument('--session-dir', type=Path, required=True)
    for command in ('status', 'install', 'restore', 'evidence'):
        s = sub.add_parser(command)
        s.add_argument('--session-dir', type=Path, required=True)
        if command in ('install', 'restore'):
            s.add_argument('--apply', action='store_true', help='Explicitly opt in to file replacement')
            s.add_argument('--game-closed', action='store_true', help='Acknowledge game is closed; tool also checks')
        if command == 'evidence':
            s.add_argument('--procmon-csv', type=Path, required=True)
    a = p.parse_args()
    if a.command in ('preflight', 'prepare'):
        fn = preflight if a.command == 'preflight' else prepare
        args = ([a.session_dir] if a.command == 'prepare' else []) + [
            a.carbon_bun, a.pristine_stream, a.staged_stream, a.installed_stream,
            a.section, a.codec, a.slot]
        result = fn(*args)
        if a.command == 'preflight':
            result = _public_report('preflight_only_no_files_modified', result)
    elif a.command == 'status':
        result = status(a.session_dir)
    elif a.command == 'evidence':
        result = evidence(a.session_dir, a.procmon_csv)
    else:
        result = apply_session(a.session_dir, a.command, a.apply, a.game_closed)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
