#!/usr/bin/env python3
"""No-game-file V44 cache-trace patch atomicity and version safety checks."""
import tempfile
from pathlib import Path
from apply_cache_trace_v44 import apply, FILE, OLD, NEW

checks=0

def test(ok,reason):
    global checks
    if not ok:
        raise AssertionError(reason)
    checks+=1


def main():
    with tempfile.TemporaryDirectory(prefix='v44_cache_trace_guards_') as d:
        root=Path(d)
        path=root/FILE
        path.parent.mkdir(parents=True)
        base='// independently-authored fixture\n'+OLD[0]+'\n'+OLD[1]+'\n'
        path.write_text(base)
        test(apply(root),'V43 -> V44 cache-trace patch not installed')
        upgraded=path.read_text()
        test(all(upgraded.count(x)==1 for x in NEW),'new trace capacities not installed uniquely')
        test(all(x not in upgraded for x in OLD),'old trace capacities retained')
        test(not apply(root),'reinstall was not idempotent')
        test(path.read_text()==upgraded,'idempotent apply changed file')
        def reject(body,reason):
            path.write_text(body)
            try:apply(root)
            except ValueError:pass
            else:raise AssertionError(reason)
            test(path.read_text()==body,'failed patch unexpectedly wrote partial source')
        reject('// other revision\n','unknown runtime source accepted')
        reject(OLD[0]+'\n','missing invalidate trace accepted')
        reject(OLD[1]+'\n','missing flush trace accepted')
        reject(OLD[0]+'\n'+OLD[0]+'\n'+OLD[1],'duplicate old anchor accepted')
        reject(NEW[0]+'\n'+NEW[0]+'\n'+NEW[1],'duplicate new anchor accepted')
        reject(NEW[0]+'\n'+OLD[1],'partially updated trace accepted')
        reject(OLD[0]+'\n'+NEW[1],'inverse partial source accepted')
        reject(OLD[0]+'\n'+OLD[1]+'\n'+NEW[0],
               'mixed current and previous flush anchor accepted')
        reject(NEW[0]+'\n'+NEW[1]+'\n'+OLD[1],
               'mixed current and previous invalidate anchor accepted')
        path.write_text(base)
        test(apply(root),'known previous revision not recovered after rejection tests')
        test(path.read_text()==upgraded,'recovery result differs from originally upgraded source')
    print(f'PASS: {checks} V44 original-free cache trace guard checks')


if __name__=='__main__':main()
