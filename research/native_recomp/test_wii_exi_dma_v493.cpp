#include "wii_exi_controller_v489.h"
#include "wii_physical_ram.h"
#include <iostream>
using namespace undercover::wii;
static void need(bool b){if(!b)throw std::runtime_error("EXI DMA");}
template<class F>void reject(F f){bool caught=false;try{f();}catch(const std::exception&){caught=true;}need(caught);}
int main(){
    std::vector<uint8_t> m1(512,0x5a),m2(512,0x7b);
    WiiPhysicalRam ram(m1,m2);std::atomic<uint32_t> cause{0x100};WiiIrqBanks banks(cause);ExiController exi(banks,&ram);
    std::array<uint8_t,64> data{};for(unsigned i=0;i<data.size();++i)data[i]=uint8_t(i*7);
    unsigned cases=0;
    for(unsigned ch=0;ch<3;++ch){
        exi.attach(ch,0,true);exi.write(ch,0,0x84);
        for(uint32_t address:{0x40u,0x80000040u,0xc0000040u,0x10000040u,0x90000040u,0xd0000040u}){
            exi.write(ch,0,0x8c);exi.write(ch,4,address);exi.write(ch,8,64);
            auto& mem=(address&0x10000000u)?m2:m1;
            const auto before=mem;exi.write(ch,12,3);auto q=exi.pending(ch);
            need(q&&q->dma&&q->physical==(address&0x3fffffffu)&&q->length==64&&q->direction==0);
            for(unsigned i=0;i<20;++i)need(exi.read(ch,12)==3);
            need(before==mem&&cause==0x100);
            reject([&]{exi.complete_immediate(ch,q->token,0);});
            reject([&]{exi.complete_dma(ch,q->token+1,data);});
            reject([&]{exi.complete_dma(ch,q->token,std::span<const uint8_t>(data).first(63));});
            reject([&]{exi.dma_tx(ch,q->token);});
            need(before==mem&&exi.pending(ch).has_value());
            exi.complete_dma(ch,q->token,data);need(!exi.pending(ch)&&exi.read(ch,12)==2);
            need(std::equal(data.begin(),data.end(),mem.begin()+64));
            for(unsigned i=0;i<mem.size();++i)if(i<64||i>=128)need(mem[i]==before[i]);
            need(cause==(0x100|WiiIrqBanks::PI_EXI));exi.write(ch,0,0x8c);
            exi.write(ch,12,7);q=exi.pending(ch);need(q&&q->direction==1);
            const auto tx=exi.dma_tx(ch,q->token);need(std::equal(tx.begin(),tx.end(),data.begin(),data.end()));
            const auto snapshot=mem;reject([&]{exi.complete_dma(ch,q->token,data);});
            exi.complete_dma(ch,q->token,{});need(mem==snapshot&&exi.read(ch,12)==6);
            exi.write(ch,0,0x8c);need(cause==0x100);cases+=2;
        }
        for(uint32_t address:{0x40000040u,0x0d006800u,0x1fffffe0u,0xffffffe0u,0x800001e0u}){
            exi.write(ch,4,address);exi.write(ch,8,64);reject([&]{exi.write(ch,12,3);});need(!exi.pending(ch));
        }
        exi.write(ch,4,0);exi.write(ch,8,0);reject([&]{exi.write(ch,12,3);});
        exi.write(ch,8,64);reject([&]{exi.write(ch,12,11);});
        exi.write(ch,8,0xffffffff);reject([&]{exi.write(ch,12,3);});
    }
    std::cout<<"PASS: "<<cases<<" EXI DMA transfers across RAM banks and aliases; atomic rejected lengths, tokens and ranges\n";
}
