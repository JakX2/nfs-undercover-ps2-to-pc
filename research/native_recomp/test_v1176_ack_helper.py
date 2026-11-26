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
class AckFrontierMetadata(unittest.TestCase):
    def test_metadata(self):
        C=H+0x1000;S=C+0x400;T=C+0x500;D=T+0x100;U=T+0x200;R=T+0x300
        site=C+16;ts=C+64;resume=ts+4;A=C+0x1000;B=A+0x100
        words=[W]*172;seen=[resume+4*i for i in range(27)]
        stops={seen[5]:(3,A),seen[-1]:(5,B)}
        roots={C:words,S:[BLR],T:[W]*25,D:[BLR],U:[BLR],R:[BLR]}
        leaves=[(T+4,D,D+4,W,1,[BLR]),(T+16,U,U+4,W,2,[BLR]),(T+28,R,R+4,W,3,[BLR])]
        q=((roots,C,S,site,11,-24),T,D,U,R,ts,leaves)
        prior=(roots,C,T,D,U,R,site+4,ts,leaves)
        old='#define UNDERCOVER_V1111_PRIVATE_POSTALARM_FRONTIER 1\n'
        rows={pc:(C,W) for pc in seen}
        with tempfile.TemporaryDirectory() as td:
            dest=Path(td);h=dest/'v831_private_callback_frontier.h'
            h.write_text(ins.frontier_render(C,resume,rows,stops))
            n='wii_callback_frontier_v829.h';(dest/n).write_bytes((HOST/n).read_bytes())
            with patch.object(ins,'callback_frontier_plan',return_value=(q,seen,stops,A,B)),patch.object(ins,'exact',return_value=words),patch.object(ins,'callback_expectations',return_value=(C,words,(H,H+4))):
                self.assertEqual(ins.verify_frontier_metadata(b'',b'',old,dest,HOST,prior),(C,rows,stops))
                for bad in (old+old,old.replace('FRONTIER 1','FRONTIER 0'),old+'#define UNDERCOVER_V1193_PRIVATE_ACK_FRONTIER 1\n'):
                    with self.assertRaises(ValueError):ins.verify_frontier_metadata(b'',b'',bad,dest,HOST,prior)
                with self.assertRaisesRegex(ValueError,'predecessor'):
                    ins.verify_frontier_metadata(b'',b'',old,dest,HOST,(roots,C,T,D,U,R,site+4,ts+4,leaves))
                h.write_text(h.read_text()+'// changed\n')
                with self.assertRaisesRegex(ValueError,'metadata'):ins.verify_frontier_metadata(b'',b'',old,dest,HOST,prior)
    def test_requires_time(self):
        with self.assertRaisesRegex(ValueError,'ACK frontier mode'):
            ins.install(b'',b'',Path('.'),Path('.'),True,True,False,True)
class AckWirelessMetadata(unittest.TestCase):
    def test_metadata(self):
        C=H+0x1000;T=C+0x400;D=ins.DISABLE;R=ins.RESTORE;TB=C+0x600
        A=C+0x1000;B=A+0x100;U=B+0x100;L=U+0x400
        original=[W]*172;stops={C+64:(3,A),C+100:(5,B)}
        rows={pc:(C,W) for pc in stops}
        roots={A:[W]*39,B:[W]*30,U:[W]*184,D:[W]*5,R:[W]*9}
        order=(A,B,U,D,R);edges=[(pc,W,W,o) for pc,(o,_) in sorted(stops.items())]
        prior=({D:roots[D],R:roots[R]},C,T,D,TB,R,C+20,C+60,[])
        old='#define UNDERCOVER_V1118_PRIVATE_POSTALARM_WIRELESS 1\n'
        with tempfile.TemporaryDirectory() as td:
            dest=Path(td);h=dest/'v847_private_wireless_wrapper.h'
            h.write_text(ins.wireless_render(roots,order,edges,L,W))
            n='wii_wireless_wrapper_v844.h';(dest/n).write_bytes((HOST/n).read_bytes())
            with patch.object(ins,'wireless_plan',return_value=(roots,A,B,U,L,[])),patch.object(ins,'exact',side_effect=lambda d,e,a,n:original if n==172 else [W]):
                self.assertEqual(ins.verify_wireless_metadata(b'',b'',old,dest,HOST,prior,(C,rows,stops)),(roots,order,L,W,C,original,stops))
                for bad in (old+old,old.replace('WIRELESS 1','WIRELESS 0'),old+'#define UNDERCOVER_V1197_PRIVATE_ACK_WIRELESS 1\n'):
                    with self.assertRaises(ValueError):ins.verify_wireless_metadata(b'',b'',bad,dest,HOST,prior,(C,rows,stops))
                with self.assertRaisesRegex(ValueError,'predecessor'):
                    ins.verify_wireless_metadata(b'',b'',old,dest,HOST,prior,(C+4,rows,stops))
                h.write_text(h.read_text()+'// changed\n')
                with self.assertRaisesRegex(ValueError,'metadata'):ins.verify_wireless_metadata(b'',b'',old,dest,HOST,prior,(C,rows,stops))
    def test_requires_frontier(self):
        with self.assertRaisesRegex(ValueError,'ACK wireless mode'):
            ins.install(b'',b'',Path('.'),Path('.'),True,True,True,False,True)
