#!/usr/bin/env python3
"""Derive private cold IPC client expectations from authenticated owner images."""
import argparse,hashlib,struct
from pathlib import Path
from prepare_v419_full_start import OWNER_SHA,MAX_DOL,words_at,direct_bl
from make_private_elf_symbol_map import ORIGINAL_SHA256,parse_functions
from audit_v264_osinit_retry_elf import read_words
from make_start_to_ipc_client_v69 import SPANS,EDGES,ROOT
CALL=0x80520948
RETURN=CALL+4
# Execution order, not sorted address order. Nested calls are interleaved.
ROUTE=((CALL,ROOT),(0x805194f4,0x80518fc8),(0x80518fe0,0x8052ae70),
       (0x80518fe8,0x8052ae78),(0x805194f8,0x80519084),(0x80519504,0x8051907c),
       (0x80519520,0x8051aa04),(0x8051aa28,0x805265ac),(0x8051ab10,0x805265d4),
       (0x8051952c,0x8051908c),(0x8051953c,0x805265f8),(0x80519544,0x805269bc),
       (0x805269d8,0x805265ac),(0x80526a08,0x805266e0),(0x80526a18,0x805265d4),
       (0x80519550,0x8051906c),(0x80519554,0x8051af28))
REGISTER=0x8051953c
ERRORS={'identity','span','span identity','call coverage','handler constant','handler root','handler span','word identity','route','return'}
def constants(words):
    """Conservative straight-line constant propagation; unknown op clears facts."""
    facts={}
    for w in words:
        op=w>>26;rd=(w>>21)&31;ra=(w>>16)&31;rb=(w>>11)&31;imm=w&0xffff
        signed=imm-(0x10000 if imm&0x8000 else 0)
        if op in (14,15):
            src=0 if not ra else facts.get(ra)
            val=None if src is None else (src+(signed<<(16 if op==15 else 0)))&0xffffffff
            dest=rd
        elif op in (24,25):
            src=facts.get(rd);val=None if src is None else src|(imm<<(16 if op==25 else 0));dest=ra
        elif op==31 and ((w>>1)&1023)==444:
            lhs,rhs=facts.get(rd),facts.get(rb);val=None if lhs is None or rhs is None else lhs|rhs;dest=ra
        else:
            # No guessed preservation across unclassified instructions or branches.
            facts.clear();continue
        if val is None:facts.pop(dest,None)
        else:facts[dest]=val
    return facts
def derive_handler(words,sizes):
    facts=constants(words);p=facts.get(4,0)
    if facts.get(3)!=27:raise ValueError('handler constant')
    n=sizes.get(p,0)
    if not 0x80519094<=p<ROOT or p&3 or not 4<=n<=0x1000 or p+n>ROOT:
        raise ValueError('handler root')
    return p,n
def exact_words(dol,elf,pc,n):
    words=words_at(dol,pc,n)
    if words!=tuple(read_words(elf,pc,n)):raise ValueError('word identity')
    return words
def geometry(dol,elf,dd=OWNER_SHA,ed=ORIGINAL_SHA256):
    if hashlib.sha256(dol).hexdigest()!=dd or hashlib.sha256(elf).hexdigest()!=ed:raise ValueError('identity')
    sizes=parse_functions(elf)
    if len(ROUTE)!=17 or not set(EDGES).issubset(ROUTE):raise ValueError('route')
    for pc,n in SPANS:
        if sizes.get(pc)!=n:raise ValueError('span')
        words=exact_words(dol,elf,pc,n//4)
        if words[-1]!=0x4e800020:raise ValueError('return')
        got={(pc+4*i,direct_bl(w,pc+4*i)) for i,w in enumerate(words) if w>>26==18 and w&3==1}
        want={(s,t) for s,t in ROUTE if pc<=s<pc+n}
        if got!=want:raise ValueError('call coverage')
    rows=[]
    for site,target in ROUTE:
        word=exact_words(dol,elf,site,1)[0]
        if direct_bl(word,site)!=target or not sizes.get(target):raise ValueError('route')
        rows.append((target,site+4,word,exact_words(dol,elf,target,1)[0]))
    # The handler pointer must actually be materialized by the original
    # caller, not inferred from a function's approximate address range.
    handler,n=derive_handler(exact_words(dol,elf,REGISTER-48,12),sizes)
    hword=exact_words(dol,elf,handler,n//4)[0]
    return rows,handler,hword,exact_words(dol,elf,RETURN,1)[0]
def render(rows,handler,hword,ret):
    if len(rows)!=17:raise ValueError('route')
    fmt=lambda seq:','.join(f'0x{w:08x}u' for w in seq)
    return ('#pragma once\n#include "wii_ipc_client_witness_v623.h"\nnamespace undercover::wii::v624 {\n'
            'inline constexpr IpcClientExpectations expected_client{std::array<VectorEdge,17>{'
            +','.join('VectorEdge{'+fmt(row)+'}' for row in rows)+'},'+fmt((handler,hword,ret))+'};\n}\n')
def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path)
    p.add_argument('--private-header',type=Path);a=p.parse_args()
    try:
        if not 256<=a.dol.stat().st_size<=MAX_DOL or not 52<=a.elf.stat().st_size<=64*1024*1024:
            raise ValueError('identity')
        g=geometry(a.dol.read_bytes(),a.elf.read_bytes())
        if a.private_header:
            if a.private_header.is_symlink():raise ValueError('identity')
            with a.private_header.open('x',encoding='utf-8') as f:f.write(render(*g))
    except (OSError,ValueError,struct.error) as e:
        reason=str(e) if str(e) in ERRORS else 'other'
        print('V624_IPC_GEOMETRY accepted=0 reason='+reason.replace(' ','_'));return 1
    print('V624_IPC_GEOMETRY owner=1 accepted=1 calls=17 spans=10 handler=1 exact_dol_elf=1')
    return 0
if __name__=='__main__':raise SystemExit(main())
