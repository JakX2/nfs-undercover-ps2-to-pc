#!/usr/bin/env python3
import argparse,struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL
from prepare_v1176_ack_helper import metadata
from prepare_v667_si_dispatch import HANDLER
from prepare_v789_alarm_suffix import expectations
from derive_nested_ack_path_v1331 import derive
def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);a=p.parse_args()
    try:
        if not 256<=a.dol.stat().st_size<=MAX_DOL or not 52<=a.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        d,e=a.dol.read_bytes(),a.elf.read_bytes()
        spans,edges,rows,msr,expected,*_=metadata(d,e)
        _,_,sites=expectations(d,e)
        site,dst,paths=derive(rows,edges,msr,HANDLER,expected[0],sites[0])
        if (site,dst)!=edges[3] or dst!=spans[3][0]:raise ValueError('nested census candidate')
        print(f'V1331_NESTED_CENSUS verified=1 paths={len(paths)} min_visits={min(p[0] for p in paths)} max_visits={max(p[0] for p in paths)} min_calls={min(p[1] for p in paths)} max_calls={max(p[1] for p in paths)} min_msr={min(p[2] for p in paths)} max_msr={max(p[2] for p in paths)} original_execution=0')
        return 0
    except (OSError,ValueError,KeyError,IndexError,TypeError,struct.error) as ex:
        allowed=('size','nested census limit','nested census candidate','nested census identity','nested census frontier','nested census complexity','nested census no route')
        print('V1331_NESTED_CENSUS verified=0 reason='+(str(ex).replace(' ','_') if str(ex) in allowed else 'prior_or_io'));return 1
if __name__=='__main__':raise SystemExit(main())
