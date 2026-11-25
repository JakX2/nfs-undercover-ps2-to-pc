#pragma once
#include <array>
#include <cstdint>
namespace undercover::wii {
// This independently written witness is only for already authenticated
// leaf functions in an interrupt-disabled context. No guest state mutation.
struct PostAckLeafExpectation {
    uint32_t site,root,end,branch;
    unsigned kind; // 1 disable, 2 timebase, 3 restore
};
class PostAckOsLeaf {
public:
    explicit PostAckOsLeaf(PostAckLeafExpectation e):e_(e){}
    unsigned stage()const{return stage_;}
    unsigned failure()const{return error_;}
    unsigned visits()const{return visits_;}
    unsigned polls()const{return polls_;}
    template<class C>bool start(C& c,uint32_t pc,uint32_t word){
        if(stage_||error_||!valid(c)||pc!=e_.site||word!=e_.branch||
           (word>>26)!=18u||(word&3u)!=1u||
           pc+(((word&0x03fffffcu)^0x02000000u)-0x02000000u)!=e_.root||
           e_.end<=e_.root||e_.end-e_.root>64u||((e_.root|e_.end|e_.site)&3u)||
           e_.kind<1||e_.kind>3||(e_.kind==3&&c.gpr[3]!=0))return fail(1);
        ctx_=&c;gp_=c.gpr;msr_=c.msr;srr0_=c.srr0;srr1_=c.srr1;
        ctr_=c.ctr;last_=c.inst_count;stage_=1;return true;
    }
    template<class C>bool entry(uint32_t pc,C& c){
        if(stage_!=1||!common(c)||pc!=e_.root||c.pc!=pc||c.lr!=e_.site+4||
           c.inst_count!=last_)return fail(2);
        stage_=2;next_=e_.root;return true;
    }
    template<class C>bool before(C& c,uint32_t pc,uint32_t word){
        if(stage_!=2||!common(c)||pending_||pc<e_.root||pc>=e_.end||(pc&3u)||
           (pc!=next_&&pc!=alternate_)||c.inst_count-last_!=1u||
           !c.mmu.get_ptr(pc)||!c.mmu.get_ptr(pc+3u)||c.mmu.read32(pc)!=word||
           ++visits_>64)return fail(3);
        last_=c.inst_count;next_=pc+4u;alternate_=0;
        const auto op=word>>26,xo=(word>>1)&1023u;
        if(word==0x4e800020u){
            if(c.lr!=e_.site+4u||(e_.kind!=2&&c.gpr[3]!=0u))return fail(4);
            stage_=3;return true;
        }
        if(op==31u&&xo==146u){
            if(e_.kind==2||c.gpr[(word>>21)&31u]!=msr_||polls_!=0)return fail(5);
            pending_=true;return true;
        }
        if(op==17u||op==19u||((op==16u||op==18u)&&(word&1u)))return fail(6);
        if(op==16u||op==18u){
            const uint32_t bits=op==16u?0x0000fffcu:0x03fffffcu,sign=op==16u?0x8000u:0x02000000u;
            const auto delta=((word&bits)^sign)-sign,dst=(word&2u)?delta:pc+delta;
            if(dst<e_.root||dst>=e_.end)return fail(6);
            if(op==18u)next_=dst;else alternate_=dst;
        }
        if(next_>=e_.end)return fail(6);
        return true;
    }
    template<class C>bool poll(C& c){
        if(stage_!=2||!pending_||!common(c)||c.pc!=next_||
           c.inst_count!=last_||++polls_!=1)return fail(5);
        pending_=false;return true;
    }
    template<class C>bool returned(C& c,uint32_t pc){
        if(stage_!=3||!common(c)||pending_||pc!=e_.site+4u||c.pc!=pc||c.lr!=pc||
           c.inst_count-last_!=1u||c.gpr[1]!=gp_[1]||c.gpr[2]!=gp_[2]||
           c.gpr[13]!=gp_[13]||(e_.kind!=2&&polls_!=1)||(e_.kind==2&&polls_))return fail(4);
        for(unsigned i=14;i<32;++i)if(c.gpr[i]!=gp_[i])return fail(4);
        stage_=4;return true;
    }
private:
    PostAckLeafExpectation e_;const void* ctx_=nullptr;
    unsigned stage_=0,error_=0,visits_=0,polls_=0;
    bool pending_=false;uint32_t next_=0,alternate_=0,msr_=0,ctr_=0,srr0_=0,srr1_=0;
    uint64_t last_=0;std::array<uint32_t,32> gp_{};
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    template<class C>static bool valid(C& c){return c.is_running&&!c.in_callback&&!c.dispatch_saved_ctx&&!(c.msr&0x8000u);}
    template<class C>bool common(C& c)const{
        return !error_&&ctx_==&c&&valid(c)&&c.msr==msr_&&c.ctr==ctr_&&c.srr0==srr0_&&c.srr1==srr1_;
    }
};
}
