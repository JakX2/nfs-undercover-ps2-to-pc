#pragma once
#include "wii_ipc_dispatch_execution.h"
#include <bit>
namespace undercover::wii {
struct StmFinalSlot {int32_t caller_offset;uint32_t reg;}; // reg 32 = saved LR
struct StmFinalExpectation {
    uint32_t root,start,caller,caller_word,frame_size,store_pc,store_address,store_reg;
    AllocatorRange object;
    std::span<const StmFinalSlot> slots;
    std::span<const IpcDispatchWord> words;
};
// Original STM final epilogue. Observe the actual native load/store/return
// operations and their values, never perform guest writes or an HLE return.
class StmFinalReturnWitness {
public:
    explicit StmFinalReturnWitness(StmFinalExpectation e):e_(e){}
    unsigned stage()const{return stage_;}
    unsigned failure()const{return error_;}
    unsigned visits()const{return visits_;}
    unsigned loads()const{return loads_;}
    unsigned stores()const{return stores_;}
    template<class C>static uint32_t abi_cr(C& c){return pack(c)&0x00fff000u;}
    template<class C>bool begin(C& c,const std::array<uint32_t,32>& caller_gp,uint32_t caller_cr,bool held){
        if(stage_||error_||!held||!safe(c)||!(c.msr&0x8000u)||c.pc!=e_.start||c.lr!=e_.start||
           !known(c,e_.start)||!word(c,e_.caller,e_.caller_word)||!known(c,e_.store_pc)||
           e_.frame_size<8u||e_.frame_size>256u||(e_.frame_size&7u)||
           uint64_t(c.gpr[1])+e_.frame_size!=caller_gp[1]||(caller_gp[1]&7u)||
           e_.slots.empty()||e_.slots.size()>19u||e_.words.empty()||e_.words.size()>32u||
           e_.object.size<4u||e_.object.size>4096u||!e_.object.contains(e_.store_address,4u)||
           (e_.store_address&3u)||e_.store_reg>31u)return fail(1);
        frame_={c.gpr[1],e_.frame_size+8u};
        if(!mapped(c,frame_)||!mapped(c,e_.object)||overlap(frame_,e_.object)||
           c.mmu.read32(frame_.base)!=caller_gp[1]||abi_cr(c)!=caller_cr)return fail(1);
        uint64_t reg_mask=0;
        for(auto slot:e_.slots){
            const int64_t a=int64_t(caller_gp[1])+slot.caller_offset;
            if((slot.reg<14u||slot.reg>32u)||slot.caller_offset<-int32_t(e_.frame_size)+4||
               slot.caller_offset>4||a<0||a>0xffffffffll||(a&3)||
               !frame_.contains(uint32_t(a),4u)||(reg_mask&(uint64_t(1)<<slot.reg))||
               c.mmu.read32(uint32_t(a))!=(slot.reg==32u?e_.caller:caller_gp[slot.reg]))return fail(1);
            if(std::count_if(e_.slots.begin(),e_.slots.end(),[&](auto x){return x.caller_offset==slot.caller_offset;})!=1)return fail(1);
            reg_mask|=uint64_t(1)<<slot.reg;
        }
        if(!(reg_mask&(uint64_t(1)<<32)))return fail(1);
        if(c.gpr[2]!=caller_gp[2]||c.gpr[13]!=caller_gp[13])return fail(1);
        for(unsigned i=14;i<32;++i)if(!(reg_mask&(uint64_t(1)<<i))&&c.gpr[i]!=caller_gp[i])return fail(1);
        for(unsigned i=0;i<frame_.size;++i)stack_.push_back(c.mmu.read8(frame_.base+i));
        for(unsigned i=0;i<e_.object.size;++i)object_.push_back(c.mmu.read8(e_.object.base+i));
        cpu_=&c;caller_=caller_gp;caller_cr_=caller_cr;gp_=c.gpr;gqr_=c.gqr;msr_=c.msr;cr_=pack(c);
        lr_=c.lr;ctr_=c.ctr;xer_=c.xer;srr0_=c.srr0;srr1_=c.srr1;
        save_mask_=reg_mask;last_=c.inst_count;next_=e_.start;stage_=1;return true;
    }
    template<class C>bool entry(C& c,uint32_t pc,bool held){
        if(stage_!=1u||!common(c,held)||visits_||!initial_poll_||entry_seen_||
           pc!=e_.start||c.pc!=pc||c.inst_count-last_!=1u)return fail(2);
        entry_seen_=true;return true;
    }
    template<class C>bool before(C& c,uint32_t pc,uint32_t w,bool held){
        if(stage_!=1u||!common(c,held)||return_due_||pc!=next_||
           c.inst_count-last_!=(visits_?1u:2u)||(!visits_&&(!initial_poll_||c.pc!=pc))||
           !known(c,pc,w)||++visits_>32u)return fail(2);
        last_=c.inst_count;next_=pc+4u;
        const unsigned op=w>>26,rs=(w>>21)&31u,ra=(w>>16)&31u,rb=(w>>11)&31u,xo=(w>>1)&1023u;
        const int32_t imm=int32_t((w&0xffffu)^0x8000u)-0x8000;
        if(w==0x4e800020u){
            if(lr_!=e_.caller||restored_mask_!=save_mask_||stores_!=1u||gp_[1]!=caller_[1]||
               !abi(c)||!lr_loaded_)return fail(3);
            return_due_=true;next_=e_.caller;return true;
        }
        if(op==36u){
            const int64_t a=int64_t(ra?gp_[ra]:0u)+imm;
            if(pc!=e_.store_pc||stores_||rs!=e_.store_reg||(ra!=2u&&ra!=13u)||
               a!=e_.store_address||gp_[rs]!=1u)return fail(4);
            for(unsigned i=0;i<4;++i)object_[e_.store_address-e_.object.base+i]=uint8_t(1u>>(24u-i*8u));
            ++stores_;
        }else if(op==32u||op==46u){
            if(ra!=1u)return fail(5);
            const auto base=int64_t(gp_[1])+imm;
            for(unsigned n=0;n<(op==46u?32u-rs:1u);++n){
                const auto a=base+4u*n;const auto offset=a-int64_t(caller_[1]);const unsigned dest=rs+n;
                auto it=std::find_if(e_.slots.begin(),e_.slots.end(),[&](auto x){return x.caller_offset==offset;});
                if(it==e_.slots.end()||(restored_mask_&(uint64_t(1)<<it->reg))||
                   (it->reg==32u?!volatile_reg(dest):dest!=it->reg)||
                   a<0||a>0xffffffffll||!frame_.contains(uint32_t(a),4u))return fail(5);
                gp_[dest]=c.mmu.read32(uint32_t(a));
                restored_mask_|=uint64_t(1)<<it->reg;++loads_;
                if(it->reg==32u){lr_source_=dest;lr_loaded_=true;}
            }
        }else if(op==31u&&xo==467u&&(ra|(rb<<5))==8u){
            if(!lr_loaded_||lr_source_!=rs||gp_[rs]!=e_.caller||lr_==e_.caller)return fail(3);
            lr_=gp_[rs];
        }else if(op==14u&&rs==ra==1u){
            if(gp_[1]!=frame_.base||imm!=int32_t(e_.frame_size))return fail(3);
            gp_[1]=caller_[1];
        }else if((op==14u||op==15u)&&volatile_reg(rs)){
            gp_[rs]=(ra?gp_[ra]:0u)+(op==15u?(uint32_t(imm)<<16):uint32_t(imm));
            if(lr_loaded_&&rs==lr_source_&&lr_!=e_.caller)return fail(3);
        }else if(op==24u&&volatile_reg(ra)){
            gp_[ra]=gp_[rs]|(w&0xffffu);
            if(lr_loaded_&&ra==lr_source_&&lr_!=e_.caller)return fail(3);
        }else if(op==31u&&xo==444u&&!(w&1u)&&volatile_reg(ra)){
            gp_[ra]=gp_[rs]|gp_[rb];
            if(lr_loaded_&&ra==lr_source_&&lr_!=e_.caller)return fail(3);
        }else if(op==21u&&!(w&1u)&&volatile_reg(ra)){
            gp_[ra]=std::rotl(gp_[rs],int(rb))&mask((w>>6)&31u,(w>>1)&31u);
            if(lr_loaded_&&ra==lr_source_&&lr_!=e_.caller)return fail(3);
        }else return fail(3);
        if(!known(c,next_))return fail(3);
        return true;
    }
    template<class C>bool poll(C& c,bool held){
        if(stage_!=1u||!common(c,held)||c.inst_count!=last_)return fail(6);
        if(!visits_&&!initial_poll_&&c.pc==e_.start){initial_poll_=true;return true;}
        if(!return_due_||c.pc!=e_.caller||!word(c,e_.caller,e_.caller_word)||!abi(c))return fail(6);
        stage_=2;return true;
    }
    template<class C>bool reached(C& c,bool held)const{
        return stage_==2u&&return_due_&&common(c,held)&&abi(c)&&c.inst_count==last_&&
            c.pc==e_.caller&&word(c,e_.caller,e_.caller_word);
    }
private:
    StmFinalExpectation e_;const void* cpu_=nullptr;AllocatorRange frame_{};
    std::array<uint32_t,32> gp_{},caller_{};std::array<uint32_t,8> gqr_{};
    std::vector<uint8_t> stack_,object_;
    uint32_t caller_cr_=0,cr_=0,msr_=0,lr_=0,ctr_=0,xer_=0,srr0_=0,srr1_=0,next_=0,lr_source_=0;
    uint64_t last_=0,save_mask_=0,restored_mask_=0;unsigned stage_=0,error_=0,visits_=0,loads_=0,stores_=0;
    bool initial_poll_=false,entry_seen_=false,return_due_=false,lr_loaded_=false;
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    static bool volatile_reg(unsigned r){return r==0u||(r>=3u&&r<=12u);}
    static uint32_t mask(unsigned mb,unsigned me){
        uint32_t out=0;for(unsigned n=mb;;n=(n+1u)&31u){out|=1u<<(31u-n);if(n==me)break;}return out;
    }
    static bool overlap(AllocatorRange a,AllocatorRange b){return a.size&&b.size&&a.base<b.end()&&b.base<a.end();}
    template<class C>static bool safe(C& c){return c.is_running&&!c.in_callback&&!c.dispatch_saved_ctx;}
    template<class C>static uint32_t pack(C& c){uint32_t v=0;for(auto f:c.cr)v=(v<<4)|(unsigned(f.lt)<<3)|(unsigned(f.gt)<<2)|(unsigned(f.eq)<<1)|unsigned(f.so);return v;}
    template<class C>bool abi(C& c)const{
        if(c.gpr[1]!=caller_[1]||c.gpr[2]!=caller_[2]||abi_cr(c)!=caller_cr_)return false;
        for(unsigned i=13;i<32;++i)if(c.gpr[i]!=caller_[i])return false;
        return true;
    }
    template<class C>bool common(C& c,bool held)const{
        if(error_||!held||cpu_!=&c||!safe(c)||c.gpr!=gp_||c.gqr!=gqr_||c.msr!=msr_||
           pack(c)!=cr_||c.lr!=lr_||c.ctr!=ctr_||c.xer!=xer_||c.srr0!=srr0_||c.srr1!=srr1_||
           !mapped(c,frame_)||!mapped(c,e_.object))return false;
        for(unsigned i=0;i<stack_.size();++i)if(c.mmu.read8(frame_.base+i)!=stack_[i])return false;
        for(unsigned i=0;i<object_.size();++i)if(c.mmu.read8(e_.object.base+i)!=object_[i])return false;
        return true;
    }
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
};
}
