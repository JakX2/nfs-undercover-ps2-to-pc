import unittest,tempfile
from pathlib import Path
from unittest.mock import patch
import prepare_v1097_after_alarm as installer
from prepare_v789_alarm_suffix import patch_private
from prepare_v807_callback_prefix import render
from collect_third_alarm_suffix_v1044 import collect_after_alarm
from prepare_v1097_after_alarm import patch_label,ACTIVE,OLD_ACTIVE,OLD_THIRD,CALLBACK,OLD_SUPPRESS,NEW_SUPPRESS,SI,suffix_line
P=0x80004000;W=0x60000000
L=f'loc_{P:X}: ;\n    // 0x{P:08X}: {W:08X}\n    ++ctx.inst_count;\n'+SI
B=f'undercover::wii::v958::before(ctx,0x{P:08x}u,0x{W:08x}u,'
CURRENT='    '+B+'false);\n'
GUARD='    '+B+'true);\n'
LEGACY=f'undercover::wii::v786::before(ctx,0x{P:08x}u,0x{W:08x}u);'
def conditional(p):return '    if('+p+') '+CURRENT.lstrip()
class Hooks(unittest.TestCase):
    def test_exact_existing_shapes(self):
        for old,expected in (
            ('',conditional(ACTIVE)),
            (CURRENT,CURRENT),
            (GUARD,conditional(ACTIVE)+'    else '+GUARD.lstrip()),
            (conditional(CALLBACK),conditional(CALLBACK+'||'+ACTIVE)),
            (conditional(OLD_ACTIVE),conditional(OLD_ACTIVE+'||'+ACTIVE)),
            (conditional(OLD_ACTIVE+'||'+CALLBACK),conditional(OLD_ACTIVE+'||'+CALLBACK+'||'+ACTIVE)),
            (conditional(OLD_ACTIVE)+'    else '+GUARD.lstrip(),conditional(OLD_ACTIVE+'||'+ACTIVE)+'    else '+GUARD.lstrip())):
            with self.subTest(shape=old):
                self.assertEqual(patch_label(L+old,P,W),L+expected)
    def test_legacy_order(self):
        old=OLD_SUPPRESS+LEGACY+' }\n'
        got=patch_label(L+old+conditional(OLD_ACTIVE)+old,P,W)
        self.assertEqual(got,L+NEW_SUPPRESS+LEGACY+' }\n'+conditional(OLD_ACTIVE+'||'+ACTIVE)+NEW_SUPPRESS+LEGACY+' }\n')
        for extra in ('    '+LEGACY+'\n','    if(!'+CALLBACK+') '+LEGACY+'\n'):
            self.assertIn('    if(!'+ACTIVE+') { '+extra.strip()+' }\n',patch_label(L+CURRENT+extra,P,W))
    def test_refusals(self):
        for bad in (L+SI,L.replace(SI,''),L+CURRENT+CURRENT,L+conditional('untrusted()'),
                    L+conditional(OLD_ACTIVE)+'    unrelated();\n    else '+GUARD.lstrip(),
                    L+conditional(OLD_THIRD),L+conditional(ACTIVE),
                    L.replace(SI,CURRENT+SI),L.replace('++ctx.inst_count;',''),
                    L.replace('60000000','60000001')):
            with self.subTest(shape=bad):
                with self.assertRaises(ValueError):patch_label(bad,P,W)
    def test_metadata(self):
        rows={P+4:(0x4e800421,6,2),P:(W,0,0)}
        self.assertEqual(suffix_line('third_postalarm_suffix',rows),
            'inline constexpr std::array<HandlerSuffixLabel,2> third_postalarm_suffix{{HandlerSuffixLabel{0x80004000u,0x60000000u,0u,0u},HandlerSuffixLabel{0x80004004u,0x4e800421u,6u,2u}}};\n')
