#!/usr/bin/env python3
"""Fail-closed source patch guards for optional L2CR test device interface."""
import argparse
import tempfile
from pathlib import Path
from apply_l2cr_device_v62 import CHANGES,apply

def main():
    p=argparse.ArgumentParser();p.add_argument('patched_nwiirecomp_root',type=Path);a=p.parse_args()
    with tempfile.TemporaryDirectory(prefix='v62_device_patch_guard_') as d:
        root=Path(d);before={};after={}
        for rel,old,new,count in CHANGES:
            data=(a.patched_nwiirecomp_root/rel).read_text(encoding='utf-8')
            assert data.count(new)==count and data.count(old)==0
            (root/rel).parent.mkdir(parents=True,exist_ok=True)
            (root/rel).write_text(data.replace(new,old),encoding='utf-8')
            before[rel]=(root/rel).read_bytes();after[rel]=data.encode()
        assert apply(root)=='installed';assert apply(root)=='already applied'
        assert all((root/rel).read_bytes()==data for rel,data in after.items())
        n=2
        for rel,old,new,count in CHANGES:
            for state,anchor in ((before,old),(after,new)):
                for key,data in state.items():(root/key).write_bytes(data)
                path=root/rel
                text=path.read_text()
                path.write_text(text.replace(anchor,anchor[:len(anchor)//2]+'__SPOILED__'+anchor[len(anchor)//2:],1))
                snapshot={key:(root/key).read_bytes() for key in before}
                try:apply(root)
                except ValueError:pass
                else:raise AssertionError('V62 accepted mutated anchor')
                assert all((root/key).read_bytes()==data for key,data in snapshot.items())
                n+=1
            for key,data in before.items():(root/key).write_bytes(data)
            (root/rel).write_bytes(after[rel])
            snapshot={key:(root/key).read_bytes() for key in before}
            try:apply(root)
            except ValueError:pass
            else:raise AssertionError('V62 accepted mixed patch state')
            assert all((root/key).read_bytes()==data for key,data in snapshot.items())
            n+=1
            for key,data in before.items():(root/key).write_bytes(data)
            path=root/rel;path.write_text(path.read_text()+old)
            snapshot={key:(root/key).read_bytes() for key in before}
            try:apply(root)
            except ValueError:pass
            else:raise AssertionError('V62 accepted duplicate original anchor')
            assert all((root/key).read_bytes()==data for key,data in snapshot.items())
            n+=1
    print(f'PASS: V62 {n}/{n} L2CR explicit-read-provider source guards')
if __name__=='__main__':main()
