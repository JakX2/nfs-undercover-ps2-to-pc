#include "dsp_boot_device_v64.h"
#include <cassert>
#include <iostream>
int main(){
  for(unsigned trial=0;trial<16;++trial){
    DspBootDevice d;d.reset(trial);d.begin();unsigned copies=0;
    auto copy=[&](uint32_t src,uint32_t dest,uint32_t n){assert(src==0x01000000u&&dest==0&&n==32);++copies;};
    auto r=[&](uint32_t reg){return d.read16(reg,copy);};
    auto w=[&](uint32_t reg,uint16_t v){d.write16(reg,v);};
    auto reject=[&](auto f){bool bad=false;try{f();}catch(const std::runtime_error&){bad=true;}assert(bad);};
    reject([&]{d.write32(d.DMA_COUNT,32);});
    w(d.INFO,0x43);w(d.CONTROL,0x8ac);assert(r(d.CONTROL)==0x804);w(d.CONTROL,0x805);
    for(unsigned n=0;n<trial%4;++n)assert(r(d.CONTROL)==0x805);
    assert(r(d.CONTROL)==0x804);w(d.CPU_MAIL,0);
    if(trial&1u){assert(r(d.MAIL_H)==0x8000);assert(r(d.MAIL_L)==0);}
    assert(r(d.MAIL_H)==0);assert(r(d.MAIL_L)==0);
    for(unsigned i=0;i<2;++i){
      reject([&]{d.write32(d.DMA_SOURCE,0x01000020);});
      d.write32(d.DMA_SOURCE,0x01000000);d.write32(d.DMA_DEST,0);
      reject([&]{d.write32(d.DMA_COUNT,64);});d.write32(d.DMA_COUNT,32);
      for(unsigned n=0;n<(i?trial%4:(trial/4)%4);++n){assert(r(d.CONTROL)==0xa04);assert(copies==i);}
      assert(r(d.CONTROL)==0x824&&copies==i+1);w(d.CONTROL,0x824);
    }
    assert(r(d.CONTROL)==0x804);w(d.CONTROL,4);
    for(unsigned n=0;n<trial%4;++n)assert(r(d.CONTROL)==0x404);
    assert(r(d.CONTROL)==4);assert(r(d.CONTROL)==4);w(d.CONTROL,0);
    for(unsigned n=0;n<(trial/4)%4;++n)assert(r(d.MAIL_H)==0);
    assert(r(d.MAIL_H)==0x8123);assert(r(d.MAIL_L)==0x4567);
    assert(r(d.CONTROL)==0);w(d.CONTROL,4);w(d.CONTROL,0x8ac);assert(r(d.CONTROL)==0x804);
    w(d.CONTROL,0x805);for(unsigned n=0;n<(trial/4)%4;++n)assert(r(d.CONTROL)==0x805);
    assert(r(d.CONTROL)==0x804&&d.complete());reject([&]{r(d.CONTROL);});
    assert(copies==2);
  }
  std::cout<<"PASS: sixteen DSP reset/ARAM DMA/mailbox schedules and malformed request guards\n";
}
