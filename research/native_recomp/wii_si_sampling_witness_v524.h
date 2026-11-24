#pragma once
#include "wii_si_entry_witness_v520.h"
#include "wii_si_controller_v511.h"
namespace undercover::wii {
// Record only successful native device operations, not guest intent or
// observer reads. No data is written to the controller by the witness.
class SiSamplingTrace {
public:
    bool begin(uint32_t table_word,unsigned clock){
        if(active_||stage_||bad_||clock>1u)return false;
        x_=(table_word>>16)*(1u+clock);y_=(table_word>>8)&255u;clock_=clock;
        if(x_>1023u)return false;
        poll_=(x_<<16)|(y_<<8);active_=true;return true;
    }
    void vi(bool write,uint16_t value)noexcept{
        if(!active_)return;
        if(write||stage_!=0||value!=clock_){bad_=true;return;}
        ++stage_;
    }
    void si(bool write,unsigned offset,uint32_t value)noexcept{
        if(!active_)return;
        const bool ok=(stage_==1&&write&&offset==SiController::Poll&&value==poll_)||
            (stage_==2&&!write&&offset==SiController::Control&&value==0u)||
            (stage_==3&&write&&offset==SiController::Control&&value==SiController::TC_INT);
        if(!ok){bad_=true;return;}
        ++stage_;
    }
    unsigned stage()const{return stage_;}
    unsigned x()const{return x_;}
    unsigned y()const{return y_;}
    uint32_t poll()const{return poll_;}
    bool good()const{return active_&&!bad_;}
    bool finish(){const bool ok=good()&&stage_==4;active_=false;return ok;}
private:
    unsigned stage_=0,x_=0,y_=0,clock_=0;uint32_t poll_=0;
    bool active_=false,bad_=false;
};
inline thread_local SiSamplingTrace si_sampling_trace{};
struct SiSamplingExpectations {
    VectorEdge rate,tv,xy,handler,unmask,first_type;
    uint32_t table_word;
};
class SiSamplingWitness {
public:
    explicit SiSamplingWitness(const SiSamplingExpectations& e):e_(e){}
    unsigned stage()const{return stage_;}
    unsigned failure()const{return error_;}
    unsigned detail()const{return detail_;}
    template<class Cpu>bool begin(Cpu& c,bool bound,unsigned clock){
        if(stage_||error_||!bound||!c.is_running||!matches(c,e_.rate)||c.gpr[3]!=0||
           !equal(c,0x80619a88u,e_.table_word)||!equal(c,0x80619a64u,0)||
           !si_sampling_trace.begin(e_.table_word,clock))return fail(1);
        sp_=c.gpr[1];r2_=c.gpr[2];r13_=c.gpr[13];msr_=c.msr;last_=c.inst_count;
        if(sp_<0x80001000u)return fail(1);
        for(unsigned i=0;i<32;++i){if(!mapped(c,0x80003040u+4*i,4))return fail(1);
            irq_[i]=c.mmu.read32(0x80003040u+4*i);}
        if(irq_[20]!=0)return fail(1);
        stage_=1;return true;
    }
    template<class Cpu>bool observe(uint32_t addr,Cpu& c){
        if(error_||stage_<1||stage_>5||!c.is_running||c.inst_count<last_||
           c.inst_count-last_>1000000u||c.gpr[2]!=r2_||c.gpr[13]!=r13_||
           !si_sampling_trace.good()||!equal(c,r13_-3824u,exi_id_completion.id()))return fail(2);
        const auto next=stage_==1?e_.tv:stage_==2?e_.xy:stage_==3?e_.handler:stage_==4?e_.unmask:e_.first_type;
        if(matches(c,next)){
            if(c.msr!=msr_||c.gpr[1]>sp_||c.gpr[1]<sp_-1024u)return fail(3);
            switch(stage_){
            case 1:
                if(!equal(c,r13_-3000u,0)||si_sampling_trace.stage()!=0)return fail(4);
                break;
            case 2:
                if(si_sampling_trace.stage()!=1||c.gpr[3]!=si_sampling_trace.x()||
                   c.gpr[4]!=si_sampling_trace.y())return fail(4);
                break;
            case 3:
                if(c.gpr[1]!=sp_||c.gpr[3]!=20||c.gpr[4]!=0x80531b34u||
                   si_sampling_trace.stage()!=4||!equal(c,0x80003090u,0)||
                   !equal(c,0x80619a64u,si_sampling_trace.poll()))return fail(5);
                break;
            case 4:
                if(c.gpr[1]!=sp_||c.gpr[3]!=0x800u||!equal(c,0x80003090u,0x80531b34u))
                    return fail(5);
                break;
            case 5:
                // Separate the eight final invariants; do not weaken the
                // original boundary or publish guest register/memory values.
                if(c.gpr[1]!=sp_)detail_|=1u;
                if(c.gpr[3]!=0)detail_|=2u;
                // Authenticated V544: the flag is set after all four queries.
                if(!equal(c,r13_-3148u,0))detail_|=4u;
                if(!equal(c,0x80619a64u,si_sampling_trace.poll()))detail_|=8u;
                if(!equal(c,0x80619a78u,8))detail_|=16u;
                if(!equal(c,0x806fe340u,0xffffffffu))detail_|=32u;
                if(c.mmu.read32(0xcc003004u)!=0xf8u)detail_|=64u;
                for(unsigned i=0;i<32;++i)if(!equal(c,0x80003040u+4*i,i==20?0x80531b34u:irq_[i]))detail_|=128u;
                if(detail_)return fail(6);
                if(!si_sampling_trace.finish())return fail(8);
                break;
            }
            ++stage_;last_=c.inst_count;return true;
        }
        if(addr!=c.pc||addr&3u||!mapped(c,addr,4)||++extra_>256u)return fail(7);
        for(auto e:{e_.rate,e_.tv,e_.xy,e_.handler,e_.unmask,e_.first_type})
            if(addr==e.pc&&c.lr==e.lr)return fail(7);
        if(addr==e_.tv.pc||addr==e_.xy.pc||addr==e_.first_type.pc)return fail(7);
        return true;
    }
private:
    SiSamplingExpectations e_;unsigned stage_=0,error_=0,extra_=0,detail_=0;
    uint32_t sp_=0,r2_=0,r13_=0,msr_=0;uint64_t last_=0;std::array<uint32_t,32> irq_{};
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    template<class Cpu>static bool mapped(Cpu& c,uint32_t a,unsigned n){
        return n&&a>=0x80000000u&&uint64_t(a)+n<=0x81800000ull&&c.mmu.get_ptr(a)&&c.mmu.get_ptr(a+n-1u);
    }
    template<class Cpu>static bool equal(Cpu& c,uint32_t a,uint32_t w){return !(a&3u)&&mapped(c,a,4)&&c.mmu.read32(a)==w;}
    template<class Cpu>static bool matches(Cpu& c,const VectorEdge& e){return c.pc==e.pc&&c.lr==e.lr&&equal(c,e.pc,e.entry_word)&&equal(c,e.lr-4,e.branch_word);}
};
}
