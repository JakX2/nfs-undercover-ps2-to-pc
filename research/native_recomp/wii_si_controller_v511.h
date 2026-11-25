#pragma once
#include <array>
#include <atomic>
#include <cstdint>
#include <limits>
#include <optional>
#include <span>
#include <stdexcept>
namespace undercover::wii {
// Native Wii SI communication RAM and cold sampling registers.
// Register maps: WiiBrew Hardware/Serial_Interface, Hardware/Processor_Interface,
// and YAGCD 5.8. No automatic controller response, polling or VI timing.
class SiController {
public:
    static constexpr uint32_t PI_SI=1u<<3,TC_INT=1u<<31,TC_MASK=1u<<30,
        COM_ERR=1u<<29,RDST_INT=1u<<28,RDST_MASK=1u<<27,TSTART=1u;
    static constexpr uint32_t ERR_NOREP=8u,ERR_COLL=4u,ERR_OVRUN=2u,ERR_UNRUN=1u;
    static constexpr unsigned Poll=0x30,Control=0x34,Status=0x38,Buffer=0x80;
    static constexpr uint32_t ControlParams=0x007f7f06u,ControlMasks=TC_MASK|RDST_MASK,
        ControlWriteBits=ControlParams|ControlMasks|TC_INT|COM_ERR|RDST_INT|TSTART;
    struct Request{
        uint64_t token;unsigned channel,out_length,in_length;
        std::array<uint8_t,128> tx;
    };
    explicit SiController(std::atomic<uint32_t>& pi):pi_(pi){refresh();}
    SiController(const SiController&)=delete;
    SiController& operator=(const SiController&)=delete;
    static constexpr bool supported(unsigned off)noexcept{
        return off==Poll||off==Control||off==Status||(off>=Buffer&&off<0x100&&!(off&3));
    }
    uint32_t read(unsigned off)const{
        if(off==Poll)return poll_;
        if(off==Control)return config_|(tc_?TC_INT:0u)|(error_?COM_ERR:0u)|(pending_?TSTART:0u);
        if(off==Status)return status_;
        if(off>=Buffer&&off<0x100&&!(off&3)){
            uint32_t v=0;for(unsigned i=0;i<4;++i)v=(v<<8)|ram_[off-Buffer+i];return v;
        }
        throw std::out_of_range("SI register");
    }
    void write(unsigned off,uint32_t value){
        if(off==Poll){
            // The original cold SI sampling setup programs X/Y with
            // polling disabled. Reject enabled ports until VI scheduling.
            if(value&~0x03ffff0fu)throw std::runtime_error("SI active polling or reserved bits");
            poll_=value;return;
        }
        if(off==Status){
            // Error nibbles are W1C, not writable status. No output-buffer
            // strobe yet because the separate polling backend is absent.
            if(value&~0x0f0f0f0fu)throw std::runtime_error("SI status unsupported");
            status_&=~value;refresh();return;
        }
        if(off==Control){write_control(value);return;}
        if(off>=Buffer&&off<0x100&&!(off&3)){
            if(pending_)throw std::runtime_error("SI RAM busy");
            for(unsigned i=0;i<4;++i)ram_[off-Buffer+i]=uint8_t(value>>(24-8*i));
            return;
        }
        throw std::out_of_range("SI register");
    }
    std::optional<Request> pending()const{return pending_;}
    uint64_t issued_tokens()const noexcept{return sequence_;}
    // Exact-length response or explicit error; a no-response event never
    // overwrites the shared communication RAM with fabricated bytes.
    void complete(uint64_t token,std::span<const uint8_t> response,unsigned errors=0){
        if(!pending_||pending_->token!=token||errors>15u||
           response.size()!=(errors?0u:pending_->in_length))
            throw std::runtime_error("SI completion token/geometry");
        if(errors)status_|=uint32_t(errors)<<((3u-pending_->channel)*8u);
        else for(unsigned i=0;i<response.size();++i)ram_[i]=response[i];
        error_=errors!=0;tc_=true;pending_.reset();refresh();
    }
    void refresh()noexcept{
        const uint32_t desired=tc_&&(config_&TC_MASK)?PI_SI:0u;
        auto current=pi_.load(std::memory_order_relaxed);
        while(!pi_.compare_exchange_weak(current,(current&~PI_SI)|desired,std::memory_order_relaxed,std::memory_order_relaxed)){}
    }
private:
    static constexpr unsigned length(unsigned encoded){return encoded?encoded:128u;}
    void write_control(uint32_t v){
        if(v&~ControlWriteBits)
            throw std::runtime_error("SI reserved control");
        const auto params=v&ControlParams;
        if(pending_&&((v&TSTART)||params!=(config_&ControlParams)))throw std::runtime_error("SI transfer in progress");
        if((v&TSTART)&&sequence_==std::numeric_limits<uint64_t>::max())throw std::overflow_error("SI token overflow");
        if(v&TC_INT)tc_=false;
        config_=v&(ControlParams|ControlMasks);
        if(v&TSTART){
            pending_=Request{++sequence_,(v>>1)&3u,length((v>>16)&127u),length((v>>8)&127u),ram_};
            error_=false;
        }
        refresh();
    }
    std::atomic<uint32_t>& pi_;std::array<uint8_t,128> ram_{};
    uint32_t poll_=0,config_=0,status_=0;bool tc_=false,error_=false;
    uint64_t sequence_=0;std::optional<Request> pending_;
};
}
