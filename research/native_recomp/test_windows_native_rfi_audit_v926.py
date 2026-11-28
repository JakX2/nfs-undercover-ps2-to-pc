#!/usr/bin/env python3
"""Original-free strict complete-image Windows native RFI audit."""
import unittest
from test_v763_windows_handler_return import sample as handler_sample
from windows_native_rfi_v926 import (inspect,diagnostic,
    JOIN,SOURCE,FIRST,SECOND,RFI,POLL)
from windows_startup_scope_v434 import MAX_LOG

RESULT=(b'V932_REENTRY_RESULT native_rfi=1 second_exception=1 '
        b'vector_entry=1 restored_context=1 visits=86 device_held=1 '
        b'resumed_instruction_executed=0 boot_verified=0')

def sample(changed=True):
    return handler_sample(changed).rstrip(b'\r\n')+b'\n'+b'\n'.join(
        (JOIN,SOURCE,FIRST,SECOND,RFI,POLL,RESULT))+b'\n'


class WindowsNativeRfiAudit(unittest.TestCase):
    def test_strict_real_rfi_and_second_vector_log(self):
        for changed in (True,False):
            row,ok=inspect(sample(changed),0)
            self.assertTrue(ok,row)
            self.assertIn('handler_return=1 saved_context=1 native_rfi=1',row)
            self.assertIn('second_vector=1 visits=86',row)
    def test_no_rfi_no_success(self):
        for raw in (handler_sample(),sample()+b'unrecognized-trailing\n',
                    sample()+RESULT+b'\n',
                    handler_sample()+b'\n'.join((JOIN,SOURCE,FIRST,SECOND,POLL,RESULT))+b'\n',
                    sample().replace(FIRST,SECOND),sample().replace(JOIN,b'forged'),
                    sample().replace(b'visits=86',b'visits=513'),
                    sample().replace(b'resumed_instruction_executed=0',b'resumed_instruction_executed=1'),
                    sample().replace(SOURCE,b'V932_PENDING_SOURCE held_completion=0 only_si=1'),
                    sample().replace(SECOND,FIRST),
                    RESULT+b'\n'+sample()):
            self.assertFalse(inspect(raw,0)[1],raw[-100:])
    def test_failure_retains_predecessor_and_refuses_rfi(self):
        for rc in (1,126,-1073741819):
            row,ok=inspect(sample(),rc)
            self.assertFalse(ok)
            self.assertIn('handler_return=1',row)
            self.assertIn('native_rfi=0 second_vector=0',row)
        self.assertFalse(inspect(sample(),0,True)[1])
    def test_bounded_diagnostics(self):
        self.assertTrue(diagnostic(b'V922_IRQ_RETURN_INVALID kind=3 reason=2 stage=1 visits=86'))
        self.assertTrue(diagnostic(b'V932_IRQ_BEGIN_REFUSAL mask=16'))
        for invalid in (b'V922_IRQ_RETURN_INVALID kind=9 reason=2 stage=1 visits=86',
                        b'V932_IRQ_BEGIN_REFUSAL mask=1 regs=secret',
                        b'V932_REENTRY_RESULT native_rfi=1 second_exception=1',
                        b'v922 IRQ'):
            self.assertFalse(diagnostic(invalid))
    def test_bad_types_and_logs_are_refused(self):
        for args in (('str',0,False),(b'',1.0,False),(b'',0,'false'),
                     (b'x'*(MAX_LOG+1),0,False)):
            with self.assertRaises(ValueError):inspect(*args)


if __name__=='__main__':unittest.main()
