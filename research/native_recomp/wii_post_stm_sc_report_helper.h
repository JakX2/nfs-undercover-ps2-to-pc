#pragma once
#include "wii_post_stm_sc_report.h"
namespace undercover::wii {
struct ScReportHelperExpectation {
    uint32_t root,entry_lr,target,target_word,frame_size;
    std::span<const IpcDispatchWord> words;
    std::span<const StmFinalSlot> slots;
};
class ScReportHelperWitness {
public:
    explicit ScReportHelperWitness(ScReportHelperExpectation e):e_(e){}
    unsigned stage()const{return stage_;} unsigned failure()const{return error_;}
    unsigned visits()const{return visits_;} unsigned stores()const{return stores_;}
    uint32_t expected_sp()const{return gp_[1];}
    uint32_t linkage_word()const{
        uint32_t v=0;for(unsigned i=0;i<4;++i)v=(v<<8)|shadow_[e_.frame_size+4+i];return v;
    }
    template<class C>bool begin(C& c,bool held){
        if(stage_||error_||!held||!safe(c)||!(c.msr&0x8000u)||c.pc!=e_.root||c.lr!=e_.entry_lr||
           e_.frame_size!=32u||e_.words.size()!=13u||e_.slots.size()!=4u||
           (c.gpr[1]&7u)||c.gpr[1]<0x80000000u+e_.frame_size||
           !known(c,e_.root)||!word(c,e_.target,e_.target_word))return fail(1);
        frame_={c.gpr[1]-e_.frame_size,e_.frame_size+8u};
        if(!mapped(c,frame_))return fail(1);
        for(auto s:e_.slots){
            const auto at=int64_t(c.gpr[1])+s.caller_offset;
            if(s.reg<14u||s.reg>32u||at<0||at>0xffffffffll||(at&3)||!frame_.contains(uint32_t(at),4u)||
               (s.reg==32u)!=(s.caller_offset==4)||uint32_t(at)==frame_.base||
               std::count_if(e_.slots.begin(),e_.slots.end(),[&](auto x){return x.reg==s.reg||x.caller_offset==s.caller_offset;})!=1)
                return fail(1);
        }
        if(std::count_if(e_.slots.begin(),e_.slots.end(),[](auto s){return s.reg==32u;})!=1)return fail(1);
        for(unsigned i=0;i<frame_.size;++i)shadow_.push_back(c.mmu.read8(frame_.base+i));
        written_.resize(frame_.size);cpu_=&c;gp_=incoming_=c.gpr;gqr_=c.gqr;msr_=c.msr;
        cr_=pack(c);lr_=c.lr;ctr_=c.ctr;xer_=c.xer;srr0_=c.srr0;srr1_=c.srr1;
        last_=c.inst_count;next_=e_.root;stage_=1;return true;
    }
    template<class C>bool poll(C& c,bool held){
        if(stage_!=1u||!common(c,held)||visits_||initial_poll_||c.pc!=e_.root||c.inst_count!=last_)return fail(2);
        initial_poll_=true;return true;
    }
    template<class C>bool entry(C& c,uint32_t pc,bool held){
        if(stage_!=1u||!common(c,held)||c.pc!=pc)return fail(3);
        if(!visits_){
            if(!initial_poll_||entry_seen_||pc!=e_.root||c.inst_count-last_!=1u)return fail(3);
            entry_seen_=true;return true;
        }
        if(!due_||pc!=e_.target||c.inst_count!=last_||!word(c,pc,e_.target_word)||!abi(c))return fail(3);
        stage_=2;return true;
    }
    template<class C>bool before(C& c,uint32_t pc,uint32_t w,bool held){
        if(stage_!=1u||!common(c,held)||due_||pc!=next_||
           c.inst_count-last_!=(visits_?1u:2u)||(!visits_&&(!initial_poll_||!entry_seen_||c.pc!=pc))||
           !known(c,pc,w)||++visits_>e_.words.size())return fail(4);
        last_=c.inst_count;next_=pc+4u;
        const unsigned op=w>>26,rs=(w>>21)&31u,ra=(w>>16)&31u,rb=(w>>11)&31u,xo=(w>>1)&1023u;
        const uint32_t imm=uint32_t(int32_t((w&0xffffu)^0x8000u)-0x8000);
        if(op==37u&&rs==1u&&ra==1u){
            if(stores_||gp_[1]!=incoming_[1]||gp_[1]+imm!=frame_.base||!store(frame_.base,gp_[1]))return fail(5);
            ++stores_;gp_[1]=frame_.base;
        }else if((op==36u||op==47u)&&ra==1u&&gp_[1]==frame_.base){
            const auto a=gp_[1]+imm;
            if(op==47u){for(unsigned i=rs;i<32u;++i)if(!store(a+4u*(i-rs),gp_[i]))return fail(5);}
            else if(!store(a,gp_[rs]))return fail(5);
            ++stores_;
        }else if(op==31u&&xo==339u&&(ra|(rb<<5))==8u&&rs!=1u)gp_[rs]=lr_;
        else if((op==14u||op==15u)&&rs!=1u)gp_[rs]=(ra?gp_[ra]:0u)+(op==15u?imm<<16u:imm);
        else if((op==24u||op==25u)&&ra!=1u)gp_[ra]=gp_[rs]|((w&0xffffu)<<(op==25u?16u:0u));
        else if(op==31u&&xo==444u&&rs==rb&&!(w&1u)&&ra!=1u)gp_[ra]=gp_[rs];
        else if(op==18u&&(w&3u)==1u){
            if(visits_!=e_.words.size()||pc+(((w&0x03fffffcu)^0x02000000u)-0x02000000u)!=e_.target||!abi(c))return fail(6);
            lr_=pc+4u;next_=e_.target;due_=true;return true;
        }else return fail(6);
        return known(c,next_)?true:fail(6);
    }
    template<class C>bool reached(C& c,bool held)const{
        return stage_==2u&&due_&&common(c,held)&&c.pc==e_.target&&c.inst_count==last_&&abi(c);
    }
    // The dependency is a leaf with no stack accesses. Preserve this
    // helper's complete frame while the authorized data object changes.
    template<class C>bool frame_held(C& c,bool held)const{
        if(stage_!=2u||error_||!held||cpu_!=&c||!safe(c)||c.gpr[1]!=frame_.base||
           c.inst_count<last_||c.inst_count-last_>128u||!mapped(c,frame_))return false;
        for(unsigned i=0;i<shadow_.size();++i)if(c.mmu.read8(frame_.base+i)!=shadow_[i])return false;
        return true;
    }
private:
    ScReportHelperExpectation e_;const void* cpu_=nullptr;AllocatorRange frame_{};
    std::array<uint32_t,32> gp_{},incoming_{};std::array<uint32_t,8> gqr_{};
    std::vector<uint8_t> shadow_,written_;
    uint32_t msr_=0,cr_=0,lr_=0,ctr_=0,xer_=0,srr0_=0,srr1_=0,next_=0;
    uint64_t last_=0;unsigned stage_=0,error_=0,visits_=0,stores_=0;
    bool initial_poll_=false,entry_seen_=false,due_=false;
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    bool store(uint32_t a,uint32_t v){
        if(!frame_.contains(a,4u)||(a&3u)||stores_>=5u)return false;
        for(unsigned i=0;i<4;++i){const auto j=a-frame_.base+i;if(written_[j])return false;written_[j]=1;
            shadow_[j]=uint8_t(v>>(24u-i*8u));}
        return true;
    }
    template<class C>bool abi(C& c)const{
        if(stores_!=5u||gp_[1]!=frame_.base||c.mmu.read32(frame_.base)!=incoming_[1]||
           gp_[2]!=incoming_[2]||gp_[13]!=incoming_[13])return false;
        for(auto s:e_.slots){
            const auto a=uint32_t(int64_t(incoming_[1])+s.caller_offset);
            if(c.mmu.read32(a)!=(s.reg==32u?e_.entry_lr:incoming_[s.reg]))return false;
        }
        for(unsigned r=14;r<32u;++r)if(gp_[r]!=incoming_[r]&&
            std::none_of(e_.slots.begin(),e_.slots.end(),[&](auto s){return s.reg==r;}))return false;
        return true;
    }
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