class AckSuffixMetadata(unittest.TestCase):
    def test_metadata(self):
        C=H+0x1000;resume=C+64;A=C+0x1000;B=A+0x100
        original=[W]*172;frontier={resume-4:(3,A),resume+100:(5,B)}
        seen=[resume+4*i for i in range(21)]
        stops={seen[4]:(4,2,None),seen[-1]:(13,1,B)}
        rows={pc:W for pc in seen};prior=({},(),0,W,C,original,frontier)
        old='#define UNDERCOVER_V1123_PRIVATE_POSTALARM_SUFFIX 1\n'
        with tempfile.TemporaryDirectory() as td:
            dest=Path(td);h=dest/'v1123_private_postalarm_suffix.h'
            h.write_text(ins.suffix_render(C,resume,rows,stops))
            n='wii_callback_suffix_v841.h';(dest/n).write_bytes((HOST/n).read_bytes())
            with patch.object(ins,'suffix_plan',return_value=(None,C,resume,seen,stops)):
                self.assertEqual(ins.verify_suffix_metadata(b'',b'',old,dest,HOST,prior),(C,rows,stops))
                for bad in (old+old,old.replace('SUFFIX 1','SUFFIX 0'),old+'#define UNDERCOVER_V1201_PRIVATE_ACK_SUFFIX 1\n'):
                    with self.assertRaises(ValueError):ins.verify_suffix_metadata(b'',b'',bad,dest,HOST,prior)
                with self.assertRaisesRegex(ValueError,'predecessor'):
                    ins.verify_suffix_metadata(b'',b'',old,dest,HOST,({},(),0,W,C+4,original,frontier))
                h.write_text(h.read_text()+'// changed\n')
                with self.assertRaisesRegex(ValueError,'metadata'):ins.verify_suffix_metadata(b'',b'',old,dest,HOST,prior)
    def test_requires_wireless(self):
        with self.assertRaisesRegex(ValueError,'ACK suffix mode'):
            ins.install(b'',b'',Path('.'),Path('.'),True,True,True,True,False,True)
