import unittest
from audit_v584_bat_translation import bat_spr,audit_shards,audit_dispatch,ROOTS,RESUMES,RFI
def mtspr(spr,reg):
    return (31<<26)|(reg<<21)|((spr&31)<<16)|((spr>>5)<<11)|(467<<1)
def label(pc,word,body):
    return f'loc_{pc:X}: ;\n    // 0x{pc:08X}: {word:08X}\n    ++ctx.inst_count;\n'+body+'\n'
class Tests(unittest.TestCase):
    def test_spr_decode(self):
        for spr in range(1024):
            self.assertEqual(bat_spr(mtspr(spr,17)),spr if 528<=spr<=543 or 560<=spr<=575 else None)
        self.assertIsNone(bat_spr(RFI))
    def test_native_proof(self):
        pc=0x805270c4;word=mtspr(536,17)
        expected={pc:(word,536,17),pc+4:(RFI,None,None)}
        good=label(pc,word,'    ctx.write_bat(536, ctx.gpr[17]);')+label(pc+4,RFI,'    ctx.msr = ctx.srr1;\n    ctx.pc = ctx.srr0;\n    ctx.dispatch_saved_ctx = 0;\n    return;')
        self.assertEqual(audit_shards([good],expected),(1,1))
        for bad in (good+good,good.replace('ctx.write_bat(536','ctx.write_bat(537'),good.replace('ctx.gpr[17]','ctx.gpr[18]'),good.replace('ctx.pc = ctx.srr0;','ctx.pc = ctx.lr;'),good.replace('ctx.dispatch_saved_ctx = 0;',''),good.replace('return;',''),good.replace('++ctx.inst_count;',''),good.replace('ctx.write_bat(536, ctx.gpr[17]);','micro_interpret(ctx,0,0);'),good.replace(f'{word:08X}','60000000')):
            with self.assertRaises(ValueError):audit_shards([bad],expected)
    def test_dispatch(self):
        good='else if (ctx.pc < 0x80000000) ctx.pc |= 0x80000000;\n'+''.join(f'            case 0x{p:X}: fn(ctx); break;\n' for p in (*ROOTS,*RESUMES))
        audit_dispatch(good)
        for bad in (good+good,good.replace('case 0x805270C4:','case 0x805270C8:'),good.replace('ctx.pc |= 0x80000000','ctx.pc = 0')):
            with self.assertRaises(ValueError):audit_dispatch(bad)
if __name__=='__main__':unittest.main()
