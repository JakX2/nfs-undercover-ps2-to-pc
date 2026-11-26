#pragma once
#include "wii_post_stm_sc_report.h"
namespace undercover::wii {
struct ScReportReturnExpectation {
    uint32_t root,start,caller,caller_word,frame_size;
    std::span<const IpcDispatchWord> words;
};
// Original report epilogue only. The caller must independently verify
// the diagnostic helper's real return before admitting this observer.
class ScReportReturnWitness {
public:
    explicit ScReportReturnWitness(ScReportReturnExpectation e):e_(e){}
    unsigned stage()const{return stage_;} unsigned failure()const{return error_;}
    unsigned visits()const{return visits_;} unsigned loads()const{return loads_;}
    uint32_t expected_sp()const{return gp_[1];}
    template<class C>bool begin(C& c,bool helper_returned){
        if(stage_||error_||!helper_returned||!safe(c)||!(c.msr&0x8000u)||c.pc!=e_.start||c.lr!=e_.start||
           e_.words.size()<3u||e_.words.size()>12u||e_.frame_size<32u||e_.frame_size>512u||
           (e_.frame_size&7u)||(c.gpr[1]&7u)||!known(c,e_.start)||
           !word(c,e_.caller,e_.caller_word))return fail(1);
        frame_={c.gpr[1],e_.frame_size+8u};
        if(!mapped(c,frame_))return fail(1);
        caller_sp_=c.gpr[1]+e_.frame_size;
        if(c.mmu.read32(frame_.base)!=caller_sp_||c.mmu.read32(caller_sp_+4u)!=e_.caller)return fail(1);
        for(unsigned i=0;i<frame_.size;++i)shadow_.push_back(c.mmu.read8(frame_.base+i));
        cpu_=&c;gp_=c.gpr;gqr_=c.gqr;msr_=c.msr;cr_=pack(c);lr_=c.lr;ctr_=c.ctr;xer_=c.xer;
        srr0_=c.srr0;srr1_=c.srr1;last_=c.inst_count;next_=e_.start;stage_=1;return true;
    }
    template<class C>bool poll(C& c,bool held){
        if(stage_!=1u||!common(c,held)||c.inst_count!=last_)return fail(2);
        if(!visits_&&!initial_poll_&&c.pc==e_.start){initial_poll_=true;return true;}
        if(!due_||c.pc!=e_.caller||c.lr!=e_.caller||c.gpr[1]!=caller_sp_||
           !word(c,e_.caller,e_.caller_word))return fail(2);
        stage_=2;return true;
    }
    template<class C>bool entry(C& c,uint32_t pc,bool held){
        if(stage_!=1u||!common(c,held)||visits_||!initial_poll_||entry_seen_||
           pc!=e_.start||c.pc!=pc||c.inst_count-last_!=1u)return fail(3);
        entry_seen_=true;return true;
    }
    template<class C>bool before(C& c,uint32_t pc,uint32_t w,bool held){
        if(stage_!=1u||!common(c,held)||due_||pc!=next_||
           c.inst_count-last_!=(visits_?1u:2u)||(!visits_&&(!initial_poll_||!entry_seen_||c.pc!=pc))||
           !known(c,pc,w)||++visits_>e_.words.size())return fail(4);
        last_=c.inst_count;next_=pc+4u;
        const unsigned op=w>>26,rs=(w>>21)&31u,ra=(w>>16)&31u,rb=(w>>11)&31u,xo=(w>>1)&1023u;
        const uint32_t imm=uint32_t(int32_t((w&0xffffu)^0x8000u)-0x8000);
        if(w==0x4e800020u){
            if(visits_!=e_.words.size()||loads_!=1u||!restored_lr_||!restored_sp_||
               gp_[1]!=caller_sp_||lr_!=e_.caller)return fail(5);
            next_=e_.caller;due_=true;return true;
        }
        if(op==32u&&ra==1u&&volatile_reg(rs)){
            if(loads_||gp_[1]+imm!=caller_sp_+4u||c.mmu.read32(caller_sp_+4u)!=e_.caller)return fail(5);
            gp_[rs]=e_.caller;loaded_reg_=rs;++loads_;
        }else if(op==31u&&xo==467u&&(ra|(rb<<5))==8u&&loads_==1u&&rs==loaded_reg_&&!restored_lr_){
            if(gp_[rs]!=e_.caller)return fail(5);
            lr_=gp_[rs];restored_lr_=true;
        }else if(op==14u&&rs==1u&&ra==1u&&!restored_sp_){
            if(gp_[1]+imm!=caller_sp_)return fail(5);
            gp_[1]=caller_sp_;restored_sp_=true;
        }else return fail(5);
        return known(c,next_)?true:fail(5);
    }
    template<class C>bool reached(C& c,bool held)const{
        return stage_==2u&&due_&&common(c,held)&&c.pc==e_.caller&&c.inst_count==last_&&
            c.gpr[1]==caller_sp_&&c.lr==e_.caller&&word(c,e_.caller,e_.caller_word);
    }
private:
    ScReportReturnExpectation e_;const void* cpu_=nullptr;AllocatorRange frame_{};
    std::array<uint32_t,32> gp_{};std::array<uint32_t,8> gqr_{};
    std::vector<uint8_t> shadow_;
    uint32_t caller_sp_=0,msr_=0,cr_=0,lr_=0,ctr_=0,xer_=0,srr0_=0,srr1_=0,next_=0;
    uint64_t last_=0;unsigned stage_=0,error_=0,visits_=0,loads_=0,loaded_reg_=32;
    bool initial_poll_=false,entry_seen_=false,due_=false,restored_lr_=false,restored_sp_=false;
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
    template<class C>bool known(C& c,uint32_t pc)const{
        return std::count_if(e_.words.begin(),e_.words.end(),[&](auto x){return x.owner==e_.root&&x.pc==pc&&word(c,pc,x.word);})==1;
    }
    template<class C>bool known(C& c,uint32_t pc,uint32_t w)const{return known(c,pc)&&word(c,pc,w);}
    template<class C>bool common(C& c,bool held)const{
        if(error_||!held||cpu_!=&c||!safe(c)||c.gpr!=gp_||c.gqr!=gqr_||c.msr!=msr_||
           pack(c)!=cr_||c.lr!=lr_||c.ctr!=ctr_||c.xer!=xer_||c.srr0!=srr0_||c.srr1!=srr1_||!mapped(c,frame_))return false;
        for(unsigned i=0;i<shadow_.size();++i)if(c.mmu.read8(frame_.base+i)!=shadow_[i])return false;
        return true;
    }
};
}
