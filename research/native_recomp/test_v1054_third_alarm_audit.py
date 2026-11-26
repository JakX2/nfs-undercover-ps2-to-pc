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

class PostAlarmWirelessAudit(unittest.TestCase):
    def test_order_and_exact_wireless(self):
        import audit_v1121_postalarm_wireless as w
        p=w.prefix
        prefix=b'V1095_AFTER_ALARM_PREFIX original_indirect=1 original_prologue=1 save_return=1 suffix_visits=2 visits=13 writes=8 token=3 held=1 saved_fields=38 continuation_executed=0 boot_verified=0'
        prior=(D,H,T,A,a.third.third.RESULT,p.HANDOFF,R,prefix,w.time.RESULT,w.frontier.RESULT)
        result=w.RESULT
        def inspect(*rows,rc=0):return w.inspect(b'\n'.join(rows),rc)[1]
        with patch.object(a.old,'inspect',return_value=('verified=1 branch=4 admitted=0',True)):
            self.assertTrue(inspect(*prior,result))
            for old,new in ((b'original_setter=1',b'original_setter=0'),(b'original_unlock=1',b'original_unlock=0'),
                            (b'changed=0',b'changed=1'),(b'visits=66',b'visits=65'),(b'stores=12',b'stores=11'),
                            (b'token=3',b'token=4'),(b'held=1',b'held=0'),(b'saved_fields=38',b'saved_fields=37'),
                            (b'continuation_executed=0',b'continuation_executed=1'),(b'boot_verified=0',b'boot_verified=1')):
                with self.subTest(old=old):self.assertFalse(inspect(*prior,result.replace(old,new)))
            for rows in ((*prior,),(*prior[:-1],result),(*prior[:-1],result,w.frontier.RESULT),
                         (*prior,w.frontier.RESULT,result),(*prior,result,result),(*prior,result,b'V1121_POSTALARM_WIRELESS_CENSUS verified=1'),
                         (*prior,b'V1118_POSTALARM_WIRELESS_FAULT route=13 witness=5 stage=8',result),
                         (*prior,result,b'V958_ACK_INVALID'),(*prior,b'V1087_ALARM_SEAM kind=1 stage=2 reason=3',result)):
                with self.subTest(rows=rows[-3:]):self.assertFalse(inspect(*rows))
            self.assertFalse(inspect(*prior,result,rc=126))
            self.assertFalse(inspect(*prior[:-1],w.frontier.RESULT.replace(b'zero_id=1',b'zero_id=0'),result))

class PostAlarmSuffixAudit(unittest.TestCase):
    def test_order_and_exact_suffix(self):
        import audit_v1127_postalarm_suffix as s
        p=s.prefix
        prefix=b'V1095_AFTER_ALARM_PREFIX original_indirect=1 original_prologue=1 save_return=1 suffix_visits=2 visits=13 writes=8 token=3 held=1 saved_fields=38 continuation_executed=0 boot_verified=0'
        prior=(D,H,T,A,a.third.third.RESULT,p.HANDOFF,R,prefix,s.time.RESULT,s.frontier.RESULT,s.wireless.RESULT)
        result=s.RESULT
        def inspect(*rows,rc=0):return s.inspect(b'\n'.join(rows),rc)[1]
        with patch.object(a.old,'inspect',return_value=('verified=1 branch=4 admitted=0',True)):
            self.assertTrue(inspect(*prior,result))
            for old,new in ((b'ordinal=13',b'ordinal=4'),(b'target_class=0',b'target_class=3'),
                            (b'visits=37',b'visits=36'),(b'writes=0',b'writes=1'),(b'polls=4',b'polls=3'),
                            (b'token=3',b'token=4'),(b'held=1',b'held=0'),(b'saved_fields=38',b'saved_fields=37'),
                            (b'call_executed=0',b'call_executed=1'),(b'boot_verified=0',b'boot_verified=1')):
                with self.subTest(old=old):self.assertFalse(inspect(*prior,result.replace(old,new)))
            for rows in ((*prior,),(*prior[:-1],result),(*prior[:-1],result,s.wireless.RESULT),
                         (*prior,s.wireless.RESULT,result),(*prior,result,result),(*prior,result,b'V1127_POSTALARM_SUFFIX_CENSUS verified=1'),
                         (*prior,b'V1123_POSTALARM_SUFFIX_FAULT route=16 witness=5 stage=10',result),
                         (*prior,result,b'V958_ACK_INVALID'),(*prior,b'V1087_ALARM_SEAM kind=1 stage=2 reason=3',result)):
                with self.subTest(rows=rows[-3:]):self.assertFalse(inspect(*rows))
            self.assertFalse(inspect(*prior,result,rc=126))
            self.assertFalse(inspect(*prior[:-1],s.wireless.RESULT.replace(b'visits=66',b'visits=65'),result))

