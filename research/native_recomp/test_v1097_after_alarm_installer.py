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
            (conditional(OLD_ACTIVE)+'    else '+GUARD.lstrip(),conditional(OLD_ACTIVE+'||'+ACTIVE)+'    else '+GUARD.lstrip()),
            (conditional(OLD_THIRD),conditional(OLD_THIRD+'||'+ACTIVE)),
            (conditional(OLD_THIRD)+'    else '+GUARD.lstrip(),conditional(OLD_THIRD+'||'+ACTIVE)+'    else '+GUARD.lstrip()),
            (conditional(OLD_THIRD)+conditional(CALLBACK),conditional(OLD_THIRD+'||'+CALLBACK+'||'+ACTIVE))):
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
                    L+conditional(OLD_THIRD)+'    unrelated();\n'+conditional(CALLBACK),
                    L+conditional(OLD_THIRD)+conditional(OLD_THIRD),L+conditional(ACTIVE),
                    L.replace(SI,CURRENT+SI),L.replace('++ctx.inst_count;',''),
                    L.replace('60000000','60000001')):
            with self.subTest(shape=bad):
                with self.assertRaises(ValueError):patch_label(bad,P,W)
    def test_real_predecessor_save_hook(self):
        from prepare_v1029_third_transfer import hook
        from prepare_v1106_postalarm_time import verify_resume
        old=hook(L+conditional(CALLBACK),P,W,'body')
        self.assertEqual(old,L+conditional(OLD_THIRD)+conditional(CALLBACK))
        new=patch_label(old,P,W)
        self.assertEqual(new,L+conditional(OLD_THIRD+'||'+CALLBACK+'||'+ACTIVE))
        self.assertEqual(new.count('v958::before(ctx,'),1)
        verify_resume(new,P,W)
        old=hook(L,P,W,'body')
        new=patch_label(old,P,W)
        self.assertEqual(new,L+conditional(OLD_THIRD+'||'+ACTIVE))
        verify_resume(new,P,W)
        old=hook(L+GUARD,P,W,'resume')
        new=patch_label(old,P,W)
        self.assertEqual(new,L+conditional(OLD_THIRD+'||'+ACTIVE)+'    else '+GUARD.lstrip())
        verify_resume(new,P,W)
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
        handler=[bl(H+4*i,A) for i in range(4)]+[0x90010008,bl(H+20,A),self.NOP,self.BCTRL]
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
                elif addr==C:body+='    if('+CALLBACK+') '+call+'false);\n'
                elif addr==S:body+='    if('+OLD_THIRD+') '+call+'false);\n'
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
        reasons={'header':'third alarm identity','callback':'postalarm identity',
                 'metadata':'postalarm mode','owner':'postalarm owner',
                 'label':'native IPC label identity','tick':'postalarm tick',
                 'edge':'helper direct native call','indirect':'indirect dispatch',
                 'dispatch':'native IPC dispatch'}
        for fault,reason in reasons.items():
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
                with self.assertRaises(ValueError) as caught:self.install(root,f)
                self.assertEqual(str(caught.exception),reason)
                self.assertEqual(self.snapshot(root),before)

