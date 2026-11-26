import unittest
from unittest.mock import patch
import audit_v1054_third_alarm as a
from test_v1041_transfer_abi import D,H,T,A
R=b'V1048_THIRD_ALARM_RETURN original_return=1 queue=1 token=3 lane=0 timer=0 calls=3 visits=33 suffix_visits=6 status_reads=0 status_writes=0 token_held=1 saved_fields=38 handler_instruction_executed=0 boot_verified=0'
class Audit(unittest.TestCase):
    def test_prefix_independent_of_alarm(self):
        prior=b'\n'.join((D,H,T,A,a.third.third.RESULT))
        with patch.object(a.old,'inspect',return_value=('verified=1 branch=4 admitted=0',True)):
            self.assertTrue(a.transfer_prefix(prior))
            self.assertTrue(a.transfer_prefix(prior+b'\nV1048_THIRD_ALARM_FAULT route=2 alarm=0 queue=0 stage=1'))
            self.assertTrue(a.transfer_prefix(prior+b'\n'+R))
            for bad in (prior+b'\n'+a.third.third.RESULT,
                        prior.replace(b'token=3',b'token=2'),
                        b'\n'.join((D,H,T,A)),
                        prior.replace(A,b'V1040_TRANSFER_ABI admission=0 timing_only=0 unchanged_slot=0 call_executed=0 boot_verified=0')):
                self.assertFalse(a.transfer_prefix(bad))
            self.assertFalse(a.inspect(prior,126)[1])
    def test_order_and_exact_alarm(self):
        prior=b'\n'.join((D,H,T,A,a.third.third.RESULT))
        with patch.object(a.old,'inspect',return_value=('verified=1 branch=4 admitted=0',True)):
            self.assertTrue(a.inspect(prior+b'\n'+R,0)[1])
            for bad in (R.replace(b'token=3',b'token=2'),R.replace(b'visits=33',b'visits=32'),R.replace(b'calls=3',b'calls=1'),
                        R.replace(b'lane=0',b'lane=4'),R.replace(b'timer=0',b'timer=1'),R.replace(b'suffix_visits=6',b'suffix_visits=7'),
                        R.replace(b'status_reads=0',b'status_reads=1'),R.replace(b'status_writes=0',b'status_writes=1'),R+b'\n'+R,R+b'\nV958_ACK_INVALID',
                        R.replace(b'handler_instruction_executed=0',b'handler_instruction_executed=1')):
                self.assertFalse(a.inspect(prior+b'\n'+bad,0)[1])
            self.assertFalse(a.inspect(prior,0)[1])
            self.assertFalse(a.inspect(prior+b'\n'+R,126)[1])
            self.assertFalse(a.inspect(b'\n'.join((D,H,T,A,R)),0)[1])
            self.assertFalse(a.inspect(prior+b'\n'+R.replace(b'status_reads=0 status_writes=0',b'status_reads=1 status_writes=1'),0)[1])

class PostAlarmAudit(unittest.TestCase):
    def test_chain(self):
        import audit_v1101_postalarm as p
        hand=p.HANDOFF
        end=b'V1095_AFTER_ALARM_PREFIX original_indirect=1 original_prologue=1 save_return=1 suffix_visits=2 visits=13 writes=8 token=3 held=1 saved_fields=38 continuation_executed=0 boot_verified=0'
        transfer=a.third.third.RESULT
        prior=(D,H,T,A,transfer)
        def inspect(*rows,rc=0):return p.inspect(b'\n'.join(rows),rc)[1]
        with patch.object(a.old,'inspect',return_value=('verified=1 branch=4 admitted=0',True)):
            self.assertTrue(inspect(*prior,hand,R,end))
            self.assertTrue(inspect(*prior,hand,R,end.replace(b'suffix_visits=2',b'suffix_visits=256')))
            for bad in (end.replace(b'suffix_visits=2',b'suffix_visits=0'),
                        end.replace(b'suffix_visits=2',b'suffix_visits=257'),
                        end.replace(b'visits=13',b'visits=12'),
                        end.replace(b'writes=8',b'writes=7'),
                        end.replace(b'token=3',b'token=2'),
                        end.replace(b'held=1',b'held=0'),
                        end.replace(b'saved_fields=38',b'saved_fields=37'),
                        end.replace(b'continuation_executed=0',b'continuation_executed=1'),
                        end.replace(b'boot_verified=0',b'boot_verified=1'),
                        b'V1095_AFTER_ALARM_FAULT route=2 prefix=0 stage=1'):
                with self.subTest(bad=bad):self.assertFalse(inspect(*prior,hand,R,bad))
            for rows in ((*prior,R,end),(*prior,R,hand,end),(*prior,hand,end,R),
                         (*prior,hand,hand,R,end),(*prior,hand,R,end,end),
                         (*prior,hand,R,b'V1087_ALARM_SEAM kind=1 stage=2 reason=3',end),
                         (*prior,hand,R,end,b'V958_ACK_INVALID'),
                         (*prior,hand,R,end,b'V1101_POSTALARM_CENSUS verified=1'),
                         (*prior[:-1],hand,R,end),(*prior,hand,end),(*prior,hand,R)):
                with self.subTest(rows=rows[-3:]):self.assertFalse(inspect(*rows))
            self.assertFalse(inspect(*prior,hand,R,end,rc=126))
            self.assertFalse(inspect(*prior,hand,R.replace(b'token=3',b'token=2'),end))

