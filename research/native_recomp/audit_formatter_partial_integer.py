#!/usr/bin/env python3
"""Redacted classification of the next integer operation after a proven prefix."""
import argparse,struct
from collections import Counter
from pathlib import Path
from audit_formatter_partial_copy import plan as replay_plan
from prepare_v419_full_start import MAX_DOL
from private_plan_cache import plan_cache_scope

# Classify operand direction and architectural side effects independently
# of the existing symbolic engine. Never expose private operand numbers,
# literal values, instruction words, or addresses.
D={7:('multiply_immediate',False,False),8:('subtract_immediate_carry',False,True),
   12:('add_immediate_carry',False,True),13:('add_immediate_carry',True,True),
   14:('add_immediate',False,False),15:('add_immediate',False,False)}
LOGICAL={24:'or_immediate',25:'or_immediate',26:'xor_immediate',27:'xor_immediate',28:'and_immediate',29:'and_immediate'}
X_LOG={28:'and',60:'and_complement',124:'nor',284:'equivalence',316:'xor',
       412:'or_complement',444:'or',476:'nand',24:'shift_left',536:'shift_right',792:'shift_arithmetic'}
X_UNARY={26:'count_leading_zero',922:'sign_extend_half',954:'sign_extend_byte',824:'shift_arithmetic_immediate'}
# XO-form arithmetic has an OE bit; X-form operations do not.
XO_BINARY={8:'subtract_carry',10:'add_carry',40:'subtract',136:'subtract_extended',138:'add_extended',
           235:'multiply_low',266:'add',459:'divide_unsigned',491:'divide_signed'}
XO_UNARY={104:'negate',200:'subtract_zero_extended',202:'add_zero_extended',232:'subtract_minus_one_extended',234:'add_minus_one_extended'}
XER_READ={136,138,200,202,232,234}
XER_WRITE={8,10,136,138,200,202,232,234}

def classify(w):
    op,rt,ra,rb,xo=w>>26,(w>>21)&31,(w>>16)&31,(w>>11)&31,(w>>1)&1023
    rc=bool(w&1)
    if op in D:
        name,cr,carry=D[op];reads=() if op in (14,15) and not ra else (ra,)
        return name,reads,(rt,),int(cr),0,int(carry),0
    if op in LOGICAL:return LOGICAL[op],(rt,),(ra,),int(op in (28,29)),0,0,0
    if op in (10,11):return 'compare_immediate',(ra,),(),1,0,0,0
    if op in (20,21,23):
        reads=(rt,ra) if op==20 else (rt,rb) if op==23 else (rt,)
        return ('rotate_insert' if op==20 else 'rotate_mask'),reads,(ra,),int(rc),0,0,0
    if op!=31:return 'unclassified',(),(),0,0,0,0
    if xo in X_LOG:return X_LOG[xo],(rt,rb),(ra,),int(rc),0,int(xo==792),0
    if xo in X_UNARY:return X_UNARY[xo],(rt,),(ra,),int(rc),0,int(xo==824),0
    if xo in (0,32):return 'compare_register',(ra,rb),(),1,0,0,0
    if xo in (19,144):
        return ('read_condition' if xo==19 else 'write_condition'),() if xo==19 else (rt,),(rt,) if xo==19 else (),int(xo==144),0,0,0
    if xo in (339,467):
        spr=ra|(rb<<5)
        return ('read_special' if xo==339 else 'write_special'),() if xo==339 else (rt,),(rt,) if xo==339 else (),0,int(spr==1 and xo==339),int(spr==1 and xo==467),0
    code=xo&511;oe=bool(xo&512)
    if code in XO_BINARY or code in XO_UNARY:
        name=(XO_BINARY if code in XO_BINARY else XO_UNARY)[code]
        reads=(ra,rb) if code in XO_BINARY else (ra,)
        return name,reads,(rt,),int(rc),int(code in XER_READ),int(code in XER_WRITE or oe),int(oe)
    return 'unclassified',(),(),0,0,0,0

def describe(w,gp):
    name,reads,writes,cr,carry_read,xer_write,oe=classify(w)
    if len(gp)!=32:raise ValueError('integer audit register geometry')
    kinds=Counter(gp[r][0] for r in set(reads))
    if any(k not in ('const','stack','partial','reg','lr') for k in kinds):raise ValueError('integer audit provenance')
    return (name,len(set(reads)),len(set(writes)),kinds['const'],kinds['stack'],kinds['partial'],
            kinds['reg']+kinds['lr'],cr,carry_read,xer_write,oe,int(bool(set(reads)&set(writes))))

def plan(d,e):
    result,extra,trace,admitted,entry,record=replay_plan(d,e,details=True)
    if result[3:9]!=(1,1,2,2,11,'other') or extra!=('integer',11,1,16) or len(trace)!=12:
        raise ValueError('integer audit predecessor')
    _,w,gp,_=trace[-1]
    return describe(w,gp)

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);q=a.parse_args()
    safe={'size','integer audit predecessor','integer audit register geometry','integer audit provenance'}
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not 52<=q.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        with plan_cache_scope():
            name,reads,writes,constant,stack,partial,other,cr,carry_read,xer_write,oe,alias=plan(q.dol.read_bytes(),q.elf.read_bytes())
    except (OSError,ValueError,TypeError,KeyError,IndexError,struct.error) as ex:
        print('FORMATTER_PARTIAL_INTEGER verified=0 reason='+(str(ex).replace(' ','_') if str(ex) in safe else 'private_input'));return 1
    print(f'FORMATTER_PARTIAL_INTEGER verified=1 family={name} reads={reads} writes={writes} constant_inputs={constant} stack_inputs={stack} partial_inputs={partial} other_inputs={other} condition_write={cr} carry_read={carry_read} xer_write={xer_write} overflow_enable={oe} alias={alias} original_execution=0')
    return 0
if __name__=='__main__':raise SystemExit(main())
