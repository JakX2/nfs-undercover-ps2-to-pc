#!/usr/bin/env python3
"""Read-only verification of private complete focused scheduler fixture."""
import argparse,struct
from pathlib import Path
from prepare_v1321_combined_resume import plan,scope,render,ram_rows,HELPER,CLEAR
from prepare_v1281_reply_fixture import symbols
from prepare_v419_full_start import MAX_DOL,words_at
from prepare_v1299_reply_return import plan as reply_plan,verify_fixture as verify_reply

def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('out',type=Path);a=p.parse_args()
    try:
        if not 256<=a.dol.stat().st_size<=MAX_DOL or not 52<=a.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        d,e=a.dol.read_bytes(),a.elf.read_bytes()
        result=plan(d,e)
        raw=(a.out/'fixture.dol').read_bytes()
        sizes=symbols((a.out/'symbols.csv').read_text())
        if len(sizes)+2>48:raise ValueError('root budget')
        spans=dict(scope(d,e,sizes))
        if spans.get(CLEAR)!=36 or spans.get(HELPER)!=124:raise ValueError('scope extent')
        coop,helper,edges,indirect,callback=result
        roots,_,_,mask=coop
        rows=ram_rows(roots,callback)
        if len({pc for _,pc,_ in rows})!=len(rows) or any(words_at(raw,pc,1)!=(w,) for _,pc,w in rows):
            raise ValueError('ram manifest')
        if (a.out/'v1321_private_selection.h').read_text()!=render(result):raise ValueError('header roundtrip')
        verify_reply(raw,sizes,reply_plan(d,e,True))
        print(f'V1325_OWNER_COMBINED verified=1 fixture_roots={len(sizes)+2} expanded_guards=2 ram_words={len(rows)} direct_edges={len(edges)} indirect_edges={len(indirect)} gqr_count={mask.bit_count()} original_execution=0')
        return 0
    except (OSError,ValueError,KeyError,IndexError,struct.error) as ex:
        allowed=('size','root budget','scope extent','ram manifest','header roundtrip','combined GQR or callback identity','combined selection edges','combined guard scope','combined ownership','return fixture identity')
        print('V1325_OWNER_COMBINED verified=0 reason='+(str(ex).replace(' ','_') if str(ex) in allowed else 'prior_or_io'))
        return 1
if __name__=='__main__':raise SystemExit(main())
