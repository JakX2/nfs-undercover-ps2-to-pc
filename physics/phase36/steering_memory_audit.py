#!/usr/bin/env python3
"""Phase 36: SHA-gated, read-only PS2 steering memory-access census.

Lists *static* loads/stores in verified PS2 DoHumanSteering candidates.
A displacement match does not identify a C++ field or establish PC layouts.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from physics.phase33.verify_ps2_human_steering import (
    BUILDS, load_segments, verify, word_at,
)

MEMORY_OPERATIONS = {
    0x20: ('lb', 'read'), 0x21: ('lh', 'read'),
    0x22: ('lwl', 'read'), 0x23: ('lw', 'read'),
    0x24: ('lbu', 'read'), 0x25: ('lhu', 'read'),
    0x26: ('lwr', 'read'),
    0x28: ('sb', 'write'), 0x29: ('sh', 'write'),
    0x2a: ('swl', 'write'), 0x2b: ('sw', 'write'),
    0x2e: ('swr', 'write'),
    0x31: ('lwc1', 'read'), 0x35: ('ldc1', 'read'),
    0x39: ('swc1', 'write'), 0x3d: ('sdc1', 'write'),
    0x37: ('ld', 'read'), 0x3f: ('sd', 'write'),
}
# Candidate numeric offsets from earlier research, not inferred field IDs.
OFFSETS = (0x48, 0x64, 0x8c, 0x9c, 0xc0, 0xd8, 0x160, 0x188, 0x19c)
# Evidence labels attach to verified instruction addresses, never to all
# accesses using the same displacement.
ANCHORS = {
    'undercover_ps2': {
        0x408304: ('chassis_input', 0x8c, 'read'),
        0x4083A0: ('chassis_input', 0x8c, 'read'),
        0x408708: ('racer_shaped_input_write', 0x19c, 'write'),
        0x408714: ('racer_steering_write', 0x188, 'write'),
    },
    'carbon_ps2': {
        0x3D5920: ('chassis_input', 0x8c, 'read'),
        0x3D59C0: ('chassis_input', 0x8c, 'read'),
        0x3D5B04: ('racer_shaped_input_write', 0x19c, 'write'),
        0x3D5B14: ('racer_steering_write', 0x188, 'write'),
    },
}


def decode_memory_word(word: int, pc: int) -> dict | None:
    """Decode ordinary I-type memory instructions; not a disassembler."""
    if not (0 <= word <= 0xffffffff) or not (0 <= pc <= 0xffffffff):
        raise ValueError('expected unsigned 32-bit instruction/address')
    opcode = word >> 26
    operation = MEMORY_OPERATIONS.get(opcode)
    if operation is None:
        return None
    displacement = word & 0xffff
    if displacement & 0x8000:
        displacement -= 0x10000
    return {
        'pc': f'0x{pc:08X}', 'mnemonic': operation[0],
        'direction': operation[1],
        'base_register': f'r{(word >> 21) & 0x1f}',
        'target_register': (f'f{(word >> 16) & 0x1f}'
                            if opcode in (0x31, 0x35, 0x39, 0x3d)
                            else f'r{(word >> 16) & 0x1f}'),
        'signed_displacement': displacement,
    }


def scan_function(data: bytes, segments: list, start: int, end: int,
                  anchors: dict | None = None) -> list[dict]:
    """Inventory static accesses in [start,end). No dynamic-execution claim.

    Verification of source signatures and SHA is the caller's job.
    """
    if end <= start or start % 4 or end % 4:
        raise ValueError('function bounds must be ascending and 4-byte aligned')
    anchor_map = anchors or {}
    found_anchors = set()
    rows = []
    for pc in range(start, end, 4):
        result = decode_memory_word(word_at(data, segments, pc), pc)
        if result is None:
            if pc in anchor_map:
                raise ValueError(f'missing anchored memory instruction at {pc:#x}')
            continue
        result['relative_pc'] = f'+0x{pc - start:03X}'
        offset = result['signed_displacement']
        result['candidate_offset'] = (f'+0x{offset:X}' if offset in OFFSETS else '')
        result['evidence_label'] = ''
        if pc in anchor_map:
            label, expected_offset, direction = anchor_map[pc]
            if offset != expected_offset or result['direction'] != direction:
                raise ValueError(f'anchor displacement/direction mismatch at {pc:#x}')
            result['evidence_label'] = label
            found_anchors.add(pc)
        rows.append(result)
    if found_anchors != set(anchor_map):
        raise ValueError('missing verified anchor instructions')
    return rows


def audit_original(data: bytes, build: str) -> dict:
    """Fail closed on unsupported original files and modified game code."""
    if build not in BUILDS:
        raise ValueError(f'unsupported build: {build}')
    signature_report = verify(data, build)
    spec = BUILDS[build]
    rows = scan_function(data, load_segments(data), spec['start'], spec['end'],
                         ANCHORS[build])
    return {
        'build': build, 'source_sha256': signature_report['sha256'],
        'routine': signature_report['human_steering'],
        'bytes_scanned': signature_report['length_bytes'],
        'verified_instruction_signatures': signature_report['instruction_checks'],
        'verified_direct_calls': signature_report['call_checks'],
        'static_memory_operations': len(rows), 'accesses': rows,
    }


def compare_reports(uc: dict, carbon: dict) -> dict:
    if uc['build'] != 'undercover_ps2' or carbon['build'] != 'carbon_ps2':
        raise ValueError('expected ordered Undercover PS2 and Carbon PS2 reports')
    comparisons = []
    for off in OFFSETS:
        by_build = {}
        for report in (uc, carbon):
            rows = [r for r in report['accesses'] if r['signed_displacement'] == off]
            by_build[report['build']] = {
                'count': len(rows), 'pc': [r['pc'] for r in rows],
                'operations': [r['mnemonic'] for r in rows],
                'anchored_count': sum(bool(r['evidence_label']) for r in rows),
            }
        comparisons.append({'numeric_displacement': f'+0x{off:X}', **by_build})
    return {
        'schema_version': 1,
        'scope': 'SHA-matched original PS2 static steering-routine code only',
        'disclaimer': ('Matching numeric displacements or instruction counts do not '
                       'prove same object, semantics, runtime behavior, or Carbon PC layout.'),
        'builds': [uc, carbon], 'offset_comparison': comparisons,
    }


def output_csv(report: dict) -> str:
    s = io.StringIO(newline='')
    fieldnames = ['build', 'pc', 'relative_pc', 'mnemonic', 'direction',
                  'base_register', 'target_register', 'signed_displacement',
                  'candidate_offset', 'evidence_label']
    writer = csv.DictWriter(s, fieldnames=fieldnames, lineterminator='\n')
    writer.writeheader()
    for build in report['builds']:
        for r in build['accesses']:
            writer.writerow({'build': build['build'], **r})
    return s.getvalue()


def save_report(path: Path, contents: str, overwrite: bool):
    with path.open('w' if overwrite else 'x', encoding='utf-8', newline='') as f:
        f.write(contents)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--uc', type=Path, required=True, help='Locally owned Undercover PS2 SLUS_218.01')
    p.add_argument('--carbon', type=Path, required=True, help='Locally owned Carbon PS2 SLUS_214.93')
    p.add_argument('--json', type=Path, help='Local JSON report')
    p.add_argument('--csv', type=Path, help='Local access inventory CSV')
    p.add_argument('--overwrite', action='store_true', help='Permit replacing prior reports')
    args = p.parse_args(argv)
    try:
        reports = (audit_original(args.uc.read_bytes(), 'undercover_ps2'),
                   audit_original(args.carbon.read_bytes(), 'carbon_ps2'))
        report = compare_reports(*reports)
        as_json = json.dumps(report, indent=2) + '\n'
        if args.json and args.csv and args.json.resolve() == args.csv.resolve():
            raise ValueError('JSON and CSV destinations must differ')
        for path in (args.json, args.csv):
            if path and path.exists() and not args.overwrite:
                raise FileExistsError(f'refusing to overwrite {path}')
        if args.json:
            save_report(args.json, as_json, args.overwrite)
        if args.csv:
            save_report(args.csv, output_csv(report), args.overwrite)
        if not args.json and not args.csv:
            print(as_json, end='')
        else:
            print('Verified both executables; static memory-access rows:',
                  *(r['static_memory_operations'] for r in reports))
        return 0
    except (OSError, ValueError) as error:
        p.exit(1, f'FAIL (no patch attempted): {error}\n')


if __name__ == '__main__':
    raise SystemExit(main())
