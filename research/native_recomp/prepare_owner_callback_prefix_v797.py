#!/usr/bin/env python3
"""Private original callback prologue through its compiler save return.

The synthetic caller and final unreachable BLR are independent fixture
code. The original continuation word is authenticated but never executed.
"""
import argparse
import re
import struct
from pathlib import Path
from audit_callback_deps_v787 import CALLBACK
from audit_si_deep_v695 import call_kind
from audit_handler_deps_v749 import graph
from prepare_v419_full_start import MAX_DOL, direct_bl
from prepare_v667_si_dispatch import exact
from make_private_elf_symbol_map import parse_functions
from prepare_owner_pair_v753 import H, BLR, alias, pair_shape
from prepare_owner_leaf_v714 import bl
from prepare_owner_cancel_v754 import patch_analyzer
from prepare_v625_ipc_client import audit_native
from prepare_v680_si_helper import exact_function, verify_direct
from prepare_v709_os_leaves import owns_root


def prologue_word(w):
    op, xo = w >> 26, (w >> 1) & 1023
    rd, ra = (w >> 21) & 31, (w >> 16) & 31
    if op == 37:
        return rd == ra == 1 and 0x8000 <= (w & 0xffff) <= 0xfffc and not w & 3
    if op == 36:
        return ra in (1, 11) and not w & 3
    if op == 14:
        return True
    if op == 31 and xo == 339:
        return ((w >> 16) & 31) | (((w >> 11) & 31) << 5) == 8 and not w & 1
    return w == 0x60000000 or (op == 31 and xo == 444 and not w & 1)


def prefix_geometry(root, code):
    calls = [(i, call_kind(w)) for i, w in enumerate(code) if call_kind(w)]
    if not calls or calls[0][1] != 1:
        raise ValueError('first call')
    i = calls[0][0]
    if not 1 <= i <= 16 or i + 1 >= len(code):
        raise ValueError('prefix extent')
    if code[i] >> 26 != 18 or code[i] & 3 != 1:
        raise ValueError('first direct call')
    if not all(prologue_word(w) for w in code[:i]):
        raise ValueError('prefix instruction')
    if sum(w >> 26 == 37 for w in code[:i]) != 1 or sum(w >> 26 in (36, 37) for w in code[:i]) != 2:
        raise ValueError('prefix stack shape')
    # The exact next instruction is present for the stop hook, but the
    # bounded fragment must have a linear final synthetic terminator.
    w = code[i + 1]
    if w >> 26 in (16, 17, 18, 19) or w >> 26 == 31 and (w >> 1) & 1023 == 146:
        raise ValueError('continuation shape')
    return root + 4 * i, direct_bl(code[i], root + 4 * i), list(code[:i + 2]) + [BLR]


def plan(dol, elf):
    sizes = parse_functions(elf)
    C = CALLBACK
    if sizes.get(C) != 172 * 4:
        raise ValueError('callback extent')
    code = exact(dol, elf, C, 172)
    edges = graph(C, code)
    if len(edges) != 13 or sum(k == 1 for k, _ in edges) != 11 or sum(k == 2 for k, _ in edges) != 2:
        raise ValueError('callback edges')
    site, S, prefix = prefix_geometry(C, code)
    if edges[0] != (1, S) or edges[-1][0] != 1:
        raise ValueError('callback aliases')
    save = alias(dol, elf, S, sizes, 6)
    restore = alias(dol, elf, edges[-1][1], sizes, 6)
    sb, _, disp = pair_shape(save, restore, 6)
    roots = {H: [bl(H, C), 0x60000000, BLR], C: prefix, S: save}
    spans = sorted((a, a + 4 * len(ws)) for a, ws in roots.items())
    if len(roots) != 3 or any(y > u for (_, y), (u, _) in zip(spans, spans[1:])):
        raise ValueError('prefix overlap')
    return roots, C, S, site, sb, disp


def header(p, out):
    roots, C, S, site, sb, disp = p
    s = '#pragma once\n#include <array>\n#include <cstdint>\n'
    s += 'inline constexpr uint32_t ' + ','.join(f'{k}=0x{v:08x}u' for k, v in (
        ('H', H), ('C', C), ('S', S), ('SaveCall', site), ('Resume', site + 4))) + ';\n'
    s += f'inline constexpr unsigned SaveBase={sb};\ninline constexpr int32_t SaveDisp={disp};\n'
    for name, addr in (('caller_words', H), ('prefix_words', C), ('save_words', S)):
        ws = roots[addr]
        s += f'inline constexpr std::array<uint32_t,{len(ws)}> {name}{{' + ','.join(f'0x{w:08x}u' for w in ws) + '};\n'
    with out.open('x') as f:
        f.write(s)


