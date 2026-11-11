#!/usr/bin/env python3
"""Strict read-only XNFSModFiles Carbon PC one-file control configuration.

The public XNFSModFiles/dllmain.cpp parses XNFSModFiles.txt lines as:
  FileStage,ResourceFileType,RelativeFileName
It probes the current working directory before scripts/. It uses an unsafe
fixed-size C parser, so this intentionally accepts a narrower safe subset.
Does not build/install/inject the public third-party ASI or change game files.
"""
import argparse
import json
import ntpath
from pathlib import Path

MAX_CONFIG_BYTES = 4096
MAX_LINE_BYTES = 260
ALLOWED_RESOURCE_TYPES = frozenset((1, 6))
ALLOWED_STAGES = frozenset((0, 1))


def parse_one_carbon_control(config_bytes, expected_relative_path):
    """Require one unambiguous original public-loader line only.

    A valid manifest is NOT proof the loader is installed or ran. Paths
    must be relative MODS/ subpaths, a single .BUN resource, and ASCII.
    The expected file is supplied explicitly by the owner and never
    returned in a report.
    """
    if (type(config_bytes) is not bytes or
            not 0 < len(config_bytes) <= MAX_CONFIG_BYTES or
            b'\x00' in config_bytes or
            b'\r' in config_bytes.replace(b'\r\n', b'')):
        raise ValueError('Unsafe Carbon external loader manifest')
    try:
        text = config_bytes.decode('ascii')
    except UnicodeDecodeError as exc:
        raise ValueError('XNFSModFiles parser requires ASCII control') from exc
    if not isinstance(expected_relative_path, str):
        raise ValueError('Invalid expected owner-local Carbon control path')

    def safe_path(value):
        if (not value or len(value) > 230 or
                any(ord(c) < 33 or ord(c) > 126 or c in ',#"'
                    for c in value)):
            raise ValueError('Unsafe Carbon control resource path')
        path = value.replace('/', '\\')
        if ntpath.isabs(path) or ntpath.splitdrive(path)[0]:
            raise ValueError('Carbon control path must be relative')
        parts = path.split('\\')
        if (len(parts) < 2 or parts[0].casefold() != 'mods' or
                any(part in ('', '.', '..') or ':' in part for part in parts) or
                not parts[-1].lower().endswith('.bun')):
            raise ValueError('Carbon control must be a bounded MODS/*.BUN path')
        return '\\'.join(x.casefold() for x in parts)

    target = safe_path(expected_relative_path)
    entries = []
    for raw in text.splitlines():
        if len(raw.encode('ascii')) > MAX_LINE_BYTES:
            raise ValueError('XNFSModFiles input line exceeds safe C buffer')
        if not raw or raw.startswith('#'):
            continue
        if raw != raw.strip() or '#' in raw:
            raise ValueError('Ambiguous whitespace or inline comments refused')
        fields = raw.split(',')
        if len(fields) != 3 or not all(fields):
            raise ValueError('Expected exact XNFSModFiles stage,type,path row')
        stage, resource_type, filename = fields
        if (stage not in ('0', '1') or resource_type not in ('1', '6')):
            raise ValueError('Only known Carbon loader stages and types 1/6')
        if safe_path(filename) != target:
            raise ValueError('Manifest path differs from owner control file')
        entries.append((int(stage), int(resource_type)))
    if len(entries) != 1:
        raise ValueError('Exactly one external native Carbon control required')
    stage, kind = entries[0]
    return {
        'scope': 'READ_ONLY_XNFSMODFILES_CARBON_CONFIG_PARSE_NOT_RUNTIME',
        'entries': 1,
        'loader_stage': 'preinit' if stage == 0 else 'postinit',
        'resource_file_type': kind,
        'relative_control_path_match': True,
        'manifest_safe_single_source_entry': True,
        'carbon_asi_loaded_verified': False,
        'carbon_create_resource_called_verified': False,
        'carbon_begin_loading_called_verified': False,
        'carbon_model_registration_verified': False,
        'carbon_rendering_verified': False,
        'local_files_modified': False,
    }


def audit_manifest_file(manifest, expected_relative_path):
    """Read a single owner-private config and return only nonprivate fields."""
    original = Path(manifest).absolute()
    if (any(p.is_symlink() for p in (original, *original.parents)) or
            not original.is_file() or
            not 0 < original.stat().st_size <= MAX_CONFIG_BYTES):
        raise ValueError('Invalid owner-private XNFSModFiles configuration')
    before = original.stat()
    data = original.read_bytes()
    after = original.stat()
    if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) != (
            after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns):
        raise ValueError('Loader manifest changed during audit')
    return parse_one_carbon_control(data, expected_relative_path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--xnfs-manifest', required=True,
                        help='owner-private existing XNFSModFiles.txt')
    parser.add_argument('--expected-control-relative-path', required=True,
                        help=r'owner-private relative Carbon path, e.g. MODS\KnownGood.BUN')
    args = parser.parse_args()
    print(json.dumps(audit_manifest_file(
        args.xnfs_manifest, args.expected_control_relative_path), indent=2))


if __name__ == '__main__':
    main()
