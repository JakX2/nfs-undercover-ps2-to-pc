#pragma once
#include "wii_post_stm_sc_version.h"
#include <optional>
namespace undercover::wii {
struct ScReportExpectation {
    uint32_t root,target,target_word,frame_size;
    std::span<const IpcDispatchWord> path; // private ordered CR6-clear path
    unsigned store_sites;
};
// Predict only the authenticated prologue. Guest execution must perform
// every register change, stack write and call; no diagnostic HLE return.
class ScReportWitness {
public:
    explicit ScReportWitness(ScReportExpectation e):e_(e){}
    unsigned stage()const{return stage_;} unsigned failure()const{return error_;}
    unsigned visits()const{return visits_;} unsigned stores()const{return stores_;}
    uint32_t expected_sp()const{return gp_[1];}
    const std::array<uint32_t,32>& incoming_gprs()const{return incoming_;}
    template<class C>bool child_frame_held(C& c,bool held,uint32_t child_sp,uint32_t child_link,uint32_t depth=256u,uint32_t extra_frame=0u)const{
        if(stage_!=2u||error_||!held||cpu_!=&c||!safe(c)||c.gpr[1]!=child_sp||
           (extra_frame!=0u&&extra_frame!=48u)||depth>768u+extra_frame||child_sp>frame_.base||frame_.base-child_sp>depth||(child_sp&7u)||
           c.inst_count<last_||c.inst_count-last_>512u||!mapped(c,frame_))return false;
        for(unsigned i=0;i<shadow_.size();++i){
            if(i>=4u&&i<8u&&written_[i])return false;
            const uint8_t expected=(i>=4u&&i<8u)?uint8_t(child_link>>(24u-8u*(i-4u))):shadow_[i];
            if(c.mmu.read8(frame_.base+i)!=expected)return false;
        }
        return true;
    }
    // Read only a byte established by this witness's original prologue.
    // The full live frame must still match its shadow, including linkage.
    // Exclude the back chain, reserved child link, uninitialized padding
    // and the caller-owned words beyond this frame. This observes a value;
    // it does not authorize or perform the guest's pending load.
    template<class C>std::optional<uint8_t> observed_child_byte(C& c,bool held,
        uint32_t child_sp,uint32_t child_link,uint32_t depth,uint32_t address,
        uint32_t extra_frame=0u)const{
        if(address<frame_.base||address-frame_.base<8u||
           address-frame_.base>=e_.frame_size||
           !child_frame_held(c,held,child_sp,child_link,depth,extra_frame))return {};
        const auto i=address-frame_.base;
        if(i>=written_.size()||i>=shadow_.size()||!written_[i])return {};
        return shadow_[i];
    }
    uint32_t linkage_word()const{
        uint32_t v=0;for(unsigned i=0;i<4;++i)v=(v<<8)|shadow_[e_.frame_size+4+i];return v;
    }
    template<class C>bool begin(C& c,bool held){
        if(stage_||error_||!held||!safe(c)||!(c.msr&0x8000u)||c.pc!=e_.root||
           c.cr[1].eq||e_.frame_size<32u||e_.frame_size>512u||(e_.frame_size&7u)||
           e_.path.empty()||e_.path.size()>64u||e_.path.front().pc!=e_.root||
           (c.gpr[1]&7u)||c.gpr[1]<0x80000000u+e_.frame_size||
           !word(c,e_.target,e_.target_word))return fail(1);
        frame_={c.gpr[1]-e_.frame_size,e_.frame_size+8u};
        if(!mapped(c,frame_))return fail(1);
        for(auto x:e_.path)if(x.owner!=e_.root||!word(c,x.pc,x.word)||
            std::count_if(e_.path.begin(),e_.path.end(),[&](auto y){return x.pc==y.pc;})!=1)return fail(1);
        for(unsigned i=0;i<frame_.size;++i)shadow_.push_back(c.mmu.read8(frame_.base+i));
        written_.resize(frame_.size);
        cpu_=&c;gp_=incoming_=c.gpr;gqr_=c.gqr;msr_=c.msr;cr_=pack(c);lr_=caller_=c.lr;
        ctr_=c.ctr;xer_=c.xer;srr0_=c.srr0;srr1_=c.srr1;last_=c.inst_count;stage_=1;return true;
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
        if(stage_!=1u||!common(c,held)||due_||visits_>=e_.path.size()||
           c.inst_count-last_!=(visits_?1u:2u)||(!visits_&&(!initial_poll_||!entry_seen_||c.pc!=pc))||
           e_.path[visits_].pc!=pc||e_.path[visits_].word!=w||!word(c,pc,w))return fail(4);
        ++visits_;last_=c.inst_count;uint32_t next=pc+4u;
        const unsigned op=w>>26,rs=(w>>21)&31u,ra=(w>>16)&31u,rb=(w>>11)&31u,xo=(w>>1)&1023u;
        const uint32_t imm=uint32_t(int32_t((w&0xffffu)^0x8000u)-0x8000);
        if(op==37u&&rs==1u&&ra==1u){
            if(stores_||gp_[1]!=incoming_[1]||gp_[1]+imm!=frame_.base||!store(frame_.base,4,gp_[1]))return fail(5);
            ++stores_;gp_[1]=frame_.base;
        }else if((op==36u||op==38u||op==44u||op==47u)&&ra==1u&&gp_[1]==frame_.base){
            const auto a=gp_[1]+imm;
            if(op==47u){for(unsigned i=rs;i<32u;++i)if(!store(a+4u*(i-rs),4,gp_[i]))return fail(5);}
            else if(!store(a,op==36u?4u:op==38u?1u:2u,gp_[rs]))return fail(5);
            ++stores_;
        }else if(op==31u&&xo==339u&&(ra|(rb<<5))==8u&&rs!=1u){
            gp_[rs]=lr_;
        }else if((op==14u||op==15u)&&rs!=1u){
            gp_[rs]=(ra?gp_[ra]:0u)+(op==15u?imm<<16u:imm);
        }else if((op==24u||op==25u)&&ra!=1u){
            gp_[ra]=gp_[rs]|((w&0xffffu)<<(op==25u?16u:0u));
        }else if(op==31u&&xo==444u&&rs==rb&&!(w&1u)&&ra!=1u){
            gp_[ra]=gp_[rs];
        }else if(op==18u&&(w&3u)==1u){
            if(visits_!=e_.path.size()||target(pc,w)!=e_.target||!abi(c))return fail(6);
            lr_=pc+4u;due_=true;return true;
        }else if((op==16u||op==18u)&&!(w&3u)){
            if(op==16u){
                const unsigned bo=(w>>21)&31u,bi=(w>>16)&31u;
                if(!(bo&4u)||(!(bo&16u)&&bi!=6u))return fail(6);
                if((bo&16u)||bool((cr_>>(31u-bi))&1u)==bool(bo&8u))next=target(pc,w);
            }else next=target(pc,w);
        }else return fail(6);
        if(visits_>=e_.path.size()||e_.path[visits_].pc!=next)return fail(6);
        return true;
    }
    template<class C>bool reached(C& c,bool held)const{
        return stage_==2u&&due_&&common(c,held)&&c.pc==e_.target&&c.inst_count==last_&&abi(c);
    }
private:
    ScReportExpectation e_;const void* cpu_=nullptr;AllocatorRange frame_{};
    std::array<uint32_t,32> gp_{},incoming_{};std::array<uint32_t,8> gqr_{};
    std::vector<uint8_t> shadow_,written_;
    uint32_t msr_=0,cr_=0,lr_=0,caller_=0,ctr_=0,xer_=0,srr0_=0,srr1_=0;
    uint64_t last_=0;unsigned stage_=0,error_=0,visits_=0,stores_=0;
    bool initial_poll_=false,entry_seen_=false,due_=false;
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    static uint32_t target(uint32_t pc,uint32_t w){
        const bool bc=w>>26==16u;const uint32_t m=bc?0xfffcu:0x03fffffcu,s=bc?0x8000u:0x02000000u;
        return pc+(((w&m)^s)-s);
    }
    bool store(uint32_t a,unsigned n,uint32_t v){
        if(!frame_.contains(a,n)||(a%n)||stores_>=e_.store_sites)return false;
        for(unsigned i=0;i<n;++i){const auto j=a-frame_.base+i;if(written_[j])return false;written_[j]=1;
            shadow_[j]=uint8_t(v>>(8u*(n-i-1u)));}
        return true;
    }
    template<class C>bool abi(C& c)const{
        if(stores_!=e_.store_sites||gp_[1]!=frame_.base||c.gpr[3]!=incoming_[3]||
           !frame_.contains(c.gpr[4],12u)||(c.gpr[4]&3u)||
           c.mmu.read32(frame_.base)!=incoming_[1]||c.mmu.read32(incoming_[1]+4u)!=caller_)return false;
        const uint32_t va=c.gpr[4],save=c.mmu.read32(va+8u);
        if(c.mmu.read32(va)!=0x01000000u||c.mmu.read32(va+4u)!=incoming_[1]+8u||
           !frame_.contains(save,32u)||(save&3u))return false;
        for(unsigned i=0;i<8u;++i)if(c.mmu.read32(save+4u*i)!=incoming_[3u+i])return false;
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
    template<class C>bool common(C& c,bool held)const{
        if(error_||!held||cpu_!=&c||!safe(c)||c.gpr!=gp_||c.gqr!=gqr_||c.msr!=msr_||
           pack(c)!=cr_||c.lr!=lr_||c.ctr!=ctr_||c.xer!=xer_||c.srr0!=srr0_||c.srr1!=srr1_||!mapped(c,frame_))return false;
        for(unsigned i=0;i<shadow_.size();++i)if(c.mmu.read8(frame_.base+i)!=shadow_[i])return false;
        return true;
    }
};
}
