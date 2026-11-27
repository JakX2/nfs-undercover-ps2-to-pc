#!/usr/bin/env python3
import unittest
from contextlib import redirect_stdout
from io import StringIO
from prepare_formatter_nested_fixture import render,expand,render_return,render_caller,expand_caller,render_byte,expand_byte,render_integers,expand_integers,render_branch,expand_branch,expand_second_branch,expand_post_integers,expand_third_branch,expand_fourth_branch,render_mixed,expand_mixed,render_mixed_byte,expand_mixed_byte,render_post_mixed,expand_post_mixed,render_stack_move,expand_stack_move,render_final_integer,expand_final_integer,render_next_entry,expand_next_entry,verify_next_entry_trace,render_report_byte,expand_report_byte
from guarded_continuation import GUARD
from prepare_formatter_nested_fixture import (
    private_compare_checkpoint, _COMPARE_EXPANSION_STAGES,
    public_nested_refusal,
)
from prepare_formatter_report_compare_fixture import (
    promote as promote_report_compare, render as render_report_compare,
)
R=0x80010000;T=0x80020000;L=0x80030000;A=0x80040000;N=0x60000000
class Test(unittest.TestCase):
    def test_private_119_checkpoints_are_fixed_and_redacted(self):
        accepted = (
            'begin', 'base_joined', 'caller_joined', 'callee_joined',
            'byte_joined', 'compare_joined', 'spans_checked',
            'census_checked', 'image_rebuilt', 'header_rendered',
        )
        self.assertEqual(_COMPARE_EXPANSION_STAGES, frozenset(accepted))
        output = StringIO()
        with redirect_stdout(output):
            for stage in accepted:
                private_compare_checkpoint(stage)
        self.assertEqual(output.getvalue().splitlines(), [
            f'FORMATTER_NESTED_119_STAGE stage={stage}' for stage in accepted
        ])
        for illegal in ('0x80010000', 'compare=1234', 'private_input', '', None):
            with self.subTest(illegal=illegal):
                with self.assertRaisesRegex(ValueError, 'diagnostic stage'):
                    private_compare_checkpoint(illegal)

    def test_private_nested_refusal_is_redacted_and_specific(self):
        whitelist={'nested fixture expansion'}
        self.assertEqual(public_nested_refusal(ValueError('prefix ownership'),whitelist),
                         'nested_fixture_span_overlap')
        self.assertEqual(public_nested_refusal(ValueError('nested fixture expansion'),whitelist),
                         'nested_fixture_expansion')
        for error in (ValueError('private address 0x80010000'),
                      TypeError('secret instruction word'),
                      KeyError('unknown address')):
            self.assertEqual(public_nested_refusal(error,whitelist),'private_input')

    def test_header(self):
        c=({},(R,L,R+4,0x80630000,48,A,4),((R,N),),((R,4,A,False,False),),((4,32),),((R,A,b'abcd'),))
        s=render(c)
        self.assertIn('false,false,0x61626364u',s)
        self.assertIn('slots,{0x80040000u,0x00000004u}',s)
    def test_second_header(self):
        rows=tuple((R+4*i,N) for i in range(44))
        c=({},(R,L,R+176,0x80630000,48,A,4),rows,
           ((R,4,T,False,False),(R+140,4,T+4,False,False)),((4,32),),
           ((R,T,b'abcd'),(R+140,T+4,b'1234')))
        s=render(c)
        self.assertIn('IpcDispatchWord,44> path',s)
        self.assertIn('false,false,0x61626364u',s)
        self.assertIn('false,false,0x31323334u',s)
        self.assertIn('slots,{0x80040000u,0x00000004u}',s)
    def test_control_header(self):
        rows=tuple((R+4*i,N) for i in range(76))
        fields=(R,L,R+304,0x4e800420,48,0,0,R+400,N,383*4)
        c=({},fields,rows,(),((4,32),),())
        s=render(c)
        self.assertIn('IpcDispatchWord,76> path',s)
        self.assertIn('slots,{0x00000000u,0x00000000u},{0x80010190u,0x60000000u,0x000005fcu}',s)
        with self.assertRaisesRegex(ValueError,'control contract'):
            render(({},fields[:5]+(A,4)+fields[7:],rows,(),((4,32),),()))
    def test_post_ctr_header(self):
        rows=tuple((R+4*i,N) for i in range(84))
        c=({},(R,L,R+336,0x80610000,48,-20,4),rows,(),((4,32),),())
        s=render(c,stack_boundary=True)
        self.assertIn('namespace formatter_post_ctr_private',s)
        self.assertIn('slots,{0u,4u,true,-20}',s)
        self.assertIn('IpcDispatchWord,84> path',s)
        with self.assertRaisesRegex(ValueError,'stack boundary'):
            render(({},(R,L,R+336,0x80610000,48,0,4),rows,(),((4,32),),()),stack_boundary=True)
    def test_instruction_header(self):
        rows=tuple((R+4*i,N) for i in range(95))
        c=({},(R,L,R+380,N,48,0,0),rows,(),((4,32),),())
        s=render(c,instruction_boundary=True)
        self.assertIn('namespace formatter_partial_private',s)
        self.assertIn('slots,{0u,0u,false,0,true}',s)
        self.assertIn('IpcDispatchWord,95> path',s)
        for kwargs in (dict(stack_boundary=True,instruction_boundary=True),dict(instruction_boundary=True)):
            bad=c if kwargs.get('stack_boundary') else (c[0],c[1][:5]+(-40,4),*c[2:])
            with self.assertRaises(ValueError):render(bad,**kwargs)
    def test_special_header(self):
        rows=tuple((R+4*i,N) for i in range(96))
        c=({},(R,L,R+384,N,48,0,0),rows,(),((4,32),),())
        s=render(c,instruction_boundary=True,special_boundary=True)
        self.assertIn('namespace formatter_special_private',s)
        self.assertIn('IpcDispatchWord,96> path',s)
        self.assertIn('slots,{0u,0u,false,0,true}',s)
        with self.assertRaisesRegex(ValueError,'instruction boundary'):
            render(c,special_boundary=True)
    def test_release_header(self):
        rows=tuple((R+4*i,N) for i in range(97))
        c=({},(R,L,R+388,0x4e800020,48,0,0),rows,(),((4,32),),())
        s=render(c,instruction_boundary=True,release_boundary=True)
        self.assertIn('namespace formatter_release_private',s)
        self.assertIn('IpcDispatchWord,97> path',s)
        self.assertIn('slots,{0u,0u,false,0,true}',s)
        for kwargs in (dict(release_boundary=True),dict(instruction_boundary=True,special_boundary=True,release_boundary=True)):
            with self.assertRaisesRegex(ValueError,'instruction boundary'):render(c,**kwargs)
    def test_return_header(self):
        s=render_return((R,R+4,GUARD,'integer','const'))
        self.assertIn('namespace formatter_return_private',s)
        self.assertIn('caller=0x80010004u,guard=0x44000002u',s)
        for args in ((R,R,GUARD,'integer','const'),(R,R+4,N,'integer','const')):
            with self.assertRaisesRegex(ValueError,'return guard'):render_return(args)
    def test_caller_header_and_expansion(self):
        call=0x48000001|((T-R)&0x03fffffc);load=0x80610010
        info=(R,R+4,load,call)
        self.assertIn('namespace formatter_caller_private',render_caller(info))
        old={R:(call,GUARD),T:(N,GUARD)}
        new={**old,R:(call,load,GUARD)}
        self.assertEqual(expand_caller(old,new,info),new)
        for bad in ({**new,T:(N,N)},{**new,R:(call,load,N)},{**new,R:(N,load,GUARD)}):
            with self.assertRaisesRegex(ValueError,'caller expansion'):expand_caller(old,bad,info)
        with self.assertRaisesRegex(ValueError,'caller geometry'):render_caller((R,R+4,GUARD,call))
    def test_caller_byte_header_and_expansion(self):
        call=0x48000001|((T-R)&0x03fffffc);load=0x88610013
        info=(R,R+4,load,call,19,9,R+8,N)
        self.assertIn('namespace formatter_caller_byte_private',render_byte(info))
        old={R:(call,load,GUARD),T:(N,GUARD)}
        new={**old,R:(call,load,N,GUARD)}
        self.assertEqual(expand_byte(old,new,info),new)
        for bad in ({**new,T:(N,N)},{**new,R:(call,load,N,N)}):
            with self.assertRaisesRegex(ValueError,'caller byte expansion'):expand_byte(old,bad,info)
        with self.assertRaisesRegex(ValueError,'caller byte'):render_byte(info[:4]+(704,9)+info[6:])
    def test_integer_header_and_expansion(self):
        call=0x48000001|((T-R)&0x03fffffc);load=0x88610013;add=0x38830001
        info=(R,R+4,load,call,19,9,R+8,add)
        old={R:(call,load,add,GUARD),T:(N,GUARD)}
        new={**old,R:(call,load,add,N,GUARD)}
        contract=(new,((R+8,add,((3,9),)),),R+12,N)
        header=render_integers(contract)
        self.assertIn('ScCallerIntegerStep,1> path',header)
        self.assertIn('CallerIntegerInput{3u,0x00000009u}',header)
        self.assertEqual(expand_integers(old,contract,info),new)
        for bad in ((new,(),R+12,N),(new,((R+8,add,((3,9),(3,9))),),R+12,N)):
            with self.assertRaisesRegex(ValueError,'caller integers'):render_integers(bad)
        with self.assertRaisesRegex(ValueError,'integer expansion'):
            expand_integers(old,({**new,T:(N,N)},*contract[1:]),info)
    def test_branch_header_and_expansion(self):
        pc=R+8;w=(16<<26)|(12<<21)|16;chosen=pc+4;other=pc+16
        old={R:(N,N,w,GUARD,GUARD,N),T:(N,GUARD)}
        new={**old,R:(N,N,w,N,GUARD,N,GUARD)}
        info=(R,64,pc,w,False,chosen,N,other)
        c=(new,info);integer=(old,(),pc,w)
        self.assertIn('taken=false',render_branch(c))
        self.assertEqual(expand_branch(old,c,integer),new)
        for bad in ((new,info[:4]+(True,)+info[5:]),(new,info[:-1]+(other+4,)),(new,info[:6]+(GUARD,other))):
            with self.assertRaisesRegex(ValueError,'caller branch'):render_branch(bad)
        with self.assertRaisesRegex(ValueError,'branch expansion'):
            expand_branch(old,({**new,T:(N,N)},info),integer)
    def test_integer_preserves_disjoint_labels(self):
        call=0x48000001|((T-R)&0x03fffffc);load=0x88610013;add=0x38830001
        info=(R,R+4,load,call,19,9,R+8,add)
        old={R:(call,load,add,GUARD,GUARD,GUARD,N),T:(N,GUARD)}
        new={**old,R:(call,load,add,N,GUARD,GUARD,N)}
        contract=(new,((R+8,add,((3,9),)),),R+12,N)
        self.assertEqual(expand_integers(old,contract,info),new)
        for i in (3,4):
            bad=list(old[R]);bad[i]=N
            with self.assertRaisesRegex(ValueError,'overlap'):
                expand_integers({**old,R:tuple(bad)},contract,info)
    def test_second_branch_expansion(self):
        pc=R+8;w=(16<<26)|(12<<21)|16;second_pc=pc+4
        second_word=(16<<26)|(12<<21)|(1<<16)|24
        first={R:(N,N,w,second_word,GUARD,N,GUARD),T:(N,GUARD)}
        first_info=(R,64,pc,w,False,second_pc,second_word,pc+16)
        target=second_pc+24
        second={**first,R:first[R]+(GUARD,GUARD,N,GUARD)}
        second_info=(R,64,second_pc,second_word,True,target,N,second_pc+4)
        self.assertIn('formatter_caller_second_branch_private',render_branch((second,second_info),second=True))
        self.assertEqual(expand_second_branch(first,(first,first_info),(second,second_info)),second)
        with self.assertRaisesRegex(ValueError,'second branch'):
            expand_second_branch(first,(first,first_info),(second,second_info[:5]+(pc+16,)+second_info[6:]))
    def test_post_integer_expansion(self):
        pc=R+8;w=(16<<26)|(12<<21)|16;second_pc=pc+4
        second_word=(16<<26)|(12<<21)|(1<<16)|24
        target=second_pc+24;cmp=0x2c030009
        old={R:(N,N,w,second_word,GUARD,N,GUARD,GUARD,GUARD,cmp,GUARD,GUARD,N),T:(N,GUARD)}
        first=(None,(R,64,pc,w,False,second_pc,second_word,pc+16))
        second=(old,(R,64,second_pc,second_word,True,target,cmp,second_pc+4))
        v=list(old[R]);v[10]=N;new={**old,R:tuple(v)}
        contract=(new,((target,cmp,((3,9),)),),target+4,N)
        self.assertIn('formatter_caller_post_integer_private',render_integers(contract,post_branch=True))
        self.assertEqual(expand_post_integers(old,contract,first,second),new)
        bad=(None,first[1][:-1]+(target+4,))
        with self.assertRaisesRegex(ValueError,'guard'):
            expand_post_integers(old,contract,bad,second)
        with self.assertRaisesRegex(ValueError,'expansion'):
            expand_post_integers(old,({**new,T:(N,N)},*contract[1:]),first,second)
    def test_third_branch_expansion(self):
        cmp=0x2c030009;pc=R+40;word=(16<<26)|(12<<21)|20
        old={R:(N,N,N,N,GUARD,N,N,GUARD,GUARD,cmp,word,GUARD),T:(N,GUARD)}
        first=(None,(R,96,R+8,N,False,R+12,N,R+28))
        second=(None,(R,96,R+12,N,True,R+36,cmp,R+16))
        post=(old,((R+36,cmp,((3,9),)),),pc,word)
        v=list(old[R])+[GUARD]*4;v[11]=N;new={**old,R:tuple(v)}
        info=(R,96,pc,word,False,pc+4,N,pc+20)
        contract=(new,info)
        self.assertIn('formatter_caller_third_branch_private',render_branch(contract,third=True))
        self.assertEqual(expand_third_branch(old,first,second,post,contract),new)
        bad=(None,first[1][:-1]+(pc+4,))
        with self.assertRaisesRegex(ValueError,'third branch'):
            expand_third_branch(old,bad,second,post,contract)
    def test_fourth_branch_expansion(self):
        pc=R+44;w=(16<<26)|(12<<21)|24
        old={R:(N,N,N,N,GUARD,N,N,GUARD,GUARD,N,N,w,GUARD,GUARD,GUARD,GUARD),T:(N,GUARD)}
        first=(None,(R,96,R+8,N,False,R+12,N,R+28))
        second=(None,(R,96,R+12,N,True,R+36,N,R+16))
        third=(old,(R,96,R+40,N,False,pc,w,R+60))
        v=list(old[R])+[GUARD]*2;v[12]=N;new={**old,R:tuple(v)}
        info=(R,96,pc,w,False,pc+4,N,pc+24)
        contract=(new,info)
        self.assertIn('formatter_caller_fourth_branch_private',render_branch(contract,fourth=True))
        self.assertEqual(expand_fourth_branch(old,first,second,third,contract),new)
        bad=(None,first[1][:-1]+(pc+4,))
        with self.assertRaisesRegex(ValueError,'fourth branch'):
            expand_fourth_branch(old,bad,second,third,contract)
    def test_mixed_expansion(self):
        pc=R+48;add=0x38830001;branch=(16<<26)|(12<<21)|(2<<16)|16
        old={R:(N,N,N,N,GUARD,N,N,GUARD,GUARD,N,N,N,add,GUARD,GUARD,GUARD,GUARD,GUARD),T:(N,GUARD)}
        first=(None,(R,128,R+8,N,False,R+12,N,R+28))
        second=(None,(R,128,R+12,N,True,R+36,N,R+16))
        third=(None,(R,128,R+40,N,False,R+44,N,R+60))
        fourth=(old,(R,128,R+44,N,False,pc,add,R+68))
        end=pc+20;v=list(old[R])+[GUARD];v[13]=branch;v[17]=N;new={**old,R:tuple(v)}
        # The branch's selected edge must not consume the earlier guard.
        fourth=(old,fourth[1][:-1]+(R+64,))
        contract=(new,((pc,add,((3,9),),pc+4,None,None),(pc+4,branch,(),end,pc+8,True)),end,N)
        self.assertIn('ScCallerMixedStep,2> path',render_mixed(contract))
        self.assertEqual(expand_mixed(old,contract,(first,second,third,fourth)),new)
        bad=(old,fourth[1][:-1]+(end,))
        with self.assertRaisesRegex(ValueError,'overlap'):
            expand_mixed(old,contract,(first,second,third,bad))
        with self.assertRaisesRegex(ValueError,'mixed'):
            render_mixed((new,((pc,add,((3,9),),pc+8,None,None),),pc+8,N))
    def test_mixed_generated_header_compiles(self):
        import shutil,subprocess,tempfile
        from pathlib import Path
        cxx=shutil.which('g++')
        if cxx is None:self.skipTest('g++ not installed')
        pc=R+48;add=0x38830001;branch=(16<<26)|(12<<21)|(2<<16)|16
        end=pc+20
        contract=({},((pc,add,((3,9),),pc+4,None,None),
                      (pc+4,branch,(),end,pc+8,True)),end,N)
        # Entirely synthetic words; compile the actual generated C++ data
        # against the real witness types rather than a duplicated schema.
        source='#include "wii_post_stm_sc_formatter.h"\n'+render_mixed(contract)+'''
using namespace formatter_caller_mixed_private;
static_assert(path.size()==2);
static_assert(path[0].inputs.size()==1 && path[0].inputs[0].reg==3);
static_assert(path[1].inputs.empty() && path[1].taken);
static_assert(path[1].next_pc==end_pc);
int main(){return 0;}
'''
        with tempfile.TemporaryDirectory() as d:
            src=Path(d)/'header.cpp';src.write_text(source)
            result=subprocess.run([cxx,'-std=c++20','-Wall','-Wextra','-Werror','-fsyntax-only','-I',str(Path(__file__).resolve().parent),str(src)],capture_output=True,text=True,timeout=30)
            self.assertEqual(result.returncode,0,result.stderr)
    def test_mixed_byte_expansion(self):
        pc=R+48;w=0x88610013;next_pc=pc+4
        old={R:(N,GUARD,GUARD,GUARD,GUARD,N,GUARD,GUARD,N,N,N,N,w,GUARD,GUARD),T:(N,GUARD)}
        branches=tuple((None,(R,128,R+4,N,False,R+8,N,R+4*i)) for i in (1,2,3,4))
        mixed=(old,((pc-4,N,(),pc,None,None),),pc,w)
        body=list(old[R]);body[13]=N;new={**old,R:tuple(body)}
        info=(R,pc,w,19,0xa5,next_pc,N);contract=(new,info)
        self.assertIn('formatter_caller_mixed_byte_private',render_mixed_byte(contract))
        self.assertEqual(expand_mixed_byte(old,mixed,contract,branches),new)
        bad=(branches[0],branches[1],branches[2],(None,branches[3][1][:-1]+(next_pc,)))
        with self.assertRaisesRegex(ValueError,'overlap'):expand_mixed_byte(old,mixed,contract,bad)
        with self.assertRaisesRegex(ValueError,'expansion'):expand_mixed_byte(old,mixed,({**new,T:(N,N)},info),branches)
        with self.assertRaisesRegex(ValueError,'mixed byte'):render_mixed_byte((new,(R,pc,w|0x04000000,19,0xa5,next_pc,N)))
    def test_post_mixed_expansion(self):
        pc=R+48;load=0x88610013;compare=0x2c030009;branch=(16<<26)|(12<<21)|(2<<16)|16
        old={R:(N,GUARD,GUARD,GUARD,GUARD,N,GUARD,GUARD,N,N,N,N,load,compare,GUARD),T:(N,GUARD)}
        branches=tuple((None,(R,128,R+4,N,False,R+8,N,R+4*i)) for i in (1,2,3,4))
        mixed=({},((pc-4,N,(),pc,R+24,True),),pc,load)
        byte=(old,(R,pc,load,19,9,pc+4,compare))
        end=pc+24;body=list(old[R])+[GUARD]*5;body[14]=branch;body[18]=N
        new={**old,R:tuple(body)}
        post=(new,((pc+4,compare,((3,9),),pc+8,None,None),
                   (pc+8,branch,(),end,pc+12,True)),end,N)
        self.assertIn('formatter_caller_post_mixed_private',render_post_mixed(post))
        self.assertEqual(expand_post_mixed(old,byte,mixed,post,branches),new)
        bad=(branches[0],branches[1],branches[2],(None,branches[3][1][:-1]+(end,)))
        with self.assertRaisesRegex(ValueError,'overlap'):expand_post_mixed(old,byte,mixed,post,bad)
        with self.assertRaisesRegex(ValueError,'expansion'):expand_post_mixed(old,byte,mixed,({**new,T:(N,N)},*post[1:]),branches)
        with self.assertRaisesRegex(ValueError,'post mixed'):expand_post_mixed(old,byte,({},mixed[1],pc+4,load),post,branches)
    def test_stack_move_expansion(self):
        pc=R+48;w=(31<<26)|(1<<21)|(7<<16)|(1<<11)|(444<<1)
        old={R:(N,GUARD,GUARD,GUARD,GUARD,N,GUARD,GUARD,N,N,N,N,w,GUARD,GUARD),T:(N,GUARD)}
        branches=tuple((None,(R,128,R+4,N,False,R+8,N,R+4*i)) for i in (1,2,3,4))
        mixed=({},((pc-8,N,(),pc-4,R+24,True),),pc-4,N)
        post=(old,((pc-4,N,(),pc,R+28,True),),pc,w)
        body=list(old[R]);body[13]=N;new={**old,R:tuple(body)}
        info=(R,128,pc,w,864,pc+4,N);contract=(new,info)
        self.assertIn('formatter_caller_stack_move_private',render_stack_move(contract))
        self.assertEqual(expand_stack_move(old,post,mixed,contract,branches),new)
        bad=(branches[0],branches[1],branches[2],(None,branches[3][1][:-1]+(pc+4,)))
        with self.assertRaisesRegex(ValueError,'overlap'):expand_stack_move(old,post,mixed,contract,bad)
        with self.assertRaisesRegex(ValueError,'expansion'):expand_stack_move(old,post,mixed,({**new,T:(N,N)},info),branches)
        with self.assertRaisesRegex(ValueError,'stack move'):render_stack_move((new,(R,128,pc,w|1,864,pc+4,N)))
    def test_final_integer_expansion(self):
        pc=R+48;w=(14<<26)|(8<<21)|(6<<16)|3
        bl=(18<<26)|((R-0x100-(pc+4))&0x03fffffc)|1
        old={R:(N,GUARD,GUARD,GUARD,GUARD,N,GUARD,GUARD,N,N,N,N,w,GUARD,GUARD),T:(N,GUARD)}
        branches=tuple((None,(R,128,R+4,N,False,R+8,N,R+4*i)) for i in (1,2,3,4))
        mixed=({},((pc-12,N,(),pc-8,R+24,True),),pc-8,N)
        post=({},((pc-8,N,(),pc-4,R+28,True),),pc-4,N)
        move=(old,(R,128,pc-4,N,864,pc,w))
        body=list(old[R]);body[13]=bl;new={**old,R:tuple(body)}
        contract=(new,((pc,w,((6,9),),pc+4,None,None),),pc+4,bl)
        self.assertIn('formatter_caller_final_integer_private',render_final_integer(contract))
        self.assertEqual(expand_final_integer(old,move,mixed,post,contract,branches),new)
        bad=(branches[0],branches[1],branches[2],(None,branches[3][1][:-1]+(pc+4,)))
        with self.assertRaisesRegex(ValueError,'overlap'):expand_final_integer(old,move,mixed,post,contract,bad)
        with self.assertRaisesRegex(ValueError,'final integer'):render_final_integer((*contract[:3],bl^1))
        with self.assertRaisesRegex(ValueError,'expansion'):expand_final_integer(old,move,mixed,post,({**new,T:(N,N)},*contract[1:]),branches)
    def test_next_entry_expansion(self):
        pc=R+48;dst=R-0x100;w=(18<<26)|((dst-pc)&0x03fffffc)|1;entry=0x88630000
        old={R:(N,)*12+(w,GUARD),T:(N,GUARD)}
        final=(old,((pc-4,N,(),pc,None,None),),pc,w)
        new={**old,dst:(entry,GUARD)};info=(R,128,pc,w,dst,entry,pc+4)
        self.assertIn('formatter_caller_next_entry_private',render_next_entry((new,info)))
        self.assertEqual(expand_next_entry(old,final,(new,info)),new)
        with self.assertRaisesRegex(ValueError,'expansion'):expand_next_entry(old,final,({**new,dst:(entry,N)},info))
        with self.assertRaisesRegex(ValueError,'expansion'):expand_next_entry(old,final,({**new,T:(N,N)},info))
        with self.assertRaisesRegex(ValueError,'next entry'):render_next_entry((new,(*info[:4],dst+4,entry,pc+4)))
    def test_report_byte_expansion(self):
        pc=R+48;dst=R-0x100
        w=(18<<26)|((dst-pc)&0x03fffffc)|1;load=0x88630000
        after=0x38630001
        old={R:(N,)*12+(w,GUARD),T:(N,GUARD),dst:(load,GUARD)}
        entry=(old,(R,128,pc,w,dst,load,pc+4))
        new={**old,dst:(load,after,GUARD)}
        info=(dst,load,753,17,0xa5,dst+4,after,pc+4)
        contract=(new,info)
        header=render_report_byte(entry,contract)
        self.assertIn('formatter_caller_report_byte_private',header)
        self.assertIn('parent_offset=753;',header)
        self.assertIn('report_offset=17u;',header)
        self.assertEqual(expand_report_byte(old,entry,contract),new)
        for blocks in ({**new,R:(N,)*14},{**new,T:(N,N)},
                       {**new,dst:(load,after,N)},old,{**new,L:(N,)}):
            with self.assertRaisesRegex(ValueError,'report byte expansion'):
                expand_report_byte(old,entry,(blocks,info))
        for index,value in ((0,dst+4),(1,load^1),(2,752),(3,7),
                            (4,256),(5,dst+8),(6,GUARD),(7,pc+8)):
            bad=list(info);bad[index]=value
            with self.assertRaisesRegex(ValueError,'report byte'):
                render_report_byte(entry,(new,tuple(bad)))
    def test_report_compare_stays_within_existing_callee_root(self):
        # The 119th operation must extend the verified 118 callee, not
        # introduce a second synthetic function or overwrite its caller.
        pc=R+48
        dst=R-0x100
        branch=(18<<26)|((dst-pc)&0x03fffffc)|1
        byte_load=(34<<26)|(9<<21)|(3<<16)
        comparison=(11<<26)|(2<<23)|(7<<16)|0x8000
        following=N
        original={R:(N,)*12+(branch,GUARD),T:(N,GUARD),dst:(byte_load,GUARD)}
        entry=(original,(R,128,pc,branch,dst,byte_load,pc+4))
        byte_blocks={**original,dst:(byte_load,comparison,GUARD)}
        byte=(byte_blocks,(dst,byte_load,753,17,0xa5,dst+4,comparison,pc+4))
        self.assertEqual(expand_report_byte(original,entry,byte),byte_blocks)
        extended,fields=promote_report_compare(byte,following,(7,0x81234567))
        self.assertEqual(set(extended),set(original))
        self.assertEqual(len(extended),3)
        self.assertEqual(extended[R],original[R])
        self.assertEqual(extended[T],original[T])
        self.assertEqual(extended[dst],
                         (byte_load,comparison,following,GUARD))
        self.assertEqual(fields[2:6],(dst+8,following,7,0x81234567))
        self.assertIn('source_value=0x81234567u',
                      render_report_compare((extended,fields)))
        self.assertEqual(byte_blocks[dst],(byte_load,comparison,GUARD))
        for bad in ((32,0),(7,0x100000000),('7',0)):
            with self.subTest(source=bad):
                with self.assertRaisesRegex(ValueError,'source provenance'):
                    promote_report_compare(byte,following,bad)
        with self.assertRaisesRegex(ValueError,'input identity'):
            promote_report_compare(byte,following,(9,0xa5))
        with self.assertRaisesRegex(ValueError,'successor'):
            promote_report_compare(byte,GUARD,(7,0x81234567))

    def test_next_entry_trace(self):
        dst=R-0x100
        trace=f'    if (nwii::runtime::g_trace_calls && ctx.pc == 0x{dst:X}) nwii::runtime::trace_call(0x{dst:X}, ctx);'
        label=f'loc_{dst:08X}: ;'
        verify_next_entry_trace(trace+'\n'+label,dst)
        for bad in (label,trace+'\n'+trace+'\n'+label,label+'\n'+trace,trace+'\n'+label+'\n'+label):
            with self.assertRaisesRegex(ValueError,'trace'):verify_next_entry_trace(bad,dst)
    def test_expand(self):
        old={R:(N,GUARD),T:(N,)};new={**old,R:(N,N,GUARD)}
        self.assertEqual(expand(old,new,old,R),new)
        for blocks in ({**new,T:(GUARD,)},{**new,L:(N,)},old):
            with self.assertRaises(ValueError):expand(old,blocks,old,R)
        with self.assertRaises(ValueError):expand(old,new,{**old,R:(GUARD,)},R)
    def test_missing_const_read(self):
        c=({},(R,L,R+4,0x80630000,48,A,4),((R,N),),((R,4,A,False,False),),((4,32),),())
        with self.assertRaisesRegex(ValueError,'data contract'):render(c)
    def test_stack_read_not_a_file_constant(self):
        c=({},(R,L,R+4,0x80630000,48,A,4),((R,N),),((R,4,-8,True,False),),((4,32),),())
        self.assertIn('true,false}',render(c))
if __name__=='__main__':unittest.main(verbosity=2)