class TimeTree(unittest.TestCase):
    def fixture(self,root):
        import prepare_v1106_postalarm_time as time
        from prepare_v813_callback_time import render as render_time
        prior=Tree();f=prior.fixture(root);H,C,S,A=prior.H,prior.C,prior.S,prior.A
        T,D,U,R=0x80008000,0x80009000,0x8000a000,0x8000b000
        host=Path(time.__file__).parent
        prefix=f[1][0][C][:-1];save=f[1][0][S];resume=C+20;ts=C+64
        code=prefix+[prior.NOP]*10+[prior.branch(ts,T),prior.NOP]
        full=tuple(code+[prior.BLR]+[prior.NOP]*(172-len(code)-1));sites=f[2][2]
        dest=f[-1].parent
        (dest/'v786_private_alarm.h').write_text(patch_private(f[3],C,full,sites))
        f=(f[0],f[1],(C,full,sites),f[3],f[4])
        prior.install(root,f)
        system=[prior.NOP]*24+[prior.BLR]
        for i,a in ((1,D),(4,U),(7,R)):system[i]=prior.branch(T+4*i,a)
        leaves_words={D:[prior.NOP]*5+[prior.BLR],U:[prior.NOP]*7+[prior.BLR],R:[prior.NOP]*5+[prior.BLR]}
        leaves=[(T+4*i,a,a+4*len(leaves_words[a]),system[i],kind,leaves_words[a])
                for kind,(i,a) in enumerate(((1,D),(4,U),(7,R)),1)]
        roots={H:f[0],C:code+[prior.BLR],S:save,T:system,**leaves_words}
        (dest/'wii_callback_time_v810.h').write_bytes((host/'wii_callback_time_v810.h').read_bytes())
        (dest/'v813_private_callback_time.h').write_text(render_time(C,ts,code[5:],T,system,leaves))
        def labels(addr,words,shared,start=0):
            body=''
            for i in range(start,len(words)):
                pc=addr+4*i;w=words[i]
                body+=f'loc_{pc:X}: ;\n    // 0x{pc:08X}: {w:08X}\n    ++ctx.inst_count;\n'+SI
                if shared:body+=f'    undercover::wii::v958::before(ctx,0x{pc:08x}u,0x{w:08x}u,false);\n'
                body+=f'    undercover::wii::v813::before(ctx,0x{pc:08x}u,0x{w:08x}u);\n'
                if w>>26==18 and w&3==1:
                    target=pc+(((w&0x03fffffc)^0x02000000)-0x02000000)
                    body+=f'    ctx.pc = 0x{target:X}; fn_{target:X}(ctx);\n    if (ctx.pc != 0x{pc+4:X}) return;\n'
            return body
        p=root/'output_1.cpp';s=p.read_text()
        p.write_text(s[:-2]+labels(C,code,False,6)+'}\n')
        for idx,a in enumerate((T,D,U,R),4):
            s='#include "runtime/cpu_context.h"\n'
            s+=f'void fn_{a:X}(CPUContext& ctx) {{\n    if (nwii::runtime::g_trace_calls && ctx.pc == 0x{a:X}) nwii::runtime::trace_call(0x{a:X}, ctx);\n'
            (root/f'output_{idx}.cpp').write_text(s+labels(a,roots[a],True)+'}\n')
        p=root/'main_output.cpp';s=p.read_text()
        p.write_text(s[:-2]+''.join(f'case 0x{a:X}: fn_{a:X}(ctx); break;\n' for a in (T,D,U,R))+'}\n')
        return ((roots,C,S,C+16,0,0),T,D,U,R,ts,leaves),(C,full,sites),f[-1]
    def install(self,root,f):
        import prepare_v1106_postalarm_time as time
        q,callback,_=f
        with patch.object(time,'plan',return_value=q),patch.object(time,'expectations',return_value=callback), \
             patch.object(time,'exact',return_value=callback[1]):
            time.install(b'',b'',root,Path(time.__file__).parent)
    def test_time_tree(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);f=self.fixture(root);before=Tree.snapshot(root);self.install(root,f);after=Tree.snapshot(root)
            self.assertEqual(set(before),set(after))
            self.assertEqual({p for p in before if before[p]!=after[p]},
                             {Path(f'output_{i}.cpp') for i in (1,4,5,6,7)}|{f[-1].relative_to(root)})
            self.assertIn('UNDERCOVER_V1103_PRIVATE_POSTALARM_TIME 1',f[-1].read_text())
            for i in (1,4,5,6,7):
                p=Path(f'output_{i}.cpp')
                self.assertEqual(before[p].count(b'++ctx.inst_count;'),after[p].count(b'++ctx.inst_count;'))
            self.assertEqual((root/'output_1.cpp').read_text().count('v958::before(ctx,0x80005014u,'),1)
    def test_time_tree_refusals(self):
        reasons={'resume':'postalarm time resume','header':'postalarm time identity','metadata':'postalarm time metadata',
                 'owner':'postalarm time owner','edge':'helper direct native call','label':'native IPC label identity',
                 'tick':'postalarm tick','dispatch':'native IPC dispatch'}
        for fault,reason in reasons.items():
            with self.subTest(fault=fault),tempfile.TemporaryDirectory() as td:
                root=Path(td);f=self.fixture(root);private=f[-1]
                if fault=='header':
                    p=private.parent/'v813_private_callback_time.h';p.write_text(p.read_text()+'// tamper\n')
                elif fault=='metadata':private.write_text(private.read_text().replace('third_postalarm_words','other_words'))
                elif fault=='owner':(root/'output_19.cpp').write_bytes((root/'output_4.cpp').read_bytes())
                elif fault=='dispatch':
                    p=root/'main_output.cpp';p.write_text(p.read_text().replace('fn_80008000(ctx)','fn_80008004(ctx)'))
                elif fault=='resume':
                    p=root/'output_1.cpp';p.write_text(p.read_text().replace('v958::before(ctx,0x80005014u,','v958::other(ctx,0x80005014u,'))
                else:
                    p=root/'output_4.cpp';s=p.read_text()
                    if fault=='edge':s=s.replace('fn_80009000(ctx);','fn_80009004(ctx);')
                    elif fault=='label':s=s.replace('// 0x80008000: 60000000','// 0x80008000: 60000001')
                    else:s=s.replace(SI,'',1)
                    p.write_text(s)
                before=Tree.snapshot(root)
                with self.assertRaises(ValueError) as caught:self.install(root,f)
                self.assertEqual(str(caught.exception),reason)
                self.assertEqual(Tree.snapshot(root),before)


