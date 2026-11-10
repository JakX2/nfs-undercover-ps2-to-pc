#!/usr/bin/env python3
"""Read-only, symbol-bounded Wii PowerPC call-reference census.

A static branch-with-link target is evidence of a possible call edge, NOT a
runtime call or a proof that all code is reachable. Calls through CTR/LR and
function pointers remain unresolved. Only summary counts are emitted.

Does not copy game instructions, symbols or original binary data to output.
"""
import argparse
from bisect import bisect_right
from collections import Counter
import json
from pathlib import Path
import struct

from wii_elf_dol_audit import inspect_elf, _load, SHT_PROGBITS, SHF_EXECINSTR

MAX_CALLS_PER_FUNCTION = 32768
MAX_FOCUS_EDGES = 20


def signed_field(value, bits):
    """Sign-extend an aligned PPC branch displacement to Python int."""
    return value - (1 << bits) if value & (1 << (bits - 1)) else value


def branch_kind(word, pc):
    """Classify only PPC branch control transfers; (kind, target or None).

    Do not confuse b (LK=0) with bl, nor bclr with bctrl. On a bcl/bccl,
    the bo/bi conditions are not evaluated: this is only a *static* site.
    """
    op = word >> 26
    lk = word & 1
    if op == 18:  # I-form b/bl, signed LI<<2, absolute-address flag AA
        disp = signed_field(word & 0x03FFFFFC, 26)
        target = (disp if word & 2 else pc + disp) & 0xFFFFFFFF
        return ('direct_call' if lk else 'direct_jump'), target
    if op == 16:  # B-form bc/bcl; 14-bit BD<<2 signed to 16-bit
        disp = signed_field(word & 0x0000FFFC, 16)
        target = (disp if word & 2 else pc + disp) & 0xFFFFFFFF
        return ('conditional_call' if lk else 'conditional_jump'), target
    if op == 19:  # XL-form bclr/bcctr and link variants
        ext = (word >> 1) & 0x3FF
        if ext in (16, 528):
            return ('indirect_call' if lk else 'indirect_jump'), None
    return None


