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
class AckCallbackMetadata(unittest.TestCase):
    def test_metadata(self):
        h=ins.HANDLER;site=h+12;target=H+0x800
        words=[W]*172;sites=(site,h+16);spans=[(h,h+20,0)]
        rows=[(site,0x4e800421,h,True)]
        old='\n'.join(('#define UNDERCOVER_V995_PRIVATE_SUCCESS_FRONTIER 1',
            f'inline constexpr uint32_t transfer_call=0x{h:08x}u,transfer_branch=0x48000101u,transfer_callback=0x{target:08x}u;',
            'inline constexpr std::array<uint32_t,172> success_callback_words{'+ins.fmt(words)+'};',
            'inline constexpr std::array<uint32_t,2> success_callback_sites{'+ins.fmt(sites)+'};'))
        with patch.object(ins,'callback_expectations',return_value=(target,words,sites)),patch.object(ins,'exact',return_value=[W]*5),patch.object(ins,'handler_edge',return_value=(h,target,0x48000101)):
            self.assertEqual(ins.verify_callback_metadata(b'',b'',spans,rows,old),site)
            for bad in (old.replace('172','171'),old+'\n'+old,old.replace('0x48000101','0x48000100'),old.replace('0x60000000','0x60000001'),old.replace('SUCCESS_FRONTIER 1','SUCCESS_FRONTIER 0')):
                with self.assertRaises(ValueError):ins.verify_callback_metadata(b'',b'',spans,rows,bad)
            for bad in ([],rows+rows,[(site,0x4e800421,h,False)],[(site,0x4e800421,h+4,True)]):
                with self.assertRaises(ValueError):ins.verify_callback_metadata(b'',b'',spans,bad,old)
    def test_guard(self):
        pc=ins.HANDLER+12
        guard=f'    undercover::wii::v958::before(ctx,0x{pc:08x}u,0x4e800421u,true);\n'
        with patch.object(ins,'block_at',return_value=guard):self.assertTrue(ins.verify_callback_guard('',pc))
        inherited=ins.inherited_hooks(pc,0x4e800421)[guard]
        with patch.object(ins,'block_at',return_value=inherited):self.assertFalse(ins.verify_callback_guard('',pc))
        for bad in (guard.replace('true','false'),guard+guard,'',inherited+guard,inherited.replace(ins.ACTIVE,'unrelated()')):
            with patch.object(ins,'block_at',return_value=bad),self.assertRaises(ValueError):ins.verify_callback_guard('',pc)
class AckPrefixMetadata(unittest.TestCase):
    def test_metadata(self):
        C=H+0x1000;S=H+0x2000;site=C+16
        prefix=[W]*6;save=[W]*6+[BLR];words=prefix+[W]*166;sites=(H,H+4)
        plan=({C:prefix+[BLR],S:save},C,S,site,11,-24)
        old='#define UNDERCOVER_V1095_PRIVATE_AFTER_ALARM 1\n'
        old+=f'inline constexpr uint32_t third_postalarm_save_root=0x{S:08x}u;\n'
        for name,ws in (('third_postalarm_prefix',prefix),('third_postalarm_save',save),
                        ('third_postalarm_words',words),('third_postalarm_sites',sites)):
            old+=f'inline constexpr std::array<uint32_t,{len(ws)}> {name}{{'+ins.fmt(ws)+'};\n'
        with patch.object(ins,'prefix_plan',return_value=plan),patch.object(ins,'callback_expectations',return_value=(C,words,sites)):
            self.assertEqual(ins.verify_prefix_metadata(b'',b'',old),(C,S,site,prefix,save))
            for bad in (old+old,old.replace('AFTER_ALARM 1','AFTER_ALARM 0'),old.replace('0x60000000','0x60000001'),old.replace('third_postalarm_save_root','wrong')):
                with self.assertRaises(ValueError):ins.verify_prefix_metadata(b'',b'',bad)
    def test_requires_callback(self):
        with self.assertRaisesRegex(ValueError,'ACK prefix mode'):
            ins.install(b'',b'',Path('.'),Path('.'),False,True)
class AckTimeMetadata(unittest.TestCase):
    def test_metadata(self):
        C=H+0x1000;S=C+0x100;T=C+0x200;D=T+0x100;U=T+0x200;R=T+0x300
        site=C+16;resume=site+4;ts=resume+44
        prefix=[W]*6;save=[W]*6+[BLR];code=[W]*18
        roots={C:code+[BLR],S:save,T:[W]*25,D:[BLR],U:[BLR],R:[BLR]}
        leaves=[(T+4,D,D+4,W,1,[BLR]),(T+16,U,U+4,W,2,[BLR]),(T+28,R,R+4,W,3,[BLR])]
        plan=((roots,C,S,site,11,-24),T,D,U,R,ts,leaves)
        old='#define UNDERCOVER_V1103_PRIVATE_POSTALARM_TIME 1\n'
        with tempfile.TemporaryDirectory() as td:
            dest=Path(td)
            (dest/'v813_private_callback_time.h').write_text(ins.time_render(C,ts,code[5:],T,roots[T],leaves))
            for n in ('wii_callback_time_v810.h','wii_postack_os_leaf_v703.h'):
                (dest/n).write_bytes((HOST/n).read_bytes())
            prior=(C,S,site,prefix,save)
            with patch.object(ins,'callback_time_plan',return_value=plan),patch.object(ins,'exact',return_value=code+[W]*154):
                meta=ins.verify_time_metadata(b'',b'',old,dest,HOST,prior)
                self.assertEqual(meta,(roots,C,T,D,U,R,resume,ts,leaves))
                for bad in (old+old,old.replace('TIME 1','TIME 0'),old+'#define UNDERCOVER_V1189_PRIVATE_ACK_TIME 1\n'):
                    with self.assertRaises(ValueError):ins.verify_time_metadata(b'',b'',bad,dest,HOST,prior)
                with self.assertRaisesRegex(ValueError,'predecessor'):
                    ins.verify_time_metadata(b'',b'',old,dest,HOST,(C,S,site+4,prefix,save))
                h=dest/'v813_private_callback_time.h';h.write_text(h.read_text()+'// changed\n')
                with self.assertRaisesRegex(ValueError,'metadata'):ins.verify_time_metadata(b'',b'',old,dest,HOST,prior)
    def test_requires_prefix(self):
        with self.assertRaisesRegex(ValueError,'ACK time mode'):
            ins.install(b'',b'',Path('.'),Path('.'),True,False,True)
if __name__=='__main__':unittest.main()
