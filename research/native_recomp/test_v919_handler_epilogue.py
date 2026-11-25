import unittest
from pathlib import Path
from unittest.mock import patch
from prepare_v919_handler_epilogue import epilogue,patch_binding,patch_alias
from audit_v919_handler_epilogue import inspect,MARKERS
from audit_v870_handler_suffix import STATUS,STORE
from test_v870_handler_suffix_audit import prefix,markers,P
HERE=Path(__file__).parent
class Epilogue(unittest.TestCase):
    def test_geometry(self):
        h=0x80004000
        self.assertEqual(epilogue(h,[0x48001001,0x60000000,0x4e800020],h),[(h+4,0x60000000),(h+8,0x4e800020)])
        with self.assertRaises(ValueError):epilogue(h,[0x48001001,0x48000001,0x4e800020],h)
        with self.assertRaises(ValueError):epilogue(h,[0x48001001,0x90010000,0x4e800020],h)
    def test_patch(self):
        s=patch_binding((HERE/'wii_handler_suffix_binding_v868.h').read_text())
        self.assertIn('restore_returned(c,pc,restore.visits(),true,12u)',s)
        self.assertIn('v726::witness.stage()!=3u',s)
        with self.assertRaises(ValueError):patch_binding(s)
        b='loc_80004000: ;\n    // 0x80004000: 4E800020\n    ++ctx.inst_count;\n    ctx.si_instruction_boundary();\n    return;\n}'
        self.assertIn('v868::restore_before',patch_alias(b,0x80004000,[0x4e800020]))
        with self.assertRaises(ValueError):patch_alias(b.replace('    ctx.si_instruction_boundary();\n',''),0x80004000,[0x4e800020])
    def test_audit(self):
        j,s=markers(6,12,1,20)
        rows=(*prefix(P,6),j,STATUS,STORE,b'V911_HANDLER_INDEX_BRANCH original_load=1 compare=1 branch_taken=1 successor=1',s)
        with patch('audit_v809_callback_prefix.alarm',return_value=('',True)):
            self.assertTrue(inspect(b'\n'.join((*rows,*MARKERS)),0)[1])
            for t in (MARKERS[:-1],MARKERS[::-1],[*MARKERS,MARKERS[-1]],[*MARKERS,b'V919_unknown']):
                self.assertFalse(inspect(b'\n'.join((*rows,*t)),0)[1])
            self.assertFalse(inspect(b'\n'.join((*rows,*MARKERS)),126)[1])
if __name__=='__main__':unittest.main()
