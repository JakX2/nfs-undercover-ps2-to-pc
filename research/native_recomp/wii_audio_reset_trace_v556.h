#pragma once
#include <array>
#include <cstdint>
namespace undercover::wii {
// Read-only event observer for the original Hollywood audio clock helper.
// Timebase uses the runtime's virtual instruction clock, not measured PLL
// settling time. MMIO operations are recorded only after successful access.
class AudioResetTrace {
public:
    static constexpr std::array<uint32_t,6> Registers{
        0x0d800180u,0x0d8001d0u,0x0d8001ccu,0x0d8001d0u,0x0d8001d0u,0x0d8001d0u};
    static constexpr std::array<uint32_t,5> Minimum{6075,6075,60750,60750,60750};
    bool begin(bool bound){
        if(!bound||active_||bad_||reads_||writes_)return false;
        active_=true;return true;
    }
    void record(bool write,uint32_t address,uint32_t value)noexcept{
        if(!active_)return;
        const auto i=write?writes_:reads_;
        if(bad_||i>=Registers.size()||address!=Registers[i]){bad_=true;return;}
        if(!write){
            if(reads_>=6||reads_!=writes_){bad_=true;return;}
            if(reads_>=2&&!finish_wait()){bad_=true;return;}
            if(reads_>=3&&value!=ext_){bad_=true;return;}
            read_=value;++reads_;return;
        }
        if(writes_>=6||reads_!=writes_+1||value!=expected(writes_,read_)){bad_=true;return;}
        if(address==Registers[1])ext_=value;
        ++writes_;
    }
    bool start(uint32_t tb){
        if(!good()||waiting_||waits_>=5||reads_!=writes_||writes_!=waits_+2)return fail();
        waiting_=true;crossed_=false;start_=tb;last_=0;polls_=0;return true;
    }
    bool poll(uint32_t tb){
        if(!good()||!waiting_||crossed_||waits_>=5)return fail();
        const uint32_t delta=tb-start_;
        if(delta<=last_||delta-last_>64u||++polls_>65536u)return fail();
        last_=delta;
        if(delta>=Minimum[waits_]){
            if(polls_<2||delta-Minimum[waits_]>=64u)return fail();
            crossed_=true;
        }
        return true;
    }
    bool finish(){
        const bool ok=good()&&reads_==6&&writes_==6&&finish_wait()&&waits_==5;
        active_=false;return ok;
    }
    bool good()const noexcept{return active_&&!bad_;}
    unsigned waits()const noexcept{return waits_;}
    bool waiting()const noexcept{return waiting_;}
    bool crossed()const noexcept{return crossed_;}
    unsigned writes()const noexcept{return writes_;}
private:
    unsigned reads_=0,writes_=0,waits_=0,polls_=0;
    uint32_t read_=0,ext_=0,start_=0,last_=0;
    bool active_=false,bad_=false,waiting_=false,crossed_=false;
    bool fail()noexcept{bad_=true;return false;}
    bool finish_wait()noexcept{
        if(!waiting_||!crossed_||waits_>=5)return fail();
        ++waits_;waiting_=false;crossed_=false;return true;
    }
    static uint32_t expected(unsigned i,uint32_t v)noexcept{
        switch(i){
        case 0:return (v|0x100u)&~0x80u;
        case 1:return v&0x3fffffffu;
        case 2:return (v&0xf8000000u)|0x04b0ffceu;
        case 3:return v&~0x10000000u;
        case 4:return v|0x40000000u;
        case 5:return v|0x80000000u;
        default:return 0;
        }
    }
};
inline thread_local AudioResetTrace audio_reset_trace{};
}
