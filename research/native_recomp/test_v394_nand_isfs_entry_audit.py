#!/usr/bin/env python3
"""V394 strict original-free, no private-address or IOS result leaks."""
import tempfile
import unittest
from pathlib import Path
from analyze_v394_nand_isfs_entry import inspect
from diagnose_v299_native_log import WINDOW
E='V394_NAND_ISFS_ENTRY guest=1 clear=1 masked=1 registered=1 mapped=1 selected=1 result=1 userdata=1\n'
T='V394_NAND_ISFS_TRIAL context=1 isfs=1 completed=1\n'
def run(raw,rc=0):
    with tempfile.TemporaryDirectory() as td:
        file=Path(td)/'hidden-original.log'
        file.write_text(raw,encoding='utf-8')
        return inspect(file,rc)
class Tests(unittest.TestCase):
    def test_original_entry_and_request_metadata_classified(self):
        report=run('private guest registers\n'+E+T)
        self.assertIn('entries=1 trials=1 mapped_any=1 selected_any=1',report)
        self.assertIn('result_any=1 userdata_any=1 isfs_entry_verified=1',report)
        self.assertNotIn('private guest',report)
    def test_optional_request_status_does_not_override_guest_entry(self):
        e=E.replace('result=1','result=0').replace('userdata=1','userdata=0')
        self.assertIn('isfs_entry_verified=1',run(e+T))
        self.assertIn('result_any=0 userdata_any=0',run(e+T))
    def test_unpaired_or_false_required_fields_rejected(self):
        for raw in ('',E,T,T+E+T,E+E+T,E+T+T,
                    E.replace('guest=1','guest=0')+T,
                    E.replace('clear=1','clear=0')+T,
                    E+T+E+T.replace('completed=1','completed=0')):
            self.assertIn('isfs_entry_verified=0',run(raw),raw)
    def test_large_input_reports_incomplete(self):
        with tempfile.TemporaryDirectory() as td:
            file=Path(td)/'owner-private.log'
            with file.open('wb') as f:
                f.write((E+T).encode('ascii'))
                f.seek(WINDOW+48)
                f.write(b'\n')
            self.assertIn('sample_complete=0',inspect(file,124))
if __name__=="__main__":unittest.main()
