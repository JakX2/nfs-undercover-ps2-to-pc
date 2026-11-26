#!/usr/bin/env python3
"""Trace only the actual call arguments into the first diagnostic leaf."""
import argparse,struct
from pathlib import Path
from prepare_post_stm_sc_report_helper_fixture import plan as helper_plan
from prepare_post_stm_sc_report_helper_prefix import prefix
from prepare_post_stm_sc_report_abi import model
from prepare_post_stm_sc_report import REPORT
from prepare_post_stm_sc_report_dependency import census
from prepare_v419_full_start import MAX_DOL
from make_private_elf_symbol_map import parse_functions
from make_v624_ipc_geometry import exact_words

def compose(value,report_regs,report_frame):
    kind,n=value
    if kind=='reg':return report_regs[n]
    if kind=='stack':return ('stack',n-report_frame)
    return value

def classify(words):
    # This is an opcode census, not a reconstruction of private instructions.
    # Return only counts of admissible public PPC operation forms.
    counts={}
    for w in words:
        op=w>>26;xo=(w>>1)&1023
        if w==0x4e800020:k='return'
        elif op==16:k='bc_cr' if (w>>21)&4 else 'bc_ctr'
        elif op==18:k='b'
        elif op in (10,11):k='cmp_imm'
        elif op in (14,15):k='add_imm'
        elif op in (20,21,23):k='rotate'
        elif op in (24,25,26,27,28,29):k='logic_imm'
        elif op in (32,34,40,42):k='load_'+str({32:4,34:1,40:2,42:2}[op])
        elif op in (36,38,44):k='store_'+str({36:4,38:1,44:2}[op])
        elif op==31 and xo in (0,32):k='cmp_reg'
        elif op==31 and xo in (444,28,316):k='logic_reg'
        elif op==31 and xo in (266,40):k='add_sub_reg'
        elif op==31 and xo in (24,536):k='shift_reg'
        else:k='other'
        counts[k]=counts.get(k,0)+1
    return counts

def arguments(report_regs,report_frame,helper_regs):
    args=tuple(compose(helper_regs[r],report_regs,report_frame) for r in range(3,11))
    if args[0][0]!='stack' or not -report_frame<=args[0][1]<=-12 or args[0][1]&3:
        raise ValueError('dependency argument provenance')
    if args[1][0]!='const':raise ValueError('dependency argument type')
    return args

def plan(d,e):
    prior=helper_plan(d,e);helper,_,root,_,_=prior[3]
    sizes=parse_functions(e)
    report=exact_words(d,e,REPORT,sizes[REPORT]//4)
    report_regs,report_slots=model(REPORT,report,details=True)
    helper_regs,_,_,_=prefix(helper,exact_words(d,e,helper,30),details=True)
    args=arguments(report_regs,128,helper_regs)
    ws=exact_words(d,e,root,33)
    edges,rows,returns,_,_,_,back,_=census(root,ws)
    if edges or back or len(returns)!=2:raise ValueError('dependency leaf')
    # The report's va_list is the only mutable object in this leaf.
    at=args[0][1]
    if report_slots.get(at)!=('const',0x01000000) or report_slots.get(at+4)!=('stack',8) or report_slots.get(at+8,(None,))[0]!='stack':
        raise ValueError('dependency va list')
    if any(w>>26 in (32,34,40,42,36,38,44) and ((w>>16)&31)!=3 for w in ws):
        raise ValueError('dependency memory base')
    counts=classify(ws)
    if counts.get('other',0) or counts.get('bc_ctr',0):raise ValueError('dependency instruction class')
    return counts,args,at

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);q=a.parse_args()
    safe={'size','dependency argument provenance','dependency argument type','dependency leaf','dependency va list','dependency memory base','dependency instruction class'}
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not 52<=q.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        counts,args,at=plan(q.dol.read_bytes(),q.elf.read_bytes())
    except (OSError,ValueError,KeyError,IndexError,TypeError,struct.error) as ex:
        print('POST_STM_SC_REPORT_DEPENDENCY_ABI verified=0 reason='+(str(ex).replace(' ','_') if str(ex) in safe else 'private_input'))
        return 1
    print('POST_STM_SC_REPORT_DEPENDENCY_ABI verified=1 va_list=1 constant_selector=1 argument_memory_only=1 original_execution=0')
    print('POST_STM_SC_REPORT_DEPENDENCY_OPS '+' '.join(f'{k}={v}' for k,v in sorted(counts.items())))
    return 0
if __name__=='__main__':raise SystemExit(main())
