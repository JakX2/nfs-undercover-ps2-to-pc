import unittest,tempfile
from pathlib import Path
from unittest.mock import patch
import prepare_v1161_held_dispatch as installer
from prepare_v1161_held_dispatch import patch_label,render,DISPATCH_ACTIVE
from prepare_v951_second_dispatch import patch_label as prior
from prepare_v922_irq_return import patch_label as ep
from prepare_v975_second_time import shared_label
from prepare_v1097_after_alarm import patch_label as post
from prepare_v667_si_dispatch import DISPATCH,SCHED,TIME,DISABLE,RESTORE
from prepare_v1097_after_alarm import SI
H=0x80004000;W=0x60000000
A=f'ctx,0x{H:08x}u,0x{W:08x}u'
L=f'loc_{H:X}: ;\n    // 0x{H:08X}: {W:08X}\n'
T='    ++ctx.inst_count;\n'
class HeldDispatchHooks(unittest.TestCase):
    def test_unshared(self):
        for root in (DISPATCH,SCHED):
            for guard in (False,True):
                body=prior(L+T+SI,H,W,root,guard)
                out=patch_label(body,H,W,root,guard)
                self.assertIn(f'if({DISPATCH_ACTIVE}) undercover::wii::v958::before({A},{str(guard).lower()});',out)
                self.assertEqual(out.count(T),1);self.assertEqual(out.count(SI),1)
                self.assertIn('else undercover::wii::v922::second_dispatch_before',out)
                for bad in (body.replace(T,T+T),body.replace(SI,''),body.replace('v922::','bad::'),out):
                    with self.assertRaises(ValueError):patch_label(bad,H,W,root,guard)
    def test_shared(self):
        for root in (DISABLE,RESTORE,TIME):
            if root==TIME:
                body=prior(L+T+SI+f'    undercover::wii::v709::before({A},2u);\n',H,W,root,False)
            else:body=ep(L+T+SI,H,W)
            body=post(shared_label(body,H,W,root,False),H,W)
            self.assertEqual(patch_label(body,H,W,root,False),body)
            for bad in (body.replace('v922::','bad::'),body.replace('v958::before','wrong::before'),body.replace(SI,''),body+T):
                with self.assertRaises(ValueError):patch_label(bad,H,W,root,False)
            with self.assertRaises(ValueError):patch_label(body,H,W,root,True)
    def test_metadata(self):
        self.assertIn('expected=v667::expected;',render())

