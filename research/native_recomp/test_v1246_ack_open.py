import unittest
from pathlib import Path
from prepare_v1246_ack_open import plan_native,patch_ios,SC,RESUME,PROFILE,ALLOC,OPEN,SC_INCLUDE,SC_HOOK
from prepare_v641_open_request import OLD_SC,NEW_SC,IOS_INC,IOS_HOOK
from prepare_v625_ipc_client import patch_return

W=0x60000000
BLR=0x4e800020
T='    ++ctx.inst_count;\n'
STM=0x8052b08c
FLUSH=0x805222c0
DIS=0x805265ac
REST=0x805265d4
SUB=0x805195ec
link=lambda a,b:0x48000001|((b-a)&0x03fffffc)
def fixture():
    sites=((STM,OPEN),(OPEN+4,PROFILE),(ALLOC+4,DIS),(ALLOC+8,REST),(RESUME-4,FLUSH),(RESUME+4,SUB))
    blocks={OPEN:[W]*((RESUME+8-OPEN)//4+1),PROFILE:[link(PROFILE,ALLOC)&~1],ALLOC:[W]*4,
            FLUSH:[W]*12,DIS:[BLR],REST:[BLR],SUB:[BLR]}
    blocks[FLUSH][-2:]=[0x44000002,BLR]
    rows=[]
    for pc,a in sites:
        w=link(pc,a)
        rows.append((a,pc+4,w,blocks[a][0]))
        if pc!=STM:
            root=OPEN if OPEN<=pc<=RESUME+4 else ALLOC
            blocks[root][(pc-root)//4]=w
    # Separate synthetic STM owner containing the real edge shape.
    all_blocks={**blocks,STM:[rows[0][2]]}
    src={};calls=dict(sites)
    for a,ws in all_blocks.items():
        body=f'void fn_{a:X}(CPUContext& ctx) {{\n    if (nwii::runtime::g_trace_calls && ctx.pc == 0x{a:X}) nwii::runtime::trace_call(0x{a:X}, ctx);\n'
        for i,w in enumerate(ws):
            pc=a+4*i
            body+=f'loc_{pc:X}: ;\n    // 0x{pc:08X}: {w:08X}\n'
            if pc==SC:body+=OLD_SC
            body+=T
            if pc in calls:
                dst=calls[pc];body+=f'    ctx.pc = 0x{dst:X}; fn_{dst:X}(ctx);\n    if (ctx.pc != 0x{pc+4:X}) return;\n'
            if pc==PROFILE:body+=f'    ctx.pc = 0x{ALLOC:X}; return;\n'
        src[Path(str(a))]=body+'}\n'
    outer=''.join(f'case 0x{a:X}: fn_{a:X}(ctx); break;\n' for a in all_blocks)
    return src,outer,(rows,(blocks[ALLOC][0],0x44000002,W),blocks)

class OpenSource(unittest.TestCase):
    def test_plan(self):
        src,outer,g=fixture()
        op=Path(str(OPEN));sc=Path(str(FLUSH))
        prior={op:src[op].replace(T,T+'    previous_hook(ctx);\n',1)}
        snap=src.copy()
        result=plan_native(src,outer,prior,g)
        self.assertEqual(result[op],patch_return(prior[op],W,RESUME))
        self.assertIn(NEW_SC,result[sc])
        self.assertEqual(src,snap)
        self.assertNotIn(NEW_SC,src[sc])
        with self.assertRaises(ValueError):plan_native(src,outer,result,g)
    def test_refusals(self):
        for fault in ('tail','edge','return','trace','word','dispatcher','duplicate','sc'):
            with self.subTest(fault=fault):
                src,outer,g=fixture();op=Path(str(OPEN));sc=Path(str(FLUSH))
                if fault=='tail':src[Path(str(PROFILE))]=src[Path(str(PROFILE))].replace('return;','goto loc_8051AB34;')
                if fault=='edge':src[Path(str(STM))]=src[Path(str(STM))].replace(f'fn_{OPEN:X}(ctx);','wrong(ctx);')
                if fault=='return':src[op]=src[op].replace(f'ctx.pc != 0x{RESUME:X}',f'ctx.pc != 0x{RESUME+4:X}')
                if fault=='trace':src[Path(str(SUB))]=src[Path(str(SUB))].replace('nwii::runtime::trace_call','wrong_trace')
                if fault=='word':src[Path(str(STM))]=src[Path(str(STM))].replace(f'{g[0][0][2]:08X}\n','00000000\n')
                if fault=='dispatcher':outer=outer.replace(f'case 0x{ALLOC:X}: fn_{ALLOC:X}(ctx); break;\n','')
                if fault=='duplicate':src[Path('duplicate')]=src[sc]
                if fault=='sc':src[sc]=src[sc].replace(OLD_SC,'')
                before=src.copy()
                with self.assertRaises(ValueError):plan_native(src,outer,{},g)
                self.assertEqual(src,before)
    def test_ios(self):
        boot='  if (undercover::wii::v574::try_sc(ctx)) return false;'
        src=IOS_INC+'\n'+IOS_HOOK+'\n'+boot
        got=patch_ios(src)
        self.assertIn(SC_INCLUDE,got)
        self.assertLess(got.index(SC_HOOK),got.index(IOS_HOOK))
        self.assertLess(got.index(IOS_HOOK),got.index(boot))
        for bad in ('',src+src,got,IOS_INC+'\n'+boot+'\n'+IOS_HOOK):
            with self.assertRaises(ValueError):patch_ios(bad)
if __name__=='__main__':unittest.main()
