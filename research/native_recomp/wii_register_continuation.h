#pragma once
#include "wii_post_stm_sc_formatter.h"
#include <bit>
namespace undercover::wii {
// Read-only observer of an already-established frame's register-only path.
// No guest state is changed by the observer. The caller supplies its frame
// and device continuity predicate at every boundary.
struct RegisterContinuationSpec {
    uint32_t owner,start,target,target_word;
    uint32_t saved_mask;
    std::span<const IpcDispatchWord> path;
};
class RegisterContinuationWitness {
public:
    explicit RegisterContinuationWitness(RegisterContinuationSpec s):s_(s){}
    unsigned stage()const{return stage_;}
    unsigned failure()const{return error_;}
    unsigned visits()const{return visits_;}
    unsigned polls()const{return polls_;}
    template<class C>bool begin(C& c,bool held){
        if(stage_||error_||!held||!safe(c)||!(c.msr&0x8000u)||c.pc!=s_.start||c.lr!=s_.start||
           s_.path.empty()||s_.path.size()>128||s_.path.front().pc!=s_.start||
           (s_.saved_mask&0x3fffu)||!word(c,s_.target,s_.target_word))return fail(1);
        for(auto x:s_.path)if(x.owner!=s_.owner||!word(c,x.pc,x.word))return fail(1);
        auto tail=s_.path.back();
        if(tail.word>>26!=18u||(tail.word&3u)!=1u||branch_target(tail.pc,tail.word)!=s_.target)return fail(1);
        cpu_=&c;gp_=c.gpr;gqr_=c.gqr;cr_=pack(c);lr_=c.lr;ctr_=c.ctr;xer_=c.xer;msr_=c.msr;
        srr0_=c.srr0;srr1_=c.srr1;last_=c.inst_count;stage_=1;return true;
    }
    template<class C>bool poll(C& c,bool held){
        if(stage_!=1||c.inst_count!=last_)return fail(2);
        if(!visits_&&!initial_poll_&&c.pc==s_.start&&same(c,held)){
            initial_poll_=true;return true;
        }
        if(!pending_poll_||c.pc!=poll_pc_||!same(c,held,true))return fail(2);
        pending_poll_=false;++polls_;return true;
    }
    template<class C>bool entry(C& c,uint32_t pc,bool held){
        if(stage_!=1||pending_poll_||!same(c,held)||c.pc!=pc)return fail(3);
        if(!visits_){
            if(!initial_poll_||entry_seen_||pc!=s_.start||c.inst_count-last_!=1)return fail(3);
            entry_seen_=true;return true;
        }
        if(!call_due_||visits_!=s_.path.size()||pc!=s_.target||c.inst_count!=last_||!word(c,pc,s_.target_word))return fail(3);
        stage_=2;return true;
    }
    template<class C>bool before(C& c,uint32_t pc,uint32_t w,bool held){
        if(stage_!=1||pending_poll_||call_due_||!same(c,held)||visits_>=s_.path.size()||
           c.inst_count-last_!=(visits_?1u:2u)||(!visits_&&(!initial_poll_||!entry_seen_||c.pc!=pc))||
           s_.path[visits_].pc!=pc||s_.path[visits_].word!=w||!word(c,pc,w))return fail(4);
        ++visits_;last_=c.inst_count;uint32_t next=pc+4u;
        const unsigned op=w>>26,rs=(w>>21)&31u,ra=(w>>16)&31u,rb=(w>>11)&31u,xo=(w>>1)&1023u;
        const uint32_t imm=uint32_t(int32_t((w&0xffffu)^0x8000u)-0x8000);
        if(op==14u||op==15u){
            if(!writable(rs))return fail(5);
            gp_[rs]=(ra?gp_[ra]:0u)+(op==15u?imm<<16u:imm);
        }else if(op==10u||op==11u){
            if(w&0x00200000u)return fail(5);
            const uint32_t a=gp_[ra],b=op==10u?w&0xffffu:imm;
            compare((w>>23)&7u,op==10u?a<b:std::bit_cast<int32_t>(a)<std::bit_cast<int32_t>(b),a==b);
        }else if(op==31u&&(xo==0u||xo==32u)){
            if(w&0x00200000u)return fail(5);
            const uint32_t a=gp_[ra],b=gp_[rb];
            compare((w>>23)&7u,xo==32u?a<b:std::bit_cast<int32_t>(a)<std::bit_cast<int32_t>(b),a==b);
        }else if(op>=24u&&op<=29u){
            if(!writable(ra))return fail(5);
            const uint32_t n=(w&0xffffu)<<((op&1u)?16u:0u);
            gp_[ra]=op<26u?gp_[rs]|n:op<28u?gp_[rs]^n:gp_[rs]&n;
            if(op>=28u)record(gp_[ra]);
        }else if(op==20u||op==21u||op==23u){
            if(!writable(ra))return fail(5);
            const unsigned sh=op==23u?gp_[rb]&31u:rb;
            const auto m=mask((w>>6)&31u,(w>>1)&31u),v=std::rotl(gp_[rs],int(sh))&m;
            gp_[ra]=op==20u?(gp_[ra]&~m)|v:v;if(w&1u)record(gp_[ra]);
        }else if(op==31u&&(xo==444u||xo==28u||xo==316u)){
            if(!writable(ra))return fail(5);
            const auto a=gp_[rs],b=gp_[rb];gp_[ra]=xo==444u?a|b:xo==28u?a&b:a^b;
            if(w&1u)record(gp_[ra]);
        }else if(op==31u&&(xo==922u||xo==954u)){
            if(!writable(ra))return fail(5);
            const uint32_t m=xo==922u?0xffffu:0xffu,t=xo==922u?0x8000u:0x80u;
            gp_[ra]=((gp_[rs]&m)^t)-t;if(w&1u)record(gp_[ra]);
        }else if(op==31u&&(xo==266u||xo==40u)){
            if(!writable(rs))return fail(5);
            gp_[rs]=xo==266u?gp_[ra]+gp_[rb]:gp_[rb]-gp_[ra];if(w&1u)record(gp_[rs]);
        }else if(op==31u&&xo==339u&&(ra|(rb<<5))==8u){
            if(!writable(rs))return fail(5);
            gp_[rs]=lr_;
        }else if(op==31u&&xo==467u&&(ra|(rb<<5))==9u)ctr_=gp_[rs];
        else if(op==18u&&(w&3u)==1u){
            if(visits_!=s_.path.size()||branch_target(pc,w)!=s_.target)return fail(5);
            lr_=pc+4u;call_due_=true;return true;
        }else if(op==16u||op==18u){
            if(w&3u)return fail(5);
            const auto dst=branch_target(pc,w);
            // The upstream emitter polls before evaluating local backedges.
            if(dst<=pc&&dst>=s_.owner){
                pending_poll_=true;poll_pc_=pc;poll_ctr_=ctr_;
            }
            const unsigned bo=(w>>21)&31u,bi=(w>>16)&31u;bool ct=true;
            if(op==16u&&!(bo&4u)){--ctr_;ct=bool(ctr_)!=bool(bo&2u);}
            if(op==18u||(ct&&((bo&16u)||bool((cr_>>(31u-bi))&1u)==bool(bo&8u))))next=dst;
        }else return fail(5); // No memory, system, floating-point or indirect operations.
        if(visits_>=s_.path.size()||s_.path[visits_].pc!=next)return fail(5);
        return true;
    }
    template<class C>bool reached(C& c,bool held)const{
        return stage_==2&&call_due_&&!pending_poll_&&same(c,held)&&c.pc==s_.target&&c.inst_count==last_;
    }
private:
    RegisterContinuationSpec s_;const void* cpu_=nullptr;
    std::array<uint32_t,32> gp_{};std::array<uint32_t,8> gqr_{};
    uint32_t lr_=0,ctr_=0,xer_=0,msr_=0,cr_=0,srr0_=0,srr1_=0,poll_pc_=0,poll_ctr_=0;
    uint64_t last_=0;unsigned stage_=0,error_=0,visits_=0,polls_=0;
    bool initial_poll_=false,entry_seen_=false,pending_poll_=false,call_due_=false;
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    bool writable(unsigned r)const{return r==0u||(r>=3u&&r<=12u)||(r>=14u&&(s_.saved_mask&(uint32_t(1)<<r)));}
    static uint32_t mask(unsigned mb,unsigned me){
        uint32_t v=0;for(unsigned i=0;i<32;++i)if(mb<=me?(i>=mb&&i<=me):(i>=mb||i<=me))v|=1u<<(31-i);return v;
    }
    static uint32_t branch_target(uint32_t pc,uint32_t w){
        const bool bc=w>>26==16u;const uint32_t m=bc?0xfffcu:0x03fffffcu,s=bc?0x8000u:0x02000000u;
        return pc+(((w&m)^s)-s);
    }
    void compare(unsigned f,bool lt,bool eq){
        const unsigned sh=28u-4u*f;
        cr_=(cr_&~(15u<<sh))|(((lt?8u:eq?2u:4u)|((xer_>>31)&1u))<<sh);
    }
    void record(uint32_t v){compare(0u,(v&0x80000000u)!=0u,v==0u);}
    template<class C>static bool safe(C& c){return c.is_running&&!c.in_callback&&!c.dispatch_saved_ctx;}
    template<class C>static uint32_t pack(C& c){
        uint32_t v=0;for(auto f:c.cr)v=(v<<4)|(unsigned(f.lt)<<3)|(unsigned(f.gt)<<2)|(unsigned(f.eq)<<1)|unsigned(f.so);return v;
    }
    template<class C>static bool word(C& c,uint32_t a,uint32_t w){
        if((a&3u)||a<0x80000000u||uint64_t(a)+4>0x81800000ull)return false;
        auto p=c.mmu.get_ptr(a),q=c.mmu.get_ptr(a+3u);
        return p&&q&&reinterpret_cast<uintptr_t>(q)==reinterpret_cast<uintptr_t>(p)+3u&&c.mmu.read32(a)==w;
    }
    template<class C>bool same(C& c,bool held,bool pre_branch=false)const{
        return !error_&&held&&cpu_==&c&&safe(c)&&c.gpr==gp_&&c.gqr==gqr_&&c.lr==lr_&&
            c.ctr==(pre_branch?poll_ctr_:ctr_)&&c.xer==xer_&&c.msr==msr_&&pack(c)==cr_&&c.srr0==srr0_&&c.srr1==srr1_;
    }
};
}
