#pragma once
#include "wii_cooperative_save_lane_v1314.h"

namespace undercover::wii {
// Observe only the original cooperative loader, after the scheduler has
// selected the original saved thread. Distinct from the idle IRQ RFI.
class CooperativeLoadLane {
public:
    struct Expectation {
        std::span<const uint32_t> words;
        uint32_t caller_return;
        unsigned gqr_mask;
    };
    explicit CooperativeLoadLane(Expectation e):e_(e){}
    unsigned stage()const{return stage_;}
    unsigned failure()const{return error_;}
    unsigned visits()const{return visits_;}
    template<class C>bool begin(C& c,CooperativeSaveLane& save,bool held){
        const auto& g=save.expectation().geometry;
        if(stage_||error_||!held||!save.preserved(c,held)||c.pc!=g.loader||
           c.lr!=e_.caller_return||e_.words.empty()||e_.words.size()>128u||
           e_.words.back()!=0x4c000064u||g.rfi!=g.loader+4u*(e_.words.size()-1u)||
           !e_.gqr_mask||e_.gqr_mask>255u||
           e_.gqr_mask!=save.expectation().gqr_mask||
           !word(c,e_.caller_return-4u,branch(e_.caller_return-4u,g.loader)))return fail(1);
        for(unsigned i=0;i<e_.words.size();++i)if(!word(c,g.loader+4u*i,e_.words[i]))return fail(1);
        for(unsigned i=0;i<8;++i){
            const uint32_t a=g.context+0x1a4u+4u*i;
            if(!mapped(c,a))return fail(1);
            gqr_[i]=(e_.gqr_mask&(1u<<i))?c.mmu.read32(a):c.gqr[i];
        }
        if(!save.context().loader_entry(c,held))return fail(2);
        cpu_=&c;save_=&save;next_=g.loader;last_=c.inst_count;stage_=1;return true;
    }
    template<class C>bool before(C& c,uint32_t pc,uint32_t w,bool held){
        if(!live(c,held)||stage_!=1u||pc!=next_||c.inst_count-last_!=1u||
           poll_due_||++visits_>256u)return fail(3);
        const auto& g=save_->expectation().geometry;
        if(pc<g.loader||((pc-g.loader)&3u)||(pc-g.loader)/4u>=e_.words.size()||
           w!=e_.words[(pc-g.loader)/4u]||!word(c,pc,w))return fail(3);
        last_=c.inst_count;next_=pc+4u;
        const unsigned op=w>>26,xo=(w>>1)&1023u;
        if(w==0x4c000064u){
            if(pc!=g.rfi||c.gqr!=gqr_||!save_->context().before_rfi(c,pc,w,held))return fail(4);
            stage_=2;return true;
        }
        if(op==17u||(op==19u&&(xo==16u||xo==528u||xo==50u)))return fail(5);
        if(op==31u&&xo==146u){
            if(c.gpr[(w>>21)&31u]&0x8000u)return fail(5);
            // The generated mtmsr seam can yield at its exact next label.
            poll_due_=true;poll_pc_=next_;
        }
        if(op==16u||op==18u){
            if(w&3u)return fail(5);
            const auto dst=target(pc,w);
            if(dst<g.loader||dst>g.rfi||((dst-g.loader)&3u))return fail(5);
            if(dst<=pc){poll_due_=true;poll_pc_=pc;}
            if(op==18u||taken(c,w))next_=dst;
        }
        return true;
    }
    template<class C>bool poll(C& c,bool held){
        if(!live(c,held)||c.inst_count!=last_)return fail(6);
        if(stage_==1u&&poll_due_&&c.pc==poll_pc_){poll_due_=false;return true;}
        if(stage_==2u&&c.gqr==gqr_&&save_->context().returned(c,held)){stage_=3;return true;}
        if(stage_==3u&&c.gqr==gqr_&&save_->context().resumed_at(c,held)){stage_=4;return true;}
        return fail(6);
    }
    template<class C>bool restored(C& c,bool held)const{
        return stage_==4u&&live(c,held)&&c.inst_count==last_&&c.gqr==gqr_&&save_->context().resumed_at(c,held);
    }
private:
    Expectation e_;CooperativeSaveLane* save_=nullptr;const void* cpu_=nullptr;
    std::array<uint32_t,8> gqr_{};uint32_t next_=0,poll_pc_=0;uint64_t last_=0;
    unsigned stage_=0,error_=0,visits_=0;bool poll_due_=false;
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    template<class C>bool live(C& c,bool held)const{
        return !error_&&held&&cpu_==&c&&save_&&c.is_running&&!c.in_callback&&!c.dispatch_saved_ctx;
    }
    template<class C>static bool mapped(C& c,uint32_t a){return !(a&3u)&&a>=0x80000000u&&a<=0x817ffffcu&&c.mmu.get_ptr(a)&&c.mmu.get_ptr(a+3u);}
    template<class C>static bool word(C& c,uint32_t a,uint32_t w){return mapped(c,a)&&c.mmu.read32(a)==w;}
    static uint32_t branch(uint32_t pc,uint32_t dst){return 0x48000001u|((dst-pc)&0x03fffffcu);}
    static uint32_t target(uint32_t pc,uint32_t w){
        const bool bc=w>>26==16u;const uint32_t m=bc?0xfffcu:0x03fffffcu,s=bc?0x8000u:0x02000000u;
        return pc+(((w&m)^s)-s);
    }
    template<class C>static bool taken(C& c,uint32_t w){
        const unsigned bo=(w>>21)&31u,bi=(w>>16)&31u;const auto& f=c.cr[bi/4u];
        const bool bit=bi%4u==0u?f.lt:bi%4u==1u?f.gt:bi%4u==2u?f.eq:f.so;
        return ((bo&4u)||(((c.ctr-1u)!=0u)^bool(bo&2u)))&&((bo&16u)||bit==bool(bo&8u));
    }
};
}
