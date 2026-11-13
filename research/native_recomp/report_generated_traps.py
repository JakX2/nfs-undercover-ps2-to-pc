#!/usr/bin/env python3
"""Aggregate unsupported translation traps without exposing game code or addresses."""
import argparse
from collections import Counter
from pathlib import Path
import re

def report(base: Path) -> dict:
    shards = list(base.glob('output_*.cpp'))
    if not shards:
        raise ValueError('No numbered translation shards present')
    traps = Counter()
    mtspr = Counter()
    for path in shards:
        content = path.read_text(encoding='utf-8')
        for opcode in re.findall(r'UNIMPLEMENTED Opcode (\d+) \(ps_\*\)', content):
            traps[f'opcode_{opcode}'] += 1
        for opcode in re.findall(r'UNIMPLEMENTED OPCODE (\d+)', content):
            traps[f'opcode_{opcode}'] += 1
        for opcode in re.findall(r'UNIMPLEMENTED Opcode (\d+) XO', content):
            traps[f'opcode_{opcode}'] += 1
        for spr in re.findall(r'// unhandled mtspr (\d+)', content):
            mtspr[int(spr)] += 1
    return {'numbered_cpp_shards': len(shards), 'hard_traps_total': sum(traps.values()),
            'hard_traps_by_opcode': dict(sorted(traps.items())),
            'unhandled_mtspr_total': sum(mtspr.values()),
            'unhandled_mtspr_unique_sprs': len(mtspr)}

if __name__ == '__main__':
    import json
    ap = argparse.ArgumentParser()
    ap.add_argument('generated_output', type=Path)
    args = ap.parse_args()
    print(json.dumps(report(args.generated_output), indent=2))
