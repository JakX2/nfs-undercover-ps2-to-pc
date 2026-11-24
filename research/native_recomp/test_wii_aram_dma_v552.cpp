#include "wii_aram_dma_v552.h"
#include <iostream>
#include <vector>
#include <source_location>
using namespace undercover::wii;
static void need(bool b,const std::source_location loc=std::source_location::current()){
    if(!b)throw std::runtime_error("ARAM DMA line "+std::to_string(loc.line()));
}
template<class F>static void reject(F f){bool caught=false;try{f();}catch(const std::exception&){caught=true;}need(caught);}
int main(){
    using D=AramDma;constexpr uint32_t Other=0x108u,Base=WiiPhysicalRam::MEM2_BASE;
    for(unsigned trial=0;trial<16;++trial){
        std::array<uint8_t,256> mem1{},mem2{};mem1.fill(0xa7);mem2.fill(0x5c);
        WiiPhysicalRam ram(mem1,mem2);std::atomic<uint32_t> pi{Other};
        const bool reverse=trial&1u,masked=trial&2u;
        const uint32_t n=(1u+(trial>>2))*32u,src=reverse?Base+32:32,dst=reverse?32:Base+32;
        for(unsigned i=0;i<n;++i)ram.write8(src+i,uint8_t(i*17u+trial));
        const auto before=reverse?mem1:mem2;
        {
            D dma(ram,pi,8);
            reject([&]{dma.start(32);});
            reject([&]{dma.set_info(0x44);});
            dma.set_info(0x43);dma.set_main_address(32);dma.set_aram_address(32);
            dma.write_irq_control(masked?0:D::ArMask);
            for(auto bad:{0u,1u,33u,0x10020u,0x80000001u,0x7fffffe0u}){
                reject([&]{dma.start(bad);});need(dma.count()==0&&dma.control_bits()==(masked?0:D::ArMask));
            }
            dma.start(n|(reverse?D::Reverse:0));need(dma.control_bits()&D::Busy);
            reject([&]{dma.start(32);});reject([&]{dma.set_main_address(64);});
            reject([&]{dma.set_aram_address(64);});reject([&]{dma.set_info(0x43);});
            for(unsigned i=0;i<100;++i)need(dma.count()==(n|(reverse?D::Reverse:0))&&(dma.control_bits()&D::Busy));
            need((reverse?mem1:mem2)==before&&pi==Other);
            dma.advance(100);dma.advance(107);need((reverse?mem1:mem2)==before);
            reject([&]{dma.advance(106);});
            for(unsigned block=0;block<n/32;++block){
                dma.advance(108+8*block);dma.advance(108+8*block);
                for(unsigned i=0;i<n;++i)need(ram.read8(dst+i)==(i<(block+1)*32?ram.read8(src+i):before[32+i]));
                need(dma.main_address()==32+(block+1)*32&&dma.aram_address()==dma.main_address());
                need((dma.count()&~D::Reverse)==n-(block+1)*32);
            }
            need(dma.completed()==1&&!(dma.control_bits()&D::Busy)&&(dma.control_bits()&D::ArInt));
            need(pi==(Other|(masked?0:D::PiDsp)));
            dma.write_irq_control(D::ArMask);need(pi==(Other|D::PiDsp));
            pi.fetch_and(~D::PiDsp);dma.refresh();need(pi==(Other|D::PiDsp));
            dma.write_irq_control(D::ArInt|D::ArMask);need(pi==Other&&dma.control_bits()==D::ArMask);
            dma.advance(1000);need(dma.completed()==1);
            const auto& after=reverse?mem1:mem2;
            for(unsigned i=0;i<after.size();++i)if(i<32||i>=32+n)need(after[i]==before[i]);
            dma.set_main_address(224);dma.set_aram_address(32);
            reject([&]{dma.start(64);});
            dma.set_main_address(32);dma.set_aram_address(224);reject([&]{dma.start(64);});
            reject([&]{dma.set_main_address(1);});reject([&]{dma.set_aram_address(1);});
            reject([&]{dma.write_irq_control(D::Busy);});
        }
        need(pi==Other);
    }
    {
        std::array<uint8_t,64> a{},b{};WiiPhysicalRam ram(a,b);std::atomic<uint32_t> pi{Other};
        D dma(ram,pi,8);dma.set_info(0x43);dma.advance(std::numeric_limits<uint64_t>::max()-7);
        reject([&]{dma.start(32);});need(dma.count()==0&&dma.control_bits()==0&&pi==Other);
    }
    std::cout<<"PASS: 16 timed Wii MEM1/MEM2 DMA profiles, bidirectional 32-byte bursts, W1C, bounds, PI ownership and inert polling\n";
}
