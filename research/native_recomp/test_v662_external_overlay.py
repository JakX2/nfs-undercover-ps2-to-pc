import unittest
from audit_v662_external_overlay import audit_body,DEF,DEFAULT,VECTOR
class Tests(unittest.TestCase):
    def test_native_body(self):
        words=[0x60000000]*38
        labels=''.join(f'loc_{VECTOR+4*i:X}: ;\n    // 0x{VECTOR+4*i:08X}: {words[i]:08X}\n    ++ctx.inst_count;\n' for i in range(12))
        body=DEF+'\n'+DEFAULT+'\n'+labels+'}\n'
        self.assertEqual(audit_body(body,words),12)
        for bad in (body.replace('60000000','60000001',1),body.replace('++ctx.inst_count;','nwii::runtime::interpret_step(ctx);',1),body.replace('++ctx.inst_count;','',1),body.replace('loc_80000500','loc_80000504',1),body+body):
            with self.assertRaises(ValueError):audit_body(bad,words)
if __name__=='__main__':unittest.main()
