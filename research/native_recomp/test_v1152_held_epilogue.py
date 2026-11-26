import unittest,tempfile
from pathlib import Path
from unittest.mock import patch
from prepare_v1152_held_epilogue import patch_label,render,NEW,ACK
from prepare_v922_irq_return import patch_label as ep
from prepare_v939_second_vector import patch_label as vector
from prepare_v975_second_time import shared_label
from prepare_v667_si_dispatch import DISABLE,RESTORE
from prepare_v1097_after_alarm import SI
H=0x80004000;W=0x60000000
A=f'ctx,0x{H:08x}u,0x{W:08x}u'
L=f'loc_{H:X}: ;\n    // 0x{H:08X}: {W:08X}\n'
T='    ++ctx.inst_count;\n'
class HeldEpilogueHooks(unittest.TestCase):
    def test_original_hooks(self):
        for vector_mode,prior in ((False,ep),(True,vector)):
            body=prior(L+T+SI,H,W)
            out=patch_label(body,H,W,vector_mode)
            self.assertEqual(out.count(T),1)
            self.assertEqual(out.count('v958::before(ctx,'),1)
            self.assertIn(f'if({NEW}) undercover::wii::v958::before({A},false);',out)
            self.assertIn('else undercover::wii::v922::',out)
            for bad in (body.replace(T,T+T),body.replace(SI,''),body.replace('v922::','bad::'),
                        body+f'    undercover::wii::v958::before({A},false);\n',out):
                with self.assertRaises(ValueError):patch_label(bad,H,W,vector_mode)
    def test_shared_hooks(self):
        for root in (DISABLE,RESTORE):
            body=ep(L+T+SI,H,W)
            shared=shared_label(body,H,W,root,False)
            self.assertEqual(patch_label(shared,H,W,False,True),shared)
            for bad in (body,shared.replace('false);','true);'),shared.replace(f'if(!{ACK}) ',''),
                        shared+f'    undercover::wii::v922::before({A});\n'):
                with self.assertRaises(ValueError):patch_label(bad,H,W,False,True)
    def test_real_shared_leaf_composition(self):
        # V922 explicitly gates an already-present V709 observer, then
        # V975 gates V922 and inserts the one admitted V958 hook.
        for role,root in ((1,DISABLE),(3,RESTORE)):
            legacy=f'    undercover::wii::v709::before({A},{role}u);\n'
            body=ep(L+T+SI+legacy,H,W,shared=role)
            shared=shared_label(body,H,W,root,False)
            self.assertIn('if(!undercover::wii::v922::active()) undercover::wii::v709::before(',shared)
            self.assertEqual(patch_label(shared,H,W,False,True),shared)
            # Also exercise the V1097 suppression wrapper around V709.
            from prepare_v1097_after_alarm import patch_label as postalarm
            wrapped=postalarm(shared,H,W)
            self.assertEqual(patch_label(wrapped,H,W,False,True),wrapped)
            for bad in (shared.replace('v922::before(', 'v922::wrong('),
                        shared+f'    undercover::wii::v922::second_dispatch_before({A},false);\n',
                        shared.replace(f'if(!{ACK}) undercover::wii::v922::before', 'undercover::wii::v922::before')):
                with self.assertRaises(ValueError):patch_label(bad,H,W,False,True)
    def test_metadata(self):
        h=render()
        self.assertIn('epilogue=v922::expected;',h)
        self.assertIn('vector=v922::second_expected;',h)
        self.assertIn('image=v663::expected.vector;',h)

