#pragma once
#include "wii_stm_final_return.h"
namespace undercover::wii {
struct PostStmScExpectation{
    uint32_t caller,root,disable,disable_word,frame_size;
    std::span<const StmFinalSlot> slots;
    std::span<const IpcDispatchWord> words;
};
// Observe the authentic OSInit BL and straight-line SC prologue. The
// native CPU executes the words; this object only predicts ABI effects.
class PostStmScEntryWitness{
public:
    explicit PostStmScEntryWitness(PostStmScExpectation e):e_(e){}
    unsigned stage()const{return stage_;}
    unsigned failure()const{return error_;}
    unsigned visits()const{return visits_;}
    unsigned stores()const{return stores_;}
    template<class C>bool begin(C& c,bool held){
        if(stage_||error_||!held||!safe(c)||!(c.msr&0x8000u)||c.pc!=e_.caller||c.lr!=e_.caller||
           e_.words.size()!=6u||e_.slots.size()!=2u||e_.frame_size<8u||e_.frame_size>256u||(e_.frame_size&7u)||
           c.gpr[1]<0x80000000u+e_.frame_size||c.gpr[1]&7u||
           !known(c,e_.caller,e_.caller)||!known(c,e_.root,e_.root)||!word(c,e_.disable,e_.disable_word))return fail(1);
        frame_={c.gpr[1]-e_.frame_size,e_.frame_size+8u};
        if(!mapped(c,frame_))return fail(1);
        for(auto s:e_.slots){
            const auto a=int64_t(c.gpr[1])+s.caller_offset;
            if(s.reg<14u||s.reg>32u||a<0||a>0xffffffffll||(a&3)||
               !frame_.contains(uint32_t(a),4u)||uint32_t(a)==frame_.base||
               std::count_if(e_.slots.begin(),e_.slots.end(),[&](auto x){return x.reg==s.reg||x.caller_offset==s.caller_offset;})!=1)
                return fail(1);
        }
        if(std::count_if(e_.slots.begin(),e_.slots.end(),[](auto s){return s.reg==32u;})!=1)return fail(1);
        for(unsigned i=0;i<frame_.size;++i)shadow_.push_back(c.mmu.read8(frame_.base+i));
        cpu_=&c;gp_=c.gpr;incoming_=c.gpr;gqr_=c.gqr;msr_=c.msr;cr_=pack(c);lr_=c.lr;ctr_=c.ctr;xer_=c.xer;
        srr0_=c.srr0;srr1_=c.srr1;last_=c.inst_count;next_=e_.caller;stage_=1;return true;
    }
    template<class C>bool poll(C& c,bool held){
        if(stage_!=1u||!common(c,held)||visits_||initial_poll_||c.pc!=e_.caller||c.inst_count!=last_)return fail(2);
        initial_poll_=true;return true;
    }
    template<class C>bool entry(C& c,uint32_t pc,bool held){
        if(stage_!=1u||!common(c,held)||c.pc!=pc)return fail(3);
        if(!visits_){
            if(!initial_poll_||outer_entry_||pc!=e_.caller||c.inst_count-last_!=1u)return fail(3);
            outer_entry_=true;return true;
        }
        if(!entry_due_||pc!=next_||c.inst_count!=last_)return fail(3);
        entry_due_=false;
        if(pc==e_.root&&visits_==1u&&!root_entry_){root_entry_=true;owner_=e_.root;return true;}
        if(pc!=e_.disable||visits_!=e_.words.size()||stores_!=3u||!root_entry_||
           c.gpr[1]!=frame_.base||c.mmu.read32(frame_.base)!=incoming_[1]||!word(c,pc,e_.disable_word))return fail(3);
        for(auto slot:e_.slots){
            const auto a=uint32_t(int64_t(incoming_[1])+slot.caller_offset);
            if(c.mmu.read32(a)!=(slot.reg==32u?e_.caller+4u:incoming_[slot.reg]))return fail(3);
        }
        stage_=2;return true;
    }
    template<class C>bool before(C& c,uint32_t pc,uint32_t w,bool held){
        if(stage_!=1u||!common(c,held)||entry_due_||pc!=next_||
           c.inst_count-last_!=(visits_?1u:2u)||(!visits_&&(!initial_poll_||c.pc!=pc))||
           !known(c,visits_?owner_:e_.caller,pc,w)||++visits_>e_.words.size())return fail(4);
        last_=c.inst_count;next_=pc+4u;
        const unsigned op=w>>26,rs=(w>>21)&31u,ra=(w>>16)&31u,rb=(w>>11)&31u,xo=(w>>1)&1023u;
        const int32_t d=int32_t((w&0xffffu)^0x8000u)-0x8000;
        if(op==18u&&(w&3u)==1u){
            const uint32_t dst=pc+(((w&0x03fffffcu)^0x02000000u)-0x02000000u);
            if((visits_==1u&&pc==e_.caller&&dst==e_.root)||
               (visits_==e_.words.size()&&root_entry_&&dst==e_.disable&&stores_==3u)){
                lr_=pc+4u;next_=dst;entry_due_=true;return true;
            }
            return fail(5);
        }
        if(!root_entry_)return fail(5);
        if(op==37u&&rs==1u&&ra==1u){
            if(stores_||d!=-int32_t(e_.frame_size)||gp_[1]!=incoming_[1])return fail(6);
            if(!store(frame_.base,gp_[1]))return fail(6);
            gp_[1]=frame_.base;
        }else if(op==31u&&xo==339u&&(ra|(rb<<5))==8u&&volatile_reg(rs)){
            gp_[rs]=lr_;
        }else if(op==36u&&ra==1u&&gp_[1]==frame_.base){
            const auto a=int64_t(gp_[1])+d;
            if(a<0||a>0xffffffffll)return fail(6);
            auto it=std::find_if(e_.slots.begin(),e_.slots.end(),[&](auto x){return int64_t(incoming_[1])+x.caller_offset==a;});
            if(it==e_.slots.end()||(saved_&(uint64_t(1)<<it->reg))||
               gp_[rs]!=(it->reg==32u?e_.caller+4u:incoming_[it->reg])||!store(uint32_t(a),gp_[rs]))return fail(6);
            saved_|=uint64_t(1)<<it->reg;
        }else return fail(5);
        if(!known(c,owner_,next_))return fail(5);
        return true;
    }
    template<class C>bool reached(C& c,bool held)const{
        return stage_==2u&&common(c,held)&&c.pc==e_.disable&&c.inst_count==last_&&
            visits_==e_.words.size()&&stores_==3u&&word(c,e_.disable,e_.disable_word);
    }
    // The next original leaf owns its register/MSR effects, but the
    // SC frame remains immutable until another explicit witness takes over.
    template<class C>bool frame_held(C& c,bool held)const{
        if(stage_!=2u||error_||!held||cpu_!=&c||!safe(c)||c.gpr[1]!=frame_.base||
           !mapped(c,frame_)||c.inst_count<last_||c.inst_count-last_>128u)return false;
        for(unsigned i=0;i<shadow_.size();++i)if(c.mmu.read8(frame_.base+i)!=shadow_[i])return false;
        return true;
    }
    // A native child may use the caller's reserved LR linkage word at
    // SP+4. Preserve every other byte, including SC's own saved LR/GPR.
    template<class C>bool nested_frame_held(C& c,bool held,uint32_t child_sp,uint32_t link_word,uint32_t depth=512u,uint64_t ticks=128u)const{
        return ticks<=256u&&nested_frame_storage_held(c,held,child_sp,link_word,depth,ticks);
    }
    template<class C>uint64_t frame_age(C& c)const{
        return c.inst_count>=last_?c.inst_count-last_:UINT64_MAX;
    }
    // Capture only at a separately verified child checkpoint. The original
    // 256-tick check and all storage checks must still pass at capture.
    template<class C>bool capture_nested_checkpoint(C& c,bool held,uint32_t child_sp,uint32_t link_word,uint32_t depth){
        if(nested_checkpoint_valid_||!nested_frame_held(c,held,child_sp,link_word,depth,256u))return false;
        nested_checkpoint_tick_=c.inst_count;nested_checkpoint_age_=frame_age(c);
        nested_checkpoint_sp_=child_sp;nested_checkpoint_link_=link_word;nested_checkpoint_depth_=depth;
        nested_checkpoint_valid_=true;return true;
    }
    bool nested_checkpoint_valid()const{return nested_checkpoint_valid_;}
    uint64_t nested_checkpoint_age()const{return nested_checkpoint_valid_?nested_checkpoint_age_:0u;}
    // The child's bounded, independently counted continuation supplies the
    // extra budget. Recheck the same frame and linkage at every boundary.
    template<class C>bool nested_frame_held_after_checkpoint(C& c,bool held,uint32_t child_sp,uint32_t link_word,
                                                            uint32_t depth,unsigned authorized_ticks)const{
        if(!nested_checkpoint_valid_||authorized_ticks>36u||child_sp!=nested_checkpoint_sp_||
           link_word!=nested_checkpoint_link_||depth!=nested_checkpoint_depth_||
           c.inst_count<nested_checkpoint_tick_||c.inst_count-nested_checkpoint_tick_>authorized_ticks)return false;
        return nested_frame_storage_held(c,held,child_sp,link_word,depth,nested_checkpoint_age_+authorized_ticks);
    }
private:
    template<class C>bool nested_frame_storage_held(C& c,bool held,uint32_t child_sp,uint32_t link_word,uint32_t depth,uint64_t ticks)const{
        if(stage_!=2u||error_||!held||cpu_!=&c||!safe(c)||c.gpr[1]!=child_sp||
           depth>1024u||child_sp>frame_.base||frame_.base-child_sp>depth||(child_sp&7u)||
           !mapped(c,frame_)||c.inst_count<last_||c.inst_count-last_>ticks||
           frame_.size<8u)return false;
        for(auto s:e_.slots)if(int64_t(incoming_[1])+s.caller_offset==int64_t(frame_.base)+4)return false;
        for(unsigned i=0;i<shadow_.size();++i){
            const auto v=(i>=4u&&i<8u)?uint8_t(link_word>>(24u-8u*(i-4u))):shadow_[i];
            if(c.mmu.read8(frame_.base+i)!=v)return false;
        }
        return true;
    }
    bool nested_checkpoint_valid_=false;
    uint64_t nested_checkpoint_tick_=0,nested_checkpoint_age_=0;
    uint32_t nested_checkpoint_sp_=0,nested_checkpoint_link_=0,nested_checkpoint_depth_=0;
    PostStmScExpectation e_;const void* cpu_=nullptr;AllocatorRange frame_{};
    std::array<uint32_t,32> gp_{},incoming_{};std::array<uint32_t,8> gqr_{};
    std::vector<uint8_t> shadow_;
    uint32_t msr_=0,cr_=0,lr_=0,ctr_=0,xer_=0,srr0_=0,srr1_=0,next_=0,owner_=0;
    uint64_t last_=0,saved_=0;unsigned stage_=0,error_=0,visits_=0,stores_=0;
    bool initial_poll_=false,outer_entry_=false,root_entry_=false,entry_due_=false;
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    static bool volatile_reg(unsigned r){return r==0u||(r>=3u&&r<=12u);}
    bool store(uint32_t a,uint32_t v){
        if((a&3u)||!frame_.contains(a,4u)||stores_>=3u)return false;
        for(unsigned i=0;i<4;++i)shadow_[a-frame_.base+i]=uint8_t(v>>(24u-i*8u));
        ++stores_;return true;
    }
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
    template<class C>bool common(C& c,bool held)const{
        if(error_||!held||cpu_!=&c||!safe(c)||c.gpr!=gp_||c.gqr!=gqr_||c.msr!=msr_||
           pack(c)!=cr_||c.lr!=lr_||c.ctr!=ctr_||c.xer!=xer_||c.srr0!=srr0_||c.srr1!=srr1_||!mapped(c,frame_))return false;
        for(unsigned i=0;i<shadow_.size();++i)if(c.mmu.read8(frame_.base+i)!=shadow_[i])return false;
        return true;
    }
};
}
