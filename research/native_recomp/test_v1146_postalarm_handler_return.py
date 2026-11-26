import unittest,tempfile
from pathlib import Path
from unittest.mock import patch
import prepare_v1146_postalarm_handler_return as installer
from prepare_v1141_postalarm_handler import patch_handler,render as render_suffix
from prepare_v1146_postalarm_handler_return import patch_restore,patch_dispatch,render
from prepare_v919_handler_epilogue import patch_alias
from prepare_v920_handler_return import patch_label
from prepare_v1097_after_alarm import ACTIVE,SI
H=0x80004000;W=0x60000000
A=f'ctx,0x{H:08x}u,0x{W:08x}u'
L=f'loc_{H:X}: ;\n    // 0x{H:08X}: {W:08X}\n'
T='    ++ctx.inst_count;\n'
class HandlerReturnHooks(unittest.TestCase):
    def test_restore(self):
        for old in ('',f'    undercover::wii::v726::restore_before({A});\n'):
            body=patch_alias(L+T+old+SI,H,[W])
            new=patch_restore(body,H,W)
            self.assertIn(f'if(!{ACTIVE}) undercover::wii::v868::restore_before({A});',new)
            self.assertEqual(new.count(T),1)
            self.assertEqual(new.count('v958::before(ctx,'),1)
            for bad in (body.replace('v868::restore_before','other'),body+f'    undercover::wii::v868::restore_before({A});\n',
                        body.replace(T,T+T),body.replace(SI,'')):
                with self.assertRaises(ValueError):patch_restore(bad,H,W)
    def test_dispatch(self):
        old=patch_label(L+T+f'    undercover::wii::v726::resume({A});\n'+SI,H,W)
        new=patch_dispatch(old,H,W)
        self.assertLess(new.index('postalarm_handler_dispatch_resume'),new.index(T))
        self.assertLess(new.index(SI),new.index('v958::before(ctx,'))
        self.assertIn(f'if(!{ACTIVE}) undercover::wii::v868::dispatcher_resume({A});',new)
        self.assertEqual(new.count(T),1)
        for bad in (old.replace('v868::dispatch_resume','other'),old.replace('v868::dispatcher_resume','other'),
                    old.replace('v726::resume','other'),old+T,old.replace(SI,''),old.replace('0x60000000u','0x60000001u')):
            with self.assertRaises(ValueError):patch_dispatch(bad,H,W)
    def test_metadata(self):
        s=render(H,H+0x100,H+0x200,[W]*16,[W]*4,W)
        self.assertIn('HandlerReturnExpectation expected{0x80004000u,0x80004100u,0x80004200u',s)

