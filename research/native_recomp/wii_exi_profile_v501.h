#pragma once
#include "wii_exi_tick_binding_v497.h"
#include <charconv>
#include <fstream>
#include <filesystem>
#include <string>
#include <string_view>
namespace undercover::wii {
// Explicit host profile, not a dump or assertion about real console data.
// No defaults, implicit file creation, or device responses without a profile.
struct ExiHostProfile {
    uint32_t id,di_config,rtc_seconds,latency;
    ExiMxDevice::Sram sram;
    static ExiHostProfile parse(std::string_view text){
        if(text.size()>512)throw std::invalid_argument("EXI profile length");
        ExiHostProfile p{};
        auto field=[&](std::string_view key){
            const auto end=text.find('\n');if(end==std::string_view::npos)throw std::invalid_argument("EXI profile newline");
            auto line=text.substr(0,end);text.remove_prefix(end+1);
            if(!line.empty()&&line.back()=='\r')line.remove_suffix(1);
            if(!line.starts_with(key))throw std::invalid_argument("EXI profile field");
            return line.substr(key.size());
        };
        auto number=[](std::string_view s,unsigned digits){
            if(s.size()!=digits)throw std::invalid_argument("EXI profile number length");
            uint32_t v=0;auto rc=std::from_chars(s.data(),s.data()+s.size(),v,16);
            if(rc.ec!=std::errc{}||rc.ptr!=s.data()+s.size())throw std::invalid_argument("EXI profile number");
            return v;
        };
        if(!field("UNDERCOVER_EXI_PROFILE_V1").empty())throw std::invalid_argument("EXI profile version");
        p.id=number(field("id="),8);p.di_config=number(field("di_config="),8);
        p.rtc_seconds=number(field("rtc_seconds="),8);p.latency=number(field("latency="),8);
        const auto bytes=field("sram=");
        if(bytes.size()!=128||!text.empty()||!p.latency||p.latency>1000000u)
            throw std::invalid_argument("EXI profile geometry");
        for(unsigned i=0;i<64;++i)p.sram[i]=uint8_t(number(bytes.substr(2*i,2),2));
        return p;
    }
    static ExiHostProfile load(const std::filesystem::path& path){
        std::ifstream file(path,std::ios::binary);if(!file)throw std::runtime_error("EXI profile unavailable");
        std::array<char,513> buf{};file.read(buf.data(),buf.size());
        const auto n=file.gcount();
        if(file.bad()||n<=0||n>512||!file.eof())throw std::runtime_error("EXI profile size/read");
        return parse(std::string_view(buf.data(),size_t(n)));
    }
};
// Wii-side DI configuration read, explicitly owned only in a device profile
// session. See WiiBrew Hardware/Drive_Interface (DICFG at offset 0x24).
// This is not the Hollywood revision register or a full optical drive backend.
class ExiDiConfigBinding {
public:
    explicit ExiDiConfigBinding(uint32_t value):value_(value){
        if(active_)throw std::logic_error("EXI DI config already bound");
        active_=this;
    }
    ~ExiDiConfigBinding(){active_=nullptr;}
    ExiDiConfigBinding(const ExiDiConfigBinding&)=delete;
    ExiDiConfigBinding& operator=(const ExiDiConfigBinding&)=delete;
    static bool active()noexcept{return active_!=nullptr;}
    static void check(uint32_t a,unsigned width,bool integer,bool write){
        if(!active_)return;
        const uint32_t p=a&0x3fffffffu;const uint64_t end=uint64_t(p)+width;
        const auto overlaps=[&](uint32_t base){return p<base+4u&&end>base;};
        if(!overlaps(Base)&&!overlaps(Mirror))return;
        if(!integer||width!=4||write||(p!=Base&&p!=Mirror)||(a&0xc0000000u)==0x40000000u)
            throw std::runtime_error("EXI DI config access");
    }
    static std::optional<uint32_t> read32(uint32_t a){
        if(!active_)return std::nullopt;
        check(a,4,true,false);
        const uint32_t p=a&0x3fffffffu;
        return p==Base||p==Mirror?std::optional<uint32_t>(active_->value_):std::nullopt;
    }
private:
    static constexpr uint32_t Base=0x0d006024u,Mirror=0x0d806024u;
    uint32_t value_;inline static thread_local ExiDiConfigBinding* active_=nullptr;
};
class ExiProfileSession {
public:
    // Fixed RTC base for deterministic startup. A production clock may be
    // injected by the caller later. No file writes from device execution.
    ExiProfileSession(ExiController& ctl,const ExiHostProfile& p)
        :ctl_(ctl),mx_(p.sram,[seconds=p.rtc_seconds]{return seconds;}),id_(p.id),
         scheduler_(ctl,mx_,id_,p.latency),di_(p.di_config),tick_(scheduler_){
        if(active_)throw std::logic_error("EXI profile already bound");
        active_=this;
    }
    ~ExiProfileSession(){active_=nullptr;}
    ExiProfileSession(const ExiProfileSession&)=delete;
    ExiProfileSession& operator=(const ExiProfileSession&)=delete;
    uint64_t completed()const{return scheduler_.completed();}
    const ExiMxDevice::Sram& sram()const{return mx_.sram();}
    bool sram_dirty()const{return mx_.dirty();}
    static const ExiProfileSession* current()noexcept{return active_;}
    const ExiController& controller()const noexcept{return ctl_;}
    const ExiMxDevice& endpoint()const noexcept{return mx_;}
    const ExiEndpointScheduler& scheduler()const noexcept{return scheduler_;}
private:
    inline static thread_local const ExiProfileSession* active_=nullptr;
    ExiController& ctl_;
    ExiMxDevice mx_;ExiIdEndpoint id_;ExiEndpointScheduler scheduler_;
    ExiDiConfigBinding di_;ExiTickBinding tick_;
};
}
