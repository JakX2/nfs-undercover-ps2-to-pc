import unittest
from unittest.mock import patch
from audit_v862_wireless_write import inspect
from test_v848_wireless_wrapper import Q,E,R,EC,RC,QG,EG,RG
T=b'V861_WIRELESS_WRITE_RESULT original_setter_return=1 original_unlock=1 transfers=12 bytes=44 visits=3187 polls=74 mmio=52 payload=1 abi=1 callback_return=0 boot_verified=0'
P=(*Q,EC,RC)
class WriteAudit(unittest.TestCase):
    def check(self,rows,rc=0):
        with patch('audit_v809_callback_prefix.alarm',return_value=('',True)):
            return inspect(b'\n'.join(rows),rc)
    def test_valid(self):
        row,ok=self.check((*P,T))
        self.assertTrue(ok);self.assertIn('changed_write_return=1',row);self.assertIn('transfers=12 bytes=44',row)
        for p in ((*Q,E,R),(*QG,EG,RG)):
            row,ok=self.check(p)
            self.assertTrue(ok);self.assertIn('changed_write_return=0',row)
    def test_false_completion(self):
        for tail in ((),(T,T),(T,b'V861_WIRELESS_WRITE_INVALID kind=5 device=2 reason=3 witness=0 completed=3 bytes=8')):
            self.assertFalse(self.check((*P,*tail))[1])
        self.assertFalse(self.check((T,*P,T))[1])
        self.assertFalse(self.check((*P,T),126)[1])
        self.assertFalse(self.check((*Q,E,R,T))[1])
    def test_geometry(self):
        for old,new in ((b'transfers=12',b'transfers=11'),(b'bytes=44',b'bytes=40'),(b'visits=3187',b'visits=12001'),
                        (b'visits=3187',b'visits=62'),(b'polls=74',b'polls=0'),(b'mmio=52',b'mmio=4097'),
                        (b'original_unlock=1',b'original_unlock=0'),(b'abi=1',b'abi=0'),(b'callback_return=0',b'callback_return=1')):
            self.assertFalse(self.check((*P,T.replace(old,new)))[1])
if __name__=='__main__':unittest.main()