class AckReturnMetadata(unittest.TestCase):
    def test_metadata(self):
        C=H+0x1000;call=C+144;R=C+0x1000;site=H+12;caller=site+4
        resume=C+64;words=[W]*172;rows={resume:W,call:W};stops={call:(13,1,R)}
        restore=[W]*6+[BLR];tail=[W]*3+[BLR];callers=[(site,0x4e800421,6,W)]
        derive=(C,resume,rows,stops,words,call,R,caller,restore,tail,W,callers)
        old='#define UNDERCOVER_V1132_PRIVATE_POSTALARM_RETURN 1\n'
        with tempfile.TemporaryDirectory() as td:
            dest=Path(td);h=dest/'v1132_private_postalarm_return.h'
            h.write_text(ins.return_render(call,R,caller,restore,tail,W))
            n='wii_callback_return_v846.h';(dest/n).write_bytes((HOST/n).read_bytes())
            with patch.object(ins,'return_derive',return_value=derive):
                self.assertEqual(ins.verify_return_metadata(b'',b'',old,dest,HOST,(C,rows,stops),site),(C,call,R,caller,restore,tail,W,W))
                for bad in (old+old,old.replace('RETURN 1','RETURN 0'),old+'#define UNDERCOVER_V1205_PRIVATE_ACK_RETURN 1\n'):
                    with self.assertRaises(ValueError):ins.verify_return_metadata(b'',b'',bad,dest,HOST,(C,rows,stops),site)
                with self.assertRaisesRegex(ValueError,'predecessor'):
                    ins.verify_return_metadata(b'',b'',old,dest,HOST,(C,rows,stops),site+4)
                h.write_text(h.read_text()+'// changed\n')
                with self.assertRaisesRegex(ValueError,'metadata'):ins.verify_return_metadata(b'',b'',old,dest,HOST,(C,rows,stops),site)
    def test_dispatch_hook(self):
        pc=H+16
        hook=f'    undercover::wii::v958::postalarm_dispatch_resume(ctx,0x{pc:08x}u,0x{W:08x}u);\n'
        label=f'loc_{pc:X}: ;\n    // 0x{pc:08X}: {W:08X}\n'
        ins.verify_return_dispatch_hook(label+hook+T+SI,pc,W)
        for fault in (T+hook+SI,hook+hook+T+SI,hook+'    ctx.inst_count+=1;\n'+T+SI,
                      hook.replace('0x60000000u','0x60000001u')+T+SI,
                      '    if(false) '+hook.lstrip()+T+SI,hook+T+T+SI,T+SI):
            with self.subTest(fault=fault),self.assertRaisesRegex(ValueError,'ACK return dispatch'):
                ins.verify_return_dispatch_hook(label+fault,pc,W)
    def test_requires_suffix(self):
        with self.assertRaisesRegex(ValueError,'ACK return mode'):
            ins.install(b'',b'',Path('.'),Path('.'),True,True,True,True,True,False,True)
class AckHandlerMetadata(unittest.TestCase):
    def test_metadata(self):
        caller=H+16;rd=caller+20;wr=caller+36
        rows={caller+4*i:(W,0,0) for i in range(52)}
        rows[rd]=(0x80830038,0,0);rows[wr]=(0x90830038,0,0)
        for i,o in zip((49,50,51),(7,8,12)):rows[caller+4*i]=(0x48000001,o,1)
        census={pc:(o,k) for pc,(_,o,k) in rows.items() if k}
        index=(caller,[W]*14,(H+0x400,H+0x404,H+0x408,H+0x40c),20,caller+64)
        prior=(H+0x1000,H+0x1040,H+0x2000,caller,[],[],W,W)
        old='#define UNDERCOVER_V1139_PRIVATE_POSTALARM_HANDLER 1\n'
        with tempfile.TemporaryDirectory() as td:
            dest=Path(td);h=dest/'v1139_private_postalarm_handler.h'
            h.write_text(ins.handler_render(rows,rd,wr,index))
            for n in ('wii_handler_suffix_guard_v868.h','wii_handler_index_branch_v911.h'):
                (dest/n).write_bytes((HOST/n).read_bytes())
            with patch.object(ins,'handler_derive',return_value=([],[caller-4,caller+4],[rows,{}],rd,wr,index)),patch.object(ins,'call_census',return_value=census):
                self.assertEqual(ins.verify_handler_metadata(b'',b'',old,dest,HOST,prior),(rows,caller))
                for bad in (old+old,old.replace('HANDLER 1','HANDLER 0'),old+'#define UNDERCOVER_V1210_PRIVATE_ACK_HANDLER 1\n'):
                    with self.assertRaises(ValueError):ins.verify_handler_metadata(b'',b'',bad,dest,HOST,prior)
                with self.assertRaisesRegex(ValueError,'predecessor'):
                    ins.verify_handler_metadata(b'',b'',old,dest,HOST,(*prior[:3],caller+4,*prior[4:]))
                h.write_text(h.read_text()+'// changed\n')
                with self.assertRaisesRegex(ValueError,'metadata'):ins.verify_handler_metadata(b'',b'',old,dest,HOST,prior)
    def test_requires_return(self):
        with self.assertRaisesRegex(ValueError,'ACK handler mode'):
            ins.install(b'',b'',Path('.'),Path('.'),True,True,True,True,True,True,False,True)
