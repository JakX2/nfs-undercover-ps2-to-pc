#!/usr/bin/env python3
"""Audit Wii extracted disc categories without unpacking or distributing assets.

Supports ordinary directories, .zip, and .7z (via libarchive on Linux or the
7z executable). Only pathnames/file lengths are examined; no media is decoded.
"""
import argparse
from collections import Counter
import ctypes
from ctypes.util import find_library
import json
import os
from pathlib import Path
import shutil
import subprocess
import zipfile

DEFAULT_EXPECTED = [
    r'NFS\ZDIR.BIN',
    r'GLOBAL\GAMEPLAY.BIN',
    r'FRONTEND\FRONTB1.BUN',
    r'MOVIES\WIDESCREEN\NFS09_FMV3_ENGLISH_NTSC.VP6',
    r'MEMCARD\BANNER.RAW',
    r'CREDITS\POLISH.TXT',
]


def normalized(path: str):
    # Flatten the NFS.Unpacker ExtractXYZ folder convention to XYZ.
    p = path.replace('\\', '/').split('/')
    if not p or any(not x or x in ('.', '..') or ':' in x or '\x00' in x for x in p):
        return None
    if p[0].upper().startswith('EXTRACT') and len(p[0]) > 7:
        p[0] = p[0][7:]
    return '/'.join(p).upper()


def zip_items(path: Path):
    with zipfile.ZipFile(path) as file:
        for entry in file.infolist():
            if not entry.is_dir():
                yield entry.filename, entry.file_size


def sevenz_items_libarchive(path: Path):
    library = find_library('archive')
    if not library:
        raise RuntimeError('libarchive unavailable')
    lib = ctypes.CDLL(library)
    lib.archive_read_new.restype = ctypes.c_void_p
    for name in ('archive_read_support_filter_all', 'archive_read_support_format_all', 'archive_read_free'):
        getattr(lib, name).argtypes = [ctypes.c_void_p]
    lib.archive_read_open_filename.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_size_t]
    lib.archive_read_next_header.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p)]
    lib.archive_entry_pathname.argtypes = [ctypes.c_void_p]
    lib.archive_entry_pathname.restype = ctypes.c_char_p
    lib.archive_entry_size.argtypes = [ctypes.c_void_p]
    lib.archive_entry_size.restype = ctypes.c_int64
    a = lib.archive_read_new()
    if not a: raise RuntimeError('archive_read_new failed')
    try:
        lib.archive_read_support_filter_all(a)
        lib.archive_read_support_format_all(a)
        if lib.archive_read_open_filename(a, os.fsencode(path), 65536) != 0:
            raise RuntimeError(f'cannot open 7z: {path}')
        while True:
            e = ctypes.c_void_p()
            code = lib.archive_read_next_header(a, ctypes.byref(e))
            if code == 1: break  # ARCHIVE_EOF
            if code != 0: raise RuntimeError(f'7z header error {code}: {path}')
            raw = lib.archive_entry_pathname(e)
            name = raw.decode('utf-8', 'replace') if raw else ''
            size = int(lib.archive_entry_size(e))
            if name and not name.endswith('/') and size >= 0:
                yield name, size
    finally:
        lib.archive_read_free(a)


def sevenz_items_cli(path: Path):
    binary = shutil.which('7z') or shutil.which('7za') or shutil.which('7zz')
    if not binary: raise RuntimeError('7z executable not found')
    result = subprocess.run([binary, 'l', '-slt', str(path)], text=True,
                            capture_output=True, timeout=120, check=True)
    records = result.stdout.split('----------', 1)
    if len(records) != 2: raise ValueError('unexpected 7z -slt listing format')
    name, size, folder = None, None, False
    for line in records[1].splitlines() + ['']:
        if not line.strip():
            if name is not None and not folder and size is not None:
                yield name, size
            name, size, folder = None, None, False
        elif line.startswith('Path = '): name = line[7:]
        elif line.startswith('Size = '): size = int(line[7:])
        elif line.startswith('Folder = '): folder = line[9:] == '+'


def entries(source: Path):
    if source.is_dir():
        prefix = source.name if source.name.upper().startswith('EXTRACT') and len(source.name) > 7 else ''
        for path in source.rglob('*'):
            if path.is_file() and not path.is_symlink():
                relative = path.relative_to(source).as_posix()
                if prefix: relative = prefix + '/' + relative
                yield relative, path.stat().st_size
    elif source.suffix.lower() == '.zip':
        yield from zip_items(source)
    elif source.suffix.lower() == '.7z':
        if os.name == 'nt': yield from sevenz_items_cli(source)
        else:
            try: yield from sevenz_items_libarchive(source)
            except (RuntimeError, OSError): yield from sevenz_items_cli(source)
    else:
        raise ValueError(f'not a resource directory, zip or 7z: {source}')


def inspect(sources, expected):
    found = Counter()
    extensions, categories = Counter(), Counter()
    count, size, rejected = 0, 0, 0
    for source in sources:
        for rel, length in entries(source):
            path = normalized(rel)
            if path is None or length < 0:
                rejected += 1
                continue
            found[path] += 1
            category = path.split('/')[0]
            categories[category] += 1
            extensions[Path(path).suffix or '(none)'] += 1
            count += 1
            size += length
    return {
        'sources_scanned': len(sources),
        'file_entries': count,
        'sum_uncompressed_bytes': size,
        'categories': dict(sorted(categories.items())),
        'file_types': dict(extensions.most_common()),
        'casefold_duplicate_paths': sum(c - 1 for c in found.values() if c > 1),
        'rejected_archive_paths': rejected,
        'expected': {p: bool(found[normalized(p)]) for p in expected},
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('sources', nargs='+', type=Path, help='Extracted directory, ZIP, or 7z')
    parser.add_argument('--expect', action='append', default=None, help='Wii-disc-relative filename')
    parser.add_argument('--strict', action='store_true', help='Fail if any requested file is absent')
    args = parser.parse_args()
    result = inspect(args.sources, args.expect if args.expect is not None else DEFAULT_EXPECTED)
    print(json.dumps(result, indent=2))
    if args.strict and (not all(result['expected'].values()) or result['rejected_archive_paths']):
        raise SystemExit('Required resource paths missing or suspicious archive names found')
