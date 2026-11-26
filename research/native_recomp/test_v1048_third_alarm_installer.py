import unittest,tempfile
from pathlib import Path
from unittest.mock import patch
import prepare_v1048_third_alarm as installer
from prepare_v1029_third_transfer import hook as transfer_hook
from prepare_v1048_third_alarm import hook,SI,verify_alarm_identity
from prepare_v789_alarm_suffix import patch_private
P=0x80004000;W=0x48000101
L=f'loc_{P:X}: ;\n    // 0x{P:08X}: {W:08X}\n    ++ctx.inst_count;\n'+SI
B=f'undercover::wii::v958::before(ctx,0x{P:08x}u,0x{W:08x}u,'
OLD=f'    undercover::wii::v786::before(ctx,0x{P:08x}u,0x{W:08x}u);\n'
class Hooks(unittest.TestCase):
    def test_shared(self):
        self.assertEqual(hook(L+'    '+B+'false);\n',P,W),L+'    '+B+'false);\n')
        for extra in ('','    '+B+'true);\n','    if(undercover::wii::v958::callback_active()) '+B+'false);\n'):
            got=hook(L+extra+OLD,P,W)
            self.assertEqual(got.count(SI),1)
            self.assertIn('third_alarm_active()',got)
            self.assertIn('if(!undercover::wii::v958::third_active()&&!undercover::wii::v958::third_alarm_active()) { '+OLD.strip()+' }',got)
            self.assertLess(got.index(SI),got.index('v958::before'))
        self.assertIn('else '+B+'true);',hook(L+'    '+B+'true);\n',P,W))
    def test_handoff_legacy_order(self):
        old=L+'    '+B+'true);\n'+OLD
        legacy=f'    undercover::wii::v768::before(ctx,0x{P:08x}u,0x{W:08x}u);\n'
        source=transfer_hook(old+legacy,P,W,'resume')
        out=hook(source,P,W,handoff=True)
        self.assertEqual(out.count('v958::before('),2)
        self.assertEqual(out.count(SI),1)
        self.assertEqual(out.count('third_alarm_active()) {'),2)
        self.assertIn('if(!undercover::wii::v958::third_active()) '+legacy.strip(),out)
        for mode in ('    '+B+'false);\n','    if(undercover::wii::v958::third_active()) '+B+'false);\n'):
            self.assertEqual(hook(L+mode,P,W,handoff=True),L+mode)
        with self.assertRaisesRegex(ValueError,'third alarm handoff hook'):
            hook(L+'    '+B+'true);\n',P,W,handoff=True)
    def test_composed_alarm_identity(self):
        base='#pragma once\nnamespace undercover::wii::v786 {\ninline constexpr unsigned marker=1;\n}\n'
        callback=(0x80006000,(0x60000000,0x4e800020),(0x80004000,0x80004004))
        composed=patch_private(base,*callback)
        verify_alarm_identity(composed,base,callback)
        for bad in (base,composed.replace('marker=1','marker=2'),
                    composed.replace('0x80006000u','0x80006004u'),
                    composed.replace('0x60000000u','0x60000001u'),
                    composed.replace('0x80004004u','0x80004008u'),
                    composed+'// unexpected\n'):
            with self.subTest(bad=bad):
                with self.assertRaisesRegex(ValueError,'third alarm identity'):
                    verify_alarm_identity(bad,base,callback)
    def test_refusals(self):
        for bad in (L+SI,L.replace(SI,''),L+'    '+B+'false);\n    '+B+'true);\n',
                    L+'    if(other()) '+B+'false);\n'):
            with self.assertRaises(ValueError):hook(bad,P,W)
