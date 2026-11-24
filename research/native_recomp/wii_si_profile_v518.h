#pragma once
#include "wii_si_type_scheduler_v514.h"
#include "wii_si_binding_v512.h"
#include <charconv>
#include <filesystem>
#include <fstream>
#include <string_view>
namespace undercover::wii {
// Test profile only. Every port must explicitly be absent or have a
// caller-supplied 3-byte type response. No inferred controller identity.
struct SiHostProfile {
    uint32_t latency;
    SiTypeScheduler::Profile ports;
    static SiHostProfile parse(std::string_view text){
        if(text.size()>256)throw std::invalid_argument("SI profile length");
        auto field=[&](std::string_view key){
            auto end=text.find('\n');
            if(end==std::string_view::npos)throw std::invalid_argument("SI profile newline");
            auto line=text.substr(0,end);text.remove_prefix(end+1);
            if(!line.empty()&&line.back()=='\r')line.remove_suffix(1);
            if(!line.starts_with(key))throw std::invalid_argument("SI profile field");
            return line.substr(key.size());
        };
        auto hex=[](std::string_view s,unsigned digits){
            if(s.size()!=digits)throw std::invalid_argument("SI profile hex length");
            uint32_t n=0;auto result=std::from_chars(s.data(),s.data()+s.size(),n,16);
            if(result.ec!=std::errc{}||result.ptr!=s.data()+s.size())
                throw std::invalid_argument("SI profile hex");
            return n;
        };
        if(!field("UNDERCOVER_SI_PROFILE_V1").empty())throw std::invalid_argument("SI profile version");
        SiHostProfile p{};
        p.latency=hex(field("latency="),8);
        if(!p.latency||p.latency>1000000u)throw std::invalid_argument("SI profile latency");
        constexpr std::array<std::string_view,4> keys{"port0=","port1=","port2=","port3="};
        for(unsigned i=0;i<4;++i){
            const auto v=field(keys[i]);
            if(v=="absent")p.ports[i]=SiTypeScheduler::Port::absent();
            else{
                const auto n=hex(v,6);
                p.ports[i]=SiTypeScheduler::Port::present({uint8_t(n>>16),uint8_t(n>>8),uint8_t(n)});
            }
        }
        if(!text.empty())throw std::invalid_argument("SI profile trailing data");
        return p;
    }
    static SiHostProfile load(const std::filesystem::path& path){
        std::ifstream f(path,std::ios::binary);if(!f)throw std::runtime_error("SI profile unavailable");
        std::array<char,257> buf{};f.read(buf.data(),buf.size());
        const auto n=f.gcount();
        if(f.bad()||n<=0||n>256||!f.eof())throw std::runtime_error("SI profile size/read");
        return parse(std::string_view(buf.data(),size_t(n)));
    }
};
// Controller and MMIO binding are owned by the caller and must outlive
// this session. Scope destruction unbinds ticks; no background service.
class SiProfileSession {
public:
    SiProfileSession(SiController& ctl,const SiHostProfile& p)
        :scheduler_(ctl,p.ports,p.latency),tick_(scheduler_){
        if(!SiBinding::active())throw std::logic_error("SI profile missing MMIO binding");
    }
    SiProfileSession(const SiProfileSession&)=delete;
    SiProfileSession& operator=(const SiProfileSession&)=delete;
    uint64_t completed()const noexcept{return scheduler_.completed();}
private:
    SiTypeScheduler scheduler_;
    SiTickBinding tick_;
};
}
