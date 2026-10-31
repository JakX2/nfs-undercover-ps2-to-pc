#!/usr/bin/env python3
"""Phase 38: conservative basic-block-local GPR provenance for PS2 steering.

Only verified originals may enter the CLI via the Phase36 audit. This does not
identify object types, dynamic values, source-level semantics, or Carbon PC fields.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

CANDIDATE_DISPLACEMENTS = frozenset((0x48, 0x64, 0x8c, 0x9c, 0xc0, 0xd8,
                                     0x160, 0x188, 0x19c))
MEMORY_LOADS = frozenset((0x20, 0x21, 0x22, 0x23, 0x24, 0x25, 0x26,
                          0x30, 0x34, 0x37))
MEMORY_STORES = frozenset((0x28, 0x29, 0x2a, 0x2b, 0x2e, 0x38, 0x3c, 0x3f))
FLOAT_MEMORY = frozenset((0x31, 0x35, 0x39, 0x3d))
ALL_MEMORY = MEMORY_LOADS | MEMORY_STORES | FLOAT_MEMORY
BRANCH_OPCODES = frozenset((1, 4, 5, 6, 7, 0x14, 0x15, 0x16, 0x17))
GPR_IMMEDIATE_WRITES = frozenset((8, 9, 10, 11, 12, 13, 14, 15,
                                   0x18, 0x19))
SPECIAL_WRITES_RD = frozenset((0, 2, 3, 4, 6, 7, 0x0a, 0x0b,
                               0x10, 0x12, 0x20, 0x21, 0x22, 0x23,
                               0x24, 0x25, 0x26, 0x27, 0x2a, 0x2b,
                               0x2c, 0x2d, 0x2e, 0x2f))
SPECIAL_NO_GPR_WRITES = frozenset((8, 0x0c, 0x0d, 0x0f, 0x11, 0x13,
                                   0x18, 0x19, 0x1a, 0x1b))


def signed16(n: int) -> int:
    return (n & 0xffff) - (0x10000 if n & 0x8000 else 0)


def fields(word: int) -> tuple[int, int, int, int, int, int]:
    return word >> 26, (word >> 21) & 31, (word >> 16) & 31, (word >> 11) & 31, word & 63, signed16(word)


def transfer_target(word: int, pc: int) -> int | None:
    """Return direct branch/jump target; None for indirect and non-control."""
    op, rs, rt, _, fn, imm = fields(word)
    if op in BRANCH_OPCODES or (op in (0x10, 0x11, 0x12) and rs == 8):
        return (pc + 4 + (imm << 2)) & 0xffffffff
    if op in (2, 3):
        return ((pc + 4) & 0xf0000000) | ((word & 0x03ffffff) << 2)
    return None


def is_control_transfer(word: int) -> bool:
    op, rs, _, _, fn, _ = fields(word)
    return (op in BRANCH_OPCODES or op in (2, 3)
            or (op == 0 and fn in (8, 9))
            or (op in (0x10, 0x11, 0x12) and rs == 8))


def basic_block_starts(words: list[int], start: int) -> list[int]:
    """Conservative boundaries include branch targets and both delay-slot sides.

    Delay slots are intentionally cut off from preceding definitions. This
    loses precision rather than falsely proving provenance across branches.
    """
    if start & 3 or start < 0 or any(w < 0 or w > 0xffffffff for w in words):
        raise ValueError('unaligned start or invalid MIPS instruction word')
    positions = {0}
    end = start + 4 * len(words)
    for i, word in enumerate(words):
        if not is_control_transfer(word):
            continue
        for index in (i + 1, i + 2):
            if index < len(words):
                positions.add(index)
        target = transfer_target(word, start + 4 * i)
        if target is not None and start <= target < end and not (target & 3):
            positions.add((target - start) // 4)
    return sorted(positions)


def decode_gpr_effect(word: int) -> tuple[str, int | None, tuple[int, ...], int]:
    """(kind, destination GPR, input GPRs, signed immediate).

    Opaque instructions invalidate ancestry; never step over an instruction
    that might define the requested GPR without accounting for it.
    """
    op, rs, rt, rd, fn, imm = fields(word)
    if op in (0x22, 0x26):  # LWL/LWR merge bytes with prior destination contents
        return 'partial_load_unknown', rt, (), imm
    if op in MEMORY_LOADS:
        return 'load', rt, (rs,), imm
    if op in MEMORY_STORES or op in FLOAT_MEMORY:
        return 'no_gpr_write', None, (), imm
    if op == 15:
        return 'lui', rt, (), word & 0xffff
    if op == 9:
        return 'addiu', rt, (rs,), imm
    if op == 13:
        return 'ori', rt, (rs,), word & 0xffff
    if op in GPR_IMMEDIATE_WRITES:
        return 'unknown_definition', rt, (rs,), imm
    if op == 0:
        if word == 0:
            return 'no_gpr_write', None, (), 0
        if fn in (0x21, 0x25) and (rs == 0 or rt == 0):
            return 'move', rd, (rt if rs == 0 else rs,), 0
        if fn in (0x21, 0x25):
            return 'binary', rd, (rs, rt), 0
        if fn == 9:
            return 'unknown_definition', rd, (), 0
        if fn in SPECIAL_WRITES_RD:
            return 'unknown_definition', rd, (rs, rt), 0
        if fn in SPECIAL_NO_GPR_WRITES:
            return 'no_gpr_write', None, (), 0
        return 'opaque', None, (), 0
    if op == 1:
        if rt in (16, 17, 18, 19):
            return 'unknown_definition', 31, (), 0
        return 'no_gpr_write', None, (), 0
    if op == 3:
        return 'unknown_definition', 31, (), 0
    if op in (2, 4, 5, 6, 7, 0x14, 0x15, 0x16, 0x17):
        return 'no_gpr_write', None, (), 0
    if op == 0x11:
        if rs in (0, 2):
            return 'unknown_definition', rt, (), 0
        return 'no_gpr_write', None, (), 0
    if op in (0x10, 0x12):
        if rs in (0, 1, 2):
            return 'unknown_definition', rt, (), 0
        return 'no_gpr_write', None, (), 0
    if op == 0x1c:
        return 'opaque', None, (), 0
    return 'opaque', None, (), 0


def trace_register(words: list[int], start: int, block_begin: int,
                   before_index: int, register: int, max_depth: int = 8) -> dict:
    """Trace *within* the current syntactic basic block, no predecessor merging."""
    if not (0 <= register <= 31) or not (0 <= block_begin <= before_index <= len(words)):
        raise ValueError('invalid trace location or register')
    if register == 0:
        return {'kind': 'architectural_zero'}

    def walk(reg: int, before: int, depth: int) -> dict:
        if reg == 0:
            return {'kind': 'architectural_zero'}
        if depth == 0:
            return {'kind': 'depth_limit', 'register': f'r{reg}'}
        for i in range(before - 1, block_begin - 1, -1):
            kind, dest, sources, imm = decode_gpr_effect(words[i])
            if kind == 'opaque':
                return {'kind': 'opaque_barrier', 'register': f'r{reg}',
                        'barrier_pc': f'0x{start + i * 4:08X}'}
            if dest != reg:
                continue
            pc = f'0x{start + i * 4:08X}'
            result = {'kind': kind, 'register': f'r{reg}', 'definition_pc': pc}
            if kind == 'lui':
                result['upper_immediate'] = imm
            elif kind in ('addiu', 'ori'):
                result['immediate'] = imm
                result['source'] = walk(sources[0], i, depth - 1)
            elif kind == 'move':
                result['source'] = walk(sources[0], i, depth - 1)
            elif kind == 'binary':
                result['sources'] = [walk(src, i, depth - 1) for src in sources]
            elif kind == 'load':
                result['displacement'] = imm
                result['address_base'] = walk(sources[0], i, depth - 1)
            return result
        return {'kind': 'block_live_in_unknown', 'register': f'r{reg}',
                'block_start_pc': f'0x{start + block_begin * 4:08X}'}

    return walk(register, before_index, max_depth)


def report_from_verified_words(build: str, sha: str, start: int,
                               words: list[int], reference_rows: list[dict]) -> dict:
    """Caller must supply Phase36-verifiably scanned words. For pure synthetic tests
    these are caller-generated fixtures; never label them source-binary evidence.
    """
    positions = basic_block_starts(words, start)
    findings = []
    for row in reference_rows:
        disp = row['signed_displacement']
        if disp not in CANDIDATE_DISPLACEMENTS and not row['evidence_label']:
            continue
        pc = int(row['pc'], 16)
        if pc < start or (pc - start) % 4 or (pc - start) // 4 >= len(words):
            raise ValueError('Phase36 access address outside routine')
        index = (pc - start) // 4
        op, base, _, _, _, decoded_disp = fields(words[index])
        if op not in ALL_MEMORY or decoded_disp != disp or row['base_register'] != f'r{base}':
            raise ValueError(f'Phase36/Phase38 memory-access mismatch at {pc:#x}')
        block_begin = max(x for x in positions if x <= index)
        findings.append({
            'pc': row['pc'], 'mnemonic': row['mnemonic'],
            'signed_displacement': disp, 'direction': row['direction'],
            'evidence_label': row['evidence_label'],
            'base_register': row['base_register'],
            'block_start_pc': f'0x{start + 4 * block_begin:08X}',
            'base_provenance': trace_register(words, start, block_begin, index, base),
        })
    return {'build': build, 'sha256': sha, 'routine_start': f'0x{start:08X}',
            'instruction_count': len(words), 'block_count': len(positions),
            'candidate_access_count': len(findings), 'candidate_accesses': findings}


def audit_source_file(data: bytes, build: str) -> dict:
    """Gated by Phase33+36; only local original executables qualify."""
    root = Path(__file__).resolve().parents[2]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from physics.phase33.verify_ps2_human_steering import BUILDS, load_segments, word_at
    from physics.phase36.steering_memory_audit import audit_original

    verified = audit_original(data, build)
    spec = BUILDS[build]
    segments = load_segments(data)
    words = [word_at(data, segments, pc) for pc in range(spec['start'], spec['end'], 4)]
    return report_from_verified_words(build, verified['source_sha256'],
                                      spec['start'], words, verified['accesses'])


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--uc', type=Path, required=True, help='Original Undercover PS2 SLUS_218.01')
    parser.add_argument('--carbon', type=Path, required=True, help='Original Carbon PS2 SLUS_214.93')
    parser.add_argument('--output', type=Path, help='Report JSON (stdout if omitted)')
    parser.add_argument('--overwrite', action='store_true')
    args = parser.parse_args(argv)
    try:
        report = {
            'schema_version': 1,
            'scope': 'read-only, static MIPS within-block GPR ancestry',
            'limitations': [
                'Not a control-flow graph, object identity proof, or full dataflow analysis.',
                'No propagation across branch targets, delay slots, calls, or basic blocks.',
                'Unmodeled GPR writes stop ancestry; a live-in register is unknown.',
                'No Carbon PC or runtime mappings, physics parameters, or behavioral results.',
            ],
            'builds': [audit_source_file(args.uc.read_bytes(), 'undercover_ps2'),
                       audit_source_file(args.carbon.read_bytes(), 'carbon_ps2')],
        }
        output = json.dumps(report, indent=2) + '\n'
        if args.output:
            with args.output.open('w' if args.overwrite else 'x', encoding='utf8') as f:
                f.write(output)
            print('Saved read-only Phase 38 report:', args.output)
        else:
            print(output, end='')
        return 0
    except (ValueError, OSError) as exc:
        parser.exit(1, f'FAIL: {exc}\n')


if __name__ == '__main__':
    raise SystemExit(main())
