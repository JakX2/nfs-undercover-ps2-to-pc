#include "wii_second_completion_ack_v950.h"
#include <iostream>
#include <map>
#include <source_location>
using namespace undercover::wii;
constexpr uint32_t A=0x80004000u,Other=0x100u,SI=8u,Base=0xcd006400u;
constexpr uint32_t Load=(32u<<26)|(4u<<21)|(3u<<16)|0x34u;
constexpr uint32_t Store=(36u<<26)|(4u<<21)|(3u<<16)|0x34u;
constexpr uint32_t Status=(36u<<26)|(4u<<21)|(3u<<16)|0x38u;
constexpr uint32_t Nop=0x60000000u;
struct Mmu{
    std::map<uint32_t,uint32_t> words;uint8_t byte=0;
    uint8_t* get_ptr(uint32_t a){return words.count(a&~3u)?&byte:nullptr;}
    uint32_t read32(uint32_t a){return words.at(a);}
};
struct Cpu{
    Mmu mmu;std::array<uint32_t,32> gpr{};
    uint32_t msr=0x32,dispatch_saved_ctx=0;uint64_t inst_count=100;
    bool is_running=true,in_callback=false;
};
static void need(bool b,const std::source_location loc=std::source_location::current()){
    if(!b){std::cerr<<"V950_ASSERT line="<<loc.line()<<std::endl;throw std::runtime_error("second ACK");}
}
static void response_provenance(){
    unsigned verified=0,unknown=0,refused=0;
    for(unsigned profile=0;profile<8;++profile){
        const unsigned ch=profile%4u;const bool absent=(profile&4u)!=0;
        for(unsigned lane=0;lane<3;++lane){
            std::atomic<uint32_t> cause{Other},mask{SI};SiController ctl(cause);SecondCompletionAck w;Cpu c;
            const uint32_t cfg=SiController::TC_MASK|0x00010300u|(ch<<1);
            const std::array<uint8_t,3> response{9,0,0};
            ctl.write(SiController::Control,cfg|SiController::TSTART);ctl.complete(ctl.pending()->token,response);
            ctl.write(SiController::Control,cfg|SiController::TC_INT);
            ctl.write(SiController::Control,cfg|SiController::TSTART);
            if(absent)ctl.complete(ctl.pending()->token,{},SiController::ERR_NOREP);
            else ctl.complete(ctl.pending()->token,response);
            c.gpr[3]=Base;c.mmu.words={{A,Status},{A+4,Load},{A+8,Store},{A+12,Nop}};
            const auto snapshot=ctl.read(SiController::Control),status=ctl.read(SiController::Status);
            const std::optional<bool> claim=lane==0?std::optional<bool>{absent}:lane==1?std::optional<bool>{!absent}:std::nullopt;
            const bool ok=w.arm(ctl,cause,mask,c.inst_count,2,true,claim);
            if(lane==1){
                need(!ok&&w.failure()==1&&!w.response_class_verified()&&!w.no_response_verified());
                need(ctl.read(SiController::Control)==snapshot&&ctl.read(SiController::Status)==status&&cause==(Other|SI));
                ++refused;continue;
            }
            need(ok&&w.response_class_verified()==(lane==0)&&w.no_response_verified()==(lane==0&&absent));
            // The guest clears its per-port error nibble before the ACK.
            // The immutable completion class is independent of that register.
            auto step=[&](uint32_t pc,uint32_t word){++c.inst_count;return w.before(c,pc,word,true);};
            c.gpr[4]=0xfu<<((3u-ch)*8u);
            need(step(A,Status)&&w.write(ctl,SiController::Status,c.gpr[4])&&ctl.read(SiController::Status)==0u);
            uint32_t value=0;
            need(step(A+4,Load)&&w.read(ctl,SiController::Control,value)&&value==snapshot);
            c.gpr[4]=value|SiController::TC_INT;
            need(step(A+8,Store)&&w.write(ctl,SiController::Control,c.gpr[4]));
            need(step(A+12,Nop)&&w.resume_after_ack(c,A+12,Nop)&&w.postack_held());
            need(w.response_class_verified()==(lane==0)&&w.no_response_verified()==(lane==0&&absent));
            need(cause==Other&&mask==SI&&!ctl.pending()&&ctl.issued_tokens()==2u);
            if(lane==0)++verified;else ++unknown;
        }
    }
    need(verified==8&&unknown==8&&refused==8);
    std::cout<<"V1019_COMPLETION_PROVENANCE verified=8 unknown=8 refused=8 status_clear=1 token_preserved=1 original_execution=0\n";
}
int main(){
    response_provenance();
    unsigned valid=0,refused=0;
    for(unsigned i=0;i<36;++i){
        const unsigned ch=i%4;const bool absent=(i&4u)!=0;
        std::atomic<uint32_t> cause{Other},mask{SI};SiController ctl(cause);SecondCompletionAck w;Cpu c;
        const uint32_t cfg=SiController::TC_MASK|0x00010300u|(ch<<1);
        const std::array<uint8_t,3> response{9,0,0};
        ctl.write(SiController::Control,cfg|SiController::TSTART);ctl.complete(ctl.pending()->token,response);
        ctl.write(SiController::Control,cfg|SiController::TC_INT);need(cause==Other);
        ctl.write(SiController::Control,cfg|SiController::TSTART);
        if(absent)ctl.complete(ctl.pending()->token,{},SiController::ERR_NOREP);else ctl.complete(ctl.pending()->token,response);
        c.gpr[3]=Base;c.mmu.words={{A,Load},{A+4,Status},{A+8,Store},{A+12,Nop},{A+16,Nop}};
        const unsigned fault=i<8?0:i-7;
        if(fault==3)mask=0;
        bool ok=w.arm(ctl,cause,mask,c.inst_count,fault==1?1u:2u,fault!=2);
        if(fault>=1&&fault<=3){need(!ok&&w.failure()==1);++refused;continue;}need(ok);
        if(fault>=21){
            uint32_t pc=A;
            if(fault==21)pc=A+1;
            if(fault==22)pc=0x7ffffffcu;
            if(fault==23)pc=0x81800000u;
            if(fault==24)pc=0xfffffffcu;
            if(fault==25)c.gpr[3]=Base+1u; // unaligned word access
            if(fault==26)c.gpr[3]=Base+8u; // unsupported register
            if(fault==27)c.gpr[3]=0x4d006400u; // invalid virtual segment
            if(fault==28)c.gpr[3]=Base-0x35u; // overlaps first aperture byte
            if(fault>=22&&fault<=24)c.mmu.words[pc]=Load;
            ++c.inst_count;
            need(!w.before(c,pc,Load,true)&&w.failure()==2&&w.reads()==0&&w.writes()==0);
            need(ctl.issued_tokens()==2&&cause==(Other|SI)&&mask==SI&&
                 (ctl.read(SiController::Control)&SiController::TC_INT));
            ++refused;continue;
        }
        if(fault==4)ctl.write(SiController::Buffer,0x12345678u);
        if(fault!=5)++c.inst_count;
        ok=w.before(c,A,Load,fault!=6);
        if(fault>=4&&fault<=6){need(!ok&&w.failure()==2);++refused;continue;}need(ok);
        uint32_t v=0;
        if(fault==7)++c.inst_count;
        ok=w.read(ctl,fault==8?SiController::Status:SiController::Control,v);
        if(fault==7||fault==8){need(!ok&&w.failure()==3);++refused;continue;}need(ok&&v==ctl.read(SiController::Control));
        if(fault==9){need(!w.read(ctl,SiController::Control,v)&&w.failure()==3);++refused;continue;}
        if(fault==10)cause.fetch_or(0x200u);
        ++c.inst_count;c.gpr[4]=0xfu<<((3-ch)*8u);
        if(fault==11)c.gpr[4]=0xffffffffu;
        ok=w.before(c,A+4,Status,true);
        if(fault==10){need(!ok&&w.failure()==2);++refused;continue;}need(ok);
        ok=w.write(ctl,SiController::Status,c.gpr[4]);
        if(fault==11){need(!ok&&w.failure()==4);++refused;continue;}need(ok&&cause==(Other|SI));
        ++c.inst_count;c.gpr[4]=ctl.read(SiController::Control)|SiController::TC_INT;
        if(fault==12)c.gpr[4]|=SiController::TSTART;
        if(fault==13)c.gpr[4]&=~SiController::TC_MASK;
        if(fault==14)c.gpr[4]&=~SiController::TC_INT;
        if(fault==15)c.gpr[4]^=2u;
        if(fault==16)c.gpr[3]+=0x4c;
        need(w.before(c,A+8,Store,true));
        ok=w.write(ctl,SiController::Control,c.gpr[4]^(fault==17?2u:0u));
        if(fault>=12&&fault<=17){need(!ok&&w.failure()==(fault>=16?3u:4u)&&cause==(Other|SI));++refused;continue;}need(ok&&w.stage()==2&&cause==Other&&ctl.issued_tokens()==2);
        if(fault!=18)++c.inst_count;
        if(fault==19)cause.fetch_or(0x200u);
        ok=w.before(c,fault==20?A+16:A+12,Nop,true);
        if(fault>=18){need(!ok&&w.failure()==(fault==18?2u:5u));++refused;continue;}
        need(ok&&w.stage()==3&&w.token()==2&&w.reads()==1&&w.writes()==2&&mask==SI);
        ++valid;
    }
    need(valid==8&&refused==28);
    std::cout<<"V950_SECOND_ACK synthetic=1 valid=8 refused=28 real_device=1 token_preserved=1 original_execution=0\n";
}
