import unittest
from unittest.mock import patch
from audit_v822_callback_time import inspect,TIME_ENTRY
from test_v809_callback_prefix import X,Y
from test_v789_alarm_suffix import A,B
Z=b'V813_CALLBACK_TIME_RESULT original_return=1 abi=1 leaves=3 system_visits=25 leaf_visits=18 polls=1 reads=3 offset=1 follow=3 continuation_executed=0 callback_return=0 boot_verified=0'
class TimeAudit(unittest.TestCase):
    def test_valid(self):
        with patch('audit_v809_callback_prefix.alarm',return_value=('',True)):
            for p in (1,2,3,4,12):
                z=Z.replace(b'polls=1',f'polls={p}'.encode()).replace(b'reads=3',f'reads={3*p}'.encode()).replace(b'leaf_visits=18',f'leaf_visits={18+5*(p-1)}'.encode())
                row,ok=inspect(b'\n'.join((A,B,X,Y,TIME_ENTRY,z)),0)
                self.assertTrue(ok);self.assertIn('original_time_return=1',row)
    def test_refusals(self):
        with patch('audit_v809_callback_prefix.alarm',return_value=('',True)):
            for tail in ((TIME_ENTRY,), (Z,TIME_ENTRY),(TIME_ENTRY,Z,Z),(TIME_ENTRY,TIME_ENTRY,Z),
                         (TIME_ENTRY,Z.replace(b'offset=1',b'offset=0')),
                         (TIME_ENTRY,Z.replace(b'leaf_visits=18',b'leaf_visits=20')),
                         (TIME_ENTRY,Z.replace(b'polls=1',b'polls=2')),
                         (TIME_ENTRY,Z.replace(b'leaf_visits=18',b'leaf_visits=78').replace(b'polls=1',b'polls=13').replace(b'reads=3',b'reads=39')),
                         (TIME_ENTRY,Z.replace(b'reads=3',b'reads=4')),
                         (TIME_ENTRY,Z.replace(b'callback_return=0',b'callback_return=1')),
                         (TIME_ENTRY,Z.replace(b'boot_verified=0',b'boot_verified=1')),
                         (TIME_ENTRY,Z.replace(b'follow=3',b'follow=2')),
                         (TIME_ENTRY,Z,b'V813_CALLBACK_TIME_INVALID kind=4 stage=4 witness=5 device=0 visits=45 cursor=3')):
                self.assertFalse(inspect(b'\n'.join((A,B,X,Y,*tail)),0)[1])
            self.assertFalse(inspect(b'\n'.join((A,B,X,Y,TIME_ENTRY,Z)),126)[1])
            self.assertFalse(inspect(b'\n'.join((TIME_ENTRY,A,B,X,Y,TIME_ENTRY,Z)),0)[1])
            self.assertFalse(inspect(b'\n'.join((A,B,Y,TIME_ENTRY,Z)),0)[1])
        with patch('audit_v809_callback_prefix.alarm',return_value=('',False)):
            self.assertFalse(inspect(b'\n'.join((A,B,X,Y,TIME_ENTRY,Z)),0)[1])
if __name__=='__main__':unittest.main()