class AckHandlerReturnMetadata(unittest.TestCase):
    def test_metadata(self):
        call=H+64;R=H+0x1000;resume=H+0x2000
        restore=[W]*15+[BLR];tail=[W]*3+[BLR];branch=0x48000001
        prior=({call:(branch,12,1)},H+16)
        geo=(call,R,resume,restore,tail,W,branch,'restore metadata','resume metadata')
        old='#define UNDERCOVER_V1145_PRIVATE_POSTALARM_HANDLER_RETURN 1\n'
        with tempfile.TemporaryDirectory() as td:
            dest=Path(td);h=dest/'v1145_private_postalarm_handler_return.h'
            h.write_text(ins.handler_return_render(call,R,resume,restore,tail,W))
            (dest/'v919_private_handler_epilogue.h').write_text(geo[-2])
            (dest/'v920_private_handler_resume.h').write_text(geo[-1])
            n='wii_callback_return_v846.h';(dest/n).write_bytes((HOST/n).read_bytes())
            with patch.object(ins,'handler_return_geometry',return_value=geo):
                self.assertEqual(ins.verify_handler_return_metadata(b'',b'',old,dest,HOST,prior),(call,R,resume,restore,tail,W,branch,H+16))
                for bad in (old+old,old.replace('RETURN 1','RETURN 0'),old+'#define UNDERCOVER_V1214_PRIVATE_ACK_HANDLER_RETURN 1\n'):
                    with self.assertRaises(ValueError):ins.verify_handler_return_metadata(b'',b'',bad,dest,HOST,prior)
                with self.assertRaisesRegex(ValueError,'predecessor'):
                    ins.verify_handler_return_metadata(b'',b'',old,dest,HOST,({call:(branch,7,1)},H+16))
                h.write_text(h.read_text()+'// changed\n')
                with self.assertRaisesRegex(ValueError,'metadata'):ins.verify_handler_return_metadata(b'',b'',old,dest,HOST,prior)
    def test_dispatch_hook(self):
        pc=H+16
        hook=f'    undercover::wii::v958::postalarm_handler_dispatch_resume(ctx,0x{pc:08x}u,0x{W:08x}u);\n'
        label=f'loc_{pc:X}: ;\n    // 0x{pc:08X}: {W:08X}\n'
        ins.verify_handler_return_dispatch_hook(label+hook+T+SI,pc,W)
        for fault in (T+hook+SI,hook+hook+T+SI,hook+'    ctx.inst_count+=1;\n'+T+SI,
                      '    if(false) '+hook.lstrip()+T+SI,hook+T+T+SI,T+SI):
            with self.subTest(fault=fault),self.assertRaisesRegex(ValueError,'ACK handler return dispatch'):
                ins.verify_handler_return_dispatch_hook(label+fault,pc,W)
    def test_requires_handler(self):
        with self.assertRaisesRegex(ValueError,'ACK handler return mode'):
            ins.install(b'',b'',Path('.'),Path('.'),True,True,True,True,True,True,True,False,True)
class AckFinalMetadata(unittest.TestCase):
    def test_metadata(self):
        j=ins.DISPATCH+64;entries=tuple(H+0x100*i for i in range(5))
        ep={j:(ins.DISPATCH,W),**{entries[0]+4*i:(entries[0],W) for i in range(50)}}
        ep[entries[-1]]=(entries[-1],0x4c000064)
        edges=((ins.DISPATCH,[(j,entries[0])]),(entries[0],[]))
        prior={'v922_private_irq_return.h':'test metadata'}
        geo=(ep,j,{},edges,entries,W,prior)
        returned=(H,H+4,j,[],[],W,W,H)
        old='#define UNDERCOVER_V1151_PRIVATE_HELD_EPILOGUE 1\n'
        with tempfile.TemporaryDirectory() as td:
            dest=Path(td);h=dest/'v1151_private_held_epilogue.h';h.write_text(ins.final_render())
            for n,s in prior.items():(dest/n).write_text(s)
            for n in ('wii_live_epilogue_v762.h','wii_external_return_v706.h'):(dest/n).write_bytes((HOST/n).read_bytes())
            with patch.object(ins,'final_metadata',return_value=geo):
                self.assertEqual(ins.verify_final_metadata(b'',b'',old,dest,HOST,returned),(ep,j,edges,entries))
                for bad in (old+old,old.replace('EPILOGUE 1','EPILOGUE 0'),old+'#define UNDERCOVER_V1217_PRIVATE_ACK_FINAL 1\n'):
                    with self.assertRaises(ValueError):ins.verify_final_metadata(b'',b'',bad,dest,HOST,returned)
                with self.assertRaisesRegex(ValueError,'predecessor'):
                    ins.verify_final_metadata(b'',b'',old,dest,HOST,(*returned[:2],j+4,*returned[3:]))
                h.write_text(h.read_text()+'// changed\n')
                with self.assertRaisesRegex(ValueError,'metadata'):ins.verify_final_metadata(b'',b'',old,dest,HOST,returned)
    def test_hook(self):
        pc=H+16;arg=f'ctx,0x{pc:08x}u,0x{W:08x}u'
        hook=f'    if({ins.FINAL_ACTIVE}) undercover::wii::v958::before({arg},false);\n    else undercover::wii::v922::before({arg});\n'
        label=f'loc_{pc:X}: ;\n    // 0x{pc:08X}: {W:08X}\n'
        ins.verify_final_hook(label+T+SI+hook,pc,W)
        for bad in (hook+T+SI,T+hook+SI,T+SI+hook+hook,T+SI+hook.replace('false);','true);'),T+SI+hook.replace('else ','if(true) ')):
            with self.assertRaisesRegex(ValueError,'ACK final hook'):ins.verify_final_hook(label+bad,pc,W)
    def test_requires_handler_return(self):
        with self.assertRaisesRegex(ValueError,'ACK final mode'):
            ins.install(b'',b'',Path('.'),Path('.'),True,True,True,True,True,True,True,True,False,True)
