#!/usr/bin/env python3
"""Static Wii PPC branch and function coverage census (no original code emitted).

Works with the owner's private matching Wii ELF/DOL. Not a translator, emulator,
or execution trace. All results are STATIC evidence only.
"""
from __future__ import annotations

import argparse
from collections import Counter, deque
from bisect import bisect_right
import json
from pathlib import Path
import sys
from typing import NamedTuple

from wii_recomp_preflight import PreflightError, parse_dol, parse_elf, verify_elf_dol


class Branch(NamedTuple):
    kind: str
    target: int | None
    link: bool


def sign_extend(number: int, bits: int) -> int:
    sign = 1 << (bits - 1)
    return (number ^ sign) - sign


def decode_branch(pc: int, word: int) -> Branch | None:
    """Return relative/absolute PPC direct branches and LR/CTR indirect branches."""
    major = word >> 26
    if major == 18:  # b / bl
        displacement = sign_extend(word & 0x03FFFFFC, 26)
        target = (displacement if word & 2 else pc + displacement) & 0xFFFFFFFF
        return Branch('b', target, bool(word & 1))
    if major == 16:  # bc / bcl
        displacement = sign_extend(word & 0x0000FFFC, 16)
        target = (displacement if word & 2 else pc + displacement) & 0xFFFFFFFF
        return Branch('bc', target, bool(word & 1))
    if major == 19:
        xo = (word >> 1) & 1023
        if xo == 16:
            return Branch('bclr', None, bool(word & 1))
        if xo == 528:
            return Branch('bcctr', None, bool(word & 1))
    return None