class PostAlarmReturnAudit(unittest.TestCase):
    def test_order_and_exact_return(self):
        import audit_v1135_postalarm_return as r
        p=r.prefix
        prefix=b'V1095_AFTER_ALARM_PREFIX original_indirect=1 original_prologue=1 save_return=1 suffix_visits=2 visits=13 writes=8 token=3 held=1 saved_fields=38 continuation_executed=0 boot_verified=0'
        prior=(D,H,T,A,a.third.third.RESULT,p.HANDOFF,R,prefix,r.time.RESULT,r.frontier.RESULT,r.wireless.RESULT,r.suffix.RESULT)
        result=r.RESULT
        def inspect(*rows,rc=0):return r.inspect(b'\n'.join(rows),rc)[1]
        with patch.object(a.old,'inspect',return_value=('verified=1 branch=4 admitted=0',True)):
            self.assertTrue(inspect(*prior,result))
            for old,new in ((b'original_restore=1',b'original_restore=0'),(b'original_return=1',b'original_return=0'),
                            (b'visits=12',b'visits=11'),(b'token=3',b'token=4'),(b'held=1',b'held=0'),
                            (b'saved_fields=38',b'saved_fields=37'),(b'handler_instruction_executed=0',b'handler_instruction_executed=1'),
                            (b'boot_verified=0',b'boot_verified=1')):
                with self.subTest(old=old):self.assertFalse(inspect(*prior,result.replace(old,new)))
            for rows in ((*prior,),(*prior[:-1],result),(*prior[:-1],result,r.suffix.RESULT),
                         (*prior,r.suffix.RESULT,result),(*prior,result,result),(*prior,result,b'V1135_POSTALARM_RETURN_CENSUS verified=1'),
                         (*prior,b'V1132_POSTALARM_RETURN_FAULT route=19 witness=5 stage=12',result),
                         (*prior,result,b'V958_ACK_INVALID'),(*prior,b'V1087_ALARM_SEAM kind=1 stage=2 reason=3',result)):
                with self.subTest(rows=rows[-3:]):self.assertFalse(inspect(*rows))
            self.assertFalse(inspect(*prior,result,rc=126))
            self.assertFalse(inspect(*prior[:-1],r.suffix.RESULT.replace(b'visits=37',b'visits=36'),result))


class PostAlarmHandlerAudit(unittest.TestCase):
    def test_exact_handler(self):
        import audit_v1143_postalarm_handler as h
        r=h.ret;p=r.prefix
        prefix=b'V1095_AFTER_ALARM_PREFIX original_indirect=1 original_prologue=1 save_return=1 suffix_visits=11 visits=13 writes=8 token=3 held=1 saved_fields=38 continuation_executed=0 boot_verified=0'
        prior=(D,H,T,A,a.third.third.RESULT,p.HANDOFF,R,prefix,r.time.RESULT,r.frontier.RESULT,r.wireless.RESULT,r.suffix.RESULT,r.RESULT)
        result=h.RESULT
        def inspect(*rows,rc=0):return h.inspect(b'\n'.join(rows),rc)[1]
        with patch.object(a.old,'inspect',return_value=('verified=1 branch=4 admitted=0',True)):
            self.assertTrue(inspect(*prior,result))
            for old,new in ((b'ordinal=12',b'ordinal=8'),(b'branch_taken=1',b'branch_taken=0'),
                            (b'visits=20',b'visits=21'),(b'stores=0',b'stores=1'),
                            (b'status_reads=1',b'status_reads=0'),(b'status_writes=1',b'status_writes=0'),
                            (b'token=3',b'token=4'),(b'held=1',b'held=0'),(b'saved_fields=38',b'saved_fields=37'),
                            (b'call_executed=0',b'call_executed=1'),(b'boot_verified=0',b'boot_verified=1')):
                with self.subTest(old=old):self.assertFalse(inspect(*prior,result.replace(old,new)))
            for rows in ((*prior,),(*prior[:-1],result),(*prior[:-1],result,r.RESULT),
                         (*prior,r.RESULT,result),(*prior,result,result),(*prior,result,b'V1143_POSTALARM_HANDLER_CENSUS verified=1'),
                         (*prior,b'V1139_POSTALARM_HANDLER_FAULT route=23 witness=3 stage=14',result),
                         (*prior,result,b'V958_ACK_INVALID'),(*prior,b'V1087_ALARM_SEAM kind=1 stage=2 reason=3',result)):
                with self.subTest(rows=rows[-3:]):self.assertFalse(inspect(*rows))
            self.assertFalse(inspect(*prior,result,rc=126))
            self.assertFalse(inspect(*prior[:-1],r.RESULT.replace(b'visits=12',b'visits=11'),result))


