#!/usr/bin/env python3
"""Owner-local Wii ELF symbol bridge for NWiiRecomp's expected CSV/TOML formats.

This is a static-analysis setup tool, not a PowerPC translator or hardware emulator.
Its generated CSV contains privately derived game symbols and MUST NOT be committed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from wii_recomp_preflight import PreflightError, emit, parse_elf, safe_symbol


def canonical_functions(functions: list[tuple[int, int, str, int]]):
    """Select one deterministic symbol per guest address, matching V1 precedence."""
    result: dict[int, tuple[tuple[bool, bool, int, str], int, str]] = {}
    for addr, size, name, binding in functions:
        if not (0 <= addr <= 0xffffffff) or size < 4 or addr & 3 or size & 3:
            raise PreflightError(f"bad PPC function span: 0x{addr:08X} size={size}")
        candidate = (binding == 1, bool(name), -len(name), name)
        if addr not in result or candidate > result[addr][0]:
            result[addr] = (candidate, size, name)
    return [(addr, result[addr][1], result[addr][2]) for addr in sorted(result)]


def emit_nwii(elf_blob: bytes, dol_blob: bytes, output: Path, nwii_root: Path) -> dict:
    """Verify the actual ELF/DOL pair and emit owner-private NWiiRecomp files."""
    nwii_root = nwii_root.resolve()
    if not (nwii_root / 'nWiiRecomp' / 'src' / 'main.cpp').is_file():
        raise PreflightError('NWiiRecomp source root not found (missing nWiiRecomp/src/main.cpp)')
    runtime_source = nwii_root / 'nWiiRuntime'
    if not (runtime_source / 'CMakeLists.txt').is_file():
        raise PreflightError('NWiiRecomp runtime source directory not found')
    output = output.resolve()
    if output == nwii_root or nwii_root in output.parents:
        raise PreflightError('owner-private outputs must live OUTSIDE the upstream source tree')
    base = emit(elf_blob, dol_blob, output)
    funcs = canonical_functions(parse_elf(elf_blob)['functions'])
    if len(funcs) != base['unique_function_addresses']:
        raise PreflightError('NWii symbol map count disagrees with original preflight')

    csv_file = output / 'undercover-nwii-symbols.csv'
    # The upstream CSV reader discards its first line and consumes only columns 1/2.
    # It uses std::getline(..., ',') rather than RFC 4180 quoting. Names must be
    # syntactically safe, unique, comma-free and possess eight-digit hex addresses.
    contents = 'Name,Location,Size\n' + ''.join(
        f'fn_{addr:08X}_{safe_symbol(name)},{addr:08X},{size}\n'
        for addr, size, name in funcs)
    csv_file.write_text(contents, encoding='utf-8')

    # NWiiRecomp's load_unpacked_game() accepts a raw .dol path as input_game_dir
    # for static analysis. Actual boot will still require full source filesystem.
    # Do NOT copy the retail binary. Only point the config at the owner's original.
    # Supply a concrete path at generation time in main() via --dol.
    return {'csv_path': str(csv_file), 'symbol_count': len(funcs),
            'csv_sha256': hashlib.sha256(contents.encode()).hexdigest(),
            'runtime_source_dir': str(runtime_source),
            'base': base}


def quote_toml_path(path: Path) -> str:
    """Encode absolute filesystem paths as TOML basic strings."""
    return json.dumps(path.resolve().as_posix(), ensure_ascii=True)


def write_config(output: Path, dol_path: Path, nwii_root: Path) -> Path:
    output = output.resolve()
    path = output / 'undercover-nwii.toml'
    payload = '\n'.join([
        '# Generated owner-local experimental NWiiRecomp config.',
        '# This DOL-only run verifies translation, NOT Wii IOS/graphics/game boot.',
        'project_name = "NFSUndercoverWii"',
        'input_game_dir = ' + quote_toml_path(dol_path),
        'output_dir = ' + quote_toml_path(output / 'nwii-generated'),
        'runtime_source_dir = ' + quote_toml_path(nwii_root / 'nWiiRuntime'),
        'symbols_csv = ' + quote_toml_path(output / 'undercover-nwii-symbols.csv'),
        'split_output = true',
        'instructions_per_file = 10000',
        ''])
    path.write_text(payload, encoding='utf-8')
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--elf', type=Path, required=True)
    parser.add_argument('--dol', type=Path, required=True)
    parser.add_argument('--nwii-root', type=Path, required=True,
                        help='unpacked NWiiRecomp-master root containing nWiiRecomp and nWiiRuntime')
    parser.add_argument('--output', type=Path, required=True,
                        help='owner-private scratch directory outside the recompiler source checkout')
    args = parser.parse_args()
    try:
        elf = args.elf.read_bytes()
        dol = args.dol.read_bytes()
        info = emit_nwii(elf, dol, args.output, args.nwii_root)
        config = write_config(args.output, args.dol, args.nwii_root)
        # Summary must be safe for public aggregate discussion, unlike the CSV/TOML.
        report = {'unique_symbols': info['symbol_count'],
                  'elf_sha256': info['base']['elf_sha256'],
                  'dol_sha256': info['base']['dol_sha256'],
                  'entry': info['base']['elf_entry'],
                  'nwii_config_was_generated': config.is_file(),
                  'translation_executed': False}
        (args.output / 'nwii_setup_summary.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
        print(json.dumps(report, indent=2))
    except (PreflightError, OSError) as exc:
        parser.exit(1, f'NWiiRecomp bridge failed: {exc}\n')


if __name__ == '__main__':
    main()
