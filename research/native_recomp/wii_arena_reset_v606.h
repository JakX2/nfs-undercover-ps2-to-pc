#pragma once
#include <cstdint>
#include <optional>
#include <stdexcept>
namespace undercover::wii {
// Explicit cold reset test profile, not a general PI reset implementation.
// The previous V67 owner fixture used 0x100 + trial*8 for this register.
class ArenaResetProfile {
public:
    static constexpr uint32_t Address=0x0c003024u,ColdValue=0x100u;
    bool arm(unsigned lane){
        if(failed_||armed_||lane!=reads_+1||lane>2)return fail();
        armed_=true;return true;
    }
    uint32_t read(){
        if(failed_||!armed_||reads_>=2){fail();throw std::runtime_error("arena reset read out of phase");}
        armed_=false;++reads_;return ColdValue;
    }
    unsigned reads()const noexcept{return reads_;}
    bool armed()const noexcept{return armed_;}
    bool failed()const noexcept{return failed_;}
    bool complete()const noexcept{return reads_==2&&!armed_&&!failed_;}
    void reject(){fail();throw std::runtime_error("unsupported arena reset access");}
private:
    unsigned reads_=0;
    bool armed_=false,failed_=false;
    bool fail(){failed_=true;return false;}
};
class ArenaResetBinding {
public:
    explicit ArenaResetBinding(ArenaResetProfile& p):profile_(p){
        if(active_)throw std::logic_error("arena reset already bound");
        active_=this;
    }
    ~ArenaResetBinding(){active_=nullptr;}
    ArenaResetBinding(const ArenaResetBinding&)=delete;
    ArenaResetBinding& operator=(const ArenaResetBinding&)=delete;
    static void check(uint32_t a,unsigned n,bool integer,bool write){
        if(!active_)return;
        const auto p=a&0x3fffffffu;
        if(p>=ArenaResetProfile::Address+4||uint64_t(p)+n<=ArenaResetProfile::Address)return;
        if(!integer||write||n!=4||p!=ArenaResetProfile::Address||(a&0xc0000000u)==0x40000000u)
            active_->profile_.reject();
    }
    static std::optional<uint32_t> read32(uint32_t a){
        if(!active_)return {};
        check(a,4,true,false);
        if((a&0x3fffffffu)!=ArenaResetProfile::Address)return {};
        return active_->profile_.read();
    }
private:
    ArenaResetProfile& profile_;
    inline static thread_local ArenaResetBinding* active_=nullptr;
};
}
