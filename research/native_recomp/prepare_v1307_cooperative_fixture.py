#!/usr/bin/env python3
"""Private cooperative scheduler continuation geometry; no owner words published."""
import argparse,struct
from pathlib import Path
from make_v1256_scheduler_fixture import geometry as sched_geometry,SELECT,SAVE,SET,GET,ENABLE
from make_v1252_sleep_fixture import geometry as sleep_geometry,SLEEP
from prepare_v1270_ipc_epilogue import geometry as ep_geometry,L,DISABLE,RESTORE
from prepare_v1289_wake_fixture import plan as wake_plan,scope as wake_scope
from prepare_v1281_reply_fixture import symbols
from prepare_v1260_scheduler_vector import SOURCE,SC_SOURCE,VECTORS,BLR
from make_v624_ipc_geometry import ROOT,exact_words
from make_v626_ipc_fixture import assemble
from prepare_v419_full_start import words_at,direct_bl,MAX_DOL
from prepare_v453_debug_leaf import data_at
from make_private_elf_symbol_map import parse_functions
from prepare_owner_context_v720 import validate_shape
from prepare_v625_ipc_client import audit_native
from prepare_v680_si_helper import verify_direct
from prepare_v1299_reply_return import verify_resume
from prepare_owner_scheduler_v722 import reachable
from audit_handler_suffix_v728 import target
from prepare_v1270_ipc_epilogue import analyzer
CLEAR=0x80522af4
SAVE_RETURN=0x80529818
SLEEP_RETURN=0x8052a4fc
RESTORE_SITE=0x8052a500
RFI=0x4c000064

def leaf_shape(root,ws):
    if not 1<=len(ws)<=64 or ws[-1]!=BLR:raise ValueError('clear extent')
    for i,w in enumerate(ws):
        pc=root+4*i;op=w>>26;xo=(w>>1)&1023
        if op in (16,18) and (w&3 or not root<=target(pc,w)<root+4*len(ws)):
            raise ValueError('clear control')
        if op==17 or (op==19 and (xo in (50,528) or (xo==16 and w&1))) or (op==31 and xo==146):
            raise ValueError('clear control')

def saved_offsets(ws):
    # Structural check only: base r3, scalar word/halfword stores and stmw.
    # The runtime witness still authenticates actual values and provenance.
    out=set()
    for w in ws:
        op=w>>26;rs=(w>>21)&31;ra=(w>>16)&31;d=w&0xffff
        if ra!=3 or d>=0x2c8:continue
        if op==36 and not d&3:out.add(d)
        if op==47 and not d&3:out.update(d+4*i for i in range(32-rs))
    return out

def check_save(ws):
    required={4,8,12,128,132,136,140,408,412}|set(range(13*4,32*4,4))
    if len(ws)!=32 or ws[-1]!=BLR or not required<=saved_offsets(ws):
        raise ValueError('cooperative save coverage')
    if any(w>>26 in (16,18,17) or (w>>26==19 and ((w>>1)&1023) in (50,528)) for w in ws):
        raise ValueError('cooperative save control')

def call(roots,owner,site,dst):
    ws=roots[owner];i=(site-owner)//4
    if not 0<=i<len(ws) or (site-owner)&3 or direct_bl(ws[i],site)!=dst:raise ValueError('resume direct edge')

def plan(dol,elf):
    sn,st,edges,indirect,mt=sched_geometry(dol,elf);ep=ep_geometry(dol,elf)
    sleep,_,_=sleep_geometry(dol,elf);sizes=parse_functions(elf)
    if sizes.get(CLEAR)!=0x24:raise ValueError('clear extent')
    clear=tuple(exact_words(dol,elf,CLEAR,9));leaf_shape(CLEAR,clear)
    if st.get(CLEAR)!=(clear[0],):raise ValueError('clear predecessor')
    roots={SELECT:tuple(sn[SELECT]),SAVE:tuple(sn[SAVE]),SET:tuple(sn[SET]),GET:tuple(sn[GET]),
           CLEAR:clear,ENABLE:tuple(sn[ENABLE]),L:tuple(ep[3][L]),DISABLE:tuple(ep[3][DISABLE]),RESTORE:tuple(ep[3][RESTORE]),
           SLEEP:tuple(sleep)}
    check_save(roots[SAVE]);gqr=validate_shape(roots[L],L)
    sites=((SELECT,SAVE_RETURN-4,SAVE),(SELECT,0x80529870,DISABLE),(SELECT,0x80529888,CLEAR),
           (SELECT,0x80529918,SET),(SELECT,0x80529920,L),(SLEEP,SLEEP_RETURN-4,SELECT),(SLEEP,RESTORE_SITE,RESTORE))
    for owner,site,dst in sites:call(roots,owner,site,dst)
    return roots,sites,mt[0],gqr

