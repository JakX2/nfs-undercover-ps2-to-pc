#!/usr/bin/env python3
"""Join the verified focused STM prefix and original Open fixture privately."""
import argparse,re,struct
from pathlib import Path
from make_v651_open_fixture import build as open_build,SOURCE
from make_v1243_stm_fixture import build as stm_build,BLR
from make_v626_ipc_fixture import assemble
from make_v624_ipc_geometry import ROOT
from prepare_v629_stm_open import STM,OPEN,FIRST_OPEN_CALL
from prepare_v419_full_start import words_at,MAX_DOL

def merge(raw,csv,stm_raw):
    blocks={}
    for row in csv.splitlines()[1:]:
        name,addr,n=row.split(',');pc=int(addr,16);size=int(n)
        if not re.fullmatch(r'func_[0-9A-F]{8}',name) or not size or size%4 or pc in blocks:
            raise ValueError('open symbols')
        blocks[pc]=words_at(raw,pc,size//4)
    if STM in blocks or SOURCE in blocks or OPEN not in blocks:raise ValueError('open merge roots')
    prefix=words_at(stm_raw,STM,(FIRST_OPEN_CALL-STM)//4+1)
    # The fixture-only BLR is never executed in the admitted lane.
    blocks[STM]=prefix+(BLR,)
    symbols='Name,Location,Size\n'+''.join(f'func_{pc:08X},{pc:08x},{len(ws)*4}\n' for pc,ws in sorted(blocks.items()))
    return assemble({**blocks,SOURCE:words_at(raw,SOURCE,7)},ROOT),symbols

def build(dol,elf):
    raw,csv,ipc,op,header,vector=open_build(dol,elf)
    stm_raw,_,prior_ipc,_,stm,data=stm_build(dol,elf)
    if prior_ipc!=ipc:raise ValueError('IPC identity')
    raw,csv=merge(raw,csv,stm_raw)
    return raw,csv,ipc,op,header,vector,stm,data

def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('out',type=Path);a=p.parse_args()
    try:
        if not 256<=a.dol.stat().st_size<=MAX_DOL or not 52<=a.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        raw,csv,ipc,op,header,vector,stm,data=build(a.dol.read_bytes(),a.elf.read_bytes())
        a.out.mkdir(mode=0o700)
        for name,body in (('symbols.csv',csv),('v624_private_ipc_expectations.h',ipc),('v639_private_open_expectations.h',op),
                          ('v626_private_words.h',header),('v629_private_stm_expectations.h',stm),('v1243_private_stm_data.h',data)):
            (a.out/name).write_text(body)
        (a.out/'fixture.dol').write_bytes(raw);(a.out/'vector.bin').write_bytes(vector)
    except (OSError,ValueError,struct.error,IndexError,KeyError):
        print('V1245_OPEN_FIXTURE accepted=0');return 1
    print('V1245_OPEN_FIXTURE accepted=1 owner=1 stm_prefix=23 vector=7 synthetic_stm_tail=1')
    return 0
if __name__=='__main__':raise SystemExit(main())
