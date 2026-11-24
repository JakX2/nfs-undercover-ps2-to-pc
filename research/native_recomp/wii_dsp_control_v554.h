#pragma once
#include "wii_aram_dma_v552.h"
#include <optional>
namespace undercover::wii {
// One CPU-thread owner, independent mailbox transport. Hardware references:
// WiiBrew Hardware/DSP, Dolphin GameCube DSP Users Manual, Mailboxes.
// No automatic DSP replies, firmware, or DSP ISA execution.
class DspMailbox {
public:
    static constexpr uint32_t Pending=0x80000000u;
    uint16_t high()const noexcept{return uint16_t((data_>>16)|(pending_?0x8000u:0u));}
    uint16_t low()const noexcept{return uint16_t(data_);}
    bool pending()const noexcept{return pending_;}
    void write_high(uint16_t v){
        idle();data_=(uint32_t(v&0x7fffu)<<16)|(data_&0xffffu);
    }
    void write_low(uint16_t v){
        idle();data_=(data_&0x7fff0000u)|v;pending_=true;
    }
    uint16_t consume_low()noexcept{pending_=false;return low();}
    std::optional<uint32_t> consume()noexcept{
        if(!pending_)return std::nullopt;
        pending_=false;return data_;
    }
    void post(uint32_t data){
        if(data&Pending)throw std::invalid_argument("DSP mailbox payload");
        idle();data_=data;pending_=true;
    }
private:
    uint32_t data_=0;bool pending_=false;
    void idle()const{if(pending_)throw std::logic_error("DSP mailbox busy");}
};
class DspControl {
public:
    static constexpr uint16_t Reset=1u,Halt=4u,AiInt=8u,AiMask=0x10u,
        DspInt=0x80u,DspMask=0x100u,Init=0x400u,Boot=0x800u;
    static constexpr uint16_t Masks=AiMask|DspMask,Status=AiInt|DspInt;
    struct Request{uint64_t token;bool boot;};
    explicit DspControl(AramDma& dma):dma_(dma){dma_.claim_peer();refresh();}
    ~DspControl(){dma_.release_peer();}
    DspControl(const DspControl&)=delete;
    DspControl& operator=(const DspControl&)=delete;
    bool owns(const AramDma& dma)const noexcept{return &dma_==&dma;}
    uint16_t read_control()const noexcept{
        return uint16_t(mode_|status_|masks_|dma_.control_bits()|
            (reset_?Reset:0u)|(init_?Init:0u));
    }
    void write_control(uint16_t v){
        constexpr uint16_t accepted=Reset|Halt|Masks|Status|Init|Boot|
            AramDma::ArInt|AramDma::ArMask|AramDma::Busy;
        if(v&~accepted)throw std::runtime_error("unsupported DSP control");
        if(reset_||init_)throw std::logic_error("DSP backend transition pending");
        const bool reset=(v&Reset)!=0,init=!reset&&(mode_&Boot)&&!(v&Boot);
        if((reset||init)&&!(v&Halt))throw std::runtime_error("DSP transition without halt");
        if((reset||init)&&(dma_.control_bits()&AramDma::Busy))throw std::logic_error("DSP transition during DMA");
        if((reset||init)&&sequence_==std::numeric_limits<uint64_t>::max())throw std::overflow_error("DSP event token");
        // Init and ARAM busy are read-only in this subset. Mask and W1C
        // writes are independent of each other and of peer PI sources.
        mode_=v&(Halt|Boot);masks_=v&Masks;status_&=~(v&Status);
        dma_.write_irq_control(v&(AramDma::ArInt|AramDma::ArMask));
        if(reset)reset_=Request{++sequence_,bool(mode_&Boot)};
        if(init)init_=Request{++sequence_,false};
        refresh();
    }
    std::optional<Request> reset_request()const noexcept{return reset_;}
    std::optional<Request> init_request()const noexcept{return init_;}
    void complete_reset(uint64_t token){
        if(!reset_||reset_->token!=token)throw std::logic_error("stale DSP reset completion");
        reset_.reset();
    }
    void complete_init(uint64_t token){
        if(!init_||init_->token!=token)throw std::logic_error("stale DSP init completion");
        init_.reset();
    }
    void cpu_write_high(uint16_t v){cpu_.write_high(v);}
    void cpu_write_low(uint16_t v){cpu_.write_low(v);}
    uint16_t cpu_high()const noexcept{return cpu_.high();}
    uint16_t cpu_low()const noexcept{return cpu_.low();}
    std::optional<uint32_t> consume_cpu_mail()noexcept{return cpu_.consume();}
    uint16_t dsp_high()const noexcept{return dsp_.high();}
    uint16_t dsp_read_low()noexcept{return dsp_.consume_low();}
    void post_dsp_mail(uint32_t v){dsp_.post(v);}
    // Backend event sources, not implicit effects of polling or mailbox reads.
    void raise_dsp_irq()noexcept{status_|=DspInt;refresh();}
    void raise_ai_irq()noexcept{status_|=AiInt;refresh();}
    void refresh()noexcept{
        dma_.set_peer_irq((status_&uint16_t(masks_>>1))!=0);
    }
private:
    AramDma& dma_;DspMailbox cpu_{},dsp_{};
    uint16_t mode_=Halt,status_=0,masks_=0;uint64_t sequence_=0;
    std::optional<Request> reset_,init_;
};
}
