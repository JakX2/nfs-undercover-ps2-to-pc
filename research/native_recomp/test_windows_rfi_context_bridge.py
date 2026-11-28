#!/usr/bin/env python3
"""Original-free Windows SI saved-context bridge regressions."""
from __future__ import annotations
from pathlib import Path
import inspect
import tempfile
import unittest

from prepare_windows_rfi_context_bridge import (
    HEADERS, patch_external, patch_handler, plan, install,
)

HOST=Path(__file__).resolve().parent

HANDLER='''#pragma once
#include "v920_private_handler_resume.h"
namespace undercover::wii::v868 {
template<class C>void dispatcher_resume(C& c,uint32_t pc,uint32_t w){
    std::cout<<"V920_HANDLER_RETURN original_blr=1 original_dispatcher=1 abi=1 outer_tick=1 follow_held=1 dispatcher_instruction_executed=0 rfi_return=0 boot_verified=0"<<std::endl;
    if(scheduler_enabled()){scheduler_start(c,pc,w);return;}
    std::_Exit(0);
}
}
'''

class WindowsContextBridge(unittest.TestCase):
    def make_tree(self,root):
        dest=root/'nWiiRuntime/include/undercover'
        dest.mkdir(parents=True)
        a=dest/'wii_external_entry_binding_v663.h'
        b=dest/'wii_handler_suffix_binding_v868.h'
        a.write_text((HOST/a.name).read_text(encoding='utf-8'),encoding='utf-8')
        b.write_text(HANDLER,encoding='utf-8')
        return dest,a,b

    def test_owner_windows_build_installs_bridge_only_after_native_scheduler(self):
        from windows_full_build_v426 import build
        source=inspect.getsource(build)
        self.assertIn("if owner_handler_return or owner_progression_matrix:",source)
        self.assertIn("run_stage('rfi_context_bridge',",source)
        self.assertIn("generated,'--install']",source)
        self.assertLess(source.index('for stage,script in transfer_plan.observers:'),
                        source.index("run_stage('rfi_context_bridge',"))
        self.assertLess(source.index("run_stage('rfi_context_bridge',"),
                        source.index("run_stage('external_translation_audit'"))

    def test_exact_capture_and_post_handler_join_gated_by_environment(self):
        external=(HOST/'wii_external_entry_binding_v663.h').read_text(encoding='utf-8')
        patched=patch_external(external)
        self.assertIn('if(entered&&capture_enabled())',patched)
        self.assertIn('v921::join.attach(c,capture.witness()',patched)
        self.assertLess(patched.index('V751_CAPTURE_STAGE n=1'),
                        patched.index('v921::join.attach('))
        self.assertLess(patched.index('v921::join.attach('),
                        patched.index('V751_CAPTURE_STAGE n=2'))
        handler=patch_handler(HANDLER)
        self.assertIn('UNDERCOVER_V751_CAPTURE',handler)
        self.assertIn('WINDOWS_RFI_CONTEXT_JOIN',handler)
        self.assertIn('if(windows_context_bridge_enabled())',handler)
        self.assertLess(handler.index('v921::join.returned('),
                        handler.index('scheduler_start(c,pc,w)'))
        with self.assertRaises(ValueError):patch_handler(handler)
        with self.assertRaises(ValueError):patch_external(patched)

    def test_read_only_default_install_and_synthetic_headers(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            dest,a,b=self.make_tree(root)
            a_old=a.read_bytes();b_old=b.read_bytes()
            changes=plan(root,HOST)
            self.assertEqual(len(changes),5)
            self.assertEqual(set(changes),{a,b,*[dest/h for h in HEADERS]})
            self.assertEqual(install(root,HOST),5)
            self.assertEqual((a.read_bytes(),b.read_bytes()),(a_old,b_old))
            for h in HEADERS:self.assertFalse((dest/h).exists())
            self.assertEqual(install(root,HOST,write=True),5)
            self.assertIn('WINDOWS_RFI_CONTEXT_JOIN',b.read_text())
            self.assertIn('V751_CAPTURE_STAGE n=2',a.read_text())
            for h in HEADERS:
                self.assertEqual((dest/h).read_bytes(),(HOST/h).read_bytes())
            with self.assertRaises(ValueError):install(root,HOST)

    def test_malformed_and_ambiguous_source_fails_closed(self):
        external=(HOST/'wii_external_entry_binding_v663.h').read_text()
        for bad in (external.replace('ColdExternalEntry route(expected)', 'ColdExternalEntry route(other)'),
                    external.replace('if(route.stage()==6){','if(route.stage()==7){')):
            with self.assertRaises(ValueError):patch_external(bad)
        for bad in (HANDLER.replace('original_blr=1','original_blr=0'),
                    HANDLER.replace('#include "v920_private_handler_resume.h"',''),
                    HANDLER.replace('template<class C>void dispatcher_resume','template<class C>void other_resume')):
            with self.assertRaises(ValueError):patch_handler(bad)
        with self.assertRaises(ValueError):install('not a path',HOST)
        with self.assertRaises(ValueError):install(Path('.'),HOST,write='yes')

    def test_conflict_and_symlink_are_not_modified(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);dest,a,b=self.make_tree(root)
            original=a.read_bytes()
            (dest/HEADERS[0]).write_text('conflicting source',encoding='utf-8')
            with self.assertRaises(ValueError):install(root,HOST,write=True)
            self.assertEqual(a.read_bytes(),original)
            self.assertEqual((dest/HEADERS[0]).read_text(),'conflicting source')
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);dest,a,b=self.make_tree(root)
            external=a.read_bytes()
            b.unlink()
            try:b.symlink_to(a)
            except (OSError,NotImplementedError):return
            with self.assertRaises(ValueError):install(root,HOST,write=True)
            self.assertEqual(a.read_bytes(),external)

if __name__=='__main__':
    unittest.main()
