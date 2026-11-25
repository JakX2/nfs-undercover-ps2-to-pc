#!/usr/bin/env python3
"""Private callback continuation and dependency sharing census.

Report only bounded ordinals, aggregate counts and public SDK classifications.
Each continuation is hypothetical until observed in native execution.
"""
import argparse
import struct
from pathlib import Path
from audit_callback_deps_v787 import CALLBACK
from audit_handler_deps_v749 import graph, leaf_alias
from audit_handler_suffix_v728 import suffix
from audit_handler_third_v740 import edge
from audit_si_nested_v690 import target
from audit_si_deep_v695 import call_kind
from classify_save_leaf_v683 import inspect_suffix, symbol_evidence
from make_private_elf_symbol_map import parse_functions
from prepare_v419_full_start import MAX_DOL
from prepare_v667_si_dispatch import exact, DISABLE, RESTORE, TIME, SCHED
from prepare_v668_si_ack import geometry, HANDLER
from si_nested_geometry_v693 import nested_plan


def call_sites(root, words):
    if root & 3 or not 1 <= len(words) <= 1024:
        raise ValueError('extent')
    out = []
    for i, w in enumerate(words):
        kind = call_kind(w)
        if not kind:
            continue
        pc = root + 4 * i
        if kind == 1 and w >> 26 == 18 and w & 3 == 1:
            dst = target(pc, w)
        elif kind == 2 and w == 0x4e800421:
            dst = None
        else:
            raise ValueError('unsupported call form')
        out.append((pc, kind, dst))
    return out


def groups(sites):
    ids = {}
    result = []
    for _, kind, dst in sites:
        if kind == 2:
            result.append(0)
        else:
            if dst not in ids:
                ids[dst] = len(ids) + 1
            result.append(ids[dst])
    return tuple(result)


def continuations(root, words):
    sites = call_sites(root, words)
    rows = []
    for ordinal, start in enumerate([root] + [pc + 4 for pc, _, _ in sites]):
        labels, backs, stores, stops = suffix(root, words, start)
        calls = tuple(sorted({o for _, k, o, _ in stops if k in (1, 5) and o}))
        if any(not 1 <= o <= len(sites) for o in calls):
            raise ValueError('call ordinal')
        counts = tuple(sum(k == t for _, k, _, _ in stops) for t in (2, 3, 4, 6))
        rows.append((ordinal, labels, backs, stores, calls, counts))
    return rows


def child_rows(dol, elf, sites, known, sizes):
    seen = set()
    ids = groups(sites)
    for (_, kind, dst), group in zip(sites, ids):
        if kind != 1 or group in seen:
            continue
        seen.add(group)
        n = sizes.get(dst, 0)
        if not 4 <= n <= 4096 or n & 3:
            continue
        code = exact(dol, elf, dst, n // 4)
        children = graph(dst, code)
        for i, (k, a) in enumerate(children, 1):
            # Unknown exact roots are kept separate from compiler aliases.
            sz = sizes.get(a, 0)
            exact_root = int(4 <= sz <= 4096 and not sz & 3)
            save = restore = 0
            if exact_root:
                exact(dol, elf, a, sz // 4)
            elif a is not None:
                restore = leaf_alias(dol, elf, a, sizes)
                if sum(p < a < p + z for p, z in sizes.items()) == 1:
                    ev = symbol_evidence(elf, a)
                    if ev['zero_func'] or ev['notype']:
                        try:
                            s = inspect_suffix(dol, elf, a)
                            if s['kind'] == 1:
                                save = s['registers']
                        except ValueError:
                            pass
            yield (group, i, k, known.get(a, 0), exact_root,
                   sz // 4 if exact_root else 0, save, restore)


def inspect(dol, elf):
    sizes = parse_functions(elf)
    if sizes.get(CALLBACK) != 688:
        raise ValueError('callback extent')
    words = exact(dol, elf, CALLBACK, 172)
    sites = call_sites(CALLBACK, words)
    if len(sites) != 13 or [i for i, (_, k, _) in enumerate(sites, 1) if k == 2] != [4, 12]:
        raise ValueError('callback shape')
    ids = groups(sites)
    n, *_ = geometry(dol, elf)
    handler = exact(dol, elf, HANDLER, n)
    known = {DISABLE: 1, RESTORE: 2, TIME: 3, SCHED: 4,
             nested_plan(dol, elf)[1]: 5, CALLBACK: 6}
    for i in (4, 5, 7, 8):
        known[edge(HANDLER, handler, i)[1]] = i + 10
    # Candidate's own unique targets can be recognized in child calls.
    for (_, k, dst), group in zip(sites, ids):
        if k == 1:
            known.setdefault(dst, 32 + group)
    rows = continuations(CALLBACK, words)
    if rows[0][4] != (1,):
        raise ValueError('first call')
    print('V799_CALLBACK_GROUPS verified=1 calls=13 direct=11 indirect=2 groups=' + str(max(ids)))
    for i, ((_, k, dst), group) in enumerate(zip(sites, ids), 1):
        print(f'V799_CALLBACK_SITE ordinal={i} kind={k} group={group} known={known.get(dst,0)}')
    for ordinal, labels, backs, stores, calls, counts in rows:
        mask = sum(1 << (i - 1) for i in calls)
        tail, returns, indirect_exit, system = counts
        print(f'V799_CALLBACK_FRONTIER after={ordinal} labels={labels} backward={backs} stores={stores} '
              f'call_mask={mask} tail={tail} returns={returns} indirect_exit={indirect_exit} system={system}')
    for row in child_rows(dol, elf, sites, known, sizes):
        print('V799_CALLBACK_CHILD ' + ' '.join(f'{k}={v}' for k, v in zip(
            ('group', 'edge', 'kind', 'known', 'exact', 'words', 'save', 'restore'), row)))
    print('V799_CALLBACK_CENSUS verified=1 dynamic_target=0 original_execution=0')


def main():
    p = argparse.ArgumentParser()
    p.add_argument('dol', type=Path)
    p.add_argument('elf', type=Path)
    a = p.parse_args()
    try:
        if a.dol.stat().st_size > MAX_DOL or a.elf.stat().st_size > 64 * 1024 * 1024:
            raise ValueError('size')
        inspect(a.dol.read_bytes(), a.elf.read_bytes())
    except (OSError, ValueError, UnicodeError, struct.error, IndexError, KeyError):
        print('V799_CALLBACK_CENSUS verified=0')
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
