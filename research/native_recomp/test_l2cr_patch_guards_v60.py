#!/usr/bin/env python3
"""V60 runtime patch guard suite, tested on an isolated source snapshot."""
import argparse
import shutil
import tempfile
from pathlib import Path
from apply_l2cr_state_v60 import EDITS, apply


def source_map(root):
    return {relative:(root/relative).read_bytes() for relative,*_ in EDITS}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('patched_nwiirecomp_root',type=Path)
    args=ap.parse_args()
    with tempfile.TemporaryDirectory(prefix='v60_l2cr_source_guard_') as dir_name:
        root=Path(dir_name)
        # Reconstruct only the exact prepatch source anchors from the already-
        # validated checkout, so no upstream source mutation escapes this test.
        seen=set()
        for relative,old,new,count in EDITS:
            if relative not in seen:
                (root/relative).parent.mkdir(parents=True,exist_ok=True)
                shutil.copy2(args.patched_nwiirecomp_root/relative,root/relative)
                seen.add(relative)
            path=root/relative
            text=path.read_text(encoding='utf-8')
            if text.count(new)!=count:
                raise AssertionError(f'missing installed V60 anchor in {relative}')
            path.write_text(text.replace(new,old),encoding='utf-8')
        original=source_map(root)
        assert apply(root)=='installed'
        installed=source_map(root)
        assert installed!=original
        assert apply(root)=='already applied'
        assert installed==source_map(root)
        n=2
        # Fail on every single source edit missing while preserving *all* files.
        for relative,old,new,count in EDITS:
            for where in ('before','after'):
                for key,contents in (original if where=='before' else installed).items():
                    (root/key).write_bytes(contents)
                path=root/relative
                data=path.read_text(encoding='utf-8')
                anchor=old if where=='before' else new
                assert anchor in data
                path.write_text(data.replace(anchor,anchor[:len(anchor)//2]+'X'+anchor[len(anchor)//2:],1),encoding='utf-8')
                snapshot=source_map(root)
                try:apply(root)
                except ValueError:pass
                else:raise AssertionError(f'V60 corrupt {where} anchor accepted: {relative}')
                assert snapshot==source_map(root), 'non-atomic failure on invalid source'
                n+=1
        # Refuse a mixed patch, including a valid single-file update.
        for relative,*_ in EDITS:
            for key,data in original.items():(root/key).write_bytes(data)
            (root/relative).write_bytes(installed[relative])
            snapshot=source_map(root)
            try:apply(root)
            except ValueError:pass
            else:raise AssertionError('V60 accepted partially updated source state')
            assert snapshot==source_map(root)
            n+=1
        # Duplicate source match is ambiguous even when otherwise original.
        for relative,old,new,count in EDITS:
            for key,data in original.items():(root/key).write_bytes(data)
            path=root/relative
            data=path.read_text(encoding='utf-8')
            path.write_text(data+old,encoding='utf-8')
            snapshot=source_map(root)
            try:apply(root)
            except ValueError:pass
            else:raise AssertionError('V60 accepted duplicated patch anchor')
            assert snapshot==source_map(root)
            n+=1
    print(f'PASS: V60 {n}/{n} guest-L2CR patch idempotency, ambiguity and atomic-failure guards')

if __name__=='__main__':main()
