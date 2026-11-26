import unittest
from pathlib import Path
from prepare_v1257_ack_submit import plan,patch_mmio,render,RESUME,SC,SUBMIT,SLEEP,INCLUDE,WRITE,SUBMIT_INCLUDE,SUBMIT_WRITE,SC_ROUTE
from prepare_v641_open_request import NEW_SC
from prepare_v625_ipc_client import patch_return
from make_start_to_ipc_submit_v72 import EDGES,SPANS
W=0x60000000
BLR=0x4e800020
T='    ++ctx.inst_count;\n'
def fixture():
    blocks={pc:[W]*(n//4) for pc,n in SPANS}
    blocks[SLEEP]=[W]
    all_blocks={pc:list(ws) for pc,ws in blocks.items()}
    for site,target in EDGES:
        all_blocks.setdefault(target,[W])
    all_blocks[0x805222c0]=[W]*12
    all_blocks[0x805222c0][-2:]=[0x44000002,BLR]
    rows=[]
    for site,target in EDGES:
        root=next(pc for pc,ws in blocks.items() if pc<=site<pc+4*len(ws))
        word=0x48000001|((target-site)&0x03fffffc)
        all_blocks[root][(site-root)//4]=word
        rows.append((target,site+4,word,all_blocks[target][0]))
    # Root entry words do not change when assigning internal branches.
    blocks={pc:tuple(all_blocks[pc]) for pc in blocks}
    calls=dict(EDGES);src={}
    for pc,ws in all_blocks.items():
        body=f'void fn_{pc:X}(CPUContext& ctx) {{\n    if (nwii::runtime::g_trace_calls && ctx.pc == 0x{pc:X}) nwii::runtime::trace_call(0x{pc:X}, ctx);\n'
        for i,w in enumerate(ws):
            at=pc+4*i
            body+=f'loc_{at:X}: ;\n    // 0x{at:08X}: {w:08X}\n'
            if at==SC:body+=NEW_SC
            body+=T
            if at in calls:
                target=calls[at]
                body+=f'    ctx.pc = 0x{target:X}; fn_{target:X}(ctx);\n    if (ctx.pc != 0x{at+4:X}) return;\n'
        src[Path(str(pc))]=body+'}\n'
    outer=''.join(f'case 0x{pc:X}: fn_{pc:X}(ctx); break;\n' for pc in all_blocks)
    return src,outer,blocks,rows,all_blocks[SUBMIT][(RESUME-SUBMIT)//4]
class SubmitPlan(unittest.TestCase):
    def test_plan(self):
        src,outer,blocks,rows,w=fixture()
        path=Path(str(SUBMIT));prior={path:src[path].replace(T,T+'    old_hook(ctx);\n',1)}
        snap=src.copy();mmio=INCLUDE+'\n'+WRITE
        result,patched=plan(src,outer,prior,blocks,rows,w,SC_ROUTE,mmio)
        self.assertEqual(result[path],patch_return(prior[path],w,RESUME))
        self.assertEqual(src,snap)
        self.assertIn(SUBMIT_INCLUDE,patched)
        self.assertLess(patched.index(SUBMIT_WRITE),patched.index(WRITE))
        self.assertEqual(patched.count(WRITE),1)
        self.assertIn('std::array<VectorEdge,14>',render(rows))
        with self.assertRaises(ValueError):plan(src,outer,result,blocks,rows,w,SC_ROUTE,mmio)
    def test_refusals(self):
        for fault in ('root','edge','return','word','tick','dispatch','duplicate','sc','ios','mmio'):
            with self.subTest(fault=fault):
                src,outer,blocks,rows,w=fixture();p=Path(str(SUBMIT));ios=SC_ROUTE;mmio=INCLUDE+'\n'+WRITE
                if fault=='root':src[p]=src[p].replace('nwii::runtime::trace_call','bad')
                if fault=='edge':src[p]=src[p].replace('fn_805293B0(ctx);','bad(ctx);')
                if fault=='return':src[p]=src[p].replace('ctx.pc != 0x80519630','ctx.pc != 0x80519634')
                if fault=='word':src[p]=src[p].replace(f'{rows[0][2]:08X}\n','00000000\n')
                if fault=='tick':src[p]=src[p].replace(T,'',1)
                if fault=='dispatch':outer=outer.replace(f'case 0x{SUBMIT:X}: fn_{SUBMIT:X}(ctx); break;\n','')
                if fault=='duplicate':src[Path('dup')]=src[p]
                if fault=='sc':
                    s=Path(str(0x805222c0));src[s]=src[s].replace(NEW_SC,'')
                if fault=='ios':ios=''
                if fault=='mmio':mmio+=mmio
                before=src.copy()
                with self.assertRaises(ValueError):plan(src,outer,{},blocks,rows,w,ios,mmio)
                self.assertEqual(src,before)
    def test_mmio(self):
        for bad in ('',INCLUDE,WRITE,patch_mmio(INCLUDE+'\n'+WRITE)):
            with self.assertRaises(ValueError):patch_mmio(bad)
if __name__=='__main__':unittest.main()
