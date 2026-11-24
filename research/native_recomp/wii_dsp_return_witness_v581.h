#pragma once
#include "wii_dsp_stage_witness_v559.h"
#include "wii_dsp_boot_profile_v580.h"
namespace undercover::wii {
struct DspReturnExpectations {
    std::array<VectorEdge,4> edges;
    uint32_t return_word;
};
class DspReturnWitness {
public:
    static constexpr uint32_t Return=0x805208d8u;
    explicit DspReturnWitness(const DspReturnExpectations& e):e_(e){}
    unsigned stage()const noexcept{return stage_;}
    unsigned failure()const noexcept{return error_;}
    template<class Cpu>bool begin(Cpu& c,DspStageWitness& staged){
        if(stage_||error_||!staged.restore_ready(c))return fail(1);
        sp_=c.gpr[1];start_=c.inst_count;
        stage_=1;return true;
    }
    template<class Cpu,class Profile>bool observe(uint32_t addr,Cpu& c,DspStageWitness& staged,const Profile& p){
        if(error_||!stage_||stage_>4||!c.is_running||c.pc!=addr||
           c.inst_count<start_||c.inst_count-start_>1000000u)return fail(2);
        if(stage_<=2&&addr==e_.edges[0].pc){
            if(c.gpr[1]!=sp_||p.acks()!=1||p.phase()!=DspBootProfile::Phase::Dma2||!staged.restore_ready(c))return fail(3);
            const auto now=uint32_t(c.read_timebase());
            if(stage_==1&&matches(c,e_.edges[0])){
                time_=now;stage_=2;return true;
            }
            if(stage_!=2||!matches(c,e_.edges[1])||++polls_>1000)return fail(3);
            const uint32_t delta=now-time_;
            if(delta<=delta_||delta_>=2194u)return fail(3);
            delta_=delta;return true;
        }
        if(stage_==2&&matches(c,e_.edges[2])){
            if(polls_<2||delta_<2194u||delta_>=2258u||!p.done()||!p.memory()||
               c.gpr[1]!=sp_||!staged.restore_ready(c))return fail(4);
            stage_=3;return true;
        }
        if(stage_==3&&matches(c,e_.edges[3])){
            if(!p.done()||!p.memory()||!staged.restore_ready(c)||
               c.gpr[3]!=DspStageWitness::Staging||c.gpr[4]!=0x816fff80u||c.gpr[5]!=128)return fail(5);
            stage_=4;return true;
        }
        if(stage_==4&&addr==Return){
            if(c.lr!=Return||!equal(c,Return,e_.return_word)||!p.done()||
               !p.aux_preserved()||!staged.finish_restore(c))return fail(6);
            stage_=5;return true;
        }
        // Original memcpy may have nested native helpers, never a repeated
        // authenticated edge or an unbounded unexplained call sequence.
        if(stage_==4&&++extra_<=64&&!(addr&3u)&&c.mmu.get_ptr(addr)){
            for(const auto& edge:e_.edges)if(addr==edge.pc&&c.lr==edge.lr)return fail(7);
            return true;
        }
        return fail(7);
    }
private:
    DspReturnExpectations e_;unsigned stage_=0,error_=0,polls_=0,extra_=0;
    uint32_t sp_=0,time_=0,delta_=0;uint64_t start_=0;
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    template<class Cpu>static bool equal(Cpu& c,uint32_t a,uint32_t w){
        return !(a&3u)&&a>=0x80000000u&&a<=0x817ffffcu&&c.mmu.get_ptr(a)&&c.mmu.get_ptr(a+3u)&&c.mmu.read32(a)==w;
    }
    template<class Cpu>static bool matches(Cpu& c,const VectorEdge& e){
        return c.pc==e.pc&&c.lr==e.lr&&equal(c,e.pc,e.entry_word)&&equal(c,e.lr-4,e.branch_word);
    }
};
}
