#include "exi_sram_test_device_v60.h"
#include <cassert>
#include <iostream>
int main(){
  for(unsigned i=0;i<16;++i){
    ExiSramTestDevice d;d.reset(0x80010000,i);d.begin();unsigned copied=0;
    auto copy=[&](uint32_t a,const auto&b){assert(a==0x80010000&&b==d.bytes);++copied;};
    auto reject=[&](auto f){bool bad=false;try{f();}catch(const std::runtime_error&){bad=true;}assert(bad);};
    reject([&]{d.write(d.CR,3);});
    assert(d.read(d.CSR,copy)==0);d.write(d.CSR,0x130);d.write(d.DATA,0x20000100);
    d.write(d.CR,0x35);
    for(unsigned n=0;n<i%4;++n)assert(d.read(d.CR,copy)==0x35);
    assert(d.read(d.CR,copy)==0x34);assert(d.read(d.REV,copy)==1);
    reject([&]{d.write(d.MAR,0x80010020);});d.write(d.MAR,0x80010000);
    reject([&]{d.write(d.LEN,32);});d.write(d.LEN,64);d.write(d.CR,3);
    for(unsigned n=0;n<(i/4)%4;++n){assert(d.read(d.CR,copy)==3);assert(copied==0);}
    assert(d.read(d.CR,copy)==2&&copied==1);assert(d.read(d.REV,copy)==1);
    assert(d.read(d.CSR,copy)==0x130);d.write(d.CSR,0);assert(d.complete());
    reject([&]{d.read(d.CR,copy);});assert(copied==1);
  }
  std::cout<<"PASS: 16 SRAM DMA device schedules and malformed access rejection\n";
}