class FullInstaller(unittest.TestCase):
    """Only owner extraction is mocked; real label/edge/entry audits run."""
    H=0x80004000
    C,D,R,T,U,K=(0x80005000+0x100*i for i in range(6))
    NOP=0x60000000
    BLR=0x4e800020
    @staticmethod
    def branch(pc,dst):
        return 0x48000001|((dst-pc)&0x03fffffc)
    def fixture(self,root):
        H,C,D,R,T,U,K=self.H,self.C,self.D,self.R,self.T,self.U,self.K
        bl=self.branch
        # Three earlier calls, transfer #4, alarm #5. The store is
        # independently authored so the real handler census accepts it.
        handler=[0x90010000,bl(H+4,D),bl(H+8,R),bl(H+12,T),bl(H+16,U),
                 self.NOP,bl(H+24,C),self.BLR]
        roots={C:[bl(C,D),bl(C+4,R),self.BLR],
               D:[self.NOP,self.BLR],R:[self.NOP,self.BLR],
               T:[bl(T,U),self.BLR],U:[self.BLR],K:[self.BLR]}
        edges=[(C,D),(C+4,R)]
        leaves=[(T,U)]
        base='#pragma once\nnamespace undercover::wii::v786 {\ninline constexpr unsigned marker=1;\n}\n'
        callback=(0x80007000,(self.NOP,self.BLR),(H+32,H+36))
        dest=root/'nWiiRuntime/include/undercover';dest.mkdir(parents=True)
        private=dest/'v958_private_second_ack.h'
        private.write_text('#define UNDERCOVER_V1028_PRIVATE_THIRD_ROUTE 1\n')
        prior=dest/'v786_private_alarm.h';prior.write_text(patch_private(base,*callback))
        allroots={H:handler,**roots}
        for idx,(a,words) in enumerate(allroots.items()):
            body=f'#include "runtime/cpu_context.h"\nvoid fn_{a:X}(CPUContext& ctx) {{\n'
            body+=f'    if (nwii::runtime::g_trace_calls && ctx.pc == 0x{a:X}) nwii::runtime::trace_call(0x{a:X}, ctx);\n'
            for i,w in enumerate(words):
                pc=a+4*i
                block=f'loc_{pc:X}: ;\n    // 0x{pc:08X}: {w:08X}\n    ++ctx.inst_count;\n'+SI
                current=f'    undercover::wii::v958::before(ctx,0x{pc:08x}u,0x{w:08x}u,'
                if a==H and pc==H+20:
                    block=transfer_hook(block+current+'true);\n',pc,w,'resume')
                elif a in (D,R,T,U):block+=current+'false);\n'
                elif a==H:block+=current+'true);\n'
                block+=f'    undercover::wii::v786::before(ctx,0x{pc:08x}u,0x{w:08x}u);\n'
                if w>>26==18 and w&3==1:
                    delta=((w&0x03fffffc)^0x02000000)-0x02000000
                    dst=pc+delta
                    block+=f'    ctx.pc = 0x{dst:X}; fn_{dst:X}(ctx);\n    if (ctx.pc != 0x{pc+4:X}) return;\n'
                body+=block
            (root/f'output_{idx}.cpp').write_text(body+'}\n')
        for i in range(len(allroots),20):(root/f'output_{i}.cpp').write_text('// unused shard\n')
        (root/'main_output.cpp').write_text('extern "C" void run_game(CPUContext& ctx) {\n'+''.join(f'case 0x{a:X}: fn_{a:X}(ctx); break;\n' for a in allroots)+'}\n')
        # Synthetic geometry: the production installer's native edge
        # and all emitted label checks remain completely unmocked.
        render=(roots,C,D,R,T,U,K,H+24,edges,leaves,base)
        return render,handler,callback,private,prior
    def run_install(self,root,fixture):
        render,handler,callback,_,_=fixture
        with patch.multiple(installer,HANDLER=self.H), \
             patch.object(installer,'render',return_value=render), \
             patch.object(installer,'geometry',return_value=(len(handler),)), \
             patch.object(installer,'exact',return_value=handler), \
             patch.object(installer,'callback_expectations',return_value=callback):
            installer.install(b'',b'',root,Path(installer.__file__).parent)
    @staticmethod
    def snapshot(root):
        return {p.relative_to(root):p.read_bytes() for p in root.rglob('*') if p.is_file()}
    def test_complete_composition(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);fixture=self.fixture(root)
            before=self.snapshot(root);self.run_install(root,fixture)
            after=self.snapshot(root)
            self.assertEqual(set(after)-set(before),{Path('nWiiRuntime/include/undercover/wii_third_alarm_suffix_v1047.h')})
            self.assertEqual(fixture[4].read_bytes(),before[fixture[4].relative_to(root)])
            self.assertIn('UNDERCOVER_V1048_PRIVATE_THIRD_ALARM 1',fixture[3].read_text())
            out=(root/'output_0.cpp').read_text()
            # The handoff resume has already been observed by the transfer
            # route; no third-alarm hook is allowed to consume its tick twice.
            a=out.index('loc_80004014:');b=out.index('loc_80004018:')
            self.assertEqual(out[a:b].count('v958::before('),2)
            self.assertEqual(out[a:b].count('third_alarm_active()) {'),1)
            self.assertIn('third_alarm_active()',out[b:])
            self.assertEqual(out.count('++ctx.inst_count;'),len(fixture[1]))
    def test_fail_closed_no_partial_edits(self):
        for fault in ('identity','duplicate','label','tick','edge','dispatch'):
            with self.subTest(fault=fault),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);fixture=self.fixture(root)
                if fault=='identity':fixture[4].write_text(fixture[4].read_text()+'// tamper\n')
                elif fault=='duplicate':(root/'output_19.cpp').write_text((root/'output_1.cpp').read_text())
                elif fault=='dispatch':
                    f=root/'main_output.cpp';f.write_text(f.read_text().replace('fn_5000','fn_5010').replace('fn_80005000','fn_80005004'))
                else:
                    f=root/'output_1.cpp';s=f.read_text()
                    if fault=='label':s=s.replace('60000000','60000001') if '60000000' in s else s.replace('4E800020','4E800021')
                    elif fault=='tick':s=s.replace(SI,'',1)
                    else:s=s.replace('fn_80005100(ctx);','fn_80005104(ctx);')
                    f.write_text(s)
                before=self.snapshot(root)
                with self.assertRaises(ValueError):self.run_install(root,fixture)
                self.assertEqual(self.snapshot(root),before)
if __name__=='__main__':unittest.main()