class PostAlarmHandlerReturnAudit(unittest.TestCase):
    def test_exact_return(self):
        import audit_v1148_postalarm_handler_return as h
        r=h.ret;p=r.prefix
        prefix=b'V1095_AFTER_ALARM_PREFIX original_indirect=1 original_prologue=1 save_return=1 suffix_visits=11 visits=13 writes=8 token=3 held=1 saved_fields=38 continuation_executed=0 boot_verified=0'
        prior=(D,H,T,A,a.third.third.RESULT,p.HANDOFF,R,prefix,r.time.RESULT,r.frontier.RESULT,r.wireless.RESULT,r.suffix.RESULT,r.RESULT,h.handler.RESULT)
        result=h.RESULT
        def inspect(*rows,rc=0):return h.inspect(b'\n'.join(rows),rc)[1]
        with patch.object(a.old,'inspect',return_value=('verified=1 branch=4 admitted=0',True)):
            self.assertTrue(inspect(*prior,result))
            for old,new in ((b'original_restore=1',b'original_restore=0'),(b'original_return=1',b'original_return=0'),
                            (b'visits=21',b'visits=20'),(b'restored_gprs=15',b'restored_gprs=14'),
                            (b'token=3',b'token=4'),(b'held=1',b'held=0'),(b'saved_fields=38',b'saved_fields=37'),
                            (b'dispatcher_instruction_executed=0',b'dispatcher_instruction_executed=1'),(b'boot_verified=0',b'boot_verified=1')):
                with self.subTest(old=old):self.assertFalse(inspect(*prior,result.replace(old,new)))
            for rows in ((*prior,),(*prior[:-1],result),(*prior[:-1],result,h.handler.RESULT),
                         (*prior,h.handler.RESULT,result),(*prior,result,result),(*prior,result,b'V1148_POSTALARM_HANDLER_RETURN_CENSUS verified=1'),
                         (*prior,b'V1145_POSTALARM_HANDLER_RETURN_FAULT route=26 witness=3 native=4 stage=16',result),
                         (*prior,result,b'V958_ACK_INVALID')):
                with self.subTest(rows=rows[-3:]):self.assertFalse(inspect(*rows))
            self.assertFalse(inspect(*prior,result,rc=126))
            self.assertFalse(inspect(*prior[:-1],h.handler.RESULT.replace(b'visits=20',b'visits=19'),result))


class HeldEpilogueAudit(unittest.TestCase):
    def test_exact_held_rfi_and_vector(self):
        import audit_v1156_held_epilogue as h
        r=h.ret;p=r.prefix
        prefix=b'V1095_AFTER_ALARM_PREFIX original_indirect=1 original_prologue=1 save_return=1 suffix_visits=11 visits=13 writes=8 token=3 held=1 saved_fields=38 continuation_executed=0 boot_verified=0'
        prior=(D,H,T,A,a.third.third.RESULT,p.HANDOFF,R,prefix,r.time.RESULT,r.frontier.RESULT,r.wireless.RESULT,r.suffix.RESULT,r.RESULT,h.handler.RESULT,h.returned.RESULT)
        def inspect(*rows,rc=0):return h.inspect(b'\n'.join(rows),rc)[1]
        with patch.object(a.old,'inspect',return_value=('verified=1 branch=4 admitted=0',True)):
            self.assertTrue(inspect(*prior,h.RFI,h.RESULT))
            for old,new in ((b'visits=82',b'visits=81'),(b'native_rfi=1',b'native_rfi=0'),(b'pending_exception=1',b'pending_exception=0'),(b'held=1',b'held=0'),(b'resumed_instruction_executed=0',b'resumed_instruction_executed=1')):
                self.assertFalse(inspect(*prior,h.RFI.replace(old,new),h.RESULT))
            for old,new in ((b'vector_visits=34',b'vector_visits=2'),(b'trampoline_visits=20',b'trampoline_visits=2'),(b'saved_fields=38',b'saved_fields=37'),(b'token=3',b'token=4'),(b'dispatcher_instruction_executed=0',b'dispatcher_instruction_executed=1'),(b'boot_verified=0',b'boot_verified=1')):
                self.assertFalse(inspect(*prior,h.RFI,h.RESULT.replace(old,new)))
            for rows in ((*prior,),(*prior,h.RFI),(*prior,h.RESULT),(*prior,h.RESULT,h.RFI),(*prior,h.RFI,h.RFI,h.RESULT),(*prior,h.RFI,h.RESULT,h.RESULT),(*prior[:-1],h.RFI,h.RESULT),(*prior,h.RFI,b'V1151_HELD_EPILOGUE_FAULT stage=4 reason=5 epilogue=0 reentry=6',h.RESULT),(*prior,h.RFI,h.RESULT,b'V958_ACK_INVALID')):
                self.assertFalse(inspect(*rows))
            self.assertFalse(inspect(*prior,h.RFI,h.RESULT,rc=126))