def parse_function_symbols(blob, sections):
    """Collect compiler symbol intervals and STT_FILE compilation-unit groups.

    STT_FILE markers can identify LOCAL symbols only. Once symtab.sh_info
    has been reached, global and weak symbols are no longer sorted by file.
    Labeling all later symbols with the last STT_FILE is incorrect.
    """
    sym_ids = [i for i, s in enumerate(sections) if s['type'] == 2]
    if len(sym_ids) != 1:
        raise ValueError('Expected exactly one Wii ELF symbol table')
    sym = sections[sym_ids[0]]
    names_sec = sections[sym['link']]
    names = blob[names_sec['offset']:names_sec['offset'] + names_sec['size']]
    functions = []
    current_file = '[unassigned local]'
    # ELF symbol table sh_info marks first nonlocal symbol.
    shoff = struct.unpack_from('>I', blob, 32)[0]
    local_boundary = struct.unpack_from('>I', blob, shoff + sym_ids[0] * 40 + 28)[0]
    if not 1 <= local_boundary <= sym['size'] // 16:
        raise ValueError('Invalid symtab local/global boundary')
    for i in range(sym['size'] // 16):
        namepos, addr, size, info, other, sect = struct.unpack_from(
            '>IIIBBH', blob, sym['offset'] + 16 * i)
        typ = info & 15
        if typ not in (2, 4):
            continue
        if namepos >= len(names):
            raise ValueError('Out-of-range symbol name')
        end = names.find(b'\0', namepos)
        if end < 0:
            raise ValueError('Unterminated symbol name')
        name = names[namepos:end].decode('latin-1')
        if typ == 4:
            if i >= local_boundary or (info >> 4) != 0:
                raise ValueError('File symbol outside local symbol range')
            current_file = name or '[unnamed compilation unit]'
            continue
        if not 0 < sect < len(sections) or size <= 0:
            continue
        sec = sections[sect]
        if sec['type'] != SHT_PROGBITS or not (sec['flags'] & SHF_EXECINSTR):
            continue
        if (addr & 3 or size & 3 or addr < sec['address'] or
                size > sec['size'] or addr - sec['address'] > sec['size'] - size):
            raise ValueError('Unaligned/out-of-range sized PPC function symbol')
        functions.append({'start': addr, 'end': addr + size,
                          'file_offset': sec['offset'] + addr - sec['address'],
                          'section': sec['name'], 'name': name,
                          'unit': (current_file if i < local_boundary else None),
                          'binding': info >> 4})
    functions.sort(key=lambda x: (x['start'], x['end'], x['name']))
    for a, b in zip(functions, functions[1:]):
        if a['end'] > b['start']:
            raise ValueError('Overlapping function ranges; cannot assign call ownership')
    if not functions:
        raise ValueError('No bounded executable function symbols')
    return functions


def analyze(blob, focus_symbol=None):
    base, sections = inspect_elf(blob)
    funcs = parse_function_symbols(blob, sections)
    starts = [f['start'] for f in funcs]
    focus_index = None
    if focus_symbol is not None:
        if not isinstance(focus_symbol, str) or not focus_symbol:
            raise ValueError('A focus symbol must be a nonempty exact name')
        matches = [i for i, f in enumerate(funcs) if f['name'] == focus_symbol]
        if len(matches) != 1:
            raise ValueError('Focus symbol must match exactly one named function')
        focus_index = matches[0]
    focus_callers = Counter()
    focus_callees = Counter()
    focus_unknown_direct_targets = 0
    focus_indirect_calls = 0
    counts = Counter()
    unit_functions = Counter(f['unit'] for f in funcs if f['unit'] is not None)
    unit_callee_edges = set()
    unknown_unit_edges = 0
    target_is_function_start = 0
    target_is_function_interior = 0
    self_calls = 0
    cross_unit_call_sites = 0
    intra_unit_call_sites = 0
    distinct_edges = set()

    for index, f in enumerate(funcs):
        size = f['end'] - f['start']
        if size // 4 > MAX_CALLS_PER_FUNCTION:
            raise ValueError('Function exceeds static scan instruction budget')
        for offset in range(0, size, 4):
            pc = f['start'] + offset
            (word,) = struct.unpack_from('>I', blob, f['file_offset'] + offset)
            hit = branch_kind(word, pc)
            if hit is None:
                continue
            kind, target = hit
            counts[kind] += 1
            if kind == 'indirect_call' and index == focus_index:
                focus_indirect_calls += 1
            if kind not in ('direct_call', 'conditional_call'):
                continue
            candidate = bisect_right(starts, target) - 1
            if candidate < 0 or not target < funcs[candidate]['end']:
                counts['unresolved_direct_target'] += 1
                if focus_index == index:
                    focus_unknown_direct_targets += 1
                continue
            other = funcs[candidate]
            counts['resolved_direct_target'] += 1
            if index == focus_index:
                focus_callees[(other['start'], other['name'])] += 1
            if candidate == focus_index:
                focus_callers[(f['start'], f['name'])] += 1
            if target == other['start']:
                target_is_function_start += 1
            else:
                target_is_function_interior += 1
            if index == candidate:
                self_calls += 1
            if f['unit'] is None or other['unit'] is None:
                unknown_unit_edges += 1
            elif f['unit'] == other['unit']:
                intra_unit_call_sites += 1
            else:
                cross_unit_call_sites += 1
                unit_callee_edges.add((f['unit'], other['unit']))
            distinct_edges.add((index, candidate))
    summary = {
        'format': 'wii-ppc-named-function-call-census-v1',
        'named_scanned_functions': len(funcs),
        'local_function_symbols_with_supported_compilation_unit': sum(unit_functions.values()),
        'global_or_weak_function_symbols_without_compilation_unit': sum(
            1 for f in funcs if f['unit'] is None),
        'compilation_units_with_local_functions': len(unit_functions),
        'static_direct_branch_with_link_sites': counts['direct_call'],
        'static_conditional_branch_with_link_sites': counts['conditional_call'],
        'unresolved_register_branch_with_link_sites': counts['indirect_call'],
        'ordinary_unconditional_branch_sites_not_classed_as_calls': counts['direct_jump'],
        'ordinary_conditional_branch_sites_not_classed_as_calls': counts['conditional_jump'],
        'indirect_nonlink_branch_sites_not_classed_as_calls': counts['indirect_jump'],
        'direct_call_sites_resolving_inside_named_functions': counts['resolved_direct_target'],
        'direct_call_sites_not_resolving_inside_named_functions': counts['unresolved_direct_target'],
        'resolved_to_function_entry_sites': target_is_function_start,
        'resolved_to_function_interior_sites': target_is_function_interior,
        'self_call_sites': self_calls,
        'same_compilation_unit_call_sites': intra_unit_call_sites,
        'cross_compilation_unit_call_sites': cross_unit_call_sites,
        'calls_with_unassignable_compilation_unit': unknown_unit_edges,
        'distinct_named_function_call_edges': len(distinct_edges),
        'distinct_compilation_unit_call_edges': len(unit_callee_edges),
        'interpretation': ('Static PPC branch-with-link instructions inside ELF STT_FUNC ranges. '
                           'Not a complete call graph, runtime execution trace or C++ reconstruction.'),
    }
    if focus_index is not None:
        f = funcs[focus_index]
        def top_edges(edges):
            ordered = sorted(edges.items(), key=lambda item: (-item[1], item[0][0]))
            return [{'function_address': f'0x{addr:08X}',
                     'function_symbol': name, 'call_sites': count}
                    for (addr, name), count in ordered[:MAX_FOCUS_EDGES]]
        summary['focus'] = {
            'function_symbol': f['name'],
            'function_address': f'0x{f["start"]:08X}',
            'function_size_bytes': f['end'] - f['start'],
            'named_direct_callers_count': len(focus_callers),
            'named_direct_callees_count': len(focus_callees),
            'incoming_direct_call_sites': sum(focus_callers.values()),
            'outgoing_direct_call_sites': sum(focus_callees.values()),
            'outgoing_unresolved_direct_sites': focus_unknown_direct_targets,
            'outgoing_indirect_branch_with_link_sites': focus_indirect_calls,
            'top_callers': top_edges(focus_callers),
            'top_callees': top_edges(focus_callees),
        }
    if (unknown_unit_edges + intra_unit_call_sites + cross_unit_call_sites !=
            counts['resolved_direct_target']):
        raise AssertionError('Unit resolution must conserve totals')
    if (summary['static_direct_branch_with_link_sites'] +
        summary['static_conditional_branch_with_link_sites'] !=
            summary['direct_call_sites_resolving_inside_named_functions'] +
            summary['direct_call_sites_not_resolving_inside_named_functions']):
        raise AssertionError('Call site classification must conserve totals')
    return summary


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--wii-elf', type=Path, required=True)
    p.add_argument('--focus-symbol', help='Exact one function symbol to show bounded caller/callee list')
    args = p.parse_args()
    print(json.dumps(analyze(_load(args.wii_elf), args.focus_symbol), indent=2))


if __name__ == '__main__':
    main()
