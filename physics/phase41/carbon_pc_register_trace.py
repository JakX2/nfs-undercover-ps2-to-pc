#!/usr/bin/env python3
"""Phase 41: guarded local x86 provenance for two known Carbon PC stores.

Requires GNU objdump on PATH. Verifies exact NFSC.exe SHA and Phase31/40
anchors BEFORE disassembling a bounded steering-function byte slice.
Not a full CFG, decompiler, runtime probe, or field-identity inference.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from physics.phase40.carbon_pc_store_audit import (  # noqa: E402
    ANCHOR_ADDRESSES, BYTES, STEERING_END, STEERING_START,
    at, decode_mov_store, extract_from_verified_image, save_report, sections,
)

LINE = re.compile(r"^\s*([0-9a-fA-F]+):\t([0-9a-fA-F ]+)\t(.*)$")
REGISTERS = {
    'eax': 'eax', 'ax': 'eax', 'al': 'eax', 'ah': 'eax',
    'ecx': 'ecx', 'cx': 'ecx', 'cl': 'ecx', 'ch': 'ecx',
    'edx': 'edx', 'dx': 'edx', 'dl': 'edx', 'dh': 'edx',
    'ebx': 'ebx', 'bx': 'ebx', 'bl': 'ebx', 'bh': 'ebx',
    'esp': 'esp', 'sp': 'esp', 'ebp': 'ebp', 'bp': 'ebp',
    'esi': 'esi', 'si': 'esi', 'edi': 'edi', 'di': 'edi',
}
FULL_REGS = frozenset(('eax', 'ecx', 'edx', 'ebx', 'esp', 'ebp', 'esi', 'edi'))
NO_GPR_WRITES = frozenset((
    'nop', 'cmp', 'test', 'fld', 'fld1', 'fldz', 'fldcw',
    'fst', 'fstp', 'fadd', 'faddp', 'fsub', 'fsubp',
    'fsubr', 'fsubrp', 'fmul', 'fmulp', 'fdiv', 'fdivp',
    'fdivr', 'fdivrp', 'fchs', 'fabs', 'fxch', 'fcom',
    'fcomp', 'fucom', 'fucomp', 'fwait',
))
COMPUTE = frozenset(('add', 'sub', 'adc', 'sbb', 'xor', 'and', 'or',
                     'imul', 'neg', 'not', 'inc', 'dec', 'shl',
                     'shr', 'sar', 'rol', 'ror'))
OTHER_DEST_WRITES = frozenset(('movzx', 'movsx', 'movsxd', 'pop', 'seta',
                               'sete', 'setne', 'setb', 'setl', 'setg'))
MAX_STEPS = 64


def parse_objdump(text: str, raw: bytes, start: int) -> list[dict]:
    """Require contiguous single-instruction coverage; reject bad data/bytes."""
    instructions = []
    for line in text.splitlines():
        match = LINE.match(line)
        if not match:
            continue
        pc = int(match.group(1), 16)
        try:
            encoded = bytes.fromhex(match.group(2))
        except ValueError as exc:
            raise ValueError('malformed disassembly byte field') from exc
        asm = match.group(3).strip()
        if not asm or len(encoded) == 0 or len(encoded) > 15:
            raise ValueError(f'incomplete disassembly at {pc:#x}')
        if asm.startswith(('.byte', '(bad)', '...', '.word')):
            raise ValueError(f'unrecognized x86 encoding at {pc:#x}')
        parts = asm.split(None, 1)
        mnemonic = parts[0].lower()
        operands = parts[1].strip() if len(parts) > 1 else ''
        # objdump uses # for optional symbol comments, not an operand.
        operands = operands.split('#', 1)[0].strip()
        instructions.append({'pc': pc, 'length': len(encoded),
                             'bytes': encoded, 'mnemonic': mnemonic,
                             'operands': operands})
    if not instructions and raw:
        raise ValueError('disassembler returned no instructions')
    cursor = start
    for ins in instructions:
        if ins['pc'] != cursor:
            raise ValueError(f'disassembler gap, overlap or boundary at {cursor:#x}')
        off = cursor - start
        if raw[off:off + ins['length']] != ins['bytes']:
            raise ValueError(f'disassembler bytes disagree at {cursor:#x}')
        cursor += ins['length']
    if cursor != start + len(raw):
        raise ValueError('incomplete x86 instruction coverage')
    return instructions


def disassemble(raw: bytes, start: int) -> list[dict]:
    """Run binutils on a temporary private slice; never execute input code."""
    executable = shutil.which('objdump')
    if not executable:
        raise RuntimeError('GNU objdump required (install binutils or use WSL)')
    if len(raw) > 4096 or len(raw) < 1:
        raise ValueError('unexpected x86 function length')
    with tempfile.TemporaryDirectory(prefix='nfs_phase41_') as folder:
        path = Path(folder) / 'routine.bin'
        path.write_bytes(raw)
        args = [executable, '-D', '-b', 'binary', '-m', 'i386', '-M', 'intel',
                '--insn-width=16', f'--adjust-vma=0x{start:x}', str(path)]
        try:
            result = subprocess.run(args, capture_output=True, text=True,
                                    check=False, timeout=10)
        except subprocess.TimeoutExpired as exc:
            raise ValueError('objdump exceeded ten-second limit') from exc
        if result.returncode != 0:
            raise ValueError('objdump failed to decode local routine')
    return parse_objdump(result.stdout, raw, start)


def split_operands(operands: str) -> list[str]:
    """Split x86 Intel operands without splitting bracketed addresses."""
    result, token, depth = [], [], 0
    for char in operands:
        if char == '[':
            depth += 1
        if char == ']':
            depth -= 1
            if depth < 0:
                raise ValueError('malformed operand brackets')
        if char == ',' and depth == 0:
            result.append(''.join(token).strip().lower())
            token = []
        else:
            token.append(char)
    if depth:
        raise ValueError('unclosed operand brackets')
    if token:
        result.append(''.join(token).strip().lower())
    return result


def transfer_kind(mnemonic: str) -> bool:
    return (mnemonic.startswith('j') or mnemonic.startswith('loop')
            or mnemonic.startswith('call') or mnemonic.startswith('ret')
            or mnemonic in ('int', 'int3', 'into', 'syscall', 'sysenter',
                            'iret', 'iretd', 'ud2'))


def branch_target(ins: dict) -> int | None:
    if not (ins['mnemonic'].startswith('j') or ins['mnemonic'].startswith('loop')):
        return None
    match = re.match(r'^(?:0x)?([a-f0-9]+)(?:\s|$)', ins['operands'].lower())
    if match is None:
        return None
    return int(match.group(1), 16)


def boundaries(instructions: list[dict]) -> set[int]:
    """All branch targets and all instructions after any control transfer."""
    if not instructions:
        return set()
    starts = {instructions[0]['pc']}
    by_pc = {ins['pc'] for ins in instructions}
    for i, ins in enumerate(instructions):
        if not transfer_kind(ins['mnemonic']):
            continue
        if i + 1 < len(instructions):
            starts.add(instructions[i + 1]['pc'])
        target = branch_target(ins)
        if target in by_pc:
            starts.add(target)
        elif target is not None:
            start, end = instructions[0]['pc'], instructions[-1]['pc'] + instructions[-1]['length']
            if start < target < end:
                raise ValueError(f'branch into middle of x86 instruction: {target:#x}')
    return starts


def root_register(operand: str) -> tuple[str | None, bool]:
    family = REGISTERS.get(operand.lower())
    return family, operand.lower() in FULL_REGS


def describe_effect(ins: dict, target_reg: str) -> dict:
    """Deliberately narrow: unknown effects are blockers, never silently skipped."""
    op = ins['mnemonic']
    items = split_operands(ins['operands'])
    if transfer_kind(op):
        return {'kind': 'control_flow_barrier'}
    if op in NO_GPR_WRITES:
        return {'kind': 'skip_no_gpr_write'}
    if op == 'push':
        return {'kind': 'unknown_definition'} if target_reg == 'esp' else {'kind': 'skip_no_target_write'}
    if op == 'mov' and len(items) == 2:
        dest, src = items
        family, full = root_register(dest)
        if family is None:
            # MOV to memory cannot modify a GPR.
            if '[' in dest:
                return {'kind': 'skip_no_target_write'}
            return {'kind': 'opaque_barrier'}
        if family != target_reg:
            return {'kind': 'skip_no_target_write'}
        if not full:
            return {'kind': 'partial_register_write_unknown', 'destination': dest}
        source_family, source_full = root_register(src)
        if source_family:
            if not source_full:
                return {'kind': 'partial_register_source_unknown', 'source': src}
            return {'kind': 'register_copy', 'source': source_family}
        if '[' in src:
            return {'kind': 'memory_load_unknown_value', 'source_operand': src}
        return {'kind': 'immediate_or_symbol', 'source_operand': src}
    if op == 'lea' and len(items) == 2:
        family, full = root_register(items[0])
        if family != target_reg:
            return {'kind': 'skip_no_target_write'} if family else {'kind': 'opaque_barrier'}
        if not full:
            return {'kind': 'partial_register_write_unknown'}
        return {'kind': 'address_expression_unresolved', 'source_operand': items[1]}
    if op in COMPUTE and items:
        dest, full = root_register(items[0])
        if dest != target_reg:
            # Modifying flags or another GPR is fine only for explicitly recognized families.
            return {'kind': 'skip_no_target_write'} if dest else {'kind': 'opaque_barrier'}
        if not full:
            return {'kind': 'partial_register_write_unknown'}
        if op == 'xor' and len(items) == 2 and items[0] == items[1]:
            return {'kind': 'known_zero'}
        return {'kind': 'arithmetic_definition_unresolved', 'operator': op}
    if op in OTHER_DEST_WRITES and items:
        dest, full = root_register(items[0])
        if dest == target_reg:
            return {'kind': 'partial_register_write_unknown' if not full
                    else 'other_definition_unresolved', 'operator': op}
        return {'kind': 'skip_no_target_write'} if dest else {'kind': 'opaque_barrier'}
    return {'kind': 'opaque_barrier'}


def trace_before(instructions: list[dict], anchor: int, register: str,
                 max_steps: int = MAX_STEPS) -> dict:
    """Backward local trace; never crosses branch targets/calls/unknown writes."""
    pos = {ins['pc']: i for i, ins in enumerate(instructions)}
    if anchor not in pos or register not in FULL_REGS:
        raise ValueError('invalid verified anchor or register')
    stops = boundaries(instructions)
    index = pos[anchor]
    start_pc = max(pc for pc in stops if pc <= anchor)
    current_reg = register
    events = []
    scanned = 0
    for i in range(index - 1, -1, -1):
        ins = instructions[i]
        if ins['pc'] < start_pc:
            break
        if scanned >= max_steps:
            return {'status': 'step_limit', 'register': current_reg,
                    'local_block_start': f'0x{start_pc:08X}', 'evidence': events}
        scanned += 1
        effect = describe_effect(ins, current_reg)
        kind = effect['kind']
        if kind.startswith('skip_'):
            continue
        event = {'pc': f"0x{ins['pc']:08X}", 'mnemonic': ins['mnemonic'],
                 'effect': effect}
        events.append(event)
        if kind == 'register_copy':
            current_reg = effect['source']
            continue
        return {'status': kind, 'register': current_reg,
                'local_block_start': f'0x{start_pc:08X}', 'evidence': events}
    return {'status': 'block_live_in_unknown', 'register': current_reg,
            'local_block_start': f'0x{start_pc:08X}', 'evidence': events}


def analyze_verified_image(data: bytes) -> dict:
    """Only this entrypoint is allowed to analyze user-owned game code."""
    phase40 = extract_from_verified_image(data)
    raw = at(data, sections(data), STEERING_START, STEERING_END - STEERING_START)
    instructions = disassemble(raw, STEERING_START)
    ins_by_pc = {ins['pc']: ins for ins in instructions}
    stores = []
    for pc, evidence in zip(ANCHOR_ADDRESSES, phase40['known_steering_store_instructions']):
        ins = ins_by_pc.get(pc)
        if ins is None or ins['bytes'] != bytes.fromhex(BYTES[pc]):
            raise ValueError(f'Phase 40 anchor not an independently decoded instruction at {pc:#x}')
        # Phase40's exact ModRM decoder defines the source reg, rather than
        # a guessed semantic interpretation of disassembler text.
        expected = decode_mov_store(ins['bytes'], pc)
        if (expected['source_register'] != evidence['source_register']
                or expected['signed_displacement'] != evidence['signed_displacement']):
            raise ValueError('store disassembly and anchor metadata disagree')
        stores.append({'store': evidence,
                       'source_register_trace': trace_before(instructions, pc,
                                                             evidence['source_register'])})
    return {
        'phase': 41, 'exe_sha256': phase40['exe_sha256'],
        'phase31_verified_checks': phase40['phase31_verified_checks'],
        'disassembler': 'GNU objdump i386 intel',
        'decoded_function_instruction_count': len(instructions),
        'total_verified_source_stores': len(stores), 'store_traces': stores,
        'carbon_pc_field_semantics_verified': False,
        'undercover_ps2_pc_equivalence_verified': False,
        'runtime_execution_observed': False,
        'gameplay_patch_created': False,
        'limitations': [
            'Static linear disassembly of known function range, not full control-flow proof.',
            'Only local intra-block EAX/EDX provenance with no predecessor merging.',
            'Unknown instructions and partial register writes terminate the trace.',
            'Source instruction immediates/addresses cannot identify fields by themselves.',
            'No real game binary, runtime measurements or handling changes in public CI.',
        ],
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('exe', type=Path, help='Locally owned exact supported Carbon PC NFSC.exe')
    parser.add_argument('--output', type=Path, help='JSON report; omit for stdout')
    parser.add_argument('--overwrite', action='store_true')
    args = parser.parse_args(argv)
    try:
        report = analyze_verified_image(args.exe.read_bytes())
        output = json.dumps(report, indent=2) + '\n'
        if args.output:
            save_report(args.output, output, args.overwrite, args.exe)
            print('Phase 41 report:', args.output)
        else:
            print(output, end='')
        return 0
    except (ValueError, OSError, RuntimeError) as error:
        parser.exit(1, f'FAIL (no game changes): {error}\n')


if __name__ == '__main__':
    raise SystemExit(main())