class PostAlarmTimeAudit(unittest.TestCase):
    def test_order_and_exact_time(self):
        import audit_v1107_postalarm_time as t
        p=t.prefix
        prefix=b'V1095_AFTER_ALARM_PREFIX original_indirect=1 original_prologue=1 save_return=1 suffix_visits=2 visits=13 writes=8 token=3 held=1 saved_fields=38 continuation_executed=0 boot_verified=0'
        result=t.RESULT
        prior=(D,H,T,A,a.third.third.RESULT,p.HANDOFF,R,prefix)
        def inspect(*rows,rc=0):return t.inspect(b'\n'.join(rows),rc)[1]
        with patch.object(a.old,'inspect',return_value=('verified=1 branch=4 admitted=0',True)):
            self.assertTrue(inspect(*prior,result))
            for old,new in ((b'leaves=3',b'leaves=2'),(b'system_visits=25',b'system_visits=24'),(b'leaf_visits=18',b'leaf_visits=19'),
                            (b'polls=1',b'polls=0'),(b'reads=3',b'reads=4'),(b'offset=1',b'offset=0'),(b'token=3',b'token=4'),
                            (b'held=1',b'held=0'),(b'saved_fields=38',b'saved_fields=37'),
                            (b'continuation_executed=0',b'continuation_executed=1'),(b'boot_verified=0',b'boot_verified=1')):
                with self.subTest(old=old):self.assertFalse(inspect(*prior,result.replace(old,new)))
            for rows in ((*prior,),(*prior[:-1],result),(*prior[:-1],result,prefix),
                         (*prior,prefix,result),(*prior,result,result),(*prior,result,b'V1107_POSTALARM_TIME_CENSUS verified=1'),
                         (*prior,b'V1103_POSTALARM_TIME_FAULT route=8 witness=3 stage=4',result),
                         (*prior,result,b'V958_ACK_INVALID'),(*prior,b'V1087_ALARM_SEAM kind=1 stage=2 reason=3',result)):
                with self.subTest(rows=rows[-3:]):self.assertFalse(inspect(*rows))
            self.assertFalse(inspect(*prior,result,rc=126))
            self.assertFalse(inspect(*prior[:-1],prefix.replace(b'visits=13',b'visits=12'),result))

class PostAlarmFrontierAudit(unittest.TestCase):
    def test_order_and_exact_frontier(self):
        import audit_v1114_postalarm_frontier as f
        p=f.prefix
        prefix=b'V1095_AFTER_ALARM_PREFIX original_indirect=1 original_prologue=1 save_return=1 suffix_visits=2 visits=13 writes=8 token=3 held=1 saved_fields=38 continuation_executed=0 boot_verified=0'
        prior=(D,H,T,A,a.third.third.RESULT,p.HANDOFF,R,prefix,f.time.RESULT)
        result=f.RESULT
        def inspect(*rows,rc=0):return f.inspect(b'\n'.join(rows),rc)[1]
        with patch.object(a.old,'inspect',return_value=('verified=1 branch=4 admitted=0',True)):
            self.assertTrue(inspect(*prior,result))
            for old,new in ((b'ordinal=3',b'ordinal=5'),(b'visits=17',b'visits=16'),(b'writes=3',b'writes=2'),
                            (b'zero_id=1',b'zero_id=0'),(b'token=3',b'token=4'),(b'held=1',b'held=0'),
                            (b'saved_fields=38',b'saved_fields=37'),(b'call_executed=0',b'call_executed=1'),
                            (b'boot_verified=0',b'boot_verified=1')):
                with self.subTest(old=old):self.assertFalse(inspect(*prior,result.replace(old,new)))
            for rows in ((*prior,),(*prior[:-1],result),(*prior[:-1],result,f.time.RESULT),
                         (*prior,f.time.RESULT,result),(*prior,result,result),(*prior,result,b'V1114_POSTALARM_FRONTIER_CENSUS verified=1'),
                         (*prior,b'V1111_POSTALARM_FRONTIER_FAULT route=11 witness=3 stage=6',result),
                         (*prior,result,b'V958_ACK_INVALID'),(*prior,b'V1087_ALARM_SEAM kind=1 stage=2 reason=3',result)):
                with self.subTest(rows=rows[-3:]):self.assertFalse(inspect(*rows))
            self.assertFalse(inspect(*prior,result,rc=126))
            self.assertFalse(inspect(*prior[:-1],f.time.RESULT.replace(b'reads=3',b'reads=2'),result))

if __name__=='__main__':unittest.main()
