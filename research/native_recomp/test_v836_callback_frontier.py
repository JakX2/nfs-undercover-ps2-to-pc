import unittest
from unittest.mock import patch
from audit_v836_callback_frontier import inspect,FRONTIER_ENTRY,TIME_ENTRY
from test_v809_callback_prefix import X,Y
from test_v789_alarm_suffix import A,B
from test_v822_callback_time import Z
P=(A,B,X,Y,TIME_ENTRY,Z)
F=b'V831_CALLBACK_FRONTIER_RESULT ordinal=3 visits=23 writes=3 zero_id=1 follow=3 store_bytes=1 wireless_executed=0 callback_return=0 boot_verified=0'
class FrontierAudit(unittest.TestCase):
    def test_valid(self):
        with patch('audit_v809_callback_prefix.alarm',return_value=('',True)):
            for f in (F,F.replace(b'zero_id=1',b'zero_id=0'),F.replace(b'ordinal=3',b'ordinal=5').replace(b'zero_id=1',b'zero_id=0')):
                row,ok=inspect(b'\n'.join((*P,FRONTIER_ENTRY,f)),0)
                self.assertTrue(ok);self.assertIn('verified=1',row)
    def test_refusals(self):
        with patch('audit_v809_callback_prefix.alarm',return_value=('',True)):
            for tail in ((FRONTIER_ENTRY,), (F,FRONTIER_ENTRY), (FRONTIER_ENTRY,F,F),
                (FRONTIER_ENTRY,FRONTIER_ENTRY,F),(FRONTIER_ENTRY,F.replace(b'ordinal=3',b'ordinal=4')),
                (FRONTIER_ENTRY,F.replace(b'ordinal=3',b'ordinal=5')),
                (FRONTIER_ENTRY,F.replace(b'visits=23',b'visits=28')),
                (FRONTIER_ENTRY,F.replace(b'visits=23',b'visits=3')),
                (FRONTIER_ENTRY,F.replace(b'writes=3',b'writes=4')),
                (FRONTIER_ENTRY,F.replace(b'follow=3',b'follow=2')),
                (FRONTIER_ENTRY,F.replace(b'store_bytes=1',b'store_bytes=0')),
                (FRONTIER_ENTRY,F.replace(b'wireless_executed=0',b'wireless_executed=1')),
                (FRONTIER_ENTRY,F.replace(b'callback_return=0',b'callback_return=1')),
                (FRONTIER_ENTRY,F.replace(b'boot_verified=0',b'boot_verified=1')),
                (FRONTIER_ENTRY,F,b'V831_CALLBACK_FRONTIER_INVALID kind=4 stage=1 witness=4 device=0 visits=8 writes=2'),
                (FRONTIER_ENTRY,F,Z)):
                self.assertFalse(inspect(b'\n'.join((*P,*tail)),0)[1])
            self.assertFalse(inspect(b'\n'.join((*P,FRONTIER_ENTRY,F)),126)[1])
            self.assertFalse(inspect(b'\n'.join((FRONTIER_ENTRY,*P,FRONTIER_ENTRY,F)),0)[1])
            self.assertFalse(inspect(b'\n'.join((*P[:-1],FRONTIER_ENTRY,F)),0)[1])
if __name__=='__main__':unittest.main()
