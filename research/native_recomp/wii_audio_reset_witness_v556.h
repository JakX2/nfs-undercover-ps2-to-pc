#pragma once
#include "wii_thread_init_witness_v549.h"
#include "wii_audio_reset_trace_v556.h"
namespace undercover::wii {
struct AudioResetExpectations{
    VectorEdge audio,reset;
    std::array<VectorEdge,10> time;
    uint32_t return_word;
};
class AudioResetWitness{
public:
    static constexpr uint32_t Return=0x80522010u;
    explicit AudioResetWitness(const AudioResetExpectations& e):e_(e){}
    unsigned stage()const noexcept{return stage_;}
    unsigned failure()const noexcept{return error_;}
    template<class Cpu>bool begin(Cpu& c,bool bound){
        if(stage_||error_||!c.is_running||c.pc!=e_.audio.lr-4u||
           !equal(c,c.pc,e_.audio.branch_word)||c.gpr[1]!=ThreadInitWitness::StackTop-88u||
           (c.msr&0x8000u)||!equal(c,0x800000e4u,ThreadInitWitness::Thread)||
           !equal(c,ThreadInitWitness::StackBottom,0xdeadbabeu)||!audio_reset_trace.begin(bound))return fail(1);
        sp_=c.gpr[1];r2_=c.gpr[2];r13_=c.gpr[13];msr_=c.msr;start_inst_=c.inst_count;
        for(unsigned i=0;i<18;++i)nv_[i]=c.gpr[i+14];
        stage_=1;return true;
    }
    template<class Cpu>bool observe(uint32_t addr,Cpu& c){
        if(error_||stage_<1||stage_>8||!c.is_running||c.pc!=addr||
           c.inst_count<start_inst_||c.inst_count-start_inst_>2000000u||
           c.gpr[2]!=r2_||c.gpr[13]!=r13_||c.msr!=msr_||!audio_reset_trace.good()||
           !equal(c,0x800000e4u,ThreadInitWitness::Thread))return fail(2);
        if(stage_==1){
            if(!matches(c,e_.audio)||c.gpr[1]!=sp_)return fail(3);
            stage_=2;return true;
        }
        if(stage_==2){
            if(!matches(c,e_.reset)||c.gpr[1]!=sp_-16u||c.gpr[3]!=1||
               !equal(c,sp_-16u,sp_))return fail(3);
            // Reset helper has its own nonvolatile frame; compare that ABI
            // at its return, not the caller's live scratch registers.
            for(unsigned i=0;i<18;++i)nv_[i]=c.gpr[i+14];
            stage_=3;return true;
        }
        if(addr==Return){
            if(stage_!=8||c.lr!=Return||c.gpr[1]!=sp_-16u||
               !equal(c,Return,e_.return_word)||!equal(c,sp_-16u,sp_)||
               !equal(c,ThreadInitWitness::StackBottom,0xdeadbabeu)||
               !audio_reset_trace.finish())return fail(5);
            for(unsigned i=0;i<18;++i)if(c.gpr[i+14]!=nv_[i])return fail(5);
            stage_=9;return true;
        }
        // Only the original five distinct helper callsite pairs are valid.
        // At this boundary no other function calls are expected inside reset.
        const unsigned i=audio_reset_trace.waits();
        if(i>=5||c.gpr[1]!=sp_-48u)return fail(4);
        const uint32_t tb=uint32_t(c.read_timebase());
        if(matches(c,e_.time[2*i])){
            if(!audio_reset_trace.start(tb))return fail(4);
        }else if(matches(c,e_.time[2*i+1])){
            if(!audio_reset_trace.poll(tb))return fail(4);
            if(audio_reset_trace.crossed())++stage_;
        }else return fail(4);
        return true;
    }
private:
    AudioResetExpectations e_;unsigned stage_=0,error_=0;
    uint32_t sp_=0,r2_=0,r13_=0,msr_=0;uint64_t start_inst_=0;
    std::array<uint32_t,18> nv_{};
    bool fail(unsigned why){if(!error_)error_=why;return false;}
    template<class Cpu>static bool equal(Cpu& c,uint32_t a,uint32_t w){
        return !(a&3u)&&a>=0x80000000u&&a<=0x817ffffcu&&c.mmu.get_ptr(a)&&c.mmu.get_ptr(a+3u)&&c.mmu.read32(a)==w;
    }
    template<class Cpu>static bool matches(Cpu& c,const VectorEdge& e){
        return c.pc==e.pc&&c.lr==e.lr&&equal(c,e.pc,e.entry_word)&&equal(c,e.lr-4,e.branch_word);
    }
};
}