class HeldDispatcherTree(unittest.TestCase):
    def fixture(self,root):
        from prepare_v667_si_dispatch import HANDLER,render as render_prior
        from prepare_v1152_held_epilogue import render as render_epilogue
        roots=(DISPATCH,SCHED,TIME,DISABLE,RESTORE,HANDLER)
        def branch(a,b):return 0x48000001|((b-a)&0x03fffffc)
        def arg(pc,w):return f'ctx,0x{pc:08x}u,0x{w:08x}u'
        def label(pc,w):return f'loc_{pc:X}: ;\n    // 0x{pc:08X}: {w:08X}\n'
        edges=[(TIME,DISPATCH+8,branch(DISPATCH+4,TIME),W),
               (SCHED,DISPATCH+12,branch(DISPATCH+8,SCHED),W),
               (DISABLE,SCHED+8,branch(SCHED+4,DISABLE),W),
               (RESTORE,SCHED+12,branch(SCHED+8,RESTORE),W)]
        indirect=DISPATCH+12;IW=0x4e800421
        guard=DISPATCH+16
        rows={a:(a,W,False) for a in roots if a!=HANDLER}
        for dst,lr,w,_ in edges:
            owner=DISPATCH if lr-4<SCHED else SCHED
            rows[lr-4]=(owner,w,False)
        rows[indirect]=(DISPATCH,IW,False);rows[guard]=(DISPATCH,W,True)
        metadata=render_prior(edges,(indirect,IW),W,W)
        host=Path(installer.__file__).parent
        dest=root/'nWiiRuntime/include/undercover';dest.mkdir(parents=True)
        for n in ('wii_second_ack_live_v958.h','wii_held_pending_epilogue_v1149.h','wii_third_pending_reentry_v1067.h',
                  'wii_second_si_dispatch_v944.h','wii_si_dispatch_v667.h'):
            (dest/n).write_bytes((host/n).read_bytes())
        (dest/'v667_private_si_dispatch_expectations.h').write_text(metadata)
        (dest/'v1151_private_held_epilogue.h').write_text(render_epilogue())
        (dest/'v958_private_second_ack.h').write_text('#define UNDERCOVER_V1151_PRIVATE_HELD_EPILOGUE 1\n')
        (dest/'wii_irq_return_witness_v482.h').write_text('        si_dispatch_pi_reads.record(write,address,width,value,native);\n        record_second_dispatch_pi(write,address,width,value,native);\n')
        for i,a in enumerate(roots):
            body='#include "runtime/cpu_context.h"\n'+f'void fn_{a:X}(CPUContext& ctx) {{\n    if (nwii::runtime::g_trace_calls && ctx.pc == 0x{a:X}) nwii::runtime::trace_call(0x{a:X}, ctx);\n'
            selected={pc:(w,g) for pc,(owner,w,g) in rows.items() if owner==a}
            if a==HANDLER:selected={a:(W,False)}
            for pc,(w,g) in sorted(selected.items()):
                body+=label(pc,w)+T+SI
                if a==TIME:body+=f'    undercover::wii::v709::before({arg(pc,w)},2u);\n'
                for dst,lr,bw,_ in edges:
                    if pc==lr-4:
                        body+=f'    ctx.pc = 0x{dst:X}; fn_{dst:X}(ctx);\n    if (ctx.pc != 0x{lr:X}) return;\n'
                if pc==indirect:body+=f'    ctx.lr = 0x{pc+4:X};\n    if (ctx.ctr) {{ ctx.pc = ctx.ctr; return; }}\n'
            body+='}\n'
            if a!=HANDLER:
                for pc,(w,g) in sorted(selected.items()):
                    if a in (DISABLE,RESTORE):
                        body=post(shared_label(ep(body,pc,w),pc,w,a,g),pc,w)
                    elif a==TIME:
                        body=post(shared_label(prior(body,pc,w,a,g),pc,w,a,g),pc,w)
                    else:body=prior(body,pc,w,a,g)
            (root/f'output_{i}.cpp').write_text(body)
        for i in range(len(roots),20):(root/f'output_{i}.cpp').write_text('// unused\n')
        (root/'main_output.cpp').write_text(''.join(f'case 0x{a:X}: fn_{a:X}(ctx); break;\n' for a in roots))
        return (rows,edges,indirect,W,metadata),dest
    @staticmethod
    def snapshot(root):return {str(p.relative_to(root)):p.read_bytes() for p in root.rglob('*') if p.is_file()}
    def run_install(self,root,data):
        with patch.object(installer,'metadata',return_value=data[0]):
            installer.install(b'',b'',root,Path(installer.__file__).parent)
    def test_complete(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);data=self.fixture(root);before=self.snapshot(root)
            self.run_install(root,data);after=self.snapshot(root)
            self.assertEqual(len(set(after)-set(before)),1)
            for i,n in enumerate((5,3,1,1,1,0)):
                p=f'output_{i}.cpp'
                self.assertEqual(before[p].count(b'++ctx.inst_count;'),after[p].count(b'++ctx.inst_count;'))
                self.assertEqual(after[p].count(b'v958::before(ctx,'),n)
            self.assertEqual(before['output_5.cpp'],after['output_5.cpp'])
            self.assertIn(b'UNDERCOVER_V1158_PRIVATE_HELD_DISPATCH 1',(data[1]/'v958_private_second_ack.h').read_bytes())
    def test_refusals(self):
        for fault in ('metadata','trace','duplicate','mapping','direct','indirect','tick','shared','mode','existing'):
            with self.subTest(fault=fault),tempfile.TemporaryDirectory() as td:
                root=Path(td);data=self.fixture(root);dest=data[1]
                if fault=='metadata':
                    q=dest/'v667_private_si_dispatch_expectations.h';q.write_text(q.read_text()+'// changed\n')
                elif fault=='trace':
                    q=dest/'wii_irq_return_witness_v482.h';q.write_text(q.read_text().replace('record_second_dispatch_pi','wrong'))
                elif fault=='duplicate':(root/'output_19.cpp').write_bytes((root/'output_1.cpp').read_bytes())
                elif fault=='mapping':
                    q=root/'main_output.cpp';q.write_text('\n'.join(q.read_text().splitlines()[:-1]))
                elif fault=='direct':
                    q=root/'output_0.cpp';q.write_text(q.read_text().replace('ctx.pc =','ctx.fake_pc =',1))
                elif fault=='indirect':
                    q=root/'output_0.cpp';q.write_text(q.read_text().replace('ctx.pc = ctx.ctr','ctx.pc = ctx.lr'))
                elif fault=='tick':
                    q=root/'output_1.cpp';q.write_text(q.read_text().replace(T,T+T,1))
                elif fault=='shared':
                    q=root/'output_2.cpp';q.write_text(q.read_text().replace('v958::before','v958::wrong',1))
                elif fault=='mode':(dest/'v958_private_second_ack.h').write_text('// absent\n')
                else:(dest/'v1158_private_held_dispatch.h').write_text('// exists\n')
                before=self.snapshot(root)
                with self.assertRaises(ValueError):self.run_install(root,data)
                self.assertEqual(self.snapshot(root),before)

if __name__=='__main__':unittest.main()
