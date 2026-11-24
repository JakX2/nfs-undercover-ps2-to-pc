#pragma once
#include <cstdint>

namespace undercover::wii {
// A host-side observation only; this never writes guest registers or memory.
class RestoredFrameWitness {
public:
    bool begin(uint32_t lr,uint32_t sp,uint64_t inst){
        if(stage_||!lr||(lr&3u)||(sp&7u)||sp<0x80000000u||sp>=0x81800000u)return false;
        lr_=lr;sp_=sp;start_=inst;stage_=1;return true;
    }
    bool before_return(uint32_t lr,uint32_t sp,uint64_t inst){
        if(stage_!=1||lr!=lr_||sp!=sp_||inst<=start_)return false;
        returning_=inst;stage_=2;return true;
    }
    bool after_return(uint32_t pc,uint32_t sp,uint64_t inst){
        if(stage_!=2||pc!=lr_||sp!=sp_||inst<returning_)return false;
        stage_=3;return true;
    }
    bool active() const noexcept{return stage_==1||stage_==2;}
    unsigned stage() const noexcept{return stage_;}
private:
    uint32_t lr_=0,sp_=0;uint64_t start_=0,returning_=0;unsigned stage_=0;
};
}
