import unittest,tempfile
from pathlib import Path
from unittest.mock import patch
import prepare_v1141_postalarm_handler as installer
from prepare_v868_handler_suffix import render as render_prior
from prepare_v1134_postalarm_return import render as render_return
from prepare_v1097_after_alarm import ACTIVE,SI
from prepare_v1134_postalarm_return import patch_return_label
from prepare_v1141_postalarm_handler import patch_handler,render
from prepare_v958_second_ack import patch_label as second
H=0x80004000;W=0x60000000
A=f'ctx,0x{H:08x}u,0x{W:08x}u'
L=f'loc_{H:X}: ;\n    // 0x{H:08X}: {W:08X}\n'
T='    ++ctx.inst_count;\n'
LEG=f'    undercover::wii::v672::before({A},0u,0u);\n'

class HeldHandlerHooks(unittest.TestCase):
    def test_reuse(self):
        body=L+f'    undercover::wii::v850::dispatch_resume({A});\n'+T+SI+f'    undercover::wii::v850::handler_resume({A});\n'+LEG
        prior=patch_return_label(body,H,W,True)
        self.assertEqual(patch_handler(prior,H,W,0,0,H),prior)
        for bad in (prior.replace('postalarm_dispatch_resume','bad_resume'),prior+LEG,
                    prior.replace('0u,0u);','1u,1u);')):
            with self.assertRaises(ValueError):patch_handler(bad,H,W,0,0,H)
    def test_old_owner(self):
        body=L+T+SI+LEG
        for old in (body,second(body,H,W,'v672',True),second(body,H,W,'v672',False)):
            new=patch_handler(old,H,W,0,0,H-4)
            self.assertEqual(new.count(T),1)
            self.assertIn(A+',false);',new)
            self.assertIn(A+',0u,0u);',new)
            self.assertEqual(patch_handler(new,H,W,0,0,H-4),new)
    def test_refusals(self):
        base=L+T+SI+LEG
        for bad in (base+LEG,base.replace(SI,''),base.replace(T,T+T),
                    base.replace('0u,0u);','1u,1u);'),base.replace(LEG,''),
                    base+f'    undercover::wii::v850::dispatch_resume({A});\n',
                    base+f'    if({ACTIVE}) unrelated();\n'):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):patch_handler(bad,H,W,0,0,H-4)
    def test_metadata(self):
        rows={H:(W,0,0),H+4:(0x80830038,0,0)}
        text=render(rows,H+4,H+8,(H,[W]*14,(H+100,H+104,H+108,H+112),20,H+64))
        self.assertIn('std::array<HandlerSuffixLabel,2> rows',text)
        self.assertIn('rd=0x80004004u,wr=0x80004008u;',text)
        self.assertIn('HandlerIndexBranchExpectation index',text)


