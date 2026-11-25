import unittest
from unittest.mock import patch
from audit_callback_deps_v787 import callback_sites
class Callback(unittest.TestCase):
    def test_order(self):
        root=0x80004000
        with patch('audit_callback_deps_v787.shape',return_value=(None,[(root+4,root+100),(root+12,root+200)],[root+8,root+16])):
            self.assertEqual(callback_sites(root,[0x60000000,0x48000061,0x4e800421,0x480000bd,0x4e800421]),[(2,root+8),(4,root+16)])
            with self.assertRaises(ValueError):callback_sites(root,[0x60000000]*5)
if __name__=='__main__':unittest.main()
