#include "wii_exi_endpoint_scheduler_v495.h"
#include "wii_physical_ram.h"
#include <iostream>
using namespace undercover::wii;
static void need(bool b){if(!b)throw std::runtime_error("EXI scheduler");}
template<class F>void reject(F f){bool caught=false;try{f();}catch(const std::exception&){caught=true;}need(caught);}
int main(){
    std::vector<uint8_t> m1(256,0xaa),m2(256,0xbb);WiiPhysicalRam ram(m1,m2);
    std::atomic<uint32_t> cause{0x100};WiiIrqBanks banks(cause);ExiController exi(banks,&ram);
    ExiMxDevice::Sram initial{};for(unsigned i=0;i<64;++i)initial[i]=uint8_t(i+1);
    ExiMxDevice mx(initial,[]{return 0x11223344u;});ExiIdEndpoint id(0xffffffffu);
    reject([&]{ExiEndpointScheduler invalid(exi,mx,id,0);});
    ExiEndpointScheduler sched(exi,mx,id,8);uint64_t now=0;
    auto run=[&](uint32_t ctrl){
        exi.write(0,12,ctrl);const auto before=sched.completed();
        sched.advance(++now);
        for(unsigned i=0;i<20;++i){sched.advance(now);need(exi.read(0,12)&1u);}
        sched.advance(now+7);need(exi.read(0,12)&1u);
        now+=8;sched.advance(now);
        need(!(exi.read(0,12)&1u)&&sched.completed()==before+1);
        sched.advance(now);need(sched.completed()==before+1);
    };
    exi.write(0,0,0x234);exi.write(0,16,0);run(0x15);run(0x31);
    need(exi.read(0,16)==0xffffffffu&&sched.completed()==2);
    exi.write(0,0,0x8);exi.write(0,0,0x134);exi.write(0,16,0x20000100);run(0x35);
    exi.write(0,4,0x80000040);exi.write(0,8,64);run(3);
    need(std::equal(initial.begin(),initial.end(),m1.begin()+64)&&sched.completed()==4);
    // A complete deselect/reselect between scheduler visits must reset
    // the protocol. A second SRAM command would otherwise be read data.
    exi.write(0,0,8);exi.write(0,0,0x134);exi.write(0,16,0x20000000);run(0x35);run(0x31);
    need(exi.read(0,16)==0x11223344u&&sched.completed()==6);
    reject([&]{sched.advance(now-1);});
    const auto epoch=exi.selection_epoch(0);
    exi.write(0,0,0x13c);need(exi.selection_epoch(0)==epoch);
    exi.write(0,0,0);need(exi.selection_epoch(0)==epoch+1);
    sched.advance(++now);need(sched.completed()==6);
    std::cout<<"PASS: EXI endpoint scheduler completes only at monotonic instruction boundaries, preserves CS epochs and DMA data\n";
}
