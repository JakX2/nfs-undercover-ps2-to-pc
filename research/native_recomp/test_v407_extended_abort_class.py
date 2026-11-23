#!/usr/bin/env python3
"""Synthetic original-free V407 abort attribution and no-private-output tests."""
from pathlib import Path
import tempfile
import unittest
from analyze_v407_extended_abort_class import inspect

SOURCE='static void check(bool ok, const char* msg); check(false,"Known public check");'
BASE=(
    'V250_CB_BEGIN candidate=1 reply=1 captured=1\n'
    'V289_NAND_ENTRY n=1 phase=0 zero=1 sc=1 guest=1 inst=100\n'
    'V296_SERVICE_ENTRY kind=1 guest=1 direct=1 inst=121\n'
)
def run(raw:str,src:str=SOURCE,rc:int=134,candidate:str='v404')->str:
    with tempfile.TemporaryDirectory() as td:
        a=Path(td)/'owner-secret.log'
        b=Path(td)/'host-private.cpp'
        a.write_text(raw,encoding='utf-8')
        b.write_text(src,encoding='utf-8')
        return inspect(a,b,rc,candidate)

class Tests(unittest.TestCase):
    def test_known_public_exception_without_printing_message(self):
        text=run(BASE+
            "terminate called after throwing an instance of 'std::runtime_error'\n"+
            'what(): Known public check\n')
        self.assertIn('candidate=v404 rc=134 kind=signal',text)
        self.assertIn('known_public=1 exception=runtime callback=1',text)
        self.assertIn('boot_verified=0',text)
        self.assertNotIn('Known public check',text)
    def test_unknown_original_guest_message_not_exported(self):
        raw=BASE+'what(): SECRET_PRIVATE_GAME_CODE 0x81234567\n'
        text=run(raw,candidate='v405')
        self.assertIn('candidate=v405 rc=134 kind=signal',text)
        self.assertIn('known_public=0 exception=unclassified',text)
        self.assertNotIn('SECRET_PRIVATE_GAME_CODE',text)
        self.assertNotIn('0x81234567',text)
    def test_cpp_exception_categories_and_no_boot_claim(self):
        for name,kind in (('std::logic_error','logic'),
                          ('std::out_of_range','range'),
                          ('std::bad_alloc','alloc')):
            with self.subTest(kind=kind):
                s=run(BASE+name+'\n')
                self.assertIn(f'exception={kind}',s)
                self.assertIn('boot_verified=0',s)
    def test_out_of_contract_inputs_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            a=Path(td)/'p.log'
            b=Path(td)/'p.cpp'
            a.write_text(BASE,encoding='ascii')
            b.write_text(SOURCE,encoding='ascii')
            for rc,can in ((-1,'v404'),(256,'v404'),(134,'v403')):
                with self.subTest(rc=rc,can=can):
                    with self.assertRaises(ValueError):
                        inspect(a,b,rc,can)
if __name__=='__main__':
    unittest.main()
