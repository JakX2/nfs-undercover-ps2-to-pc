import unittest
from pathlib import Path
from unittest.mock import patch
from prepare_v928_leaf_finish import patch_binding as prior
from prepare_v930_ipc_join import patch_binding
import audit_v930_ipc_join as a
HERE=Path(__file__).parent
class IpcJoin(unittest.TestCase):
    def test_patch(self):
        s=patch_binding(prior((HERE/'wii_live_irq_return_binding_v922.h').read_text()))
        self.assertIn('ipc.begin(c)',s)
        self.assertIn('ipc_join.start(c,pc,w,finish.stage()==5u',s)
        self.assertIn('ipc_join.entry(c,pc,v850::held(c))',s)
        with self.assertRaises(ValueError):patch_binding(s)
    def test_audit(self):
        rows=[a.old.RETURN,a.BEGIN,a.RETURN]
        with patch('audit_v928_leaf_finish.inspect',return_value=('',True)):
            self.assertTrue(a.inspect(b'\n'.join(rows),0)[1])
            for bad in (rows[:-1],rows[::-1],rows+[a.RETURN],rows+[b'V930_fault'],[a.BEGIN,*rows]):
                self.assertFalse(a.inspect(b'\n'.join(bad),0)[1])
            self.assertFalse(a.inspect(b'\n'.join(rows),126)[1])
if __name__=='__main__':unittest.main()