class HeldDispatchAudit(unittest.TestCase):
    def test_exact_third_dispatch(self):
        import audit_v1163_held_dispatch as h
        r=h.ret;p=r.prefix
        prefix=b'V1095_AFTER_ALARM_PREFIX original_indirect=1 original_prologue=1 save_return=1 suffix_visits=11 visits=13 writes=8 token=3 held=1 saved_fields=38 continuation_executed=0 boot_verified=0'
        prior=(D,H,T,A,a.third.third.RESULT,p.HANDOFF,R,prefix,r.time.RESULT,r.frontier.RESULT,r.wireless.RESULT,r.suffix.RESULT,r.RESULT,h.handler.RESULT,h.returned.RESULT,h.epilogue.RFI,h.epilogue.RESULT)
        def inspect(*rows,rc=0):return h.inspect(b'\n'.join(rows),rc)[1]
        with patch.object(a.old,'inspect',return_value=('verified=1 branch=4 admitted=0',True)):
            self.assertTrue(inspect(*prior,h.RESULT))
            for old,new in ((b'visits=153',b'visits=10'),(b'entries=5',b'entries=4'),(b'pi_reads=2',b'pi_reads=1'),
                            (b'polls=10',b'polls=4'),(b'original_leaves=4',b'original_leaves=3'),
                            (b'original_indirect=1',b'original_indirect=0'),(b'token=3',b'token=4'),(b'held=1',b'held=0'),
                            (b'saved_fields=38',b'saved_fields=37'),(b'handler_instruction_executed=0',b'handler_instruction_executed=1'),
                            (b'boot_verified=0',b'boot_verified=1')):
                self.assertFalse(inspect(*prior,h.RESULT.replace(old,new)))
            for rows in ((*prior,),(*prior[:-1],h.RESULT),(*prior[:-1],h.RESULT,h.epilogue.RESULT),
                         (*prior,h.RESULT,h.RESULT),(*prior,h.epilogue.RESULT,h.RESULT),
                         (*prior,b'V1151_HELD_EPILOGUE_FAULT stage=6 reason=7 epilogue=0 reentry=9',h.RESULT),
                         (*prior,h.RESULT,b'V1163_HELD_DISPATCH_CENSUS verified=1'),(*prior,h.RESULT,b'V958_ACK_INVALID')):
                self.assertFalse(inspect(*rows))
            self.assertFalse(inspect(*prior,h.RESULT,rc=126))


