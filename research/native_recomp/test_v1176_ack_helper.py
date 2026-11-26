import unittest,tempfile
from pathlib import Path
from unittest.mock import patch
import prepare_v1176_ack_helper as ins
from prepare_v1169_third_ack import render as render_ack
from prepare_v1097_after_alarm import SI
from test_v997_composed_success_frontier import first,second,transfer,discovery,sampling,HOST
H=0x80004000;W=0x60000000;BLR=0x4e800020;MSR=0x7c600124
T='    ++ctx.inst_count;\n'
class AckHelperTree(unittest.TestCase):
    def geometry(self):
        h,s,c,n,d,t,r=[H+i*0x100 for i in range(7)]
        spans=[(h,h+16,0),(s,s+8,1),(c,c+20,0),(n,n+16,0),(d,d+8,0),(t,t+8,0),(r,r+8,0)]
        edges=[(h,s),(h+4,c),(c,n),(h+12,n),(n,d),(n+4,t),(n+8,r),(c+8,n)]
        def link(a,b):return 0x48000001|((b-a)&0x03fffffc)
        rows=[(a,link(a,b),next(x for x,y,_ in spans if x<=a<y),False) for a,b in edges]
        rows.extend((pc,w,a,False) for pc,w,a in ((h+8,W,h),(s,W,s),(s+4,BLR,s),(c+4,W,c),
            (c+12,W,c),(c+16,BLR,c),(n+12,BLR,n),(d,MSR,d),(d+4,BLR,d),(t,W,t),(t+4,BLR,t),(r,MSR,r),(r+4,BLR,r)))
        msr=[(d,MSR),(r,MSR)];expected=(h+8,W)
        old_spans=spans[:3];old_edges=edges[:2]
        old_rows=[(pc,w,a,g or pc in (c,h+12,c+8)) for pc,w,a,g in rows if a in (h,s,c)]
        return old_spans,old_edges,old_rows,spans,edges,rows,msr,expected
    def fixture(self,root):
        os,oe,orr,spans,edges,rows,msr,expected=self.geometry()
        ins.compatible(os,oe,orr,spans,edges,rows,msr,expected)
        ack=render_ack(os,oe,orr)
        prior='inline constexpr uint32_t context=0x80009000u;\ninline constexpr unsigned shared_edges=8u;\n'
        dest=root/'nWiiRuntime/include/undercover';dest.mkdir(parents=True)
        for n in ('wii_second_ack_live_v958.h','wii_held_pending_epilogue_v1149.h','wii_third_pending_reentry_v1067.h',
                  'wii_second_completion_ack_v950.h','wii_bounded_ack_call_route_v956.h'):
            (dest/n).write_bytes((HOST/n).read_bytes())
        (dest/'v1167_private_third_ack.h').write_text(ack)
        (dest/'v958_private_second_ack.h').write_text('#define UNDERCOVER_V1167_PRIVATE_THIRD_ACK 1\n'+prior)
        (dest/'wii_si_binding_v512.h').write_text(second(transfer(first(discovery(sampling((HOST/'wii_si_binding_v512.h').read_text()))))))
        for i,(a,_,_) in enumerate(spans):
            body='#include "runtime/cpu_context.h"\n'+f'void fn_{a:X}(CPUContext& ctx) {{\n    if (nwii::runtime::g_trace_calls && ctx.pc == 0x{a:X}) nwii::runtime::trace_call(0x{a:X}, ctx);\n'
            for pc,w,owner,g in sorted(rows):
                if owner!=a:continue
                body+=f'loc_{pc:X}: ;\n    // 0x{pc:08X}: {w:08X}\n'+T+SI
                body+=f'    undercover::wii::v958::before(ctx,0x{pc:08x}u,0x{w:08x}u,{str(g).lower()});\n'
                for call,dst in edges:
                    if pc==call:body+=f'    ctx.pc = 0x{dst:X}; fn_{dst:X}(ctx);\n    if (ctx.pc != 0x{pc+4:X}) return;\n'
            (root/f'output_{i}.cpp').write_text(body+'}\n')
        for i in range(7,20):(root/f'output_{i}.cpp').write_text('// unused\n')
        (root/'main_output.cpp').write_text(''.join(f'case 0x{a:X}: fn_{a:X}(ctx); break;\n' for a,_,_ in spans))
        return (spans,edges,rows,msr,expected,ack,prior),dest
    @staticmethod
    def snapshot(root):return {str(p.relative_to(root)):p.read_bytes() for p in root.rglob('*') if p.is_file()}
    def run_install(self,root,data):
        with patch.object(ins,'metadata',return_value=data[0]):ins.install(b'',b'',root,HOST)
    def test_complete(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);data=self.fixture(root);before=self.snapshot(root)
            self.run_install(root,data);after=self.snapshot(root)
            self.assertEqual(len(set(after)-set(before)),1)
            self.assertEqual({p for p in before if before[p]!=after[p]},
                {'nWiiRuntime/include/undercover/v958_private_second_ack.h'})
            self.assertEqual((data[1]/'v1175_private_ack_helper.h').read_text(),ins.render(*data[0][:5]))
            self.assertIn('130u,6u,6u,2u}',(data[1]/'v1175_private_ack_helper.h').read_text())
    def test_refusals(self):
        for fault in ('metadata','header','bus','duplicate','mapping','direct','tick','admitted-guard','mode','existing'):
            with self.subTest(fault=fault),tempfile.TemporaryDirectory() as td:
                root=Path(td);data=self.fixture(root);dest=data[1]
                if fault=='metadata':
                    q=dest/'v958_private_second_ack.h';q.write_text(q.read_text().replace('shared_edges=8u','shared_edges=7u'))
                elif fault=='header':
                    q=dest/'v1167_private_third_ack.h';q.write_text(q.read_text()+'// changed\n')
                elif fault=='bus':
                    q=dest/'wii_si_binding_v512.h';q.write_text(q.read_text().replace('held_epilogue.ack_write','wrong'))
                elif fault=='duplicate':(root/'output_19.cpp').write_bytes((root/'output_4.cpp').read_bytes())
                elif fault=='mapping':
                    q=root/'main_output.cpp';q.write_text('\n'.join(q.read_text().splitlines()[:-1]))
                elif fault=='direct':
                    q=root/'output_3.cpp';q.write_text(q.read_text().replace('ctx.pc =','ctx.fake_pc =',1))
                elif fault=='tick':
                    q=root/'output_1.cpp';q.write_text(q.read_text().replace(T,T+T,1))
                elif fault=='admitted-guard':
                    q=root/'output_6.cpp';q.write_text(q.read_text().replace('false);','true);',1))
                elif fault=='mode':(dest/'v958_private_second_ack.h').write_text('// absent\n')
                else:(dest/'v1175_private_ack_helper.h').write_text('// exists\n')
                before=self.snapshot(root)
                with self.assertRaises(ValueError):self.run_install(root,data)
                self.assertEqual(self.snapshot(root),before)
    def test_geometry_refusals(self):
        args=self.geometry()
        ins.compatible(*args)
        for i,bad in ((0,args[0][:-1]),(1,args[1][:-1]),(2,args[2]+[(0x80000000,W,H,False)]),
                      (3,args[3][:-1]),(4,args[4][:-1]),(5,args[5]+[args[5][0]]),
                      (6,[(a,w^1) for a,w in args[6]]),(7,(args[7][0]+4,W))):
            vals=list(args);vals[i]=bad
            with self.subTest(i=i),self.assertRaises(ValueError):ins.compatible(*vals)
if __name__=='__main__':unittest.main()
