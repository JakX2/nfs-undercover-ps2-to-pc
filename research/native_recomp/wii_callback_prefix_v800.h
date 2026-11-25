#pragma once
#include <array>
#include <cstddef>
#include <cstdint>
namespace undercover::wii {
// Read-only witness for an authenticated bctrl, callback prologue,
// compiler save leaf and the first unexecuted post-save instruction.
// Original code and direct edges must be authenticated by the installer.
template<std::size_t P,std::size_t S>
class CallbackPrefixWitness {
    static_assert(P>=3&&P<=18&&S>=2&&S<=19);
public:
    CallbackPrefixWitness(uint32_t root,uint32_t save,
        std::array<uint32_t,P> prefix,std::array<uint32_t,S> leaf):
        root_(root),save_(save),prefix_(prefix),leaf_(leaf){}
    unsigned stage()const{return stage_;}
    unsigned failure()const{return error_;}
    unsigned visits()const{return visits_;}
    unsigned writes()const{return writes_;}
    uint32_t resume()const{return root_+4u*uint32_t(P-1u);}
    template<class C>bool start(C& c,uint32_t pc,uint32_t word,bool identity,bool device){
        if(stage_||error_||!identity||!device||!safe(c)||c.pc!=pc||
           word!=0x4e800421u||!match(c,pc,word)||
           (uint32_t(c.ctr)&~3u)!=root_||
           !range(root_,4u*P)||!range(save_,4u*S)||
           overlap(root_,4u*P,save_,4u*S)||
           c.inst_count>UINT64_MAX-128u||
           c.gpr[1]<0x80000400u||c.gpr[1]>0x817fff00u||
           (c.gpr[1]&3u))return fail(1);
        low_=c.gpr[1]-0x400u;
        if(overlap(low_,0x500u,root_,4u*P)||overlap(low_,0x500u,save_,4u*S)||
           overlap(low_,0x500u,pc,4u))return fail(1);
        for(std::size_t i=0;i<P;++i)if(!match(c,root_+4u*i,prefix_[i]))return fail(1);
        for(std::size_t i=0;i<S;++i)if(!match(c,save_+4u*i,leaf_[i]))return fail(1);
        for(unsigned i=0;i<stack_.size();++i){
            const auto a=low_+4u*i;if(!mapped(c,a))return fail(1);
            stack_[i]=c.mmu.read32(a);
        }
        cpu_=&c;gp_=c.gpr;lr_=pc+4u;ctr_=c.ctr;xer_=c.xer;cr_=pack(c);
        msr_=c.msr;srr0_=c.srr0;srr1_=c.srr1;last_=c.inst_count;
        next_=root_;stage_=1;return true;
    }
    template<class C>bool entry(C& c,uint32_t pc,bool device){
        if((stage_!=1&&stage_!=3)||!common(c,device)||c.pc!=pc||
           pc!=next_||c.inst_count!=last_||!state(c))return fail(2);
        stage_=stage_==1?2u:4u;return true;
    }
    template<class C>bool before(C& c,uint32_t pc,uint32_t word,bool device){
        if((stage_!=2&&stage_!=4&&stage_!=5)||!common(c,device)||
           pc!=next_||c.pc!=pc||c.inst_count-last_!=1u||
           !match(c,pc,word)||!state(c)||++visits_>P+S)return fail(3);
        last_=c.inst_count;
        if(stage_==5){
            if(pc!=resume()||word!=prefix_.back()||writes_!=S+1u||
               visits_!=P+S)return fail(4);
            stage_=6;return true;
        }
        if(stage_==2){
            if(pc!=root_+4u*index_||index_>=P-1||word!=prefix_[index_])return fail(3);
            ++index_;
            if(index_==P-1){
                if(word>>26!=18u||(word&3u)!=1u||
                   pc+(((word&0x03fffffcu)^0x02000000u)-0x02000000u)!=save_)return fail(4);
                lr_=pc+4u;next_=save_;stage_=3;return true;
            }
            if(!prologue(word))return fail(4);
            next_=pc+4u;return true;
        }
        if(pc!=save_+4u*leaf_index_||leaf_index_>=S||word!=leaf_[leaf_index_])return fail(3);
        if(++leaf_index_==S){
            if(word!=0x4e800020u||lr_!=resume())return fail(4);
            next_=resume();stage_=5;return true;
        }
        const unsigned reg=(word>>21)&31u,base=(word>>16)&31u;
        if(word>>26!=36u||reg!=32u-uint32_t(S-1u)+leaf_index_-1u||
           (base!=1u&&base!=11u)||!store(gp_[base]+disp(word),gp_[reg]))return fail(4);
        next_=pc+4u;return true;
    }
private:
    uint32_t root_,save_;std::array<uint32_t,P> prefix_;std::array<uint32_t,S> leaf_;
    std::array<uint32_t,32> gp_{};
    std::array<uint32_t,0x500u/4u> stack_{};
    const void* cpu_=nullptr;
    unsigned stage_=0,error_=0,visits_=0,writes_=0,index_=0,leaf_index_=0;
    uint32_t low_=0,next_=0,lr_=0,ctr_=0,xer_=0,cr_=0,msr_=0,srr0_=0,srr1_=0;
    uint64_t last_=0;
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    static bool range(uint32_t a,std::size_t n){return !(a&3u)&&a>=0x80000000u&&uint64_t(a)+n<=0x81800000ull;}
    static bool overlap(uint32_t a,std::size_t n,uint32_t b,std::size_t m){return uint64_t(a)<uint64_t(b)+m&&uint64_t(b)<uint64_t(a)+n;}
    template<class C>static bool mapped(C& c,uint32_t a){return range(a,4)&&c.mmu.get_ptr(a)&&c.mmu.get_ptr(a+3u);}
    template<class C>static bool match(C& c,uint32_t a,uint32_t w){return mapped(c,a)&&c.mmu.read32(a)==w;}
    template<class C>static bool safe(C& c){return c.is_running&&!c.in_callback&&!c.dispatch_saved_ctx&&!(c.msr&0x8000u);}
    template<class C>bool common(C& c,bool device)const{return !error_&&device&&cpu_==&c&&safe(c)&&c.msr==msr_&&c.srr0==srr0_&&c.srr1==srr1_;}
    template<class C>static uint32_t pack(C& c){uint32_t v=0;for(const auto& f:c.cr)v=(v<<4)|(unsigned(f.lt)<<3)|(unsigned(f.gt)<<2)|(unsigned(f.eq)<<1)|unsigned(f.so);return v;}
    template<class C>bool state(C& c)const{
        if(c.gpr!=gp_||c.lr!=lr_||c.ctr!=ctr_||c.xer!=xer_||pack(c)!=cr_)return false;
        for(unsigned i=0;i<stack_.size();++i)if(!match(c,low_+4u*i,stack_[i]))return false;
        return true;
    }
    static uint32_t disp(uint32_t w){return ((w&0xffffu)^0x8000u)-0x8000u;}
    bool store(uint32_t a,uint32_t v){
        if((a&3u)||a<low_||uint64_t(a)>=uint64_t(low_)+0x500u)return false;
        stack_[(a-low_)/4u]=v;++writes_;return true;
    }
    bool prologue(uint32_t w){
        const unsigned op=w>>26,xo=(w>>1)&1023u,rd=(w>>21)&31u,ra=(w>>16)&31u,rb=(w>>11)&31u;
        if(op==36u||op==37u){
            if(op==37u&&(rd!=1u||ra!=1u||!(w&0x8000u)))return false;
            if(ra!=1u&&ra!=11u)return false;
            const uint32_t a=gp_[ra]+disp(w);
            if(!store(a,gp_[rd]))return false;
            if(op==37u)gp_[ra]=a;
        }else if(op==14u)gp_[rd]=(ra?gp_[ra]:0u)+disp(w);
        else if(op==31u&&xo==339u&&(ra|(rb<<5))==8u&&!(w&1u))gp_[rd]=lr_;
        else if(op==31u&&xo==444u&&!(w&1u))gp_[ra]=gp_[rd]|gp_[rb];
        else if(w!=0x60000000u)return false;
        return true;
    }
};
}