class AckResumeMetadata(unittest.TestCase):
    def test_metadata(self):
        j=ins.DISPATCH+64;pc=ins.ENTRY+12
        ep={j:(ins.DISPATCH,W),pc:(ins.ENTRY,W)}
        header='namespace undercover::wii::v767 {}\n'
        geo=(ep,j,pc,header,(),())
        prior=({j:(ins.DISPATCH,W)},j,(),())
        old='#define UNDERCOVER_V1151_PRIVATE_HELD_EPILOGUE 1\n'
        with tempfile.TemporaryDirectory() as td:
            dest=Path(td);h=dest/'v922_private_irq_return.h';h.write_text(header.replace('::v767','::v922'))
            with patch.object(ins,'final_geometry',return_value=geo):
                self.assertEqual(ins.verify_resume_metadata(b'',b'',old,dest,prior),(pc,W))
                for bad in (old+old,old.replace('EPILOGUE 1','EPILOGUE 0'),old+'#define UNDERCOVER_V1220_PRIVATE_ACK_RESUME 1\n'):
                    with self.assertRaises(ValueError):ins.verify_resume_metadata(b'',b'',bad,dest,prior)
                with self.assertRaisesRegex(ValueError,'predecessor'):
                    ins.verify_resume_metadata(b'',b'',old,dest,({j:(ins.DISPATCH,BLR)},j,(),()))
                h.write_text(h.read_text()+'// changed\n')
                with self.assertRaisesRegex(ValueError,'metadata'):ins.verify_resume_metadata(b'',b'',old,dest,prior)
    def test_hook(self):
        pc=H+16;arg=f'ctx,0x{pc:08x}u,0x{W:08x}u'
        trace=f'    if (nwii::runtime::g_trace_calls) nwii::runtime::trace_call(0x{pc:X}, ctx); // V616 native IRQ resume\n'
        hook=f'    undercover::wii::v922::resume({arg});\n'
        label=f'loc_{pc:X}: ;\n    // 0x{pc:08X}: {W:08X}\n'
        source=label+trace+T+SI+hook
        out=ins.patch_final_resume(source,pc,W)
        self.assertEqual(out,source.replace(hook,f'    if({ins.FINAL_ACTIVE}) undercover::wii::v958::before({arg},false);\n    else '+hook.lstrip()))
        for bad in (T+SI+hook,trace+T+hook+SI,trace+T+SI+hook+hook,trace+T+T+SI+hook,trace+T+SI,trace+T+SI+hook.replace('resume','before')):
            with self.assertRaisesRegex(ValueError,'ACK resume hook'):ins.patch_final_resume(label+bad,pc,W)
        with self.assertRaisesRegex(ValueError,'ACK resume hook'):ins.patch_final_resume(out,pc,W)
    def test_requires_final(self):
        with self.assertRaisesRegex(ValueError,'ACK resume mode'):
            ins.install(b'',b'',Path('.'),Path('.'),True,True,True,True,True,True,True,True,True,False,True)
if __name__=='__main__':unittest.main()
