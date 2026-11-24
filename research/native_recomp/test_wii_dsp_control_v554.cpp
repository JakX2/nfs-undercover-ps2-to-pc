#include "wii_dsp_control_v554.h"
#include <iostream>
#include <source_location>
using namespace undercover::wii;
static void need(bool b,const std::source_location l=std::source_location::current()){
    if(!b)throw std::runtime_error("DSP control line "+std::to_string(l.line()));
}
template<class F>static void reject(F f){bool ok=false;try{f();}catch(const std::exception&){ok=true;}need(ok);}
int main(){
    using C=DspControl;using D=AramDma;
    constexpr uint32_t Other=0x108,Base=WiiPhysicalRam::MEM2_BASE;
    for(unsigned trial=0;trial<32;++trial){
        std::array<uint8_t,128> a{},b{};WiiPhysicalRam ram(a,b);std::atomic<uint32_t> pi{Other};
        D dma(ram,pi,8);C c(dma);
        need(c.read_control()==C::Halt&&!c.reset_request()&&!c.init_request());
        dma.set_info(0x43);
        c.write_control(0x8ac);need(c.read_control()==0x804);
        c.write_control(0x805);auto reset=*c.reset_request();need(reset.boot&&reset.token==1);
        for(unsigned i=0;i<64;++i)need(c.read_control()==0x805&&c.dsp_high()==0);
        reject([&]{c.complete_reset(reset.token+1);});
        reject([&]{c.write_control(0x804);});
        c.complete_reset(reset.token);need(c.read_control()==0x804);
        reject([&]{c.complete_reset(reset.token);});
        // CPU and DSP mailboxes remain independent; only the receiver clears pending.
        const uint32_t payload=0x12345600u+trial;
        c.cpu_write_high(uint16_t(payload>>16));need(!(c.cpu_high()&0x8000));
        c.cpu_write_low(uint16_t(payload));need(c.cpu_high()==uint16_t((payload>>16)|0x8000)&&c.cpu_low()==uint16_t(payload));
        reject([&]{c.cpu_write_high(0);});reject([&]{c.cpu_write_low(0);});
        for(unsigned i=0;i<64;++i)need(c.cpu_high()&0x8000);
        need(c.consume_cpu_mail()==payload&&!c.consume_cpu_mail()&&!(c.cpu_high()&0x8000));
        reject([&]{c.post_dsp_mail(0x80000000u);});
        c.post_dsp_mail(payload^0x40000000u);reject([&]{c.post_dsp_mail(1);});
        need(c.dsp_high()==uint16_t((payload>>16)^0xc000u));
        need(c.dsp_read_low()==uint16_t(payload)&&!(c.dsp_high()&0x8000)&&c.cpu_low()==uint16_t(payload));
        c.write_control(C::Boot|C::Halt|D::ArMask|C::Masks);
        c.raise_dsp_irq();c.raise_ai_irq();need(pi==(Other|D::PiDsp));
        dma.set_main_address(0);dma.set_aram_address(32);
        for(unsigned i=0;i<32;++i)ram.write8(i,uint8_t(i+trial));
        dma.start(32);dma.advance(1);need(c.read_control()&D::Busy);
        reject([&]{c.write_control(C::Halt|C::Reset);});
        // W1C one source while others stay pending, independent of mask.
        c.write_control(C::Boot|C::Halt|D::ArMask|C::Masks|C::DspInt|D::Busy);
        need(!(c.read_control()&C::DspInt)&&(c.read_control()&C::AiInt)&&pi==(Other|D::PiDsp));
        dma.advance(9);need((c.read_control()&D::ArInt)&&!(c.read_control()&D::Busy));
        for(unsigned i=0;i<32;++i)need(ram.read8(Base+32+i)==uint8_t(i+trial));
        c.write_control(C::Boot|C::Halt|D::ArMask|C::Masks|C::AiInt);
        need(pi==(Other|D::PiDsp)&&!(c.read_control()&C::Status));
        c.raise_dsp_irq();c.write_control(C::Boot|C::Halt|D::ArMask|C::Masks|D::ArInt);
        need(pi==(Other|D::PiDsp)&&!(c.read_control()&D::ArInt));
        c.write_control(C::Boot|C::Halt);need(pi==Other&&(c.read_control()&C::DspInt));
        c.write_control(C::Boot|C::Halt|C::DspMask);need(pi==(Other|D::PiDsp));
        pi.fetch_and(~D::PiDsp);c.refresh();need(pi==(Other|D::PiDsp));
        c.write_control(C::Halt|C::DspInt);auto init=*c.init_request();
        need(init.token==2&&!init.boot&&c.read_control()==(C::Halt|C::Init)&&pi==Other);
        for(unsigned i=0;i<64;++i)need(c.read_control()&C::Init);
        reject([&]{c.complete_init(reset.token);});c.complete_init(init.token);
        need(c.read_control()==C::Halt);
        c.write_control(0);need(c.read_control()==0&&c.dsp_high()<0x8000);
        reject([&]{c.write_control(2);});
        reject([&]{c.write_control(C::Reset);});
        c.post_dsp_mail(0x12340000u|trial);need(c.dsp_high()==0x9234&&c.dsp_read_low()==trial);
        c.write_control(0x8ac);c.write_control(0x805);
        need(c.reset_request()->token==3);
        c.complete_reset(3);need(c.read_control()==0x804);
    }
    std::cout<<"PASS: 32 shared DSP/AI/ARAM control trials, explicit reset/init tokens, bidirectional mailboxes and independent interrupt W1C\n";
}
