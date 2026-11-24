#include "wii_dsp_boot_profile_v580.h"
#include <iostream>
#include <vector>
#include <source_location>
using namespace undercover::wii;
static void need(bool b,const std::source_location loc=std::source_location::current()){
    if(!b)throw std::runtime_error("V580 test line "+std::to_string(loc.line()));
}
int main(){
    using P=DspBootProfile;
    std::vector<uint8_t> m1(0x01000100),m2(128,0x97);
    for(unsigned trial=0;trial<16;++trial){
        for(unsigned i=0;i<128;++i)m1[P::Main+i]=uint8_t(i*17+trial);
        std::fill(m2.begin(),m2.end(),0x97);
        std::atomic<uint32_t> pi{0x1000};
        WiiPhysicalRam ram(m1,m2);AramDma dma(ram,pi,8);DspControl dsp(dma);
        P p(ram,dma,dsp,100);uint64_t tick=100;
        auto advance=[&](unsigned n=1){while(n--)p.advance(++tick);};
        auto reset=[&](){dma.set_info(0x43);dsp.write_control(0x8ac);advance();dsp.write_control(0x805);advance();need(dsp.reset_request().has_value());advance(7);need(dsp.reset_request().has_value());advance();need(!dsp.reset_request());};
        reset();need(p.phase()==P::Phase::Dma1);
        dsp.cpu_write_high(0);advance();
        for(unsigned i=0;i<2;++i){
            dma.set_main_address(P::Main);dma.set_aram_address(0);dma.start(32);advance();
            need(dma.control_bits()&AramDma::Busy);advance(7);need(dma.completed()==i);advance();
            need(dma.completed()==i+1&&p.memory()&&(dma.control_bits()&AramDma::ArInt));
            dsp.write_control(0x824);advance();need(p.acks()==i+1);
            advance(16+trial);
        }
        dsp.write_control(4);advance();need(dsp.init_request().has_value());advance(8);need(!dsp.init_request());
        dsp.write_control(0);advance();need(!dsp.dsp_high());advance(8);
        need(dsp.dsp_high()==0x8123&&dsp.dsp_read_low()==0x4567);
        advance();dsp.write_control(4);advance();reset();need(p.done()&&p.aux_preserved());
        need(pi.load()==0x1000);
    }
    for(unsigned fault=0;fault<7;++fault){
        std::atomic<uint32_t> pi{0};WiiPhysicalRam ram(m1,m2);AramDma dma(ram,pi,8);DspControl dsp(dma);
        P p(ram,dma,dsp,100);bool rejected=false;
        try{
            if(fault==0){p.advance(99);}
            else if(fault==1){p.advance(1000101);}
            else if(fault==2){dsp.write_control(5);p.advance(101);}
            else{
                dma.set_info(0x43);dsp.write_control(0x805);p.advance(101);p.advance(109);
                if(fault==3)dma.set_main_address(P::Main+32);else dma.set_main_address(P::Main);
                dma.set_aram_address(fault==4?32:0);dma.start(fault==5?64:32);p.advance(110);
                if(fault==6){m1[P::Main]^=1;p.advance(118);}
            }
        }catch(const std::exception&){rejected=true;}
        need(rejected&&!p.done());
    }
    std::cout<<"V580_DSP_PROFILE trials=16 resets=32 dma=32 acks=32 mailbox=16 refusal=7 firmware_executed=0\n";
}
