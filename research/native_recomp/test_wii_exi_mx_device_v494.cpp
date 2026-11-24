#include "wii_exi_mx_device_v494.h"
#include "wii_physical_ram.h"
#include <iostream>
using namespace undercover::wii;
static void need(bool b){if(!b)throw std::runtime_error("MX protocol");}
template<class F>void reject(F f){bool caught=false;try{f();}catch(const std::exception&){caught=true;}need(caught);}
int main(){
    std::vector<uint8_t> m1(512,0x5a),m2(512,0x7b);
    WiiPhysicalRam ram(m1,m2);std::atomic<uint32_t> cause{0x100};WiiIrqBanks banks(cause);ExiController exi(banks,&ram);
    ExiMxDevice::Sram sram{};for(unsigned i=0;i<sram.size();++i)sram[i]=uint8_t(i*9);
    unsigned rtc_calls=0;uint32_t seconds=0x12345678;
    ExiMxDevice mx(sram,[&]{++rtc_calls;return seconds;});
    ExiIdEndpoint id(0xfeed1234);exi.attach(0,1,true);exi.attach(0,2,true);
    auto select=[&](unsigned cs){exi.write(0,0,(cs<<7)|0x34);};
    auto imm=[&](unsigned n,unsigned dir,uint32_t data){
        exi.write(0,16,data);exi.write(0,12,((n-1)<<4)|(dir<<2)|1);
        auto q=exi.pending(0);need(q.has_value());return *q;};
    auto mximm=[&](unsigned n,unsigned dir,uint32_t data){auto q=imm(n,dir,data);mx.service(exi,q);return exi.read(0,16);};
    select(4);auto q=imm(2,1,0);id.service(exi,q);q=imm(4,0,0);
    auto wrong=q;wrong.token++;reject([&]{id.service(exi,wrong);});
    id.service(exi,q);need(exi.read(0,16)==0xfeed1234);exi.write(0,0,8);id.deselect();
    select(2);mximm(4,1,0x20000000);need(rtc_calls==1);
    seconds=0xffffffff;need((mximm(2,0,0)>>16)==0x1234);
    need((mximm(2,0,0)>>16)==0x5678&&rtc_calls==1);
    exi.write(0,0,8);mx.deselect();
    select(2);mximm(4,1,0x20000100);exi.write(0,4,0x80000040);exi.write(0,8,64);exi.write(0,12,3);
    q=*exi.pending(0);auto bad=q;bad.physical+=32;const auto before=m1;reject([&]{mx.service(exi,bad);});need(m1==before);
    mx.service(exi,q);need(std::equal(sram.begin(),sram.end(),m1.begin()+64));need(!exi.pending(0));
    for(unsigned i=0;i<m1.size();++i)if(i<64||i>=128)need(m1[i]==before[i]);
    exi.write(0,0,8);mx.deselect();select(2);mximm(4,1,0xa0000100);
    for(unsigned i=0;i<16;++i)mximm(4,1,0x10203040+i);
    need(mx.dirty()&&mx.sram()[0]==0x10&&mx.sram()[63]==0x4f);
    const auto saved=mx.sram();mx.mark_saved();need(!mx.dirty());
    exi.write(0,0,8);mx.deselect();select(2);mximm(4,1,0x20000100);
    exi.write(0,4,0x90000040);exi.write(0,8,64);exi.write(0,12,3);q=*exi.pending(0);
    mx.service(exi,q);need(std::equal(saved.begin(),saved.end(),m2.begin()+64)&&!mx.dirty());
    exi.write(0,0,8);mx.deselect();select(2);
    q=imm(4,1,0x12345678);reject([&]{mx.service(exi,q);});
    need(exi.pending(0).has_value()&&mx.sram()==saved&&rtc_calls==1);
    std::cout<<"PASS: configured EXI ID, latched RTC, SRAM immediate writes, 64-byte MEM1/MEM2 DMA reads and stale request rejection\n";
}
