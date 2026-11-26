#!/usr/bin/env python3
import argparse,struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL
from prepare_v1176_ack_helper import metadata
from prepare_v667_si_dispatch import HANDLER
from derive_first_ack_call_v1330 import classify,first_calls

def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);a=p.parse_args()
    try:
        if not 256<=a.dol.stat().st_size<=MAX_DOL or not 52<=a.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        spans,edges,rows,msr,expected,*_=metadata(a.dol.read_bytes(),a.elf.read_bytes())
        if len(edges)!=8 or len(spans)!=7:raise ValueError('census metadata')
        candidates=classify(rows,edges,HANDLER,expected[0],20)
        reachable=first_calls(rows,edges,HANDLER,expected[0])
        print(f'V1330_ACK_CALL_CENSUS verified=1 refusal_visit=20 candidate_count={len(candidates)} distinct_first_edges={len(set(e for _,e in reachable))} original_execution=0')
        for n in candidates:
            dst=edges[n-1][1]
            roots=[i+1 for i,(a,_,_) in enumerate(spans) if a==dst]
            if len(roots)!=1:raise ValueError('census metadata')
            print(f'V1330_ACK_CALL_CANDIDATE edge_ordinal={n} root_class={roots[0]} call_visit=19')
        return 0
    except (OSError,ValueError,KeyError,IndexError,TypeError,struct.error) as ex:
        allowed=('size','call census limit','call census identity','call census start','call census edge','call census refusal','census metadata')
        print('V1330_ACK_CALL_CENSUS verified=0 reason='+(str(ex).replace(' ','_') if str(ex) in allowed else 'prior_or_io'));return 1
if __name__=='__main__':raise SystemExit(main())