class HandlerReturnTree(unittest.TestCase):
    def fixture(self,root):
        handler=H;call=H+0xcc;R=H+0x1000;D=H+0x2000;resume=D+4
        branch=0x48000001|((R-call)&0x03fffffc)
        tail=[0x80010044,0x7c0803a6,0x38210040,0x4e800020]
        restore=[0x800b0000|((17+i)<<21)|((0xffc4+4*i)&0xffff) for i in range(15)]+[0x4e800020]
        rows={H+4*i:(W,0,0) for i in range(51)}
        rows[call]=(branch,12,1)
        caller=H;lanes=[rows,{}];rd=H+4;wr=H+8
        index=(H,[W]*14,(H+0x800,H+0x804,H+0x808,H+0x80c),20,H+64)
        # Synthetic prior metadata is independent of the generated fixture.
        h='// independently authenticated synthetic restore geometry\n'
        d='// independently authenticated synthetic dispatcher geometry\n'
        dest=root/'nWiiRuntime/include/undercover';dest.mkdir(parents=True)
        host=Path(installer.__file__).parent
        for n in ('wii_third_alarm_suffix_v1047.h','wii_callback_return_v846.h','wii_second_ack_live_v958.h'):
            (dest/n).write_bytes((host/n).read_bytes())
        (dest/'v1139_private_postalarm_handler.h').write_text(render_suffix(rows,rd,wr,index))
        (dest/'v919_private_handler_epilogue.h').write_text(h)
        (dest/'v920_private_handler_resume.h').write_text(d)
        (dest/'v958_private_second_ack.h').write_text('#define UNDERCOVER_V1139_PRIVATE_POSTALARM_HANDLER 1\n')
        inc='#include "runtime/cpu_context.h"\n'
        def entry(a):
            return inc+f'void fn_{a:X}(CPUContext& ctx) {{\n    if (nwii::runtime::g_trace_calls && ctx.pc == 0x{a:X}) nwii::runtime::trace_call(0x{a:X}, ctx);\n'
        def label(a,w):
            return f'loc_{a:X}: ;\n    // 0x{a:08X}: {w:08X}\n'
        def arg(a,w):
            return f'ctx,0x{a:08x}u,0x{w:08x}u'
        # Existing V1141's terminal call has already been patched.
        body=entry(handler)+label(call,branch)+T+SI
        body+=f'    undercover::wii::v672::before({arg(call,branch)},12u,1u);\n'
        body+=f'    ctx.pc = 0x{R:X}; fn_{R:X}(ctx);\n    if (ctx.pc != 0x{call+4:X}) return;\n'
        for i,w in enumerate(tail):
            pc=call+4+4*i
            body+=label(pc,w)+T+SI+f'    undercover::wii::v672::before({arg(pc,w)},0u,0u);\n'
        body+='}\n'
        body=patch_handler(body,call,branch,12,1,caller)
        (root/'output_0.cpp').write_text(body)
        body=entry(R)
        for i,w in enumerate(restore):
            pc=R+4*i;body+=label(pc,w)+T+f'    undercover::wii::v726::restore_before({arg(pc,w)});\n'+SI
        body+='}\n'
        (root/'output_1.cpp').write_text(patch_alias(body,R,restore))
        body=entry(D)+label(resume,W)+T+f'    undercover::wii::v726::resume({arg(resume,W)});\n'+SI+'}\n'
        (root/'output_2.cpp').write_text(patch_label(body,resume,W))
        for i in range(3,20):(root/f'output_{i}.cpp').write_text('// unused\n')
        (root/'main_output.cpp').write_text(''.join(f'case 0x{pc:X}: fn_{owner:X}(ctx); break;\n' for pc,owner in
            ((handler,handler),(R,R),(D,D),(resume,D))))
        return (call,R,resume,restore,tail,W,branch,h,d),([], (caller-4,),lanes,rd,wr,index),dest,D
    def run_install(self,root,data):
        ret,geom,_,D=data
        with patch.object(installer,'HANDLER',H),patch.object(installer,'DISPATCH',D), \
             patch.object(installer,'geometry_return',return_value=ret),patch.object(installer,'derive',return_value=geom):
            installer.install(b'',b'',root,Path(installer.__file__).parent)
    @staticmethod
    def snapshot(root):
        return {str(p.relative_to(root)):p.read_bytes() for p in root.rglob('*') if p.is_file()}
    def test_complete(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);data=self.fixture(root);before=self.snapshot(root)
            self.run_install(root,data);after=self.snapshot(root)
            for i,n in ((0,5),(1,16),(2,1)):
                src=after[f'output_{i}.cpp']
                self.assertEqual(src.count(b'++ctx.inst_count;'),n)
                self.assertEqual(src.count(b'v958::before(ctx,'),n)
            self.assertEqual(after['output_2.cpp'].count(b'postalarm_handler_dispatch_resume(ctx,'),1)
            self.assertEqual(len(set(after)-set(before)),1)
            self.assertIn(b'UNDERCOVER_V1145_PRIVATE_POSTALARM_HANDLER_RETURN 1',(data[2]/'v958_private_second_ack.h').read_bytes())
    def test_refused_trees(self):
        for fault in ('metadata','restore','dispatcher','owner','edge','tick','existing','mode'):
            with self.subTest(fault=fault),tempfile.TemporaryDirectory() as td:
                root=Path(td);data=self.fixture(root);dest=data[2]
                if fault=='metadata':
                    q=dest/'v919_private_handler_epilogue.h';q.write_text(q.read_text()+'// tamper\n')
                elif fault=='restore':
                    q=root/'output_1.cpp';q.write_text(q.read_text().replace('v868::restore_before','wrong',1))
                elif fault=='dispatcher':
                    q=root/'main_output.cpp';q.write_text('\n'.join(q.read_text().splitlines()[:-1]))
                elif fault=='owner':(root/'output_19.cpp').write_bytes((root/'output_1.cpp').read_bytes())
                elif fault=='edge':
                    q=root/'output_0.cpp';q.write_text(q.read_text().replace('ctx.pc =','ctx.fake_pc =',1))
                elif fault=='tick':
                    q=root/'output_2.cpp';q.write_text(q.read_text().replace(T,T+T,1))
                elif fault=='existing':(dest/'v1145_private_postalarm_handler_return.h').write_text('// existing\n')
                else:(dest/'v958_private_second_ack.h').write_text('// missing macro\n')
                before=self.snapshot(root)
                with self.assertRaises(ValueError):self.run_install(root,data)
                self.assertEqual(self.snapshot(root),before)

if __name__=='__main__':unittest.main()