class FrontierTree(unittest.TestCase):
    def fixture(self,root):
        import prepare_v1113_postalarm_frontier as frontier
        from prepare_v831_callback_frontier import render as render_frontier
        time=TimeTree();f=time.fixture(root)
        q,callback,private=f;base,T,D,U,R,ts,leaves=q;roots,C,S,site,_,_=base
        resume=ts+4;A=0x8000c000;B=0x8000d000;host=Path(frontier.__file__).parent
        old_words=list(callback[1]);seen=list(range(resume,resume+27*4,4))
        stops={seen[24]:(3,A),seen[26]:(5,B)}
        for pc in seen:
            old_words[(pc-C)//4]=Tree.branch(pc,stops[pc][1]) if pc in stops else Tree.NOP
        full=tuple(old_words)
        # Update only independently authored fixture code and private
        # expectations before running the previous installer.
        old_row=f'inline constexpr std::array<uint32_t,{len(callback[1])}> third_postalarm_words{{'+frontier.fmt(callback[1])+'};\n'
        new_row=f'inline constexpr std::array<uint32_t,{len(full)}> third_postalarm_words{{'+frontier.fmt(full)+'};\n'
        private.write_text(private.read_text().replace(old_row,new_row))
        callback=(C,full,callback[2])
        time.install(root,(q,callback,private))
        p=root/'output_1.cpp';s=p.read_text();extra=''
        for pc in seen[1:]:
            w=full[(pc-C)//4]
            extra+=f'loc_{pc:X}: ;\n    // 0x{pc:08X}: {w:08X}\n    ++ctx.inst_count;\n'+SI
            if pc in stops:
                dst=stops[pc][1]
                extra+=f'    ctx.pc = 0x{dst:X}; fn_{dst:X}(ctx);\n    if (ctx.pc != 0x{pc+4:X}) return;\n'
        p.write_text(s[:-2]+extra+'}\n')
        dest=private.parent
        (dest/'wii_callback_frontier_v829.h').write_bytes((host/'wii_callback_frontier_v829.h').read_bytes())
        expected={pc:(C,full[(pc-C)//4]) for pc in seen}
        (dest/'v831_private_callback_frontier.h').write_text(render_frontier(C,resume,expected,stops))
        return (q,seen,stops,A,B),callback,private
    def install(self,root,f):
        import prepare_v1113_postalarm_frontier as frontier
        q,callback,_=f
        with patch.object(frontier,'plan',return_value=q),patch.object(frontier,'expectations',return_value=callback), \
             patch.object(frontier,'exact',return_value=callback[1]):
            frontier.install(b'',b'',root,Path(frontier.__file__).parent)
    def test_frontier_tree(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);f=self.fixture(root);before=Tree.snapshot(root);self.install(root,f);after=Tree.snapshot(root)
            self.assertEqual(set(before),set(after))
            self.assertEqual({p for p in before if before[p]!=after[p]},{Path('output_1.cpp'),f[-1].relative_to(root)})
            self.assertIn('UNDERCOVER_V1111_PRIVATE_POSTALARM_FRONTIER 1',f[-1].read_text())
            p=Path('output_1.cpp')
            self.assertEqual(before[p].count(b'++ctx.inst_count;'),after[p].count(b'++ctx.inst_count;'))
            self.assertEqual(after[p].count(b'v958::before(ctx,0x80005044u,'),1)
    def test_frontier_tree_refusals(self):
        reasons={'header':'postalarm frontier identity','metadata':'postalarm frontier metadata','owner':'postalarm frontier owner',
                 'edge':'helper direct native call','label':'native IPC label identity','tick':'postalarm tick',
                 'resume':'postalarm time resume','dispatch':'native IPC dispatch'}
        for fault,reason in reasons.items():
            with self.subTest(fault=fault),tempfile.TemporaryDirectory() as td:
                root=Path(td);f=self.fixture(root);private=f[-1];p=root/'output_1.cpp'
                if fault=='header':
                    h=private.parent/'v831_private_callback_frontier.h';h.write_text(h.read_text()+'// tamper\n')
                elif fault=='metadata':private.write_text(private.read_text().replace('third_postalarm_words','other_words'))
                elif fault=='owner':(root/'output_19.cpp').write_bytes(p.read_bytes())
                elif fault=='dispatch':
                    p=root/'main_output.cpp';p.write_text(p.read_text().replace('fn_80005000(ctx)','fn_80005004(ctx)'))
                else:
                    s=p.read_text()
                    if fault=='edge':s=s.replace('fn_8000C000(ctx);','fn_8000C004(ctx);')
                    elif fault=='label':s=s.replace('// 0x80005048: 60000000','// 0x80005048: 60000001')
                    elif fault=='resume':s=s.replace('v958::before(ctx,0x80005044u,','v958::other(ctx,0x80005044u,')
                    else:
                        marker='loc_80005048: ;\n    // 0x80005048: 60000000\n    ++ctx.inst_count;\n'
                        s=s.replace(marker+SI,marker)
                    p.write_text(s)
                before=Tree.snapshot(root)
                with self.assertRaises(ValueError) as caught:self.install(root,f)
                self.assertEqual(str(caught.exception),reason)
                self.assertEqual(Tree.snapshot(root),before)


class WirelessTree(unittest.TestCase):
    C,A,B,U,D,R,L=0x80005000,0x80008000,0x80009000,0x8000a000,0x8000b000,0x8000c000,0x8000d000
    def fixture(self,root):
        import prepare_v1119_postalarm_wireless as w
        C,A,B,U,D,R,L=self.C,self.A,self.B,self.U,self.D,self.R,self.L
        N,BRET=Tree.NOP,Tree.BLR;bl=Tree.branch
        roots={A:[bl(A,U),BRET]+[N]*37,B:[BRET]+[N]*29,
               U:[bl(U,D),bl(U+4,R),BRET]+[N]*181,D:[BRET]+[N]*4,R:[BRET]+[N]*8,L:[BRET]}
        seen=list(range(C+68,C+68+27*4,4));stops={seen[23]:(3,A),seen[26]:(5,B)}
        original=[N]*172
        for pc,(_,dst) in stops.items():original[(pc-C)//4]=bl(pc,dst)
        original[-1]=BRET
        original=tuple(original)
        q=(({D:roots[D],R:roots[R]},C,C+0x1000,C+16,0,0),C+0x2000,D,C+0x3000,R,C+64,[])
        fp=(q,seen,stops,A,B);wp=(roots,A,B,U,L,(L,));cb=(C,original,(0x80004000,0x80004004))
        dest=root/'nWiiRuntime/include/undercover';dest.mkdir(parents=True)
        host=Path(w.__file__).parent
        private=dest/'v958_private_second_ack.h'
        private.write_text('#define UNDERCOVER_V1111_PRIVATE_POSTALARM_FRONTIER 1\n'
                           +f'inline constexpr uint32_t transfer_callback=0x{C:08x}u;\n'
                           +f'inline constexpr std::array<uint32_t,172> third_postalarm_words{{'+w.fmt(original)+'};\n')
        for name in ('wii_callback_frontier_v829.h','wii_wireless_wrapper_v844.h','wii_third_alarm_suffix_v1047.h'):
            (dest/name).write_bytes((host/name).read_bytes())
        (dest/'v831_private_callback_frontier.h').write_text(w.render_frontier(C,C+68,{pc:(C,original[(pc-C)//4]) for pc in seen},stops))
        edges=[(pc,original[(pc-C)//4],original[(pc+4-C)//4],o) for pc,(o,_) in sorted(stops.items())]
        (dest/'v847_private_wireless_wrapper.h').write_text(w.render(roots,(A,B,U,D,R),edges,L,BRET))
        native={C:{pc:original[(pc-C)//4] for pc in set(seen)|{pc+4 for pc in stops}}}
        native.update({a:{pc:ws[(pc-a)//4] for pc in w.reachable(a,ws)} for a,ws in roots.items()})
        for idx,(a,rows) in enumerate(native.items()):
            s=f'#include "runtime/cpu_context.h"\nvoid fn_{a:X}(CPUContext& ctx) {{\n'
            s+=f'    if (nwii::runtime::g_trace_calls && ctx.pc == 0x{a:X}) nwii::runtime::trace_call(0x{a:X}, ctx);\n'
            for pc,word in sorted(rows.items()):
                s+=f'loc_{pc:X}: ;\n    // 0x{pc:08X}: {word:08X}\n    ++ctx.inst_count;\n'+SI
                if a in (D,R) or a==C and pc in seen:
                    s+=f'    if({ACTIVE}) undercover::wii::v958::before(ctx,0x{pc:08x}u,0x{word:08x}u,false);\n'
                if word>>26==18 and word&3==1:
                    dst=pc+(((word&0x03fffffc)^0x02000000)-0x02000000)
                    s+=f'    ctx.pc = 0x{dst:X}; fn_{dst:X}(ctx);\n    if (ctx.pc != 0x{pc+4:X}) return;\n'
            (root/f'output_{idx}.cpp').write_text(s+'}\n')
        for i in range(len(native),20):(root/f'output_{i}.cpp').write_text('// unused shard\n')
        (root/'main_output.cpp').write_text('extern "C" void run_game(CPUContext& ctx) {\n'+''.join(
            f'case 0x{a:X}: fn_{a:X}(ctx); break;\n' for a in native)+'}\n')
        return fp,wp,cb,private
    def install(self,root,f):
        import prepare_v1119_postalarm_wireless as w
        fp,wp,cb,_=f
        with patch.multiple(w,DISABLE=self.D,RESTORE=self.R),patch.object(w,'frontier_plan',return_value=fp), \
             patch.object(w,'wrapper_plan',return_value=wp),patch.object(w,'expectations',return_value=cb), \
             patch.object(w,'exact',side_effect=lambda d,e,a,n:cb[1] if a==self.C else (Tree.BLR,)):
            w.install(b'',b'',root,Path(w.__file__).parent)
    def test_wireless_tree(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);f=self.fixture(root);before=Tree.snapshot(root);self.install(root,f);after=Tree.snapshot(root)
            self.assertEqual(set(before),set(after))
            self.assertEqual({p for p in before if before[p]!=after[p]},
                             {Path(f'output_{i}.cpp') for i in (0,1,2,3)}|{f[-1].relative_to(root)})
            self.assertIn('UNDERCOVER_V1118_PRIVATE_POSTALARM_WIRELESS 1',f[-1].read_text())
            for i in range(7):
                p=Path(f'output_{i}.cpp')
                self.assertEqual(before[p].count(b'++ctx.inst_count;'),after[p].count(b'++ctx.inst_count;'))
            self.assertEqual(after[Path('output_0.cpp')].count(b'v958::before(ctx,'),28)
    def test_wireless_tree_refusals(self):
        reasons={'header':'postalarm wireless identity','metadata':'postalarm wireless metadata',
                 'owner':'postalarm wireless owner','edge':'helper direct native call','label':'native IPC label identity',
                 'tick':'postalarm tick','shared':'postalarm time resume','dispatch':'native IPC dispatch','lock':'native IPC label identity'}
        for fault,reason in reasons.items():
            with self.subTest(fault=fault),tempfile.TemporaryDirectory() as td:
                root=Path(td);f=self.fixture(root);private=f[-1]
                if fault=='header':
                    p=private.parent/'v847_private_wireless_wrapper.h';p.write_text(p.read_text()+'// tamper\n')
                elif fault=='metadata':private.write_text(private.read_text().replace('third_postalarm_words','other_words'))
                elif fault=='owner':(root/'output_19.cpp').write_bytes((root/'output_1.cpp').read_bytes())
                elif fault=='dispatch':
                    p=root/'main_output.cpp';p.write_text(p.read_text().replace('fn_80008000(ctx)','fn_80008004(ctx)'))
                elif fault=='shared':
                    p=root/'output_4.cpp';p.write_text(p.read_text().replace('v958::before','v958::other'))
                elif fault=='lock':
                    p=root/'output_6.cpp';p.write_text(p.read_text().replace('4E800020','4E800021'))
                else:
                    p=root/'output_1.cpp';s=p.read_text()
                    if fault=='edge':s=s.replace('fn_8000A000(ctx);','fn_8000A004(ctx);')
                    elif fault=='label':s=s.replace('4E800020','4E800021')
                    else:s=s.replace(SI,'',1)
                    p.write_text(s)
                before=Tree.snapshot(root)
                with self.assertRaises(ValueError) as caught:self.install(root,f)
                self.assertEqual(str(caught.exception),reason)
                self.assertEqual(Tree.snapshot(root),before)


class SuffixTree(unittest.TestCase):
    C,A,B,R=0x80005000,0x80008000,0x80009000,0x8000a000
    def fixture(self,root):
        import prepare_v1124_postalarm_suffix as s
        C,A,B,R=self.C,self.A,self.B,self.R
        prior=list(range(C+68,C+68+27*4,4));frontier={prior[23]:(3,A),prior[26]:(5,B)}
        resume=prior[23]+4
        seen=[resume,resume+4]+list(range(C+180,C+180+19*4,4))
        stops={seen[-2]:(4,2,None),seen[-1]:(13,1,R)}
        code=[Tree.NOP]*172
        for pc,(_,dst) in frontier.items():code[(pc-C)//4]=Tree.branch(pc,dst)
        code[(seen[-2]-C)//4]=0x4e800421;code[(seen[-1]-C)//4]=Tree.branch(seen[-1],R)
        code=tuple(code)
        q=(({},C,C+0x1000,C+16,0,0),C+0x2000,C+0x3000,C+0x4000,C+0x5000,C+64,[])
        fp=(q,prior,frontier,A,B);plan=(None,C,resume,seen,stops);cb=(C,code,(0x80004000,0x80004004))
        dest=root/'nWiiRuntime/include/undercover';dest.mkdir(parents=True)
        private=dest/'v958_private_second_ack.h'
        private.write_text('#define UNDERCOVER_V1118_PRIVATE_POSTALARM_WIRELESS 1\n'
            +f'inline constexpr uint32_t transfer_callback=0x{C:08x}u;\n'
            +f'inline constexpr std::array<uint32_t,172> third_postalarm_words{{'+s.fmt(code)+'};\n')
        host=Path(s.__file__).parent
        for name in ('wii_callback_suffix_v841.h','wii_third_alarm_suffix_v1047.h'):
            (dest/name).write_bytes((host/name).read_bytes())
        (dest/'v831_private_callback_frontier.h').write_text(s.render_frontier(C,C+68,
            {pc:(C,code[(pc-C)//4]) for pc in prior},frontier))
        src=f'#include "runtime/cpu_context.h"\nvoid fn_{C:X}(CPUContext& ctx) {{\n'
        src+=f'    if (nwii::runtime::g_trace_calls && ctx.pc == 0x{C:X}) nwii::runtime::trace_call(0x{C:X}, ctx);\n'
        for pc in sorted(set(prior)|set(seen)|{p+4 for p in frontier}):
            w=code[(pc-C)//4]
            src+=f'loc_{pc:X}: ;\n    // 0x{pc:08X}: {w:08X}\n    ++ctx.inst_count;\n'+SI
            if pc in prior or pc in {p+4 for p in frontier}:
                src+=f'    if({ACTIVE}) undercover::wii::v958::before(ctx,0x{pc:08x}u,0x{w:08x}u,false);\n'
            if w>>26==18 and w&3==1:
                dst=pc+(((w&0x03fffffc)^0x02000000)-0x02000000)
                src+=f'    ctx.pc = 0x{dst:X}; fn_{dst:X}(ctx);\n    if (ctx.pc != 0x{pc+4:X}) return;\n'
            elif w==0x4e800421:
                src+=f'    ctx.lr = 0x{pc+4:X};\n    if (ctx.ctr) {{ ctx.pc = ctx.ctr; return; }}\n'
        (root/'output_0.cpp').write_text(src+'}\n')
        for i in range(1,20):(root/f'output_{i}.cpp').write_text('// unused shard\n')
        (root/'main_output.cpp').write_text(f'extern "C" void run_game(CPUContext& ctx) {{\ncase 0x{C:X}: fn_{C:X}(ctx); break;\n}}\n')
        return fp,plan,cb,private
    def install(self,root,f):
        import prepare_v1124_postalarm_suffix as s
        fp,plan,cb,_=f
        with patch.object(s,'frontier_plan',return_value=fp),patch.object(s,'plan',return_value=plan), \
             patch.object(s,'expectations',return_value=cb),patch.object(s,'exact',return_value=cb[1]):
            s.install(b'',b'',root,Path(s.__file__).parent)
    def test_suffix_tree(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);f=self.fixture(root);before=Tree.snapshot(root);self.install(root,f);after=Tree.snapshot(root)
            new=f[-1].parent/'v1123_private_postalarm_suffix.h'
            self.assertEqual(set(after)-set(before),{new.relative_to(root)})
            self.assertEqual({p for p in before if before[p]!=after[p]},{Path('output_0.cpp'),f[-1].relative_to(root)})
            self.assertIn('UNDERCOVER_V1123_PRIVATE_POSTALARM_SUFFIX 1',f[-1].read_text())
            self.assertIn('std::array<CallbackSuffixWord,21>',new.read_text())
            p=Path('output_0.cpp')
            self.assertEqual(before[p].count(b'++ctx.inst_count;'),after[p].count(b'++ctx.inst_count;'))
            self.assertEqual(after[p].count(b'v958::before(ctx,')-before[p].count(b'v958::before(ctx,'),19)
    def test_suffix_tree_refusals(self):
        reasons={'header':'postalarm suffix identity','metadata':'postalarm suffix metadata','owner':'postalarm suffix owner',
                 'direct':'helper direct native call','indirect':'indirect dispatch','label':'native IPC label identity',
                 'resume':'postalarm time resume','dispatch':'native IPC dispatch','existing':'postalarm suffix destination'}
        for fault,reason in reasons.items():
            with self.subTest(fault=fault),tempfile.TemporaryDirectory() as td:
                root=Path(td);f=self.fixture(root);private=f[-1];p=root/'output_0.cpp'
                if fault=='header':
                    h=private.parent/'v831_private_callback_frontier.h';h.write_text(h.read_text()+'// tamper\n')
                elif fault=='metadata':private.write_text(private.read_text().replace('third_postalarm_words','other_words'))
                elif fault=='owner':(root/'output_19.cpp').write_bytes(p.read_bytes())
                elif fault=='existing':(private.parent/'v1123_private_postalarm_suffix.h').write_text('// existing\n')
                elif fault=='dispatch':
                    p=root/'main_output.cpp';p.write_text(p.read_text().replace('fn_80005000(ctx)','fn_80005004(ctx)'))
                else:
                    src=p.read_text();resume=f[1][2];new_pc=f[1][3][2]
                    if fault=='direct':src=src.replace('fn_8000A000(ctx);','fn_8000A004(ctx);')
                    elif fault=='indirect':src=src.replace('ctx.pc = ctx.ctr; return;','ctx.pc = ctx.lr; return;')
                    elif fault=='label':src=src.replace(f'// 0x{new_pc:08X}: 60000000',f'// 0x{new_pc:08X}: 60000001')
                    else:src=src.replace(f'v958::before(ctx,0x{resume:08x}u,',f'v958::other(ctx,0x{resume:08x}u,')
                    p.write_text(src)
                before=Tree.snapshot(root)
                with self.assertRaises(ValueError) as caught:self.install(root,f)
                self.assertEqual(str(caught.exception),reason)
                self.assertEqual(Tree.snapshot(root),before)


class ReturnHooks(unittest.TestCase):
    def test_exact_seams(self):
        from prepare_v1134_postalarm_return import patch_return_label
        from prepare_v1106_postalarm_time import verify_resume
        args=f'ctx,0x{P:08x}u,0x{W:08x}u'
        tick='    ++ctx.inst_count;\n'
        for dispatch in (False,True):
            old='    undercover::wii::v850::'+('handler_resume' if dispatch else 'before')+'('+args+');\n'
            pre='    undercover::wii::v850::dispatch_resume('+args+');\n'
            src=L+old
            if dispatch:src=src.replace(tick,pre+tick)
            out=patch_return_label(src,P,W,dispatch)
            verify_resume(out,P,W)
            self.assertEqual(out.count(tick),1)
            self.assertEqual(out.count('v958::before(ctx,'),1)
            self.assertIn('if(!'+ACTIVE+') { '+old.strip()+' }',out)
            if dispatch:
                hook='    undercover::wii::v958::postalarm_dispatch_resume('+args+');\n'
                self.assertIn(hook+tick,out)
                self.assertEqual(out.count(hook),1)
            else:self.assertNotIn('postalarm_dispatch_resume',out)
            for bad in (src.replace(old,''),src+old,src.replace(SI,''),src.replace(tick,tick+tick),
                        src.replace('0x60000000u','0x60000001u')):
                with self.subTest(dispatch=dispatch,bad=bad):
                    with self.assertRaises(ValueError):patch_return_label(bad,P,W,dispatch)
            if dispatch:
                for bad in (src.replace(pre,''),src.replace(pre,pre+'    unrelated();\n'),src+pre):
                    with self.assertRaises(ValueError):patch_return_label(bad,P,W,True)

class ReturnTree(unittest.TestCase):
    H,C,R=0x80004000,0x80005000,0x80006000
    def fixture(self,root):
        import prepare_v1134_postalarm_return as ret
        H,C,R=self.H,self.C,self.R
        code=[Tree.NOP]*172;resume=C+40
        seen=list(range(resume,resume+21*4,4));call=seen[-1]
        stops={seen[-2]:(4,2,None),call:(13,1,R)}
        code[(seen[-2]-C)//4]=Tree.BCTRL;code[(call-C)//4]=Tree.branch(call,R)
        tail=(0x80010044,0x7c0803a6,0x38210040,Tree.BLR)
        code[(call+4-C)//4:(call+20-C)//4]=tail
        restore=(0x834bffe8,0x836bffec,0x838bfff0,0x83abfff4,0x83cbfff8,0x83ebfffc,Tree.BLR)
        handler=[Tree.NOP,Tree.BCTRL,Tree.NOP,Tree.NOP,Tree.BCTRL,Tree.NOP,Tree.BLR]
        sites=(H+4,H+16);callers=[(site,Tree.BCTRL,ordinal,Tree.NOP) for site,ordinal in zip(sites,(6,11))]
        rows={pc:code[(pc-C)//4] for pc in seen}
        dest=root/'nWiiRuntime/include/undercover';dest.mkdir(parents=True)
        private=dest/'v958_private_second_ack.h'
        private.write_text('#define UNDERCOVER_V1123_PRIVATE_POSTALARM_SUFFIX 1\n'
            +f'inline constexpr uint32_t transfer_callback=0x{C:08x}u;\n'
            +'inline constexpr std::array<uint32_t,172> third_postalarm_words{'+ret.fmt(code)+'};\n')
        for name in ('wii_third_alarm_suffix_v1047.h','wii_callback_return_v846.h'):
            (dest/name).write_bytes((Path(ret.__file__).parent/name).read_bytes())
        (dest/'v1123_private_postalarm_suffix.h').write_text(ret.render_suffix(C,resume,rows,stops))
        (dest/'v850_private_callback_return.h').write_text(ret.render_old(C,resume,rows,stops,R,restore,tail,callers))
        def source(a,entries):
            s=f'#include "runtime/cpu_context.h"\nvoid fn_{a:X}(CPUContext& ctx) {{\n'
            s+=f'    if (nwii::runtime::g_trace_calls && ctx.pc == 0x{a:X}) nwii::runtime::trace_call(0x{a:X}, ctx);\n'
            for pc,w in entries:
                args=f'ctx,0x{pc:08x}u,0x{w:08x}u'
                s+=f'loc_{pc:X}: ;\n    // 0x{pc:08X}: {w:08X}\n'
                if a==H and pc in (sites[0]+4,sites[1]+4):
                    s+='    undercover::wii::v850::dispatch_resume('+args+');\n'
                s+='    ++ctx.inst_count;\n'+SI
                if a==C and pc in seen:s+=f'    if({ACTIVE}) undercover::wii::v958::before({args},false);\n'
                elif a==H and pc in (sites[0]+4,sites[1]+4):s+='    undercover::wii::v850::handler_resume('+args+');\n'
                elif a!=H:s+='    undercover::wii::v850::before('+args+');\n'
                if w>>26==18 and w&3==1:
                    dst=pc+(((w&0x03fffffc)^0x02000000)-0x02000000)
                    s+=f'    ctx.pc = 0x{dst:X}; fn_{dst:X}(ctx);\n    if (ctx.pc != 0x{pc+4:X}) return;\n'
                elif w==Tree.BCTRL:s+=f'    ctx.lr = 0x{pc+4:X};\n    if (ctx.ctr) {{ ctx.pc = ctx.ctr; return; }}\n'
            return s+'}\n'
        (root/'output_0.cpp').write_text(source(C,sorted(list(rows.items())+[(call+4+4*i,w) for i,w in enumerate(tail)])))
        (root/'output_1.cpp').write_text(source(R,[(R+4*i,w) for i,w in enumerate(restore)]))
        (root/'output_2.cpp').write_text(source(H,[(H+4*i,w) for i,w in enumerate(handler)]))
        for i in range(3,20):(root/f'output_{i}.cpp').write_text('// unused shard\n')
        (root/'main_output.cpp').write_text('extern "C" void run_game(CPUContext& ctx) {\n'+''.join(
            f'case 0x{pc:X}: fn_{a:X}(ctx); break;\n' for pc,a in ((C,C),(R,R),(H,H),(H+8,H),(H+20,H)))+'}\n')
        return ((None,(({R:restore},),)),C,resume,seen,stops),(C,tuple(code),sites),{C:tuple(code),R:restore,H:tuple(handler)},private
    def install(self,root,f):
        import prepare_v1134_postalarm_return as ret
        plan,cb,roots,_=f
        with patch.multiple(ret,HANDLER=self.H),patch.object(ret,'plan',return_value=plan), \
             patch.object(ret,'expectations',return_value=cb),patch.object(ret,'geometry',return_value=(len(roots[self.H]),)), \
             patch.object(ret,'exact',side_effect=lambda d,e,a,n:roots[a][:n]):
            ret.install(b'',b'',root,Path(ret.__file__).parent)
    def test_return_tree(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);f=self.fixture(root);before=Tree.snapshot(root);self.install(root,f);after=Tree.snapshot(root)
            new=f[-1].parent/'v1132_private_postalarm_return.h'
            self.assertEqual(set(after)-set(before),{new.relative_to(root)})
            self.assertEqual({p for p in before if before[p]!=after[p]},{Path('output_0.cpp'),Path('output_1.cpp'),Path('output_2.cpp'),f[-1].relative_to(root)})
            for i,n in enumerate((4,7,1)):
                p=Path(f'output_{i}.cpp')
                self.assertEqual(before[p].count(b'++ctx.inst_count;'),after[p].count(b'++ctx.inst_count;'))
                self.assertEqual(after[p].count(b'v958::before(ctx,')-before[p].count(b'v958::before(ctx,'),n)
            self.assertEqual(after[Path('output_2.cpp')].count(b'v958::postalarm_dispatch_resume(ctx,'),1)
            self.assertIn('UNDERCOVER_V1132_PRIVATE_POSTALARM_RETURN 1',f[-1].read_text())
    def test_return_tree_refusals(self):
        for fault in ('header','metadata','owner','direct','dispatch','resume','legacy','existing'):
            with self.subTest(fault=fault),tempfile.TemporaryDirectory() as td:
                root=Path(td);f=self.fixture(root);private=f[-1];p=root/'output_0.cpp'
                if fault=='header':
                    q=private.parent/'v850_private_callback_return.h';q.write_text(q.read_text()+'// tamper\n')
                elif fault=='metadata':private.write_text(private.read_text().replace('third_postalarm_words','other_words'))
                elif fault=='owner':(root/'output_19.cpp').write_bytes(p.read_bytes())
                elif fault=='direct':p.write_text(p.read_text().replace('fn_80006000(ctx);','fn_80006004(ctx);'))
                elif fault=='dispatch':
                    q=root/'main_output.cpp';q.write_text(q.read_text().replace('case 0x80004008: fn_80004000','case 0x80004008: fn_80004004'))
                elif fault=='resume':
                    q=root/'output_2.cpp';q.write_text(q.read_text().replace('v850::dispatch_resume','v850::wrong_resume',1))
                elif fault=='legacy':
                    q=root/'output_1.cpp';q.write_text(q.read_text().replace('v850::before','v850::wrong',1))
                else:(private.parent/'v1132_private_postalarm_return.h').write_text('// existing\n')
                before=Tree.snapshot(root)
                with self.assertRaises(ValueError):self.install(root,f)
                self.assertEqual(Tree.snapshot(root),before)


class ReturnComposedLegacy(unittest.TestCase):
    def test_inherited_wrappers(self):
        from prepare_v1134_postalarm_return import patch_return_label,legacy_forms
        from prepare_v1048_third_alarm import hook
        from prepare_v1097_after_alarm import patch_label
        from prepare_v1106_postalarm_time import verify_resume
        a=f'ctx,0x{P:08x}u,0x{W:08x}u';tick='    ++ctx.inst_count;\n'
        for dispatch in (False,True):
            legacy=f'    undercover::wii::v850::{"handler_resume" if dispatch else "before"}({a});\n'
            pre=f'    undercover::wii::v850::dispatch_resume({a});\n'
            raw=L+legacy
            if dispatch:raw=raw.replace(tick,pre+tick)
            for earlier in (hook(raw,P,W),patch_label(raw,P,W),patch_label(hook(raw,P,W),P,W)):
                with self.subTest(dispatch=dispatch,earlier=earlier):
                    out=patch_return_label(earlier,P,W,dispatch)
                    verify_resume(out,P,W)
                    self.assertEqual(out.count(tick),1)
                    self.assertEqual(out.count('v958::before(ctx,'),1)
                    self.assertTrue(any(x in out for x in legacy_forms(legacy)[2:]))
                    if dispatch:self.assertIn(f'postalarm_dispatch_resume({a});\n'+tick,out)
                    else:self.assertNotIn('postalarm_dispatch_resume',out)
                    for bad in (earlier.replace('v850::'+('handler_resume' if dispatch else 'before'),'v850::wrong'),
                                earlier+legacy,earlier.replace(SI,'')):
                        with self.assertRaises(ValueError):patch_return_label(bad,P,W,dispatch)

if __name__=='__main__':unittest.main()