class ThirdAckAudit(unittest.TestCase):
    def test_exact_ack(self):
        import audit_v1171_third_ack as h
        r=h.ret;p=r.prefix
        prefix=b'V1095_AFTER_ALARM_PREFIX original_indirect=1 original_prologue=1 save_return=1 suffix_visits=11 visits=13 writes=8 token=3 held=1 saved_fields=38 continuation_executed=0 boot_verified=0'
        prior=(D,H,T,A,a.third.third.RESULT,p.HANDOFF,R,prefix,r.time.RESULT,r.frontier.RESULT,r.wireless.RESULT,r.suffix.RESULT,r.RESULT,h.handler.RESULT,h.returned.RESULT,h.epilogue.RFI,h.epilogue.RESULT,h.dispatch.RESULT)
        def inspect(*rows,rc=0):return h.inspect(b'\n'.join(rows),rc)[1]
        with patch.object(a.old,'inspect',return_value=('verified=1 branch=4 admitted=0',True)):
            self.assertTrue(inspect(*prior,h.RESULT))
            for old,new in ((b'visits=48',b'visits=8'),(b'entries=2',b'entries=1'),(b'returns=1',b'returns=0'),
                            (b'reads=3',b'reads=1'),(b'writes=1',b'writes=2'),(b'original_w1c=1',b'original_w1c=0'),
                            (b'next_label=1',b'next_label=0'),(b'token=3',b'token=4'),(b'no_response=1',b'no_response=0'),
                            (b'saved_fields=38',b'saved_fields=37'),(b'retired_transfer=1',b'retired_transfer=0'),
                            (b'pi_cleared=1',b'pi_cleared=0'),(b'successor_executed=0',b'successor_executed=1'),
                            (b'boot_verified=0',b'boot_verified=1')):
                self.assertFalse(inspect(*prior,h.RESULT.replace(old,new)))
            for rows in ((*prior,),(*prior[:-1],h.RESULT),(*prior[:-1],h.RESULT,h.dispatch.RESULT),
                         (*prior,h.RESULT,h.RESULT),(*prior,h.dispatch.RESULT,h.RESULT),
                         (*prior,b'V1151_HELD_EPILOGUE_FAULT stage=8 reason=10 epilogue=0 reentry=11',h.RESULT),
                         (*prior,h.RESULT,b'V1171_THIRD_ACK_CENSUS verified=1'),(*prior,h.RESULT,b'V958_ACK_INVALID')):
                self.assertFalse(inspect(*rows))
            self.assertFalse(inspect(*prior,h.RESULT,rc=126))


class AckHelperAudit(unittest.TestCase):
    def test_exact_helper(self):
        import audit_v1177_ack_helper as h
        r=h.ret;p=r.prefix
        prefix=b'V1095_AFTER_ALARM_PREFIX original_indirect=1 original_prologue=1 save_return=1 suffix_visits=11 visits=13 writes=8 token=3 held=1 saved_fields=38 continuation_executed=0 boot_verified=0'
        prior=(D,H,T,A,a.third.third.RESULT,p.HANDOFF,R,prefix,r.time.RESULT,r.frontier.RESULT,r.wireless.RESULT,r.suffix.RESULT,r.RESULT,h.handler.RESULT,h.returned.RESULT,h.epilogue.RFI,h.epilogue.RESULT,h.dispatch.RESULT,h.ack.RESULT)
        def inspect(*rows,rc=0):return h.inspect(b'\n'.join(rows),rc)[1]
        with patch.object(a.old,'inspect',return_value=('verified=1 branch=4 admitted=0',True)):
            self.assertTrue(inspect(*prior,h.RESULT))
            for old,new in ((b'visits=130',b'visits=13'),(b'entries=6',b'entries=5'),(b'returns=6',b'returns=5'),
                            (b'msr=2',b'msr=0'),(b'original_helper=1',b'original_helper=0'),(b'token=3',b'token=4'),
                            (b'saved_fields=38',b'saved_fields=37'),(b'pi_cleared=1',b'pi_cleared=0'),
                            (b'handler_instruction_executed=0',b'handler_instruction_executed=1'),
                            (b'boot_verified=0',b'boot_verified=1')):
                self.assertFalse(inspect(*prior,h.RESULT.replace(old,new)))
            for rows in ((*prior,),(*prior[:-1],h.RESULT),(*prior[:-1],h.RESULT,h.ack.RESULT),
                         (*prior,h.RESULT,h.RESULT),(*prior,h.ack.RESULT,h.RESULT),
                         (*prior,b'V1151_HELD_EPILOGUE_FAULT stage=10 reason=14 epilogue=0 reentry=11',h.RESULT),
                         (*prior,h.RESULT,b'V1177_ACK_HELPER_CENSUS verified=1'),(*prior,h.RESULT,b'V958_ACK_INVALID')):
                self.assertFalse(inspect(*rows))
            self.assertFalse(inspect(*prior,h.RESULT,rc=126))

