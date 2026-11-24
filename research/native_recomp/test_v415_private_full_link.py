#!/usr/bin/env python3
"""Original-free integration tests of private CMake link workflow."""
import os
from pathlib import Path
import platform
import shutil
import subprocess
import tempfile
import unittest

SCRIPT=Path(__file__).with_name('run_private_full_link.sh')
@unittest.skipUnless(platform.system()=='Linux' and platform.machine()=='x86_64' and all(shutil.which(x) for x in ('cmake','ninja','g++','timeout')), 'Linux x64 build tools required')
class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='v415-private-')
        self.root=Path(self.tmp.name)
        self.src=self.root/'generated';self.src.mkdir()
        self.out=self.root/'build'
        (self.src/'CMakeLists.txt').write_text('cmake_minimum_required(VERSION 3.20)\nproject(Fixture LANGUAGES CXX)\nadd_executable(UndercoverWiiLocal main.cpp)\n')
        # Would create a file if the executable were accidentally launched.
        (self.src/'main.cpp').write_text('#include <fstream>\nint main(){std::ofstream("unexpected-launch").put(1); return 0;}\n')
    def tearDown(self):self.tmp.cleanup()
    def invoke(self):
        result=subprocess.run(['bash',str(SCRIPT),str(self.src),str(self.out)],cwd=self.root,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=40)
        self.assertNotIn(str(self.root),result.stdout+result.stderr)
        self.assertFalse((self.root/'unexpected-launch').exists())
        return result
    def test_actual_native_link_without_launch(self):
        r=self.invoke();self.assertEqual(r.returncode,0,r.stdout+r.stderr)
        self.assertIn('V415_FULL_LINK_GATE linked=1 platform=linux-x64 launch=0 boot_verified=0',r.stdout)
        self.assertTrue(os.access(self.out/'bin'/'UndercoverWiiLocal',os.X_OK))
    def test_unresolved_symbol_fails(self):
        (self.src/'main.cpp').write_text('extern int missing(); int main(){return missing();}\n')
        r=self.invoke();self.assertNotEqual(r.returncode,0)
        self.assertIn('stage=build result=failed',r.stdout)
        self.assertNotIn('linked=1',r.stdout)
        self.assertNotIn('undefined reference',r.stdout+r.stderr)
        self.assertIn('undefined reference',(self.out/'build-private.log').read_text())
    def test_existing_build_rejected(self):
        self.out.mkdir();marker=self.out/'preserve';marker.write_text('original')
        r=self.invoke();self.assertNotEqual(r.returncode,0)
        self.assertIn('stage=input result=failed',r.stdout)
        self.assertEqual(marker.read_text(),'original')
    def test_invalid_project_fails_closed(self):
        (self.src/'CMakeLists.txt').write_text('not_a_real_cmake_command()\n')
        r=self.invoke();self.assertNotEqual(r.returncode,0)
        self.assertIn('stage=configure result=failed',r.stdout)
        self.assertNotIn('not_a_real_cmake_command',r.stdout+r.stderr)
if __name__=='__main__':unittest.main()
