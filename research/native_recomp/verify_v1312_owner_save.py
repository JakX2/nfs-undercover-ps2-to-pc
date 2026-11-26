#!/usr/bin/env python3
"""Run the geometry and save audit on owner inputs without building native code."""
import argparse,struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL
from make_v1256_scheduler_fixture import geometry,SAVE
from prepare_v1307_cooperative_fixture import plan
from save_provenance_v1312 import audit_save

def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);a=p.parse_args()
    try:
        if not 256<=a.dol.stat().st_size<=MAX_DOL or not 52<=a.elf.stat().st_size<=64*1024*1024:
            raise ValueError('size')
        d,e=a.dol.read_bytes(),a.elf.read_bytes()
        sn,*_=geometry(d,e)
        mask=audit_save(sn[SAVE])
        print(f'V1312_OWNER_SAVE verified=1 saved_integer=1 gqr_count={mask.bit_count()} msr_identity=1 return_zero=1 saved_one=1')
    except (OSError,ValueError,KeyError,IndexError,struct.error) as ex:
        allowed=('size','save terminal','save store geometry','save base','save encoding','save spr','save instruction','save provenance','save preserved ABI','save gqr provenance')
        print('V1312_OWNER_SAVE verified=0 reason='+ (str(ex).replace(' ','_') if str(ex) in allowed else 'prior_or_io'))
        return 1
    try:
        roots,sites,_,_=plan(d,e)
        print(f'V1312_OWNER_GEOMETRY verified=1 roots={len(roots)} direct_edges={len(sites)}')
        return 0
    except (OSError,ValueError,KeyError,IndexError,struct.error) as ex:
        allowed=('clear extent','clear control','clear predecessor','cooperative save coverage','cooperative save control','resume direct edge')
        print('V1312_OWNER_GEOMETRY verified=0 reason='+(str(ex).replace(' ','_') if str(ex) in allowed else 'prior_or_io'))
        return 1
if __name__=='__main__':raise SystemExit(main())