class HeldEpilogueTree(unittest.TestCase):
    def fixture(self,root):
        from prepare_v1152_held_epilogue import DISPATCH,VECTOR,TRAMP
        from prepare_v1146_postalarm_handler_return import patch_dispatch
        from prepare_v920_handler_return import patch_label as prior_dispatch
        J=DISPATCH+0x40;E=0x80040000
        branch=0x48000001|((E-J)&0x03fffffc)
        labels={J:(DISPATCH,branch),J+4:(DISPATCH,W),E:(E,W),DISABLE:(DISABLE,W),RESTORE:(RESTORE,W)}
        vectors={**{VECTOR+4*i:(VECTOR,W) for i in range(38)},**{TRAMP+4*i:(TRAMP,W) for i in range(20)}}
        prior={'v1145_private_postalarm_handler_return.h':'// synthetic handler\n',
               'v922_private_irq_return.h':'// synthetic epilogue\n',
               'v939_private_second_vector.h':'// synthetic vector\n',
               'v663_private_external_expectations.h':'// synthetic external\n'}
        host=Path(__file__).parent;dest=root/'nWiiRuntime/include/undercover';dest.mkdir(parents=True)
        for n in ('wii_live_epilogue_v762.h','wii_second_vector_v939.h','wii_second_si_dispatch_v944.h',
                  'wii_pending_external_reentry_v932.h','wii_second_ack_live_v958.h','wii_third_alarm_suffix_v1047.h'):
            prior[n]=(host/n).read_text()
        for name,value in prior.items():(dest/name).write_text(value)
        (dest/'v958_private_second_ack.h').write_text('#define UNDERCOVER_V1145_PRIVATE_POSTALARM_HANDLER_RETURN 1\n')
        roots=(DISPATCH,E,DISABLE,RESTORE,VECTOR,TRAMP)
        def label(pc,w):
            return f'loc_{pc:X}: ;\n    // 0x{pc:08X}: {w:08X}\n'
        def arg(pc,w):return f'ctx,0x{pc:08x}u,0x{w:08x}u'
        def entry(a):
            return '#include "runtime/cpu_context.h"\n'+f'void fn_{a:X}(CPUContext& ctx) {{\n    if (nwii::runtime::g_trace_calls && ctx.pc == 0x{a:X}) nwii::runtime::trace_call(0x{a:X}, ctx);\n'
        for i,a in enumerate(roots):
            body=entry(a)
            if a==DISPATCH:
                body+=label(a,W)+T+SI+label(J,branch)+T+f'    undercover::wii::v726::resume({arg(J,branch)});\n'+SI
                body+=f'    ctx.pc = 0x{E:X}; fn_{E:X}(ctx);\n    if (ctx.pc != 0x{J+4:X}) return;\n'
                body+=label(J+4,W)+T+SI+'}\n'
                body=patch_dispatch(prior_dispatch(body,J,branch),J,branch)
                body=ep(body,J+4,W)
            else:
                selected={pc:w for pc,(owner,w) in {**labels,**vectors}.items() if owner==a}
                for pc,w in sorted(selected.items()):body+=label(pc,w)+T+SI
                body+='}\n'
                for pc,w in sorted(selected.items()):
                    body=(vector if a in (VECTOR,TRAMP) else ep)(body,pc,w)
                    if a in (DISABLE,RESTORE):body=shared_label(body,pc,w,a,False)
            (root/f'output_{i}.cpp').write_text(body)
        for i in range(len(roots),20):(root/f'output_{i}.cpp').write_text('// unused\n')
        (root/'main_output.cpp').write_text(''.join(f'case 0x{pc:X}: fn_{owner:X}(ctx); break;\n' for pc,owner in
            [(a,a) for a in roots]+[(J,DISPATCH)]))
        return (labels,J,vectors,((DISPATCH,[(J,E)]),),(E,DISABLE,RESTORE),W,prior),dest
    def run_install(self,root,data):
        from prepare_v1152_held_epilogue import install
        with patch('prepare_v1152_held_epilogue.metadata',return_value=data[0]):
            install(b'',b'',root,Path(__file__).parent)
    @staticmethod
    def snapshot(root):return {str(p.relative_to(root)):p.read_bytes() for p in root.rglob('*') if p.is_file()}
    def test_complete(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);data=self.fixture(root);before=self.snapshot(root)
            self.run_install(root,data);after=self.snapshot(root)
            self.assertEqual(len(set(after)-set(before)),3)
            self.assertEqual(after['output_0.cpp'].count(b'postalarm_handler_dispatch_resume(ctx,'),1)
            self.assertEqual(after['output_0.cpp'].count(b'v958::before(ctx,'),2)
            self.assertEqual(after['output_2.cpp'].count(b'v958::before(ctx,'),1)
            self.assertEqual(after['output_4.cpp'].count(b'v958::before(ctx,'),38)
            self.assertEqual(after['output_5.cpp'].count(b'v958::before(ctx,'),20)
            self.assertIn(b'UNDERCOVER_V1151_PRIVATE_HELD_EPILOGUE 1',(data[1]/'v958_private_second_ack.h').read_bytes())
    def test_refusals(self):
        for fault in ('metadata','vector','duplicate','mapping','direct','tick','shared','mode','existing'):
            with self.subTest(fault=fault),tempfile.TemporaryDirectory() as td:
                root=Path(td);data=self.fixture(root);dest=data[1]
                if fault=='metadata':
                    q=dest/'v939_private_second_vector.h';q.write_text(q.read_text()+'// changed\n')
                elif fault=='vector':
                    q=root/'output_4.cpp';q.write_text(q.read_text().replace('v922::second_before','v922::wrong',1))
                elif fault=='duplicate':(root/'output_19.cpp').write_bytes((root/'output_5.cpp').read_bytes())
                elif fault=='mapping':
                    q=root/'main_output.cpp';q.write_text('\n'.join(q.read_text().splitlines()[:-1]))
                elif fault=='direct':
                    q=root/'output_0.cpp';q.write_text(q.read_text().replace('ctx.pc =','ctx.fake_pc =',1))
                elif fault=='tick':
                    q=root/'output_1.cpp';q.write_text(q.read_text().replace(T,T+T,1))
                elif fault=='shared':
                    q=root/'output_2.cpp';q.write_text(q.read_text().replace('false);','true);',1))
                elif fault=='mode':(dest/'v958_private_second_ack.h').write_text('// absent\n')
                else:(dest/'v1151_private_held_epilogue.h').write_text('// exists\n')
                before=self.snapshot(root)
                with self.assertRaises(ValueError):self.run_install(root,data)
                self.assertEqual(self.snapshot(root),before)

if __name__=='__main__':unittest.main()
