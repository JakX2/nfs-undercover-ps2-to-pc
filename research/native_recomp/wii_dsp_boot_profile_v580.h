#pragma once
#include "wii_aram_binding_v553.h"
namespace undercover::wii {
// Explicit synthetic boot service. No DSP instruction execution. Reset/init
// completion and the boot mailbox are events, never effects of MMIO reads.
class DspBootProfile {
public:
    static constexpr uint32_t Main=0x01000000u,Aux=WiiPhysicalRam::MEM2_BASE;
    static constexpr uint32_t Reply=0x01234567u;
    enum class Phase { Reset1, Dma1, Ack1, Dma2, Ack2, Init, Mail, Drain, Reset2, Done };
    DspBootProfile(WiiPhysicalRam& ram,AramDma& dma,DspControl& dsp,uint64_t tick)
        :ram_(ram),dma_(dma),dsp_(dsp),start_(tick),last_(tick){
        need(dsp_.owns(dma_)&&dma_.completed()==0&&dma_.control_bits()==0&&
             ram_.valid(Main,128)&&ram_.valid(Aux,64));
        for(unsigned i=0;i<64;++i)aux_[i]=ram_.read8(Aux+i);
        for(unsigned i=0;i<128;++i)staged_[i]=ram_.read8(Main+i);
    }
    Phase phase()const noexcept{return phase_;}
    unsigned resets()const noexcept{return resets_;}
    unsigned acks()const noexcept{return acks_;}
    unsigned replies()const noexcept{return replies_;}
    unsigned failure()const noexcept{return failure_;}
    bool done()const noexcept{return phase_==Phase::Done&&resets_==2&&acks_==2&&replies_==1&&dma_.completed()==2;}
    void advance(uint64_t tick){
        if(failure_||tick<last_||tick-start_>1000000u)fail(1);
        last_=tick;dma_.advance(tick);
        const auto ctl=dsp_.read_control();
        const auto reset=dsp_.reset_request(),init=dsp_.init_request();
        if(phase_!=Phase::Reset1&&phase_!=Phase::Reset2&&reset)fail(2);
        if(phase_!=Phase::Init&&init)fail(2);
        switch(phase_){
        case Phase::Reset1:case Phase::Reset2:
            if(reset){
                if(!reset->boot||dma_.info()!=0x43u||(ctl&DspControl::Halt)==0)fail(3);
                if(wait(tick,reset->token)){
                    dsp_.complete_reset(reset->token);++resets_;
                    phase_=phase_==Phase::Reset1?Phase::Dma1:Phase::Done;
                }
            }
            break;
        case Phase::Dma1:case Phase::Dma2:{
            const unsigned n=phase_==Phase::Dma1?1:2;
            if(ctl&AramDma::Busy){
                if(!dma_seen_){
                    if(dma_.main_address()!=Main||dma_.aram_address()!=0||dma_.count()!=32||
                       dma_.completed()!=n-1||(ctl&AramDma::ArInt))fail(4);
                    dma_seen_=true;
                }
            }else if(dma_.completed()==n){
                if(!dma_seen_||!(ctl&AramDma::ArInt)||dma_.count()!=0||!memory())fail(5);
                dma_seen_=false;phase_=n==1?Phase::Ack1:Phase::Ack2;
            }else if(dma_.completed()!=n-1)fail(5);
            break;
        }
        case Phase::Ack1:case Phase::Ack2:
            if(ctl&AramDma::Busy)fail(6);
            if(!(ctl&AramDma::ArInt)){
                ++acks_;phase_=phase_==Phase::Ack1?Phase::Dma2:Phase::Init;
            }
            break;
        case Phase::Init:
            if(init){
                if((ctl&DspControl::Halt)==0||acks_!=2||dma_.completed()!=2)fail(7);
                if(wait(tick,init->token)){dsp_.complete_init(init->token);phase_=Phase::Mail;}
            }
            break;
        case Phase::Mail:
            if(!(ctl&DspControl::Halt)){
                if(wait(tick,3)){
                    dsp_.post_dsp_mail(Reply);++replies_;phase_=Phase::Drain;
                }
            }
            break;
        case Phase::Drain:
            if(!(dsp_.dsp_high()&0x8000u)){
                if(replies_!=1)fail(8);
                phase_=Phase::Reset2;
            }
            break;
        case Phase::Done:
            if(ctl&(AramDma::Busy|AramDma::ArInt|DspControl::Reset|DspControl::Init))fail(9);
            break;
        }
    }
    bool memory()const{
        for(unsigned i=0;i<128;++i)if(ram_.read8(Main+i)!=staged_[i])return false;
        for(unsigned i=0;i<64;++i)if(ram_.read8(Aux+i)!=(i<32?staged_[i]:aux_[i]))return false;
        return true;
    }
    bool aux_preserved()const{
        for(unsigned i=0;i<64;++i)if(ram_.read8(Aux+i)!=(i<32?staged_[i]:aux_[i]))return false;
        return true;
    }
private:
    WiiPhysicalRam& ram_;AramDma& dma_;DspControl& dsp_;
    uint64_t start_,last_,due_=0,token_=0;
    Phase phase_=Phase::Reset1;unsigned resets_=0,acks_=0,replies_=0,failure_=0;
    bool dma_seen_=false,waiting_=false;
    std::array<uint8_t,64> aux_{};std::array<uint8_t,128> staged_{};
    static void need(bool ok){if(!ok)throw std::runtime_error("V580 DSP profile geometry");}
    [[noreturn]]void fail(unsigned n){failure_=n;throw std::runtime_error("V580 DSP profile rejected");}
    bool wait(uint64_t tick,uint64_t token){
        if(!waiting_){
            if(tick>std::numeric_limits<uint64_t>::max()-8u)fail(10);
            waiting_=true;token_=token;due_=tick+8u;return false;
        }
        if(token_!=token)fail(10);
        if(tick<due_)return false;
        waiting_=false;return true;
    }
};
class DspBootSession {
public:
    DspBootSession(std::span<uint8_t> mem1,std::span<uint8_t> mem2,std::atomic<uint32_t>& pi,uint64_t tick)
        :ram_(mem1,mem2),dma_(ram_,pi,8),dsp_(dma_),profile_(ram_,dma_,dsp_,tick),binding_(dma_,dsp_){
        if(active_)throw std::logic_error("V580 DSP session already active");
        active_=this;
    }
    ~DspBootSession(){active_=nullptr;}
    DspBootSession(const DspBootSession&)=delete;
    DspBootSession& operator=(const DspBootSession&)=delete;
    DspBootProfile& profile()noexcept{return profile_;}
    static void advance(uint64_t tick){if(active_)active_->profile_.advance(tick);}
private:
    WiiPhysicalRam ram_;AramDma dma_;DspControl dsp_;DspBootProfile profile_;AramBinding binding_;
    inline static thread_local DspBootSession* active_=nullptr;
};
}