def audit(elf: dict, dol: dict, depth: int = 2) -> tuple[dict, dict]:
    if depth < 0 or depth > 8:
        raise PreflightError('depth must be 0 through 8')
    verified = verify_elf_dol(elf, dol)
    func_by_addr = {}
    for addr, size, name, binding in elf['functions']:
        if addr % 4 or size % 4:
            raise PreflightError(f'unaligned function 0x{addr:08X}, size {size}')
        if addr in func_by_addr:
            raise PreflightError(f'duplicate function address 0x{addr:08X}')
        func_by_addr[addr] = (size, name)
    if elf['entry'] not in func_by_addr:
        raise PreflightError('ELF entry is not a function start')

    code_sections = [s for s in elf['sections'] if s['flags'] & 4 and s['type'] == 1]
    def located(addr: int, size: int) -> dict:
        matches = [s for s in code_sections if s['addr'] <= addr and addr + size <= s['addr'] + s['size']]
        if len(matches) != 1:
            raise PreflightError(f'function 0x{addr:08X} has no unique executable section')
        return matches[0]

    major_opcodes = Counter()
    branch_kinds = Counter()
    total_words = 0
    direct_call_edges = set()
    unresolved_calls = set()
    other_link_branches = 0
    indirect_link_branches = 0
    root_calls = []
    for addr, (size, name) in sorted(func_by_addr.items()):
        sec = located(addr, size)
        start = sec['off'] + addr - sec['addr']
        for i in range(0, size, 4):
            pc = addr + i
            word = int.from_bytes(elf['blob'][start+i:start+i+4], 'big')
            major = word >> 26
            major_opcodes[major] += 1
            total_words += 1
            branch = decode_branch(pc, word)
            if branch is None:
                continue
            branch_kinds[branch.kind] += 1
            if branch.kind in ('bclr', 'bcctr') and branch.link:
                indirect_link_branches += 1
            elif branch.link and branch.target is not None:
                if branch.target in func_by_addr:
                    direct_call_edges.add((addr, branch.target))
                else:
                    unresolved_calls.add((addr, pc, branch.target))
                if addr == elf['entry']:
                    root_calls.append({'site': f'0x{pc:08X}', 'target': f'0x{branch.target:08X}',
                                       'target_name': func_by_addr.get(branch.target, (None, None))[1],
                                       'conditional': branch.kind == 'bc'})
                if branch.kind == 'bc':
                    other_link_branches += 1

    # A target between named starts is not automatically an error: console SDK
    # assembly helpers (notably __save_gpr / __restore_gpr) use interior entries.
    sorted_ranges = sorted((addr, addr + size) for addr, (size, _) in func_by_addr.items())
    sorted_starts = [lo for lo, _ in sorted_ranges]
    unmatched_classes = Counter()
    for _, _, target in unresolved_calls:
        pos = bisect_right(sorted_starts, target) - 1
        if pos >= 0 and target < sorted_ranges[pos][1]:
            unmatched_classes['inside_existing_named_function'] += 1
        elif any(s['addr'] <= target < s['addr'] + s['size'] for s in code_sections):
            unmatched_classes['inside_executable_not_named_function'] += 1
        else:
            unmatched_classes['outside_executable_sections'] += 1

    edges = {}
    for caller, callee in sorted(direct_call_edges):
        edges.setdefault(caller, set()).add(callee)
    levels = {elf['entry']: 0}
    todo = deque([elf['entry']])
    while todo:
        caller = todo.popleft()
        if levels[caller] >= depth:
            continue
        for target in sorted(edges.get(caller, ())):
            if target not in levels:
                levels[target] = levels[caller] + 1
                todo.append(target)
    reachable_by_level = {str(i): sum(v == i for v in levels.values()) for i in range(depth+1)}
    loaded = [{'index': r['index'], 'address': f"0x{r['addr']:08X}", 'size': r['size']} for r in dol['regions']]
    summary = {
        'classification': 'STATIC DISASSEMBLY-LEVEL CENSUS; NOT RECOMPILATION OR EMULATED EXECUTION',
        'entry': f"0x{elf['entry']:08X}",
        'verified_dol_elf_bytes': verified,
        'function_count': len(func_by_addr),
        'function_instruction_words': total_words,
        'executable_elf_section_words': sum(s['size'] // 4 for s in code_sections),
        'function_code_coverage_pct': round(100 * (total_words * 4) / sum(s['size'] for s in code_sections), 4),
        'unique_direct_call_edges': len(direct_call_edges),
        'direct_call_sites_not_at_named_function_start': len(unresolved_calls),
        'non_start_direct_call_site_classes': dict(sorted(unmatched_classes.items())),
        'indirect_link_branch_sites': indirect_link_branches,
        'conditional_direct_link_branch_sites': other_link_branches,
        'paired_single_primary_opcode_4_words': major_opcodes[4],
        'branch_kinds': dict(sorted(branch_kinds.items())),
        'primary_opcode_histogram': {str(k): n for k, n in sorted(major_opcodes.items())},
        'startup_direct_call_count': len(root_calls),
        'depth': depth,
        'reachable_named_functions_by_direct_calls': len(levels),
        'reachable_by_call_depth': reachable_by_level,
        'dol_loaded_regions': loaded,
        'limitations': ['direct BL/BCL branches only; indirect calls and data-based dispatch not followed',
                        'counts include all nominal function words and do not assert instruction support',
                        'mid-function direct targets often implement SDK save/restore helpers; audit separately',
                        'boot call graph is not a trace and has no runtime ordering guarantees']
    }
    private = {'entry_direct_calls_in_file_order': root_calls,
               'first_depth_named_functions': [
                   {'address': f'0x{a:08X}', 'depth': level, 'symbol': func_by_addr[a][1]}
                   for a, level in sorted(levels.items(), key=lambda pair: (pair[1], pair[0]))],
               'unresolved_direct_calls': [
                   {'caller': f'0x{a:08X}', 'site': f'0x{b:08X}', 'target': f'0x{c:08X}'}
                   for a, b, c in sorted(unresolved_calls)]}
    return summary, private


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--elf', required=True, type=Path)
    p.add_argument('--dol', required=True, type=Path)
    p.add_argument('--output', required=True, type=Path, help='local private output directory')
    p.add_argument('--depth', default=2, type=int)
    args = p.parse_args()
    try:
        summary, private = audit(parse_elf(args.elf.read_bytes()), parse_dol(args.dol.read_bytes()), args.depth)
        args.output.mkdir(parents=True, exist_ok=True)
        (args.output / 'boot_static_summary.json').write_text(json.dumps(summary, indent=2)+'\n', encoding='utf-8')
        (args.output / 'boot_private_call_targets.json').write_text(json.dumps(private, indent=2)+'\n', encoding='utf-8')
        print(json.dumps(summary, indent=2))
    except (PreflightError, OSError) as exc:
        p.exit(1, f'boot audit failed: {exc}\n')


if __name__ == '__main__':
    main()
