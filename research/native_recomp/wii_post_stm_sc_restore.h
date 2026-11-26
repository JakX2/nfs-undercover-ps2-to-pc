#pragma once
#include "wii_post_stm_sc_decision.h"
#include "wii_stm_outer_restore.h"
namespace undercover::wii {
// Original OSRestoreInterrupts with a quiescent external IRQ line.
// Separate the native rising-EE poll from the native post-mtmsr suffix.
// Unlike the earlier STM return, there must be no new RFI or IRQ entry.
class ScQuietRestoreWitness {
public:
    explicit ScQuietRestoreWitness(StmOuterRestoreExpectation e):e_(e){}
    unsigned stage()const{return stage_;} unsigned failure()const{return error_;}
    unsigned visits()const{return visits_;} unsigned ordinal()const{return ordinal_;}
    uint32_t expected_msr()const{return msr_;}
    template<class C>bool begin(C& c,bool held){
        if(stage_||error_||!held||!safe(c)||(c.msr&0x8000u)||c.pc!=e_.root||c.lr!=e_.caller||
           c.gpr[3]!=1u||e_.words.size()<4u||e_.words.size()>16u||e_.resume!=e_.enable_site+4u||
           !known(c,e_.root)||!known(c,e_.enable_site)||!known(c,e_.resume)||
           !word(c,e_.resume,e_.resume_word)||!word(c,e_.caller,e_.caller_word))return fail(1);
        cpu_=&c;gp_=c.gpr;gqr_=c.gqr;msr_=masked_=c.msr;cr_=pack(c);lr_=c.lr;ctr_=c.ctr;xer_=c.xer;
        srr0_=c.srr0;srr1_=c.srr1;last_=c.inst_count;next_=e_.root;stage_=1;return true;
    }
    template<class C>bool poll(C& c,bool held){
        if((stage_!=1u&&stage_!=2u)||!common(c,held)||c.inst_count!=last_)return fail(2);
        if(stage_==1u){
            if(!visits_&&!initial_poll_&&c.pc==e_.root){initial_poll_=true;return true;}
            if(!enable_due_||c.pc!=e_.resume||c.msr!=(masked_|0x8000u)||!word(c,e_.resume,e_.resume_word))return fail(2);
            enable_due_=false;stage_=2;return true;
        }
        if(!suffix_poll_&&!return_due_&&c.pc==e_.resume){suffix_poll_=true;return true;}
        if(!return_due_||c.pc!=e_.caller||!word(c,e_.caller,e_.caller_word))return fail(2);
        stage_=3;return true;
    }
    template<class C>bool entry(C& c,uint32_t pc,bool held){
        if(!common(c,held)||c.pc!=pc||c.inst_count-last_!=1u)return fail(3);
        if(stage_==1u&&!visits_&&initial_poll_&&!entry_seen_&&pc==e_.root){entry_seen_=true;return true;}
        if(stage_==2u&&suffix_poll_&&!suffix_entry_&&pc==e_.resume){suffix_entry_=true;return true;}
        return fail(3);
    }
    template<class C>bool before(C& c,uint32_t pc,uint32_t w,bool held){
        const bool first=!visits_||(stage_==2u&&!suffix_started_);
        if((stage_!=1u&&stage_!=2u)||!common(c,held)||enable_due_||return_due_||pc!=next_||
           c.inst_count-last_!=(first?2u:1u)||(first&&c.pc!=pc)||
           (!visits_&&!initial_poll_)||(stage_==2u&&!suffix_poll_)||!known(c,pc,w)||++visits_>e_.words.size())
            return fail(4);
        if(stage_==2u)suffix_started_=true;
        ordinal_=(pc-e_.root)/4u+1u;last_=c.inst_count;next_=pc+4u;
        const unsigned op=w>>26,rs=(w>>21)&31u,ra=(w>>16)&31u,rb=(w>>11)&31u,xo=(w>>1)&1023u;
        const uint32_t imm=uint32_t(int32_t((w&0xffffu)^0x8000u)-0x8000);
        if(w==0x4e800020u){
            if(stage_!=2u||!read_||!written_||msr_!=(masked_|0x8000u)||!suffix_started_)return fail(5);
            return_due_=true;next_=e_.caller;return true;
        }
        if(op==31u&&xo==83u&&volatile_reg(rs)){
            if(stage_!=1u||read_||written_)return fail(5);
            gp_[rs]=msr_;read_=true;
        }else if(op==31u&&xo==146u&&volatile_reg(rs)){
            if(stage_!=1u||!read_||written_||pc!=e_.enable_site||gp_[rs]!=(masked_|0x8000u))return fail(5);
            msr_=gp_[rs];written_=true;enable_due_=true;
        }else if(w==0x4c00012cu||w==0x7c0004acu){}
        else if((op==20u||op==21u)&&!(w&1u)&&volatile_reg(ra)){
            const auto m=mask((w>>6)&31u,(w>>1)&31u);
            const auto v=std::rotl(gp_[rs],int(rb))&m;
            gp_[ra]=op==20u?(gp_[ra]&~m)|v:v;
        }else if(op==14u&&volatile_reg(rs)){
            gp_[rs]=(ra?gp_[ra]:0u)+imm;
        }else if((op==24u||op==25u)&&volatile_reg(ra)){
            gp_[ra]=gp_[rs]|((w&0xffffu)<<(op==25u?16u:0u));
        }else if(op==31u&&!(w&1u)&&volatile_reg(ra)&&(xo==28u||xo==60u||xo==444u)){
            gp_[ra]=xo==28u?gp_[rs]&gp_[rb]:xo==60u?gp_[rs]&~gp_[rb]:gp_[rs]|gp_[rb];
        }else if((op==10u||op==11u)&&!(w&0x00200000u)){
            const auto a=gp_[ra],b=op==10u?w&0xffffu:imm;
            const bool lt=op==10u?a<b:std::bit_cast<int32_t>(a)<std::bit_cast<int32_t>(b);
            const unsigned shift=28u-4u*((w>>23)&7u);
            const auto v=(lt?8u:a==b?2u:4u)|((xer_>>31)&1u);
            cr_=(cr_&~(15u<<shift))|(v<<shift);
        }else if(op==16u||op==18u){
            if(w&3u||target(pc,w)<=pc||(op==16u&&!((w>>21)&4u)))return fail(5);
            if(op==18u||taken(w))next_=target(pc,w);
        }else return fail(5);
        if(!known(c,next_))return fail(5);
        return true;
    }
    template<class C>bool enabled(C& c,bool held)const{
        return stage_==2u&&written_&&!suffix_poll_&&!enable_due_&&common(c,held)&&
            c.pc==e_.resume&&c.inst_count==last_&&word(c,e_.resume,e_.resume_word);
    }
    template<class C>bool reached(C& c,bool held)const{
        return stage_==3u&&return_due_&&common(c,held)&&c.pc==e_.caller&&c.inst_count==last_&&
            word(c,e_.caller,e_.caller_word);
    }
private:
    StmOuterRestoreExpectation e_;const void* cpu_=nullptr;
    std::array<uint32_t,32> gp_{};std::array<uint32_t,8> gqr_{};
    uint32_t msr_=0,masked_=0,cr_=0,lr_=0,ctr_=0,xer_=0,srr0_=0,srr1_=0,next_=0;
    uint64_t last_=0;unsigned stage_=0,error_=0,visits_=0,ordinal_=0;
    bool initial_poll_=false,entry_seen_=false,read_=false,written_=false,enable_due_=false,
        suffix_poll_=false,suffix_entry_=false,suffix_started_=false,return_due_=false;
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    static bool volatile_reg(unsigned r){return r==0u||(r>=3u&&r<=12u);}
    static uint32_t mask(unsigned mb,unsigned me){
        uint32_t out=0;for(unsigned n=mb;;n=(n+1u)&31u){out|=1u<<(31u-n);if(n==me)break;}return out;
    }
    static uint32_t target(uint32_t pc,uint32_t w){const bool bc=w>>26==16u;const uint32_t m=bc?0xfffcu:0x03fffffcu,s=bc?0x8000u:0x02000000u;return pc+(((w&m)^s)-s);}
    bool taken(uint32_t w)const{
        const unsigned bo=(w>>21)&31u,bi=(w>>16)&31u;
        return (bo&16u)||bool((cr_>>(31u-bi))&1u)==bool(bo&8u);
    }
    template<class C>static bool safe(C& c){return c.is_running&&!c.in_callback&&!c.dispatch_saved_ctx;}
    template<class C>static uint32_t pack(C& c){uint32_t v=0;for(auto f:c.cr)v=(v<<4)|(unsigned(f.lt)<<3)|(unsigned(f.gt)<<2)|(unsigned(f.eq)<<1)|unsigned(f.so);return v;}
    template<class C>bool common(C& c,bool held)const{
        return !error_&&held&&cpu_==&c&&safe(c)&&c.gpr==gp_&&c.gqr==gqr_&&c.msr==msr_&&
            pack(c)==cr_&&c.lr==lr_&&c.ctr==ctr_&&c.xer==xer_&&c.srr0==srr0_&&c.srr1==srr1_;
    }
    template<class C>static bool word(C& c,uint32_t a,uint32_t w){
        if((a&3u)||a<0x80000000u||a>0x817ffffcu)return false;
        auto p=c.mmu.get_ptr(a),q=c.mmu.get_ptr(a+3u);
        return p&&q&&reinterpret_cast<uintptr_t>(q)==reinterpret_cast<uintptr_t>(p)+3u&&c.mmu.read32(a)==w;
    }
    template<class C>bool known(C& c,uint32_t pc)const{
        return std::count_if(e_.words.begin(),e_.words.end(),
            [&](auto x){return x.owner==e_.root&&x.pc==pc&&word(c,pc,x.word);})==1;
    }
    template<class C>bool known(C& c,uint32_t pc,uint32_t w)const{return known(c,pc)&&word(c,pc,w);}
};
}
