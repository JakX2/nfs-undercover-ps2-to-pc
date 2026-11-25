import unittest
from unittest.mock import patch
from audit_v848_wireless_wrapper import inspect
from test_v836_callback_frontier import P,F,FRONTIER_ENTRY

Q=(*P,FRONTIER_ENTRY,F)
E=b'V847_WIRELESS_ENTRY frontier=1 ordinal=3 changed=0'
R=b'V847_WIRELESS_RESULT ordinal=3 changed=0 visits=62 writes=12 returned=1 lock_entry=0 exi_executed=0 callback_return=0 boot_verified=0'
EC=E.replace(b'changed=0',b'changed=1')
RC=R.replace(b'changed=0',b'changed=1').replace(b'returned=1 lock_entry=0',b'returned=0 lock_entry=1')
QG=(*P,FRONTIER_ENTRY,F.replace(b'ordinal=3',b'ordinal=5').replace(b'zero_id=1',b'zero_id=0'))
EG=E.replace(b'ordinal=3',b'ordinal=5')
RG=R.replace(b'ordinal=3',b'ordinal=5')

class WrapperAudit(unittest.TestCase):
    def check(self,rows,rc=0):
        with patch('audit_v809_callback_prefix.alarm',return_value=('',True)):
            return inspect(b'\n'.join(rows),rc)

    def test_three_lanes(self):
        for q,e,r,marker in ((Q,E,R,'original_return=1'),(Q,EC,RC,'exilock_entry=1'),(QG,EG,RG,'original_return=1')):
            with self.subTest(marker=marker,e=e):
                row,ok=self.check((*q,e,r))
                self.assertTrue(ok);self.assertIn(marker,row);self.assertIn('callback_return=0',row)

    def test_bad_order_and_duplicates(self):
        for tail in ((),(E,),(R,E),(E,R,R),(E,E,R),(E,R,E),
                     (E,R,b'V847_WIRELESS_INVALID kind=4 stage=1 witness=4 device=0 visits=8 writes=2'),(E,R,F)):
            with self.subTest(tail=tail):self.assertFalse(self.check((*Q,*tail))[1])
        self.assertFalse(self.check((E,*Q,E,R))[1])
        self.assertFalse(self.check((*Q,E,R),126)[1])
        self.assertFalse(self.check((*Q[:-1],E,R))[1])

    def test_false_completion_and_geometry(self):
        for r in (R.replace(b'visits=62',b'visits=321'),R.replace(b'visits=62',b'visits=0'),
                  R.replace(b'writes=12',b'writes=65'),R.replace(b'writes=12',b'writes=62'),
                  R.replace(b'ordinal=3',b'ordinal=5'),R.replace(b'changed=0',b'changed=1'),
                  R.replace(b'returned=1',b'returned=0'),R.replace(b'lock_entry=0',b'lock_entry=1'),
                  R.replace(b'exi_executed=0',b'exi_executed=1'),
                  R.replace(b'callback_return=0',b'callback_return=1'),
                  R.replace(b'boot_verified=0',b'boot_verified=1')):
            with self.subTest(r=r):self.assertFalse(self.check((*Q,E,r))[1])
        self.assertFalse(self.check((*Q,EG,RG))[1])
        self.assertFalse(self.check((*QG,EC.replace(b'ordinal=3',b'ordinal=5'),RC.replace(b'ordinal=3',b'ordinal=5')))[1])

if __name__=='__main__':unittest.main()
