#!/usr/bin/env python3
import unittest
from prepare_formatter_nested_fixture import render,expand,render_return,render_caller,expand_caller,render_byte,expand_byte,render_integers,expand_integers,render_branch,expand_branch,expand_second_branch,expand_post_integers,expand_third_branch,expand_fourth_branch,render_mixed,expand_mixed
from guarded_continuation import GUARD
R=0x80010000;T=0x80020000;L=0x80030000;A=0x80040000;N=0x60000000
class Test(unittest.TestCase):
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
