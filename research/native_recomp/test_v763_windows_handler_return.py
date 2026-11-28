#!/usr/bin/env python3
"""Original-free Windows handler-return and strict early-stop regression."""
import inspect as std_inspect
import unittest

from audit_v870_handler_suffix import STATUS, STORE
from audit_v919_handler_epilogue import MARKERS
from audit_v920_handler_return import POLL, RETURN
from test_v762_windows_combined_callback import (
    sample as callback_sample, getter as callback_getter, S, I,
)
from windows_handler_return_v763 import inspect, diagnostic
from windows_transfer_prefix_v751 import plan
from windows_full_build_v426 import build as windows_build

JOIN=b'V868_HANDLER_SUFFIX_ENTRY ordinal=6 callback_return=1 same_tick=1'
INDEX=b'V911_HANDLER_INDEX_BRANCH original_load=1 compare=1 branch_taken=1 successor=1'
STOP=b'V868_HANDLER_SUFFIX_RESULT after=6 next=12 kind=1 visits=20 writes=1 executed=0 handler_return=0 boot_verified=0'


def sample(changed=True, tail=None):
    if tail is None:
        tail=(JOIN, STATUS, STORE, INDEX, STOP, *MARKERS, POLL, RETURN)
    return callback_sample(changed).rstrip(b'\r\n')+b'\n'+b'\n'.join(tail)+b'\n'


class WindowsHandlerReturn(unittest.TestCase):
    def test_plan_reuses_authenticated_predecessors(self):
        p=plan('os-si-handler-time',False,False,False,handler_return=True)
        self.assertEqual(p.observers[-5:-1],
                         (('combined_callback_observer','prepare_v863_combined_callback.py'),
                          ('handler_suffix_observer','prepare_v868_handler_suffix.py'),
                          ('handler_epilogue_observer','prepare_v919_handler_epilogue.py'),
                          ('handler_dispatch_return_observer','prepare_v920_handler_return.py')))
        for flag in ('UNDERCOVER_V850_CALLBACK_RETURN',
                     'UNDERCOVER_V868_HANDLER_SUFFIX',
                     'UNDERCOVER_V919_HANDLER_EPILOGUE',
                     'UNDERCOVER_V920_HANDLER_RETURN'):
            self.assertEqual(p.env[flag],'1')
        for change in ({'synthetic':True},{'scope':'startup'},
                       {'combined_callback':True},{'prefix':True},
                       {'time_suffix':True}):
            args=dict(scope='os-si-handler-time',synthetic=False,prefix=False,
                      time_suffix=False,handler_return=True)
            args.update(change)
            with self.subTest(change=change),self.assertRaises(ValueError):
                plan(**args)
        self.assertEqual(p.observers[-1],
                         ('scheduler_entry_observer','prepare_v922_windows_scheduler_entry.py'))
        self.assertIn('owner_handler_return',std_inspect.signature(windows_build).parameters)
        self.assertEqual(p.analyzer[-1], '--epilogue')

    def test_actual_return_on_changed_and_unchanged_id(self):
        for changed in (True,False):
            with self.subTest(changed=changed):
                row,ok=inspect(sample(changed),0)
                self.assertTrue(ok,row)
                self.assertIn('callback_return=1 handler_suffix=1 handler_return=1',row)
                self.assertIn('rfi=0 boot_verified=0',row)

    def test_earlier_stops_and_missing_epilogue_fail_closed(self):
        for raw in (callback_sample(),callback_getter(),
                    callback_sample(True,(S,I)),
                    sample(tail=(JOIN,STATUS,STORE,INDEX,STOP)),
                    sample(tail=(JOIN,STATUS,STORE,INDEX,STOP,*MARKERS,POLL)),
                    sample(tail=(JOIN,STATUS,STORE,INDEX,STOP,*MARKERS,POLL,RETURN,RETURN)),
                    sample(tail=(JOIN,STATUS,STORE,INDEX,STOP,*MARKERS,RETURN,POLL)),
                    sample() + b'unexpected opaque private bytes\n'):
            with self.subTest(raw=raw[-100:]):
                self.assertFalse(inspect(raw,0)[1])
        for rc,timeout in ((126,False),(1,False),(0,True),
                           (0xC0000005,False),(-1073741819,False)):
            self.assertFalse(inspect(sample(),rc,timeout)[1])

    def test_geometry_and_diagnostic(self):
        self.assertTrue(diagnostic(b'V868_HANDLER_SUFFIX_INVALID reason=3 guard=4 handler=0 visits=2 writes=1'))
        self.assertFalse(diagnostic(b'V868_HANDLER_SUFFIX_INVALID reason=3 guard=4 handler=0 visits=2 writes=1 private=1'))
        for args in ((b'unknown',True,False),(b'unknown',0,1),
                     ('text',0,False),(b'x'*(8*1024*1024+1),0,False)):
            with self.assertRaises(ValueError):
                inspect(*args)


if __name__=='__main__':
    unittest.main()