class AckCallbackAudit(unittest.TestCase):
    def test_exact_frontier(self):
        import audit_v1182_ack_callback as c
        h=c.helper;r=h.ret;p=r.prefix
        prefix=b'V1095_AFTER_ALARM_PREFIX original_indirect=1 original_prologue=1 save_return=1 suffix_visits=11 visits=13 writes=8 token=3 held=1 saved_fields=38 continuation_executed=0 boot_verified=0'
        prior=(D,H,T,A,a.third.third.RESULT,p.HANDOFF,R,prefix,r.time.RESULT,r.frontier.RESULT,r.wireless.RESULT,r.suffix.RESULT,r.RESULT,h.handler.RESULT,h.returned.RESULT,h.epilogue.RFI,h.epilogue.RESULT,h.dispatch.RESULT,h.ack.RESULT,h.RESULT)
        def inspect(*rows,rc=0):return c.inspect(b'\n'.join(rows),rc)[1]
        with patch.object(a.old,'inspect',return_value=('verified=1 branch=4 admitted=0',True)):
            self.assertTrue(inspect(*prior,c.RESULT))
            for old,new in ((b'visits=71',b'visits=1'),(b'target_class=2',b'target_class=1'),(b'aligned=1',b'aligned=0'),(b'token=3',b'token=4'),(b'saved_fields=38',b'saved_fields=37'),(b'pi_cleared=1',b'pi_cleared=0'),(b'call_executed=0',b'call_executed=1'),(b'boot_verified=0',b'boot_verified=1')):
                self.assertFalse(inspect(*prior,c.RESULT.replace(old,new)))
            for rows in ((*prior,),(*prior[:-1],c.RESULT),(*prior[:-1],c.RESULT,h.RESULT),(*prior,c.RESULT,c.RESULT),(*prior,h.RESULT,c.RESULT),(*prior,h.FAULT,c.RESULT),(*prior,c.RESULT,b'V1182_ACK_CALLBACK_CENSUS verified=1')):
                self.assertFalse(inspect(*rows))
            self.assertFalse(inspect(*prior,c.RESULT,rc=126))
class AckPrefixAudit(unittest.TestCase):
    def test_exact_prefix(self):
        import audit_v1187_ack_prefix as c
        h=c.helper;r=h.ret;p=r.prefix
        prefix=b'V1095_AFTER_ALARM_PREFIX original_indirect=1 original_prologue=1 save_return=1 suffix_visits=11 visits=13 writes=8 token=3 held=1 saved_fields=38 continuation_executed=0 boot_verified=0'
        prior=(D,H,T,A,a.third.third.RESULT,p.HANDOFF,R,prefix,r.time.RESULT,r.frontier.RESULT,r.wireless.RESULT,r.suffix.RESULT,r.RESULT,h.handler.RESULT,h.returned.RESULT,h.epilogue.RFI,h.epilogue.RESULT,h.dispatch.RESULT,h.ack.RESULT,h.RESULT,c.callback.RESULT)
        def inspect(*rows,rc=0):return c.inspect(b'\n'.join(rows),rc)[1]
        with patch.object(a.old,'inspect',return_value=('verified=1 branch=4 admitted=0',True)):
            self.assertTrue(inspect(*prior,c.RESULT))
            for old,new in ((b'visits=13',b'visits=9'),(b'writes=8',b'writes=4'),(b'original_indirect=1',b'original_indirect=0'),(b'original_prologue=1',b'original_prologue=0'),(b'save_return=1',b'save_return=0'),(b'token=3',b'token=4'),(b'saved_fields=38',b'saved_fields=37'),(b'pi_cleared=1',b'pi_cleared=0'),(b'continuation_executed=0',b'continuation_executed=1'),(b'boot_verified=0',b'boot_verified=1')):
                self.assertFalse(inspect(*prior,c.RESULT.replace(old,new)))
            for rows in ((*prior,),(*prior[:-1],c.RESULT),(*prior[:-1],c.RESULT,c.callback.RESULT),(*prior,c.RESULT,c.RESULT),(*prior,c.callback.RESULT,c.RESULT),(*prior,b'V1151_HELD_EPILOGUE_FAULT stage=14 reason=18 epilogue=0 reentry=22',c.RESULT),(*prior,c.RESULT,b'V1187_ACK_PREFIX_CENSUS verified=1')):
                self.assertFalse(inspect(*rows))
            self.assertFalse(inspect(*prior,c.RESULT,rc=126))