class HeldHandlerTree(unittest.TestCase):
    def fixture(self,root):
        # Independently authored synthetic geometry. The private derivation
        # itself remains covered by the earlier owner-authenticated installers.
        caller=H+24;sites=(caller-4,H+4*59)
        rd,wr=caller+20,caller+36
        code=[W]*80
        for i in range(6):code[i]=0x48000101
        code[5]=0x4e800421
        # Calls 7, 8 and 12 are the only admitted terminal labels.
        for i in (20,25,56,57,59,65):code[i]=0x48000101
        code[59]=0x4e800421
        code[11]=0x80830038;code[15]=0x90830038
        from prepare_v672_si_ack_route import call_census
        census=call_census(H,code)
        selected=[i for i in range(6,66) if i not in (56,57,59,60,61,62,63,64)]
        self.assertEqual(len(selected),52)
        rows={H+4*i:(code[i],*census.get(H+4*i,(0,0))) for i in selected}
        lanes=[rows,{H+240:(W,0,0)}]
        idx=(caller,code[6:20],(H+0x800,H+0x804,H+0x808,H+0x80c),20,H+0x100)
        args=(H+0x1000,H+0x2000,caller,(0x4e800020,)*7,(W,W,W,0x4e800020),W)
        dest=root/'nWiiRuntime/include/undercover';dest.mkdir(parents=True)
        host=Path(installer.__file__).parent
        for n in ('wii_handler_suffix_guard_v868.h','wii_handler_index_branch_v911.h',
                  'wii_third_alarm_suffix_v1047.h','wii_second_ack_live_v958.h'):
            (dest/n).write_bytes((host/n).read_bytes())
        (dest/'v868_private_handler_suffix.h').write_text(render_prior(lanes,rd,wr,idx))
        (dest/'v1132_private_postalarm_return.h').write_text(render_return(*args))
        (dest/'v958_private_second_ack.h').write_text('#define UNDERCOVER_V1132_PRIVATE_POSTALARM_RETURN 1\n')
        source='#include "runtime/cpu_context.h"\n'+f'void fn_{H:X}(CPUContext& ctx) {{\n'
        source+=f'    if (nwii::runtime::g_trace_calls && ctx.pc == 0x{H:X}) nwii::runtime::trace_call(0x{H:X}, ctx);\n'
        for pc,(w,o,k) in sorted(rows.items()):
            a=f'ctx,0x{pc:08x}u,0x{w:08x}u'
            source+=f'loc_{pc:X}: ;\n    // 0x{pc:08X}: {w:08X}\n'
            if pc==caller:source+=f'    undercover::wii::v850::dispatch_resume({a});\n'
            source+=T+SI
            if pc==caller:source+=f'    undercover::wii::v850::handler_resume({a});\n'
            source+=f'    undercover::wii::v672::before({a},{o}u,{k}u);\n'
        source+='}\n'
        source=patch_return_label(source,caller,W,True)
        (root/'output_0.cpp').write_text(source)
        for i in range(1,20):(root/f'output_{i}.cpp').write_text('// unused shard\n')
        (root/'main_output.cpp').write_text(f'case 0x{H:X}: fn_{H:X}(ctx); break;\ncase 0x{caller:X}: fn_{H:X}(ctx); break;\n')
        return (code,sites,lanes,rd,wr,idx),(0,0,{}, {},(),*args,[(sites[0],0x4e800421,6,W)]),dest
    @staticmethod
    def snapshot(root):
        return {str(p.relative_to(root)):p.read_bytes() for p in root.rglob('*') if p.is_file()}
    def run_install(self,root,data):
        geom,ret,_=data
        with patch.object(installer,'HANDLER',H),patch.object(installer,'derive',return_value=geom), \
             patch.object(installer,'derive_return',return_value=ret):
            installer.install(b'',b'',root,Path(installer.__file__).parent)
    def test_complete_tree(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);data=self.fixture(root);before=self.snapshot(root)
            self.run_install(root,data);after=self.snapshot(root)
            source=after['output_0.cpp']
            self.assertEqual(source.count(b'++ctx.inst_count;'),52)
            self.assertEqual(source.count(b'v958::before(ctx,'),52)
            self.assertEqual(source.count(b'v958::postalarm_dispatch_resume(ctx,'),1)
            self.assertEqual(len(set(after)-set(before)),1)
            self.assertIn(b'UNDERCOVER_V1139_PRIVATE_POSTALARM_HANDLER 1',(data[-1]/'v958_private_second_ack.h').read_bytes())
    def test_tree_refusals(self):
        for fault in ('metadata','return','witness','mode','owner','dispatch','label','existing'):
            with self.subTest(fault=fault),tempfile.TemporaryDirectory() as td:
                root=Path(td);data=self.fixture(root);dest=data[-1]
                if fault=='metadata':
                    q=dest/'v868_private_handler_suffix.h';q.write_text(q.read_text()+'// tamper\n')
                elif fault=='return':
                    q=dest/'v1132_private_postalarm_return.h';q.write_text(q.read_text()+'// tamper\n')
                elif fault=='witness':
                    q=dest/'wii_handler_index_branch_v911.h';q.write_text(q.read_text()+'// tamper\n')
                elif fault=='mode':(dest/'v958_private_second_ack.h').write_text('// missing macro\n')
                elif fault=='owner':(root/'output_19.cpp').write_bytes((root/'output_0.cpp').read_bytes())
                elif fault=='dispatch':(root/'main_output.cpp').write_text(f'case 0x{H:X}: fn_{H:X}(ctx); break;\n')
                elif fault=='label':
                    q=root/'output_0.cpp';q.write_text(q.read_text().replace('++ctx.inst_count;','++ctx.inst_count;\n    ++ctx.inst_count;',1))
                else:(dest/'v1139_private_postalarm_handler.h').write_text('// existing\n')
                before=self.snapshot(root)
                with self.assertRaises(ValueError):self.run_install(root,data)
                self.assertEqual(self.snapshot(root),before)

if __name__=='__main__':unittest.main()
