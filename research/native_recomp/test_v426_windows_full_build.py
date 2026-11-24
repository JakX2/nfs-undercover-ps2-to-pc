#!/usr/bin/env python3
import os
import shutil
import struct
import subprocess
import tempfile
import unittest
from pathlib import Path
from windows_full_build_v426 import (BuildError,CTX,CTX_NEW,SWAP,SWAP_NEW,MAIN,MAIN_NEW,CMAKE,CMAKE_NEW,TRACE,INTERPRETER,ENTRY,NEXT,synthetic_dol,portable_patch,generated_patch,validate_pe,command)

def pe_fixture():
    raw=bytearray(1024);raw[:2]=b'MZ';struct.pack_into('<I',raw,0x3c,128)
    raw[128:132]=b'PE\0\0';struct.pack_into('<HHIIIHH',raw,132,0x8664,1,0,0,0,240,0x22)
    opt=152;struct.pack_into('<H',raw,opt,0x20b);struct.pack_into('<I',raw,opt+16,0x1000);struct.pack_into('<I',raw,opt+56,0x2000)
    sec=opt+240;raw[sec:sec+5]=b'.text';struct.pack_into('<IIII',raw,sec+8,16,0x1000,512,512);struct.pack_into('<I',raw,sec+36,0x60000020);raw[512]=0xc3
    return bytes(raw)

class Tests(unittest.TestCase):
    def test_pe_validation(self):
        with tempfile.TemporaryDirectory() as td:
            exe=Path(td)/'test.exe';raw=pe_fixture();exe.write_bytes(raw);validate_pe(exe)
            for at,value,fmt in ((0x3c,0xffffffff,'I'),(132,0x14c,'H'),(150,0x2022,'H'),(152,0x10b,'H'),(168,0,'I'),(168,0x1010,'I'),(408,1000,'I'),(428,0x40000020,'I')):
                bad=bytearray(raw);struct.pack_into('<'+fmt,bad,at,value);exe.write_bytes(bad)
                with self.assertRaises(BuildError,msg=str(at)):validate_pe(exe)
            exe.write_bytes(raw[:200]);self.assertRaises(BuildError,validate_pe,exe)
    def test_portable_patch_and_conflict(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);ctx=root/'nWiiRuntime/include/runtime/cpu_context.h';rec=root/'nWiiRecomp/src/recompiler.cpp'
            for p in (ctx,rec):p.parent.mkdir(parents=True)
            ctx.write_text(CTX);rec.write_text(SWAP)
            with self.assertRaises(BuildError):portable_patch(root)
            self.assertEqual(ctx.read_text(),CTX);rec.write_text(SWAP+'v); '+SWAP+'w);')
            portable_patch(root);self.assertEqual(ctx.read_text(),CTX_NEW);self.assertEqual(rec.read_text().count(SWAP_NEW),2);portable_patch(root)
    def test_generated_patch_atomic_validation(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);main=root/'nWiiRuntime/src/core/main.cpp';cm=root/'CMakeLists.txt';stubs=root/'nWiiRuntime/src/core/os_hle_stubs.cpp';interp=root/'nWiiRuntime/src/hle/interpreter.cpp'
            for p in (main,stubs,interp):p.parent.mkdir(parents=True,exist_ok=True)
            main.write_text(MAIN);cm.write_text(CMAKE);stubs.write_text(TRACE);interp.write_text(INTERPRETER[0])
            with self.assertRaises(BuildError):generated_patch(root,True)
            self.assertEqual(main.read_text(),MAIN);self.assertEqual(cm.read_text(),CMAKE)
            interp.write_text('\n'.join(INTERPRETER));generated_patch(root,True)
            self.assertEqual(main.read_text(),MAIN_NEW);self.assertEqual(cm.read_text(),CMAKE_NEW);self.assertIn('V426_SYNTHETIC_SWAP',stubs.read_text());self.assertEqual(interp.read_text().count('std::_Exit(83)'),2)
    def test_synthetic_encodings(self):
        raw=synthetic_dol();self.assertEqual(struct.unpack_from('>I',raw,0xe0)[0],ENTRY)
        w=struct.unpack_from('>9I',raw,256)
        self.assertEqual((w[4]>>26,(w[4]>>1)&1023,w[5]>>26,(w[5]>>1)&1023),(31,662,31,534))
        self.assertEqual(ENTRY+24+(w[6]&0x3fffffc),NEXT)
    def test_real_pe_when_toolchain_present(self):
        clang=shutil.which('clang-cl');link=shutil.which('lld-link')
        if not clang or not link:self.skipTest('COFF cross compiler unavailable')
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);src=root/'fixture.cpp';obj=root/'fixture.obj';exe=root/'fixture.exe';src.write_text('extern "C" int entry(){return 0;}')
            subprocess.run([clang,'/nologo','/c','/GS-','/O1','/Fo'+str(obj),str(src)],check=True,capture_output=True)
            subprocess.run([link,'/entry:entry','/subsystem:console','/nodefaultlib','/machine:x64','/out:'+str(exe),str(obj)],check=True,capture_output=True)
            validate_pe(exe)
    @unittest.skipIf(os.name=='nt','GCC/UBSan comparison is a Linux test; Windows executes translated swaps under MSVC')
    def test_portable_swap_cpp(self):
        cc=shutil.which('g++')
        if not cc:self.skipTest('GCC unavailable')
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);src=root/'test.cpp';exe=root/'test'
            src.write_text('#include <cstdint>\nstruct CPUContext {\n'+CTX_NEW[:-len(CTX)]+'};\nint main(){for(uint32_t i=0;i<100000;++i){uint32_t x=i*2654435761u; if(CPUContext::portable_bswap32(x)!=__builtin_bswap32(x))return 1;}return 0;}')
            subprocess.run([cc,'-std=c++20','-Wall','-Wextra','-Werror','-fsanitize=undefined',str(src),'-o',str(exe)],check=True,capture_output=True)
            subprocess.run([str(exe)],check=True)
if __name__=='__main__':unittest.main()