class AckTimeAudit(unittest.TestCase):
    def test_exact_time(self):
        import audit_v1191_ack_time as c
        h=c.helper;r=h.ret;p=r.prefix
        prefix=b'V1095_AFTER_ALARM_PREFIX original_indirect=1 original_prologue=1 save_return=1 suffix_visits=11 visits=13 writes=8 token=3 held=1 saved_fields=38 continuation_executed=0 boot_verified=0'
        prior=(D,H,T,A,a.third.third.RESULT,p.HANDOFF,R,prefix,r.time.RESULT,r.frontier.RESULT,r.wireless.RESULT,r.suffix.RESULT,r.RESULT,h.handler.RESULT,h.returned.RESULT,h.epilogue.RFI,h.epilogue.RESULT,h.dispatch.RESULT,h.ack.RESULT,h.RESULT,c.callback.RESULT,c.prior_prefix.RESULT)
        def inspect(*rows,rc=0):return c.inspect(b'\n'.join(rows),rc)[1]
        with patch.object(a.old,'inspect',return_value=('verified=1 branch=4 admitted=0',True)):
            self.assertTrue(inspect(*prior,c.RESULT))
            for old,new in ((b'leaves=3',b'leaves=2'),(b'system_visits=25',b'system_visits=24'),(b'leaf_visits=18',b'leaf_visits=17'),(b'polls=1',b'polls=0'),(b'reads=3',b'reads=2'),(b'offset=1',b'offset=0'),(b'token=3',b'token=4'),(b'saved_fields=38',b'saved_fields=37'),(b'pi_cleared=1',b'pi_cleared=0'),(b'continuation_executed=0',b'continuation_executed=1'),(b'boot_verified=0',b'boot_verified=1')):
                self.assertFalse(inspect(*prior,c.RESULT.replace(old,new)))
            for rows in ((*prior,),(*prior[:-1],c.RESULT),(*prior[:-1],c.RESULT,c.prior_prefix.RESULT),(*prior,c.RESULT,c.RESULT),(*prior,c.prior_prefix.RESULT,c.RESULT),(*prior,b'V1151_HELD_EPILOGUE_FAULT stage=16 reason=20 epilogue=0 reentry=24',c.RESULT),(*prior,c.RESULT,b'V1191_ACK_TIME_CENSUS verified=1')):
                self.assertFalse(inspect(*rows))
            self.assertFalse(inspect(*prior,c.RESULT,rc=126))
class AckFrontierAudit(unittest.TestCase):
    def test_exact_frontier(self):
        import audit_v1194_ack_frontier as c
        h=c.helper;r=h.ret;p=r.prefix
        prefix=b'V1095_AFTER_ALARM_PREFIX original_indirect=1 original_prologue=1 save_return=1 suffix_visits=11 visits=13 writes=8 token=3 held=1 saved_fields=38 continuation_executed=0 boot_verified=0'
        prior=(D,H,T,A,a.third.third.RESULT,p.HANDOFF,R,prefix,r.time.RESULT,r.frontier.RESULT,r.wireless.RESULT,r.suffix.RESULT,r.RESULT,h.handler.RESULT,h.returned.RESULT,h.epilogue.RFI,h.epilogue.RESULT,h.dispatch.RESULT,h.ack.RESULT,h.RESULT,c.callback.RESULT,c.prior_prefix.RESULT,c.prior_time.RESULT)
        def inspect(*rows,rc=0):return c.inspect(b'\n'.join(rows),rc)[1]
        with patch.object(a.old,'inspect',return_value=('verified=1 branch=4 admitted=0',True)):
            self.assertTrue(inspect(*prior,c.RESULT))
            for old,new in ((b'ordinal=3',b'ordinal=5'),(b'visits=17',b'visits=4'),(b'writes=3',b'writes=1'),(b'zero_id=1',b'zero_id=0'),(b'token=3',b'token=4'),(b'saved_fields=38',b'saved_fields=37'),(b'pi_cleared=1',b'pi_cleared=0'),(b'call_executed=0',b'call_executed=1'),(b'boot_verified=0',b'boot_verified=1')):
                self.assertFalse(inspect(*prior,c.RESULT.replace(old,new)))
            for rows in ((*prior,),(*prior[:-1],c.RESULT),(*prior[:-1],c.RESULT,c.prior_time.RESULT),(*prior,c.RESULT,c.RESULT),(*prior,c.prior_time.RESULT,c.RESULT),(*prior,b'V1151_HELD_EPILOGUE_FAULT stage=18 reason=22 epilogue=0 reentry=28',c.RESULT),(*prior,c.RESULT,b'V1194_ACK_FRONTIER_CENSUS verified=1')):
                self.assertFalse(inspect(*rows))
            self.assertFalse(inspect(*prior,c.RESULT,rc=126))
