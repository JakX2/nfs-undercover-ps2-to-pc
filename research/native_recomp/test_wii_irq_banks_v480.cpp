#include "wii_irq_banks_v480.h"
#include <iostream>
using namespace undercover::wii;
using B=WiiIrqBanks;
static void need(bool v){if(!v)throw std::runtime_error("IRQ bank semantics");}
template<class F>void reject(F f){bool failed=false;try{f();}catch(const std::exception&){failed=true;}need(failed);}
int main(){
    constexpr uint32_t other=(1u<<8)|(1u<<14)|(1u<<6);
    std::atomic<uint32_t> cause{other};B b(cause);
    need(cause==other);
    for(unsigned mask=0;mask<32;++mask){
        b.clear_mi(31);b.set_mi_mask(uint16_t(mask));b.raise_mi(0x15);
        need(b.mi_mask()==mask&&b.mi_status()==0x15);
        need(bool(cause.load()&B::PI_MI)==bool(mask&0x15));
        b.clear_mi(0x11);need(b.mi_status()==4);
        need(bool(cause.load()&B::PI_MI)==bool(mask&4));
        b.clear_mi(31);need(cause==other);
    }
    b.set_mi_mask(0xffff);need(b.mi_mask()==31);reject([&]{b.raise_mi(32);});
    // Each channel owns independent pending bits; masking must not clear them.
    for(unsigned ch=0;ch<3;++ch){
        b.raise_exi(ch,B::EXI_INT|B::TC_INT);
        need(b.exi_csr(ch)==10&&cause==other);
        b.write_exi_csr(ch,1);need(b.exi_csr(ch)==11&&cause==(other|B::PI_EXI));
        b.write_exi_csr(ch,2);need(b.exi_csr(ch)==8&&cause==other);
        b.write_exi_csr(ch,4);need(b.exi_csr(ch)==12&&cause==(other|B::PI_EXI));
        b.write_exi_csr(ch,0);need(b.exi_csr(ch)==8&&cause==other);
        b.write_exi_csr(ch,8);need(b.exi_csr(ch)==0&&cause==other);
    }
    b.presence(0,true);need(b.exi_csr(0)==0x1800&&cause==other);
    b.write_exi_csr(0,0x400);need(b.exi_csr(0)==0x1c00&&cause==(other|B::PI_EXI));
    b.write_exi_csr(0,0x1c00);need(b.exi_csr(0)==0x1400&&cause==other);
    b.presence(0,false);need(b.exi_csr(0)==0xc00&&cause==(other|B::PI_EXI));
    b.write_exi_csr(0,0x800);need(b.exi_csr(0)==0&&cause==other);
    b.raise_exi(0,B::TC_INT);b.raise_exi(1,B::EXI_INT);
    b.write_exi_csr(0,4);b.write_exi_csr(1,1);
    b.write_exi_csr(0,8);need(cause==(other|B::PI_EXI));
    b.write_exi_csr(1,2);need(cause==other);
    b.write_exi_csr(0,0x230);need(b.exi_csr(0)==0x230);
    reject([&]{b.write_exi_csr(0,0x2000);});need(b.exi_csr(0)==0x230);
    reject([&]{b.write_exi_csr(2,0x400);});
    reject([&]{b.presence(2,true);});reject([&]{b.raise_exi(2,B::EXT_INT);});
    reject([&]{b.exi_csr(3);});
    b.raise_ai();need(b.ai_control()==B::AI_INT&&cause==other);
    b.write_ai_control(B::AI_MASK);need(b.ai_control()==12&&cause==(other|B::PI_AI));
    b.write_ai_control(0);need(b.ai_control()==8&&cause==other);
    b.write_ai_control(0x7e);need(b.ai_control()==0x56&&cause==other);
    reject([&]{b.write_ai_control(1);});reject([&]{b.write_ai_control(0x80);});need(b.ai_control()==0x56);
    b.raise_ai();b.raise_mi(1);b.raise_exi(1,B::EXI_INT);b.write_exi_csr(1,1);
    need(cause==(other|B::PI_MI|B::PI_EXI|B::PI_AI));
    cause.fetch_and(~B::PI_EXI);b.refresh();need(cause==(other|B::PI_MI|B::PI_EXI|B::PI_AI));
    b.clear_mi(1);b.write_ai_control(8);b.write_exi_csr(1,2);need(cause==other);
    std::cout<<"PASS: Wii MI/EXI/AI register masks, W1C status, independent channels and shared PI levels\n";
}
