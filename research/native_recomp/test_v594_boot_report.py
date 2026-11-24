import unittest,struct
from make_v594_boot_report_geometry import START,END,TARGETS,REPORT,check_table,check_control
from apply_report_table_v594 import pairs
from apply_irq_bootstrap_v475 import rewrite
from audit_v594_report_translation import check
BCTR=TARGETS[0]-4
def branch(pc,target):return 0x48000001|((target-pc)&0x03fffffc)
class Tests(unittest.TestCase):
    def test_geometry(self):
        table=struct.pack('>26I',*(list(TARGETS)*4)[:26])
        self.assertEqual(set(check_table(table)),set(TARGETS))
        for bad in (table[:-4],table[:4]*26,table[:-4]+b'\0'*4):
            with self.assertRaises(ValueError):check_table(bad)
        words=[0x60000000]*((END-START)//4)
        i=(BCTR-START)//4;words[i]=0x4e800420;words[i-1]=(31<<26)|(3<<21)|(9<<16)|(467<<1)
        words[-1]=0x4e800020
        for pc in TARGETS[:-1]:words[(pc+8-START)//4]=branch(pc+8,REPORT)
        self.assertEqual(check_control(words),BCTR)
        for at in (i,i-1,len(words)-1,(TARGETS[0]+8-START)//4):
            bad=words.copy();bad[at]=0x60000000
            with self.assertRaises(ValueError):check_control(bad)
    def test_patch(self):
        ps=pairs(BCTR);old='\n'.join(a for a,b in ps);new=rewrite(old,ps)
        self.assertEqual(rewrite(new,ps),new)
        for bad in (old+old,old.replace(ps[1][0],'')):
            with self.assertRaises(ValueError):rewrite(bad,ps)
    def test_native_audit(self):
        expected={pc:0x60000000 for pc in TARGETS};expected[BCTR]=0x4e800420
        s='void fn_805203C4(CPUContext& ctx) {\n'
        for pc in sorted(expected):
            s+=f'loc_{pc:X}: ;\n    // 0x{pc:08X}: {expected[pc]:08X}\n    ++ctx.inst_count;\n'
            if pc==BCTR:s+='    ctx.pc = ctx.ctr; return;\n'
        s+='}\n'
        main='\n'.join(f'case 0x{pc:X}: fn_805203C4(ctx); break;' for pc in TARGETS)
        self.assertTrue(check([s],main,BCTR,expected))
        for bad,m in ((s+s,main),(s.replace('fn_805203C4','fn_805203C8'),main),(s.replace('ctx.pc = ctx.ctr','ctx.pc = ctx.lr'),main),(s,main+main),(s,main.replace('fn_805203C4','other'))):
            with self.assertRaises(ValueError):check([bad],m,BCTR,expected)
if __name__=='__main__':unittest.main()