def install(p, root, extra_links=(), use_reachable=False, indirect_caller=False):
    roots, C, S, site, _, _ = p
    paths = sorted(root.glob('*.cpp'))
    if not paths or any(x.is_symlink() or x.stat().st_size > 4 * 1024 * 1024 for x in paths):
        raise ValueError('private output')
    src = {x: x.read_text() for x in paths}
    main = root / ('main_output.cpp' if (root / 'main_output.cpp').is_file() else 'output.cpp')
    outer = src[main].split('extern "C" void run_game(', 1)[1]
    if use_reachable:
        from prepare_owner_scheduler_v722 import reachable
        expected = {pc: (a, ws[(pc-a)//4]) for a, ws in roots.items() for pc in reachable(a, ws)}
    else:
        expected = {a + 4 * i: (a, w) for a, ws in roots.items() for i, w in enumerate(ws)}
    if audit_native(src.values(), outer, expected) != len(expected):
        raise ValueError('native coverage')
    if indirect_caller:
        from prepare_owner_indirect_callback_v806 import verify_indirect
        owners = [exact_function(s, H) for s in src.values() if owns_root(s, H)]
        if len(owners) != 1:
            raise ValueError('native owner')
        verify_indirect(owners[0], H)
    for owner, pc, dst in ((() if indirect_caller else ((H, H, C),)) + ((C, site, S),) + tuple(extra_links)):
        owned = [exact_function(s, owner) for s in src.values() if owns_root(s, owner)]
        if len(owned) != 1:
            raise ValueError('native owner')
        verify_direct(owned[0], pc, dst)
    seen = set()
    changes = {}
    for path, old in src.items():
        s = old
        for pc, (_, w) in expected.items():
            pat = re.compile(r'(?mi)^loc_' + f'{pc:X}' + r': ;\n    // 0x' + f'{pc:08X}: {w:08X}' + r'\n    \+\+ctx\.inst_count;\n')
            m = list(pat.finditer(s))
            if not m:
                continue
            if len(m) != 1 or pc in seen:
                raise ValueError('hook identity')
            seen.add(pc)
            s = pat.sub(lambda m: m[0] + f'    rfi_test::before(ctx,0x{pc:08x}u,0x{w:08x}u);\n', s, count=1)
        if s != old:
            a = '#include "runtime/cpu_context.h"'
            if s.count(a) != 1:
                raise ValueError('hook include')
            changes[path] = s.replace(a, a + '\n#include "rfi_test_v708.h"')
    if seen != set(expected):
        raise ValueError('hook coverage')
    for path, s in changes.items():
        path.write_text(s)
    if indirect_caller:
        print(f'V806_CALLBACK_NATIVE_ROUTE labels={len(expected)} indirect=1 direct=1 fallback=0 execution=0')
    elif use_reachable:
        print(f'V802_CALLBACK_NATIVE_ROUTE labels={len(expected)} direct_edges={2+len(extra_links)} fallback=0 execution=0')
    else:
        print('V797_PREFIX_NATIVE_ROUTE original_prefix=1 original_save=1 direct_edges=2 fallback=0 execution=0')


def main():
    a = argparse.ArgumentParser()
    a.add_argument('dol', type=Path)
    a.add_argument('elf', type=Path)
    a.add_argument('output', type=Path)
    m = a.add_mutually_exclusive_group()
    m.add_argument('--install', action='store_true')
    m.add_argument('--patch-analyzer', action='store_true')
    x = a.parse_args()
    try:
        if x.dol.stat().st_size > MAX_DOL or x.elf.stat().st_size > 64 * 1024 * 1024:
            raise ValueError('size')
        p = plan(x.dol.read_bytes(), x.elf.read_bytes())
        if x.install:
            install(p, x.output)
        elif x.patch_analyzer:
            patch_analyzer(p, x.output)
        else:
            header(p, x.output)
            print('V797_PREFIX_GEOMETRY verified=1 save_gprs=6 matched_restore=1 original_callback_return=0')
    except (OSError, ValueError, UnicodeError, struct.error, IndexError, KeyError) as e:
        allowed = ('first call', 'prefix extent', 'first direct call', 'prefix instruction',
                   'prefix stack shape', 'continuation shape', 'callback extent', 'callback edges',
                   'callback aliases', 'prefix overlap', 'private output', 'native coverage',
                   'native owner', 'hook identity', 'hook include', 'hook coverage', 'alias root',
                   'alias symbol', 'pair shape', 'frame offset')
        print('V797_PREFIX_PREP verified=0 reason=' + (str(e).replace(' ', '_') if str(e) in allowed else 'other'))
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