class Tree(unittest.TestCase):
    H=0x80004000;C=0x80005000;S=0x80006000;A=0x80007000
    NOP=0x60000000;BLR=0x4e800020;BCTRL=0x4e800421
    @staticmethod
    def branch(a,b):return 0x48000001|((b-a)&0x03fffffc)
    def fixture(self,root):
        H,C,S,A=self.H,self.C,self.S,self.A
        bl=self.branch
        # Independently authored call census: four calls, transfer resume,
        # fifth alarm call, then the sixth and eleventh indirect sites.
        handler=[bl(H+4*i,A) for i in range(4)]+[self.NOP,bl(H+20,A),self.NOP,self.BCTRL]
        handler += [bl(H+4*i,A) for i in range(8,12)]+[self.BCTRL,self.BLR]
        prefix=[0x9421ffc0,0x7c0802a6,0x90010044,0x39610040,bl(C+16,S),self.NOP]
        save=[self.NOP]*6+[self.BLR]
        words=tuple(prefix+[self.BLR]);sites=(H+28,H+48)
        prior=collect_after_alarm(H,handler,handler,set(),H+16)
        dest=root/'nWiiRuntime/include/undercover';dest.mkdir(parents=True)
        host=Path(installer.__file__).parent
        base='#pragma once\nnamespace undercover::wii::v786 {\ninline constexpr unsigned marker=1;\n}\n'
        (dest/'v786_private_alarm.h').write_text(patch_private(base,C,words,sites))
        (dest/'v807_private_callback_prefix.h').write_text(render(C,S,prefix,save))
        for name in ('wii_third_alarm_suffix_v1047.h','wii_callback_prefix_v800.h'):
            (dest/name).write_bytes((host/name).read_bytes())
        private=dest/'v958_private_second_ack.h'
        private.write_text('#define UNDERCOVER_V1048_PRIVATE_THIRD_ALARM 1\nnamespace undercover::wii::v958 {\n'
                           +f'inline constexpr uint32_t transfer_callback=0x{C:08x}u;\n'
                           +suffix_line('third_alarm_suffix',prior)+'}\n')
        native={H:handler,C:prefix,S:save,A:[self.BLR]}
        for idx,(addr,ws) in enumerate(native.items()):
            body=f'#include "runtime/cpu_context.h"\nvoid fn_{addr:X}(CPUContext& ctx) {{\n'
            body+=f'    if (nwii::runtime::g_trace_calls && ctx.pc == 0x{addr:X}) nwii::runtime::trace_call(0x{addr:X}, ctx);\n'
            for i,w in enumerate(ws):
                pc=addr+4*i
                body+=f'loc_{pc:X}: ;\n    // 0x{pc:08X}: {w:08X}\n    ++ctx.inst_count;\n'+SI
                call=f'undercover::wii::v958::before(ctx,0x{pc:08x}u,0x{w:08x}u,'
                if addr==H and pc==H+24:
                    body+='    if('+OLD_ACTIVE+') '+call+'false);\n'
                    body+=OLD_SUPPRESS+f'undercover::wii::v786::before(ctx,0x{pc:08x}u,0x{w:08x}u); }}\n'
                elif addr==H:body+='    '+call+'true);\n'
                elif addr in (C,S):body+='    if('+CALLBACK+') '+call+'false);\n'
                if w>>26==18 and w&3==1:
                    delta=((w&0x03fffffc)^0x02000000)-0x02000000;target=pc+delta
                    body+=f'    ctx.pc = 0x{target:X}; fn_{target:X}(ctx);\n    if (ctx.pc != 0x{pc+4:X}) return;\n'
                elif w==self.BCTRL:
                    body+=f'    ctx.lr = 0x{pc+4:X};\n    if (ctx.ctr) {{ ctx.pc = ctx.ctr; return; }}\n'
            (root/f'output_{idx}.cpp').write_text(body+'}\n')
        for i in range(len(native),20):(root/f'output_{i}.cpp').write_text('// unused shard\n')
        (root/'main_output.cpp').write_text('extern "C" void run_game(CPUContext& ctx) {\n'+''.join(
            f'case 0x{addr:X}: fn_{addr:X}(ctx); break;\n' for addr in native)+'}\n')
        return handler,({C:prefix+[self.BLR],S:save},C,S,C+16,0,0),(C,words,sites),base,private
    def install(self,root,fixture):
        handler,plan,callback,base,_=fixture
        with patch.multiple(installer,HANDLER=self.H), \
             patch.object(installer,'alarm_render',return_value=({},0,0,0,0,0,0,self.H+20,[],[],base)), \
             patch.object(installer,'geometry',return_value=(len(handler),)), \
             patch.object(installer,'exact',return_value=handler), \
             patch.object(installer,'plan',return_value=plan), \
             patch.object(installer,'expectations',return_value=callback):
            installer.install(b'',b'',root,Path(installer.__file__).parent)
    @staticmethod
    def snapshot(root):return {p.relative_to(root):p.read_bytes() for p in root.rglob('*') if p.is_file()}
    def test_install_composition(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);f=self.fixture(root);before=self.snapshot(root);self.install(root,f)
            after=self.snapshot(root)
            self.assertEqual(set(before),set(after))
            changed={p for p in before if before[p]!=after[p]}
            self.assertEqual(changed,{Path('output_0.cpp'),Path('output_1.cpp'),Path('output_2.cpp'),
                                    f[-1].relative_to(root)})
            self.assertIn('UNDERCOVER_V1095_PRIVATE_AFTER_ALARM 1',f[-1].read_text())
            self.assertIn(NEW_SUPPRESS,(root/'output_0.cpp').read_text())
            for p in (root/'output_0.cpp',root/'output_1.cpp',root/'output_2.cpp'):
                self.assertEqual(p.read_text().count('++ctx.inst_count;'),before[p.relative_to(root)].count(b'++ctx.inst_count;'))
    def test_fail_closed(self):
        for fault in ('header','callback','metadata','owner','label','tick','edge','indirect','dispatch'):
            with self.subTest(fault=fault),tempfile.TemporaryDirectory() as td:
                root=Path(td);f=self.fixture(root);private=f[-1]
                if fault=='header':p=private.parent/'v786_private_alarm.h';p.write_text(p.read_text()+'// tamper\n')
                elif fault=='callback':p=private.parent/'v807_private_callback_prefix.h';p.write_text(p.read_text()+'// tamper\n')
                elif fault=='metadata':private.write_text(private.read_text().replace('third_alarm_suffix','other_suffix'))
                elif fault=='owner':(root/'output_19.cpp').write_text((root/'output_1.cpp').read_text())
                elif fault=='dispatch':
                    p=root/'main_output.cpp';p.write_text(p.read_text().replace('fn_80005000(ctx)','fn_80005004(ctx)'))
                elif fault=='indirect':
                    p=root/'output_0.cpp';p.write_text(p.read_text().replace('ctx.pc = ctx.ctr; return;','ctx.pc = ctx.ctr+4; return;',1))
                else:
                    p=root/'output_1.cpp';s=p.read_text()
                    if fault=='label':s=s.replace('9421FFC0','9421FFC1')
                    elif fault=='tick':s=s.replace(SI,'',1)
                    else:s=s.replace('fn_80006000(ctx);','fn_80006004(ctx);')
                    p.write_text(s)
                before=self.snapshot(root)
                with self.assertRaises(ValueError):self.install(root,f)
                self.assertEqual(self.snapshot(root),before)
if __name__=='__main__':unittest.main()

