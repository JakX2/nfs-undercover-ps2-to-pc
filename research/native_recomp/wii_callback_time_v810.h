#pragma once
#include "wii_postack_os_leaf_v703.h"
#include <array>
#include <cstdint>
#include <span>
namespace undercover::wii {
struct CallbackTimeExpectation {
    uint32_t callback,callback_end,resume,time_site,time_root;
    std::span<const uint32_t> continuation,system;
    std::array<PostAckLeafExpectation,3> leaves;
};
// Read-only continuation following a separately verified callback save.
// The private installer must authenticate every word and native edge.
// The original helper, not this observer, calculates the system offset.
class CallbackTimeWitness {
public:
    explicit CallbackTimeWitness(CallbackTimeExpectation e):e_(e),leaves_{
        PostAckOsLeaf(e.leaves[0]),PostAckOsLeaf(e.leaves[1]),PostAckOsLeaf(e.leaves[2])}{}
    unsigned stage()const{return stage_;}
    unsigned failure()const{return error_;}
    unsigned visits()const{return visits_;}
    unsigned time_visits()const{return time_visits_;}
    unsigned leaf_visits()const{return leaf_visits_;}
    unsigned polls()const{return polls_;}
    unsigned reads()const{return reads_;}
    unsigned cursor()const{return cursor_;}
    uint64_t timebase()const{return sample_;}
    template<class C>bool start(C& c,uint32_t pc,uint32_t w,bool device,bool prefix_verified){
        if(stage_||error_||!device||!prefix_verified||!safe(c)||pc!=e_.resume||c.pc!=pc||c.lr!=pc||
           !valid_range(e_.callback,e_.callback_end)||e_.callback_end-e_.callback>4096u||
           e_.resume<e_.callback||e_.time_site<e_.resume||e_.time_site>=e_.callback_end-4u||
           e_.continuation.size()!=(e_.time_site-e_.resume)/4u+2u||e_.continuation.size()>64u||
           e_.system.size()!=25u||!valid_range(e_.time_root,e_.time_root+100u)||
           !match(c,pc,w)||w!=e_.continuation.front()||c.inst_count>UINT64_MAX-256u)return fail(1);
        if(!direct(e_.time_site,e_.continuation[e_.continuation.size()-2u],e_.time_root))return fail(1);
        for(unsigned i=0;i<3;++i){
            const auto& l=e_.leaves[i];
            if(l.kind!=i+1u||l.site<e_.time_root||l.site>=e_.time_root+100u||
               (i&&l.site<=e_.leaves[i-1].site)||!valid_range(l.root,l.end)||
               l.end-l.root>64u||e_.system[(l.site-e_.time_root)/4u]!=l.branch||!direct(l.site,l.branch,l.root))
                return fail(1);
        }
        for(unsigned i=0;i<e_.continuation.size();++i)if(!match(c,e_.resume+4*i,e_.continuation[i]))return fail(1);
        for(unsigned i=0;i<e_.system.size();++i)if(!match(c,e_.time_root+4*i,e_.system[i]))return fail(1);
        cpu_=&c;msr_=c.msr;srr0_=c.srr0;srr1_=c.srr1;start_=last_=c.inst_count;next_=pc;stage_=1;
        return true;
    }
    template<class C>bool entry(C& c,uint32_t pc,bool device){
        if(!common(c,device)||!entry_due_||c.inst_count!=last_||c.pc!=pc)return fail(2);
        if(stage_==2){
            if(pc!=e_.time_root||c.lr!=e_.time_site+4u)return fail(2);
            stage_=3;
        }else if(stage_==3&&leaf_active_&&cursor_<3){
            if(!leaves_[cursor_].entry(pc,c))return fail(2);
        }else return fail(2);
        entry_due_=false;return true;
    }
    template<class C>bool before(C& c,uint32_t pc,uint32_t w,bool device){
        if(!common(c,device)||entry_due_||stage_<1||stage_>4||!match(c,pc,w)||
           c.inst_count-last_!=unsigned(visits_!=0)||++visits_>192u)return fail(3);
        last_=c.inst_count;
        if(pending_reg_<32u){
            if(c.gpr[pending_reg_]!=pending_value_)return fail(4);
            pending_reg_=32;
        }
        if(stage_==3&&leaf_active_){
            auto& l=leaves_[cursor_];
            if(l.stage()==3){
                if(!l.returned(c,pc))return fail(4);
                if(cursor_==1u&&(reads_<3u||!polls_||
                   ((uint64_t(c.gpr[3])<<32)|c.gpr[4])!=sample_))return fail(4);
                ++cursor_;leaf_active_=false;
            }else{
                if(!l.before(c,pc,w)||!memory(c,w))return fail(4);
                ++leaf_visits_;
                const unsigned xo=(w>>1)&1023u,spr=((w>>11)&31u)*32u+((w>>16)&31u);
                if(cursor_==1u&&w>>26==31u&&(xo==339u||xo==371u)&&(spr==268u||spr==269u)){
                    const uint64_t val=c.read_timebase();
                    ++reads_;pending_reg_=(w>>21)&31u;
                    pending_value_=uint32_t(spr==269u?val>>32:val);
                    if(spr==268u)sample_=val;
                }
                return true;
            }
        }
        if(pc!=next_)return fail(3);
        if(stage_==4){
            if(pc!=e_.time_site+4u||c.pc!=pc||c.lr!=pc||w!=e_.continuation.back()||
               cursor_!=3u||time_visits_!=25u||!abi(c)||visits_!=callback_visits_+time_visits_+leaf_visits_+1u)
                return fail(5);
            stage_=5;return true;
        }
        if(!memory(c,w))return fail(6);
        next_=pc+4u;
        if(stage_==1){
            if(pc<e_.resume||pc>e_.time_site||w!=e_.continuation[(pc-e_.resume)/4u])return fail(3);
            ++callback_visits_;
            if(pc==e_.time_site){
                gp_=c.gpr;cr_=pack(c)&0x00fff000u;
                stage_=2;entry_due_=true;next_=e_.time_root;return true;
            }
            const unsigned op=w>>26;
            if(op==16u||op==18u){
                if(w&3u)return fail(6);
                const uint32_t dst=target(pc,w);
                if(dst<=pc||dst>e_.time_site)return fail(6);
                if(op==18u||taken(c,w))next_=dst;
            }else if(forbidden(w))return fail(6);
            return next_<=e_.time_site?true:fail(6);
        }
        if(stage_!=3||pc<e_.time_root||pc>=e_.time_root+100u||
           w!=e_.system[(pc-e_.time_root)/4u]||++time_visits_>25u)return fail(3);
        if(cursor_<3&&pc==e_.leaves[cursor_].site){
            if(!leaves_[cursor_].start(c,pc,w))return fail(4);
            leaf_active_=true;entry_due_=true;next_=pc+4u;return true;
        }
        if(w==0x4e800020u){
            if(cursor_!=3u||time_visits_!=25u||c.lr!=e_.time_site+4u)return fail(5);
            stage_=4;next_=e_.time_site+4u;return true;
        }
        if(w>>26==16u||w>>26==18u||forbidden(w))return fail(6);
        return next_<e_.time_root+100u?true:fail(6);
    }
    template<class C>bool poll(C& c,bool device){
        if(!common(c,device)||stage_!=3||!leaf_active_||cursor_!=1u||
           c.inst_count!=last_||!leaves_[1].poll(c))return fail(7);
        ++polls_;return true;
    }
private:
    CallbackTimeExpectation e_;std::array<PostAckOsLeaf,3> leaves_;
    const void* cpu_=nullptr;
    unsigned stage_=0,error_=0,cursor_=0,visits_=0,callback_visits_=0,time_visits_=0,leaf_visits_=0,polls_=0,reads_=0,pending_reg_=32;
    uint32_t pending_value_=0,msr_=0,srr0_=0,srr1_=0,next_=0,cr_=0;
    uint64_t start_=0,last_=0,sample_=0;
    std::array<uint32_t,32> gp_{};
    bool entry_due_=false,leaf_active_=false;
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    static bool valid_range(uint32_t a,uint32_t b){return !(a&3u)&&!(b&3u)&&a>=0x80000000u&&b>a&&b<=0x81800000u;}
    template<class C>static bool match(C& c,uint32_t a,uint32_t w){return a<=0x817ffffcu&&valid_range(a,a+4u)&&c.mmu.get_ptr(a)&&c.mmu.get_ptr(a+3u)&&c.mmu.read32(a)==w;}
    template<class C>static bool safe(C& c){return c.is_running&&!c.in_callback&&!c.dispatch_saved_ctx&&!(c.msr&0x8000u);}
    template<class C>bool common(C& c,bool device)const{return !error_&&device&&cpu_==&c&&safe(c)&&c.msr==msr_&&c.srr0==srr0_&&c.srr1==srr1_&&c.inst_count>=start_&&c.inst_count-start_<=256u;}
    template<class C>static uint32_t pack(C& c){uint32_t v=0;for(const auto& f:c.cr)v=(v<<4)|(unsigned(f.lt)<<3)|(unsigned(f.gt)<<2)|(unsigned(f.eq)<<1)|unsigned(f.so);return v;}
    template<class C>bool abi(C& c)const{
        if(c.gpr[1]!=gp_[1]||c.gpr[2]!=gp_[2]||c.gpr[13]!=gp_[13]||(pack(c)&0x00fff000u)!=cr_)return false;
        for(unsigned i=14;i<32;++i)if(c.gpr[i]!=gp_[i])return false;
        return true;
    }
    static uint32_t target(uint32_t pc,uint32_t w){const bool s=w>>26==16u;const uint32_t b=s?0xfffcu:0x03fffffcu,v=s?0x8000u:0x02000000u;return pc+(((w&b)^v)-v);}
    static bool direct(uint32_t pc,uint32_t w,uint32_t dst){return w>>26==18u&&(w&3u)==1u&&target(pc,w)==dst;}
    static bool forbidden(uint32_t w){const unsigned op=w>>26,xo=(w>>1)&1023u;return op==17u||(op==31u&&xo==146u)||(op==19u&&(xo==16u||xo==50u||xo==528u));}
    template<class C>static bool taken(C& c,uint32_t w){
        const unsigned bo=(w>>21)&31u,bi=(w>>16)&31u;
        return ((bo&4u)||(((c.ctr-1u)!=0u)^bool(bo&2u)))&&((bo&16u)||bool((pack(c)>>(31u-bi))&1u)==bool(bo&8u));
    }
    template<class C>bool memory(C& c,uint32_t w)const{
        unsigned op=w>>26,xo=(w>>1)&1023u,ra=(w>>16)&31u,rb=(w>>11)&31u,width=0;
        bool write=false;uint32_t addr=0;
        if(op>=32u&&op<=47u){
            addr=(ra?c.gpr[ra]:0u)+((w&0xffffu)^0x8000u)-0x8000u;
            width=op==34u||op==35u||op==38u||op==39u?1u:op>=40u&&op<=45u?2u:4u;
            if(op==46u||op==47u)width=4u*(32u-((w>>21)&31u));
            write=op==36u||op==37u||op==38u||op==39u||op==44u||op==45u||op==47u;
        }else if(op==31u){
            switch(xo){
            case 23:case 55:case 534:width=4;break;
            case 87:case 119:width=1;break;
            case 279:case 311:case 343:case 375:case 790:width=2;break;
            case 151:case 183:case 662:width=4;write=true;break;
            case 215:case 247:width=1;write=true;break;
            case 407:case 439:case 918:width=2;write=true;break;
            // Exact original integer instructions are audited privately.
            // Refuse unmodelled string, atomic, cache and floating accesses.
            case 20:case 150:case 533:case 597:case 661:case 725:case 535:case 567:case 599:case 631:case 663:case 695:case 727:case 759:case 983:
            case 54:case 86:case 246:case 278:case 470:case 982:case 1014:return false;
            default:break;
            }
            addr=(ra?c.gpr[ra]:0u)+c.gpr[rb];
        }else if(op>=48u||op==4u)return false;
        if(!width)return true;
        if(addr<0x80000000u||uint64_t(addr)+width>0x81800000ull||(width>1u&&(addr&(width==2u?1u:3u))))return false;
        for(unsigned i=0;i<width;++i)if(!c.mmu.get_ptr(addr+i))return false;
        if(write){
            auto hit=[&](uint32_t a,uint32_t b){return uint64_t(addr)<b&&uint64_t(a)<uint64_t(addr)+width;};
            if(hit(e_.callback,e_.callback_end)||hit(e_.time_root,e_.time_root+100u))return false;
            for(const auto& l:e_.leaves)if(hit(l.root,l.end))return false;
        }
        return true;
    }
};
}
