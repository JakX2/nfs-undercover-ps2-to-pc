#!/usr/bin/env python3
"""Aggregate generated SPR translation coverage without printing game code.

The script reads owner-private generated C++ and reports only counts. It fails
closed when old silent-ignore markers or unsupported instruction traps remain.
"""
from collections import Counter
from pathlib import Path
import argparse
import json
import re

WRITE_RE = re.compile(r'ctx\.write_unmodeled_spr\((\d+),')
READ_RE = re.compile(r'ctx\.read_unmodeled_spr\((\d+)\)')
DROP_RE = re.compile(r'// unhandled mtspr (\d+)')
OPCODE_RE = re.compile(r'UNIMPLEMENTED (?:Opcode|OPCODE)')


def family(spr: int) -> str:
    if (528 <= spr <= 543) or (560 <= spr <= 575): return 'BAT_translation'
    if spr == 25: return 'SDR1_translation'
    if 920 <= spr <= 923 or 1008 <= spr <= 1023: return 'HID_cache_related'
    if 952 <= spr <= 958: return 'performance_monitors'
    if spr in (18, 19, 26, 27): return 'exception_registers'
    if spr in (284, 285): return 'timebase_registers'
    return 'other'


def inspect(root: Path) -> dict:
    files = sorted(root.glob('output_*.cpp'))
    if not files:
        raise ValueError('No generated translation shards')
    calls, reads, drops, groups = Counter(), Counter(), Counter(), Counter()
    traps = 0
    for f in files:
        src = f.read_text(encoding='utf-8')
        wr = [int(x) for x in WRITE_RE.findall(src)]
        calls.update(wr)
        groups.update(family(spr) for spr in wr)
        reads.update(int(x) for x in READ_RE.findall(src))
        drops.update(int(x) for x in DROP_RE.findall(src))
        traps += len(OPCODE_RE.findall(src))
    return {
        'numbered_cpp_shards': len(files),
        'instrumented_spr_writes': sum(calls.values()),
        'distinct_instrumented_sprs': len(calls),
        'instrumented_spr_reads': sum(reads.values()),
        'ignored_mtspr': sum(drops.values()),
        'explicit_unsupported_traps': traps,
        'write_families': dict(sorted(groups.items())),
        'requires_hardware_implementation': True,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('generated_dir', type=Path)
    ap.add_argument('--expected-writes', type=int)
    args = ap.parse_args()
    info = inspect(args.generated_dir)
    print(json.dumps(info, indent=2))
    if info['ignored_mtspr'] or info['explicit_unsupported_traps']:
        raise SystemExit('Coverage gate failed: dropped writes or traps remain')
    if args.expected_writes is not None and info['instrumented_spr_writes'] != args.expected_writes:
        raise SystemExit('Coverage gate failed: unexpected write count')

if __name__ == '__main__':
    main()
