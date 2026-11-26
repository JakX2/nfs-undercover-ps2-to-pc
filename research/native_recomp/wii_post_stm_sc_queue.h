#pragma once
#include "wii_post_stm_sc_report.h"
namespace undercover::wii {
struct ScQueueExpectation {
    uint32_t root,start,queue,caller,caller_word,address;
    AllocatorRange object;
    std::span<const IpcDispatchWord> words;
};
// Original SC queue initializer. Admitted only after an independently
// verified report return. Do not initialize the queue in the observer.
class ScQueueWitness {
public:
    explicit ScQueueWitness(ScQueueExpectation e):e_(e){}
    unsigned stage()const{return stage_;} unsigned failure()const{return error_;}
    unsigned visits()const{return visits_;} unsigned stores()const{return stores_;}
    template<class C>bool begin(C& c,bool held){
        if(stage_||error_||!held||!safe(c)||!(c.msr&0x8000u)||c.pc!=e_.start||c.lr!=e_.start||
           e_.words.size()!=7u||e_.object.size>4096u||!e_.object.contains(e_.address,8u)||(e_.address&3u)||
           !mapped(c,e_.object)||!known(c,e_.root,e_.start)||!known(c,e_.queue,e_.queue)||
           !word(c,e_.caller,e_.caller_word))return fail(1);
        for(unsigned i=0;i<e_.object.size;++i)shadow_.push_back(c.mmu.read8(e_.object.base+i));
        cpu_=&c;gp_=c.gpr;gqr_=c.gqr;msr_=c.msr;cr_=pack(c);lr_=c.lr;ctr_=c.ctr;xer_=c.xer;
        srr0_=c.srr0;srr1_=c.srr1;last_=c.inst_count;next_=e_.start;owner_=e_.root;stage_=1;return true;
    }
    template<class C>bool poll(C& c,bool held){
        if(stage_!=1u||!common(c,held)||c.inst_count!=last_)return fail(2);
        if(!visits_&&!initial_poll_&&c.pc==e_.start){initial_poll_=true;return true;}
        if(!return_due_||c.pc!=e_.caller||c.lr!=e_.caller||visits_!=7u||stores_!=2u||seen_!=3u||
           c.mmu.read32(e_.address)||c.mmu.read32(e_.address+4u)||!word(c,e_.caller,e_.caller_word))return fail(2);
        stage_=2;return true;
    }
    template<class C>bool entry(C& c,uint32_t pc,bool held){
        if(stage_!=1u||!common(c,held)||c.pc!=pc)return fail(3);
        if(!visits_){
            if(!initial_poll_||entry_seen_||pc!=e_.start||c.inst_count-last_!=1u)return fail(3);
            entry_seen_=true;return true;
        }
        if(!call_due_||pc!=e_.queue||c.inst_count!=last_||c.gpr[3]!=e_.address||c.lr!=e_.caller)return fail(3);
        call_due_=false;owner_=e_.queue;return true;
    }
    template<class C>bool before(C& c,uint32_t pc,uint32_t w,bool held){
        if(stage_!=1u||!common(c,held)||call_due_||return_due_||pc!=next_||
           c.inst_count-last_!=(visits_?1u:2u)||(!visits_&&(!initial_poll_||!entry_seen_||c.pc!=pc))||
           !known(c,owner_,pc,w)||++visits_>7u)return fail(4);
        last_=c.inst_count;next_=pc+4u;
        const unsigned op=w>>26,rs=(w>>21)&31u,ra=(w>>16)&31u;
        const uint32_t imm=uint32_t(int32_t((w&0xffffu)^0x8000u)-0x8000);
        if(owner_==e_.root){
            if((op==14u||op==15u)&&(volatile_reg(rs)||rs>=14u)&&visits_<=2u){
                gp_[rs]=(ra?gp_[ra]:0u)+(op==15u?imm<<16u:imm);
            }else if(op==18u&&(w&3u)==1u&&visits_==3u&&pc+4u==e_.caller&&
                      pc+(((w&0x03fffffcu)^0x02000000u)-0x02000000u)==e_.queue&&gp_[3]==e_.address){
                lr_=e_.caller;next_=e_.queue;call_due_=true;return true;
            }else return fail(5);
        }else if(owner_==e_.queue){
            if(op==14u&&ra==0u&&rs!=3u&&volatile_reg(rs)&&imm==0u){
                gp_[rs]=0;
            }else if(op==36u&&ra==3u&&gp_[3]==e_.address&&(imm==0u||imm==4u)&&gp_[rs]==0u){
                unsigned bit=1u<<(imm/4u);if(seen_&bit)return fail(6);
                seen_|=bit;++stores_;
                for(unsigned i=0;i<4;++i)shadow_[e_.address-e_.object.base+imm+i]=0;
            }else if(w==0x4e800020u&&visits_==7u&&seen_==3u&&lr_==e_.caller){
                next_=e_.caller;return_due_=true;return true;
            }else return fail(5);
        }else return fail(5);
        return known(c,owner_,next_)?true:fail(5);
    }
    template<class C>bool reached(C& c,bool held)const{
        return stage_==2u&&common(c,held)&&return_due_&&c.pc==e_.caller&&c.inst_count==last_&&
            seen_==3u&&word(c,e_.caller,e_.caller_word);
    }
    template<class C>bool object_held(C& c,bool held)const{
        return stage_==2u&&!error_&&held&&cpu_==&c&&safe(c)&&settled(c);
    }
private:
    ScQueueExpectation e_;const void* cpu_=nullptr;
    std::array<uint32_t,32> gp_{};std::array<uint32_t,8> gqr_{};
    std::vector<uint8_t> shadow_;
    uint32_t msr_=0,cr_=0,lr_=0,ctr_=0,xer_=0,srr0_=0,srr1_=0,next_=0,owner_=0;
    uint64_t last_=0;unsigned stage_=0,error_=0,visits_=0,stores_=0,seen_=0;
    bool initial_poll_=false,entry_seen_=false,call_due_=false,return_due_=false;
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    static bool volatile_reg(unsigned r){return r==0u||(r>=3u&&r<=12u);}
    template<class C>static bool safe(C& c){return c.is_running&&!c.in_callback&&!c.dispatch_saved_ctx;}
    template<class C>static uint32_t pack(C& c){uint32_t v=0;for(auto f:c.cr)v=(v<<4)|(unsigned(f.lt)<<3)|(unsigned(f.gt)<<2)|(unsigned(f.eq)<<1)|unsigned(f.so);return v;}
    template<class C>static bool mapped(C& c,AllocatorRange a){
        if(!a.size||a.base<0x80000000u||a.end()>0x81800000ull)return false;
        auto p=c.mmu.get_ptr(a.base),q=c.mmu.get_ptr(uint32_t(a.end()-1u));
        return p&&q&&reinterpret_cast<uintptr_t>(q)==reinterpret_cast<uintptr_t>(p)+a.size-1u;
    }
    template<class C>static bool word(C& c,uint32_t a,uint32_t w){return !(a&3u)&&mapped(c,{a,4})&&c.mmu.read32(a)==w;}
    template<class C>bool known(C& c,uint32_t owner,uint32_t pc)const{
        return std::count_if(e_.words.begin(),e_.words.end(),[&](auto x){return x.owner==owner&&x.pc==pc&&word(c,pc,x.word);})==1;
    }
    template<class C>bool known(C& c,uint32_t owner,uint32_t pc,uint32_t w)const{return known(c,owner,pc)&&word(c,pc,w);}
    template<class C>bool settled(C& c)const{
        if(!mapped(c,e_.object))return false;
        for(unsigned i=0;i<shadow_.size();++i)if(c.mmu.read8(e_.object.base+i)!=shadow_[i])return false;
        return true;
    }
    template<class C>bool common(C& c,bool held)const{
        return !error_&&held&&cpu_==&c&&safe(c)&&c.gpr==gp_&&c.gqr==gqr_&&c.msr==msr_&&
            pack(c)==cr_&&c.lr==lr_&&c.ctr==ctr_&&c.xer==xer_&&c.srr0==srr0_&&c.srr1==srr1_&&settled(c);
    }
};
}
