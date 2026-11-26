import unittest,tempfile
from pathlib import Path
from unittest.mock import patch
import prepare_v1169_third_ack as installer
from prepare_v1169_third_ack import verify_label,verify_bus,render
from prepare_v1097_after_alarm import patch_label,SI
from prepare_v958_second_ack import patch_label as old
from prepare_v1048_third_alarm import hook
H=0x80004000;W=0x60000000
A=f'ctx,0x{H:08x}u,0x{W:08x}u'
T='    ++ctx.inst_count;\n'
L=f'loc_{H:X}: ;\n    // 0x{H:08X}: {W:08X}\n'+T+SI
class ThirdAckLabels(unittest.TestCase):
    def test_labels(self):
        for guard in (False,True):
            body=old(L+f'    undercover::wii::v672::before({A},0u,0u);\n',H,W,'v672',guard)
            for good in (body,patch_label(body,H,W),patch_label(hook(body,H,W),H,W)):
                verify_label(good,H,W)
                for bad in (good.replace(T,T+T),good.replace(SI,''),good.replace('v958::before','v958::wrong'),
                            good.replace('0x60000000u','0x60000001u'),good+f'    undercover::wii::v958::before({A},false);\n'):
                    with self.assertRaises(ValueError):verify_label(bad,H,W)
    def test_bus(self):
        from pathlib import Path
        from test_v997_composed_success_frontier import first,second,transfer,discovery,sampling,HOST
        s=second(transfer(first(discovery(sampling((HOST/'wii_si_binding_v512.h').read_text())))))
        verify_bus(s)
        for bad in (s.replace('held_epilogue.ack_read','held_epilogue.wrong'),s.replace('held_epilogue.ack_write','held_epilogue.wrong'),
                    s.replace('next_device.stage()!=3u','next_device.stage()!=2u'),s.replace('#ifdef UNDERCOVER_V1167_PRIVATE_THIRD_ACK','#ifdef WRONG')):
            with self.assertRaises(ValueError):verify_bus(bad)
    def test_render(self):
        s=render([(H,H+4,0),(H+8,H+12,1)],[(H,H+8)],[(H,W,H,False),(H+8,W,H+8,True)])
        self.assertIn('ThirdAckNativeLabel,2> labels',s)
        self.assertIn('0x80004008u,true}',s)

class ThirdAckTree(unittest.TestCase):
    def fixture(self,root):
        from prepare_v1161_held_dispatch import render as dispatch
        from test_v997_composed_success_frontier import first,second,transfer,discovery,sampling,HOST
        handler=H;save=H+0x100;helper=H+0x200
        def branch(a,b):return 0x48000001|((b-a)&0x03fffffc)
        spans=[(handler,handler+16,0),(save,save+8,1),(helper,helper+16,0)]
        edges=[(handler,save),(handler+4,helper)]
        rows=[(handler,branch(handler,save),handler,False),(handler+4,branch(handler+4,helper),handler,False),
              (handler+8,W,handler,False),(handler+12,0x4e800421,handler,True),
              (save,W,save,False),(save+4,0x4e800020,save,False),
              (helper,0x80830034,helper,False),(helper+4,0x90830034,helper,False),
              (helper+8,W,helper,False),(helper+12,0x4e800020,helper,False)]
        base='inline constexpr uint32_t context=0x80009000u;\n'
        dest=root/'nWiiRuntime/include/undercover';dest.mkdir(parents=True)
        for n in ('wii_second_ack_live_v958.h','wii_held_pending_epilogue_v1149.h','wii_third_pending_reentry_v1067.h',
                  'wii_second_completion_ack_v950.h','wii_bounded_ack_call_route_v956.h'):
            (dest/n).write_bytes((HOST/n).read_bytes())
        (dest/'v1158_private_held_dispatch.h').write_text(dispatch())
        (dest/'v958_private_second_ack.h').write_text('#define UNDERCOVER_V1158_PRIVATE_HELD_DISPATCH 1\n'+base)
        (dest/'wii_si_binding_v512.h').write_text(second(transfer(first(discovery(sampling((HOST/'wii_si_binding_v512.h').read_text()))))))
        for i,a in enumerate((handler,save,helper)):
            body='#include "runtime/cpu_context.h"\n'+f'void fn_{a:X}(CPUContext& ctx) {{\n    if (nwii::runtime::g_trace_calls && ctx.pc == 0x{a:X}) nwii::runtime::trace_call(0x{a:X}, ctx);\n'
            for pc,w,owner,g in rows:
                if owner!=a:continue
                body+=f'loc_{pc:X}: ;\n    // 0x{pc:08X}: {w:08X}\n'+T+SI
                body+=f'    undercover::wii::v958::before(ctx,0x{pc:08x}u,0x{w:08x}u,{str(g).lower()});\n'
                for call,dst in edges:
                    if pc==call:body+=f'    ctx.pc = 0x{dst:X}; fn_{dst:X}(ctx);\n    if (ctx.pc != 0x{pc+4:X}) return;\n'
            (root/f'output_{i}.cpp').write_text(body+'}\n')
        for i in range(3,20):(root/f'output_{i}.cpp').write_text('// unused\n')
        (root/'main_output.cpp').write_text(''.join(f'case 0x{a:X}: fn_{a:X}(ctx); break;\n' for a in (handler,save,helper)))
        return (spans,edges,rows,base),dest
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
            self.assertEqual({p for p in before if before[p]!=after[p]},
                {'nWiiRuntime/include/undercover/v958_private_second_ack.h'})
            self.assertIn('UNDERCOVER_V1167_PRIVATE_THIRD_ACK 1',(data[1]/'v958_private_second_ack.h').read_text())
            self.assertEqual((data[1]/'v1167_private_third_ack.h').read_text(),render(*data[0][:3]))
    def test_refusals(self):
        for fault in ('metadata','header','bus','duplicate','mapping','direct','tick','guard','mode','existing'):
            with self.subTest(fault=fault),tempfile.TemporaryDirectory() as td:
                root=Path(td);data=self.fixture(root);dest=data[1]
                if fault=='metadata':
                    q=dest/'v958_private_second_ack.h';q.write_text(q.read_text().replace('0x80009000u','0x80009004u'))
                elif fault=='header':
                    q=dest/'v1158_private_held_dispatch.h';q.write_text(q.read_text()+'// changed\n')
                elif fault=='bus':
                    q=dest/'wii_si_binding_v512.h';q.write_text(q.read_text().replace('held_epilogue.ack_read','wrong'))
                elif fault=='duplicate':(root/'output_19.cpp').write_bytes((root/'output_1.cpp').read_bytes())
                elif fault=='mapping':
                    q=root/'main_output.cpp';q.write_text('\n'.join(q.read_text().splitlines()[:-1]))
                elif fault=='direct':
                    q=root/'output_0.cpp';q.write_text(q.read_text().replace('ctx.pc =','ctx.fake_pc =',1))
                elif fault=='tick':
                    q=root/'output_1.cpp';q.write_text(q.read_text().replace(T,T+T,1))
                elif fault=='guard':
                    q=root/'output_0.cpp';q.write_text(q.read_text().replace('true);','false, true);',1))
                elif fault=='mode':(dest/'v958_private_second_ack.h').write_text('// absent\n')
                else:(dest/'v1167_private_third_ack.h').write_text('// exists\n')
                before=self.snapshot(root)
                with self.assertRaises(ValueError):self.run_install(root,data)
                self.assertEqual(self.snapshot(root),before)

if __name__=='__main__':unittest.main()
