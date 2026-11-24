#pragma once
#include "wii_exi_controller_v489.h"
#include <functional>
#include <algorithm>
namespace undercover::wii {
// Host-supplied MX23L4005 RTC/SRAM subset, not a ROM dump or console identity.
// Protocol references: WiiBrew Hardware/RTC-SRAM-ROM; YAGCD chapter 10.
// The RTC source supplies seconds in the console epoch; no host time guessing.
class ExiMxDevice {
public:
    using Sram=std::array<uint8_t,64>;
    explicit ExiMxDevice(Sram initial,std::function<uint32_t()> rtc)
        :sram_(initial),rtc_(std::move(rtc)){if(!rtc_)throw std::invalid_argument("EXI RTC source");}
    void deselect()noexcept{mode_=Mode::Command;cursor_=0;latched_=0;}
    const Sram& sram()const noexcept{return sram_;}
    bool dirty()const noexcept{return dirty_;}
    void mark_saved()noexcept{dirty_=false;}
    uint32_t immediate(const ExiController::Request& req){
        if(req.dma||!req.length||req.length>4||req.direction>1)
            throw std::runtime_error("MX immediate geometry");
        if(mode_==Mode::Command){
            if(req.direction!=1||req.length!=4)throw std::runtime_error("MX command format");
            const uint32_t cmd=req.tx;
            const bool write=(cmd&0x80000000u)!=0;const auto addr=cmd&0x7fffffffu;
            if(addr==0x20000000u&&!write){
                const auto now=rtc_();latched_=now;cursor_=0;mode_=Mode::RtcRead;return 0;
            }
            // Only the base SRAM window is supported. Reject unrelated
            // boot ROM, UART and extended Wii register protocols explicitly.
            if(addr!=0x20000100u)throw std::runtime_error("MX unsupported address");
            cursor_=0;mode_=write?Mode::SramWrite:Mode::SramRead;return 0;
        }
        const unsigned n=req.length;
        if(mode_==Mode::RtcRead&&req.direction==0){
            if(n>4u-cursor_)throw std::runtime_error("MX RTC read length");
            uint32_t v=0;for(unsigned i=0;i<n;++i)v|=((latched_>>(24u-8u*(cursor_+i)))&0xffu)<<(24u-8u*i);
            cursor_+=n;return v;
        }
        if(n>64u-cursor_)throw std::runtime_error("MX SRAM immediate range");
        if(mode_==Mode::SramRead&&req.direction==0){
            uint32_t v=0;for(unsigned i=0;i<n;++i)v|=uint32_t(sram_[cursor_+i])<<(24u-8u*i);
            cursor_+=n;return v;
        }
        if(mode_==Mode::SramWrite&&req.direction==1){
            for(unsigned i=0;i<n;++i)sram_[cursor_+i]=uint8_t(req.tx>>(24u-8u*i));
            cursor_+=n;dirty_=true;return 0;
        }
        throw std::runtime_error("MX direction");
    }
    void service(ExiController& ctl,const ExiController::Request& req){
        // This method only accepts the exact currently pending request.
        const auto live=ctl.pending(req.channel);
        if(!live||live->token!=req.token||req.channel!=0||req.device!=1||
           live->device!=req.device||live->length!=req.length||live->direction!=req.direction||
           live->tx!=req.tx||live->dma!=req.dma||live->physical!=req.physical)
            throw std::runtime_error("MX stale request");
        if(!req.dma){const auto response=immediate(req);ctl.complete_immediate(0,req.token,response);return;}
        if(mode_!=Mode::SramRead||req.direction!=0||req.length>64u-cursor_)
            throw std::runtime_error("MX unsupported DMA");
        ctl.complete_dma(0,req.token,std::span<const uint8_t>(sram_).subspan(cursor_,req.length));
        cursor_+=req.length;
    }
private:
    enum class Mode{Command,RtcRead,SramRead,SramWrite};
    Sram sram_;std::function<uint32_t()> rtc_;Mode mode_=Mode::Command;
    unsigned cursor_=0;uint32_t latched_=0;bool dirty_=false;
};
// A separately configured ID-only endpoint. The response is a host parameter,
// never a claimed hardware ID. Unsupported commands fail closed.
class ExiIdEndpoint {
public:
    explicit ExiIdEndpoint(uint32_t id):id_(id){}
    void deselect()noexcept{command_=false;}
    void service(ExiController& ctl,const ExiController::Request& req){
        const auto live=ctl.pending(req.channel);
        if(!live||live->token!=req.token||live->device!=req.device||
           live->length!=req.length||live->direction!=req.direction||live->tx!=req.tx||live->dma||req.dma)
            throw std::runtime_error("EXI ID stale request");
        if(!command_&&req.direction==1&&req.length==2&&(req.tx>>16)==0){
            ctl.complete_immediate(req.channel,req.token,0);command_=true;return;
        }
        if(command_&&req.direction==0&&req.length==4){
            ctl.complete_immediate(req.channel,req.token,id_);command_=false;return;
        }
        throw std::runtime_error("EXI ID command");
    }
private:uint32_t id_;bool command_=false;
};
}
