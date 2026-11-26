#!/usr/bin/env python3
"""Compare private planning results with and without process-local memoization."""
import argparse,struct
from pathlib import Path
from time import perf_counter_ns
from prepare_formatter_nested_fixture import plan
from private_plan_cache import plan_cache_scope
from prepare_v419_full_start import MAX_DOL

def compare(d,e,derive=plan,clock=perf_counter_ns):
    start=clock()
    uncached=derive(d,e,second=False)
    middle=clock()
    with plan_cache_scope():
        cached=derive(d,e,second=False)
    end=clock()
    if uncached!=cached:raise ValueError('cache plan mismatch')
    if not start<=middle<=end:raise ValueError('clock')
    return (middle-start)//1000000,(end-middle)//1000000

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);q=a.parse_args()
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not 52<=q.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        plain,cached=compare(q.dol.read_bytes(),q.elf.read_bytes())
    except (OSError,ValueError,TypeError,KeyError,IndexError,struct.error) as ex:
        reason=str(ex)
        print('FORMATTER_PLAN_CACHE_BENCH verified=0 reason='+(reason.replace(' ','_') if reason in ('size','clock','cache plan mismatch') else 'private_input'))
        return 1
    print(f'FORMATTER_PLAN_CACHE_BENCH verified=1 equal=1 uncached_ms={plain} cached_ms={cached} original_execution=0')
    return 0
if __name__=='__main__':raise SystemExit(main())