class AckWirelessAudit(unittest.TestCase):
    def test_exact_wireless(self):
        import audit_v1198_ack_wireless as c
        h=c.helper;r=h.ret;p=r.prefix
        prefix=b'V1095_AFTER_ALARM_PREFIX original_indirect=1 original_prologue=1 save_return=1 suffix_visits=11 visits=13 writes=8 token=3 held=1 saved_fields=38 continuation_executed=0 boot_verified=0'
        prior=(D,H,T,A,a.third.third.RESULT,p.HANDOFF,R,prefix,r.time.RESULT,r.frontier.RESULT,r.wireless.RESULT,r.suffix.RESULT,r.RESULT,h.handler.RESULT,h.returned.RESULT,h.epilogue.RFI,h.epilogue.RESULT,h.dispatch.RESULT,h.ack.RESULT,h.RESULT,c.callback.RESULT,c.prior_prefix.RESULT,c.prior_time.RESULT,c.prior_frontier.RESULT)
        def inspect(*rows,rc=0):return c.inspect(b'\n'.join(rows),rc)[1]
        with patch.object(a.old,'inspect',return_value=('verified=1 branch=4 admitted=0',True)):
            self.assertTrue(inspect(*prior,c.RESULT))
            for old,new in ((b'original_setter=1',b'original_setter=0'),(b'original_unlock=1',b'original_unlock=0'),(b'changed=0',b'changed=1'),(b'visits=66',b'visits=11'),(b'stores=12',b'stores=1'),(b'token=3',b'token=4'),(b'saved_fields=38',b'saved_fields=37'),(b'pi_cleared=1',b'pi_cleared=0'),(b'continuation_executed=0',b'continuation_executed=1')):
                self.assertFalse(inspect(*prior,c.RESULT.replace(old,new)))
            for rows in ((*prior,),(*prior[:-1],c.RESULT),(*prior[:-1],c.RESULT,c.prior_frontier.RESULT),(*prior,c.RESULT,c.RESULT),(*prior,c.prior_frontier.RESULT,c.RESULT),(*prior,b'V1151_HELD_EPILOGUE_FAULT stage=20 reason=24 epilogue=0 reentry=30',c.RESULT)):
                self.assertFalse(inspect(*rows))
            self.assertFalse(inspect(*prior,c.RESULT,rc=126))
class AckSuffixAudit(unittest.TestCase):
    def test_exact_suffix(self):
        import audit_v1203_ack_suffix as c
        h=c.helper;r=h.ret;p=r.prefix
        prefix=b'V1095_AFTER_ALARM_PREFIX original_indirect=1 original_prologue=1 save_return=1 suffix_visits=11 visits=13 writes=8 token=3 held=1 saved_fields=38 continuation_executed=0 boot_verified=0'
        prior=(D,H,T,A,a.third.third.RESULT,p.HANDOFF,R,prefix,r.time.RESULT,r.frontier.RESULT,r.wireless.RESULT,r.suffix.RESULT,r.RESULT,h.handler.RESULT,h.returned.RESULT,h.epilogue.RFI,h.epilogue.RESULT,h.dispatch.RESULT,h.ack.RESULT,h.RESULT,c.callback.RESULT,c.prior_prefix.RESULT,c.prior_time.RESULT,c.prior_frontier.RESULT,c.prior_wireless.RESULT)
        def inspect(*rows,rc=0):return c.inspect(b'\n'.join(rows),rc)[1]
        with patch.object(a.old,'inspect',return_value=('verified=1 branch=4 admitted=0',True)):
            self.assertTrue(inspect(*prior,c.RESULT))
            for old,new in ((b'ordinal=13',b'ordinal=4'),(b'target_class=0',b'target_class=2'),(b'visits=37',b'visits=4'),(b'writes=0',b'writes=1'),(b'polls=4',b'polls=1'),(b'token=3',b'token=4'),(b'saved_fields=38',b'saved_fields=37'),(b'pi_cleared=1',b'pi_cleared=0'),(b'call_executed=0',b'call_executed=1')):
                self.assertFalse(inspect(*prior,c.RESULT.replace(old,new)))
            for rows in ((*prior,),(*prior[:-1],c.RESULT),(*prior[:-1],c.RESULT,c.prior_wireless.RESULT),(*prior,c.RESULT,c.RESULT),(*prior,c.prior_wireless.RESULT,c.RESULT),(*prior,b'V1151_HELD_EPILOGUE_FAULT stage=22 reason=26 epilogue=0 reentry=33',c.RESULT)):
                self.assertFalse(inspect(*rows))
            self.assertFalse(inspect(*prior,c.RESULT,rc=126))
if __name__=='__main__':unittest.main()
