#!/usr/bin/env python3
import unittest
import shutil
import subprocess
import tempfile
from pathlib import Path
from derive_v416_nand_wait_state import patch,TRACE,NEW,STATE
from audit_v416_nand_wait_state import parse,summarize,period,FIELDS
from audit_v414_nand_resumed_coverage import RESTORE,TRIAL

PCS=(0x805265ac,0x805265d4,0x8052a824)
def sample(*,clock=True):
    raw=RESTORE+b'\nV414_RESUMED_BEGIN after=144\n'
    for i in range(145,193):
        pc=PCS[(i-145)%3]
        flags=dict.fromkeys(FIELDS,0);flags.update(mapped=1,reply=1,ee=1)
        raw+=f'V414_RESUMED_ENTRY call={i} pc={pc:08x}\n'.encode()
        raw+=(f'V416_WAIT_STATE call={i} lr={pc+4:08x} inst={i*5} tb={i if clock else 0} '+' '.join(f'{k}={v}' for k,v in flags.items())+'\n').encode()
    return raw+TRIAL+b'\n'
class Tests(unittest.TestCase):
    def test_reversible(self):
        source='// V414_RESUMED_BEGIN after=\n'+TRACE
        self.assertEqual(patch(source).replace(NEW,TRACE,1),source)
        for invalid in (source+TRACE,TRACE,patch(source)):
            with self.assertRaises(ValueError):patch(invalid)
    def test_period(self):
        self.assertEqual(period([1,2,3]*16),3)
        self.assertEqual(period(list(range(48))),0)
        self.assertEqual(period([1,2]*3),0)
    def test_wait_and_clock(self):
        out=summarize(parse(sample()*16))
        self.assertIn('same_route=16 periodic=16 period=3 inst_progress=16 tb_progress=16',out)
        self.assertIn('disable=1 restore=1 time=1 scheduler=0 ipc=0 other=0',out)
        self.assertIn('pending=0 queued=0 irq=0 ee=16 eligible=0',out)
        self.assertIn('tb_progress=0',summarize(parse(sample(clock=False)*16)))
        self.assertNotIn('805265ac',out)
    def test_cpp_observer(self):
        cc=shutil.which('g++')
        if not cc:self.skipTest('g++ unavailable')
        source=r'''#include <cstdint>
#include <iostream>
#include <optional>
namespace undercover::wii {
struct IpcMailbox { static constexpr unsigned PPCCTRL=4,PPCMSG=0,X1=1,Y1=2,Y2=4; };
struct HollywoodIrq { static constexpr unsigned PPC_FLAG=8,IPC_PPC=1; };
struct StmIos { static constexpr unsigned Reply=8; unsigned queued_replies() const{return 0;} };
struct IosBus {
  static constexpr unsigned IPC=0x0d000000,MSR_EE=0x8000;
  StmIos ios;
  std::optional<uint32_t> read32(unsigned a) const{return a==IPC?0x1000u:0u;}
  bool pending_native_ios_request() const{return false;}
  StmIos& services(){return ios;}
  bool external_irq_level() const{return false;}
  bool external_exception_pending(unsigned) const{return false;}
};
}
struct Ram { bool valid(uint32_t a,unsigned n) const{return a==0x1000u&&n==64u;} uint32_t read32(uint32_t a) const{return a==0x1000u?8u:0xfffffffau;} };
struct Cpu { uint32_t lr=0x80500004u,msr=0x8000u;uint64_t inst_count=10;uint64_t read_timebase() const{return 20;}bool dec_expired() const{return false;} };
int main(){
    Cpu ctx;Ram ipc70_ram;undercover::wii::IosBus ipc70_bus;unsigned v396_calls=145;
'''+STATE+'\nreturn 0; }\n'
        with tempfile.TemporaryDirectory() as td:
            src=Path(td)/'fixture.cpp';exe=Path(td)/'fixture';src.write_text(source)
            r=subprocess.run([cc,'-std=c++20','-Wall','-Wextra','-Werror',str(src),'-o',str(exe)],capture_output=True,text=True)
            self.assertEqual(r.returncode,0,r.stderr)
            r=subprocess.run([str(exe)],capture_output=True,text=True,timeout=5)
            self.assertEqual(r.returncode,0)
            self.assertIn('mapped=1 reply=1 negative=1 pending=0 queued=0',r.stdout)
    def test_reject_corrupt_trace(self):
        s=sample()
        for bad in (s.replace(b'eligible=0',b'eligible=1',1),s.replace(b'inst=730',b'inst=740',1),s.replace(b'V416_WAIT_STATE call=145',b'V416_WAIT_STATE call=146',1),s.replace(b'negative=0',b'negative=1',1).replace(b'reply=1',b'reply=0',1),s.replace(b'V416_WAIT_STATE',b'missing',1)):
            with self.assertRaises(ValueError):parse(bad*16)
if __name__=='__main__':unittest.main()