def merge(blocks,roots):
    out=dict(blocks)
    for pc,ws in roots.items():
        old=out.get(pc)
        if pc==CLEAR:
            if old!=(ws[0],BLR):raise ValueError('clear predecessor')
            out[pc]=ws
        elif old!=ws:raise ValueError('resume shared identity')
    spans=sorted((pc,pc+4*len(ws)) for pc,ws in out.items())
    if any(aend>b for (_,aend),(b,_) in zip(spans,spans[1:])) or len(out)+2>48:
        raise ValueError('resume ownership')
    return out

def extend(raw,csv,p):
    blocks={pc:words_at(raw,pc,n//4) for pc,n in symbols(csv).items()}
    blocks=merge(blocks,p[0]);table=data_at(raw,VECTORS,60)
    out=bytearray(assemble({**blocks,SOURCE:words_at(raw,SOURCE,38),SC_SOURCE:words_at(raw,SC_SOURCE,7)},ROOT,max_roots=48))
    for off,v in ((0x1c,len(out)),(0x64,VECTORS),(0xac,len(table))):struct.pack_into('>I',out,off,v)
    csv='Name,Location,Size\n'+''.join(f'func_{pc:08X},{pc:08x},{len(ws)*4}\n' for pc,ws in sorted(blocks.items()))
    return bytes(out)+table,csv

def scope(dol,elf,sizes):
    old={**sizes,CLEAR:8};spans=dict(wake_scope(wake_plan(dol,elf),old))
    if spans.get(CLEAR)!=8 or sizes.get(CLEAR)!=0x24:raise ValueError('resume ownership')
    spans[CLEAR]=sizes[CLEAR];out=sorted(spans.items())
    if any(a+n>b for (a,n),(b,_) in zip(out,out[1:])):raise ValueError('resume ownership')
    return out

def audit(src,main,p):
    roots,sites,mt,_=p
    expected={pc:(owner,ws[(pc-owner)//4]) for owner,ws in roots.items()
        for pc in (range(owner,owner+4*len(ws),4) if owner==L else reachable(owner,ws))}
    if audit_native(src,main,expected)!=len(expected):raise ValueError('resume coverage')
    verify_resume(main,((mt[0],ENABLE),
                        (SAVE_RETURN,SELECT),(SLEEP_RETURN,SLEEP)))
    for owner,site,dst in sites:
        hits=[s for s in src if f'loc_{site:X}: ;' in s]
        if len(hits)!=1:raise ValueError('resume direct owner')
        verify_direct(hits[0],site,dst)
    return len(expected)

def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('out',type=Path)
    m=p.add_mutually_exclusive_group();m.add_argument('--audit',action='store_true');m.add_argument('--analyzer',action='store_true')
    p.add_argument('--symbols',type=Path);a=p.parse_args()
    try:
        if not 256<=a.dol.stat().st_size<=MAX_DOL or not 52<=a.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        d,e=a.dol.read_bytes(),a.elf.read_bytes();result=plan(d,e)
        if a.analyzer:
            if a.symbols is None:raise ValueError('resume ownership')
            a.out.write_text(analyzer(a.out.read_text(),scope(d,e,symbols(a.symbols.read_text()))))
            print('V1307_COOP_ANALYZER verified=1 expanded_roots=1');return 0
        if a.audit:
            n=audit([x.read_text() for x in sorted(a.out.glob('output_*.cpp'))],(a.out/'main_output.cpp').read_text(),result)
            print(f'V1307_COOP_TRANSLATION verified=1 native_labels={n} expanded_roots=1');return 0
        image=a.out/'fixture.dol';csv=a.out/'symbols.csv'
        raw,rows=extend(image.read_bytes(),csv.read_text(),result)
        image.write_bytes(raw);csv.write_text(rows)
        print('V1307_COOP_FIXTURE accepted=1 additional_roots=0 expanded_roots=1');return 0
    except (OSError,ValueError,KeyError,IndexError,struct.error) as ex:
        allowed=('size','clear extent','clear control','clear predecessor','cooperative save coverage',
            'cooperative save control','resume direct edge','resume shared identity','resume ownership','resume coverage','resume direct owner')
        print('V1307_COOP_PREP accepted=0 reason='+(str(ex).replace(' ','_') if str(ex) in allowed else 'prior_or_io'));return 1
if __name__=='__main__':raise SystemExit(main())
