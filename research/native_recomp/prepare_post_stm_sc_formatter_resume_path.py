#!/usr/bin/env python3
"""Independent private formatter continuation after the first original leaf."""
import argparse,struct
from pathlib import Path
from prepare_post_stm_sc_report_formatter_path import first_path,plan as prefix_plan,const
from prepare_post_stm_sc_formatter_leaf_path import run as leaf_run
from prepare_v419_full_start import MAX_DOL
from make_private_elf_symbol_map import parse_functions
from make_v624_ipc_geometry import exact_words

def resume(root,ws,prefix,leaf,readonly):
    path,frame,_,saved,_,gp,mem,state=prefix
    _,_,value,_,_,out_gp,out_cr=leaf
    if len(path)==0 or value[0]!='const' or out_gp[3]!=value or out_gp[1]!=gp[1] or out_gp[2]!=gp[2] or out_gp[13:]!=gp[13:]:
        raise ValueError('formatter resume leaf ABI')
    caller=path[-1]+4
    _,_,_,ctr,_,old_frame,saves=state
    if old_frame!=frame or len(saves)!=saved:raise ValueError('formatter resume state')
    restored=(out_gp,mem,out_cr,ctr,const(caller),frame,saves)
    return first_path(root,ws,{}, {},readonly,start=caller,resume=restored,details=True)

def plan(d,e):
    path,frame,accesses,saved,root,gp,mem,ws,state,readonly=prefix_plan(d,e,details=True)
    leaf=leaf_run(root,exact_words(d,e,root,12),gp,readonly,mem,initial_cr=state[2],details=True)
    if len(leaf[0])!=8 or len(leaf[1])!=1 or len(leaf[3])!=12:raise ValueError('formatter resume predecessor')
    result=resume(path[0],ws,(path,frame,accesses,saved,root,gp,mem,state),leaf,readonly)
    active,_,sites,_,dst,*_=result
    sizes=parse_functions(e);size=sizes.get(dst,0)
    if not 4<=size<=65536 or size%4:raise ValueError('formatter resume target')
    exact_words(d,e,dst,1)
    kind='direct' if ws[(active[-1]-path[0])//4]>>26==18 else 'indirect'
    return active,sites,size//4,kind

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);q=a.parse_args()
    safe={'size','formatter resume leaf ABI','formatter resume state','formatter resume predecessor','formatter resume target','formatter protected stack write','formatter unknown arithmetic','formatter unknown value','formatter stack read provenance','formatter pointer provenance','formatter data read provenance','formatter stack write provenance','formatter caller linkage provenance','formatter duplicate stack write','formatter update store','formatter indexed store provenance','formatter path bound','formatter frame identity','formatter other boundary','formatter update load','formatter compare','formatter branch','formatter CTR provenance','formatter CR provenance','formatter escape','formatter region cap','formatter boundary'}
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not 52<=q.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        path,sites,n,kind=plan(q.dol.read_bytes(),q.elf.read_bytes())
    except (OSError,ValueError,KeyError,IndexError,TypeError,struct.error) as ex:
        reason=str(ex)
        if reason.startswith('formatter opcode '):
            _,_,k,n=reason.split()
            if k in ('integer','load','store','branch','direct','return','system_control','other') and n.isdecimal() and 1<=int(n)<=512:
                print(f'POST_STM_SC_FORMATTER_RESUME_PATH verified=0 reason=opcode category={k} ordinal={n}');return 1
        print('POST_STM_SC_FORMATTER_RESUME_PATH verified=0 reason='+(reason.replace(' ','_') if reason in safe else 'private_input'))
        return 1
    print(f'POST_STM_SC_FORMATTER_RESUME_PATH verified=1 visits={len(path)} unique={len(set(path))} loads={sum(k.endswith("_read") for _,k,_,_ in sites)} stores={sum(k=="stack_write" for _,k,_,_ in sites)} next_call={kind} target_words={n} original_execution=0')
    return 0
if __name__=='__main__':raise SystemExit(main())
