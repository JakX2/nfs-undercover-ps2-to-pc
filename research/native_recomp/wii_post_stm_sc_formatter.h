#pragma once
#include "wii_post_stm_sc_report_helper.h"
#include <bit>
#include <optional>
namespace undercover::wii {
struct ScFormatterAccess {
    uint32_t pc,width;
    int64_t address; // caller-relative for stack sites; absolute otherwise
    bool stack,write;
    std::optional<uint32_t> expected_value{}; // independently authenticated raw load value
};
struct ScFormatterBoundary {uint32_t address=0,width=0;};
struct ScFormatterExpectation {
    uint32_t root,entry_lr,target,target_word,frame_size;
    std::span<const IpcDispatchWord> path;
    std::span<const ScFormatterAccess> accesses;
    std::span<const StmFinalSlot> slots;
    ScFormatterBoundary boundary{}; // optional local load that must not execute
};
class ScFormatterWitness {
public:
    explicit ScFormatterWitness(ScFormatterExpectation e):e_(e){}
    unsigned stage()const{return stage_;}unsigned failure()const{return error_;}
    unsigned visits()const{return visits_;}unsigned back_polls()const{return back_polls_;}unsigned loads()const{return loads_;}unsigned stores()const{return stores_;}
    unsigned authenticated_loads()const{return authenticated_loads_;}
    uint32_t expected_sp()const{return gp_[1];}
    uint32_t linkage_word()const{
        uint32_t v=0;for(unsigned i=0;i<4;++i)v=(v<<8)|shadow_[e_.frame_size+4+i];return v;
    }
    template<class C>bool begin(C& c,bool held){
        if(stage_||error_||!held||!safe(c)||!(c.msr&0x8000u)||c.pc!=e_.root||c.lr!=e_.entry_lr||
           e_.frame_size<32u||e_.frame_size>704u||(e_.frame_size&7u)||(c.gpr[1]&7u)||
           c.gpr[1]<0x80000000u+e_.frame_size||e_.path.empty()||e_.path.size()>64u||
           e_.accesses.size()>(e_.boundary.width?24u:8u)||e_.slots.empty()||e_.slots.size()>19u||
           e_.path.front().pc!=e_.root||!word(c,e_.target,e_.target_word))return fail(1);
        frame_={c.gpr[1]-e_.frame_size,e_.frame_size+8u};
        if(!mapped(c,frame_))return fail(1);
        for(auto x:e_.path)if(x.owner!=e_.root||!word(c,x.pc,x.word)||
            std::count_if(e_.path.begin(),e_.path.end(),[&](auto y){return x.pc==y.pc;})!=1)return fail(1);
        for(auto s:e_.slots){
            const auto at=int64_t(c.gpr[1])+s.caller_offset;
            if(s.reg<14u||s.reg>32u||at<0||at>0xffffffffll||(at&3)||!frame_.contains(uint32_t(at),4u)||
               (s.reg==32u)!=(s.caller_offset==4)||uint32_t(at)==frame_.base||
               std::count_if(e_.slots.begin(),e_.slots.end(),[&](auto x){return x.reg==s.reg||x.caller_offset==s.caller_offset;})!=1)return fail(1);
        }
        if(std::count_if(e_.slots.begin(),e_.slots.end(),[](auto s){return s.reg==32u;})!=1)return fail(1);
        if(e_.boundary.width){
            const auto form=decode_load(e_.target_word);
            const unsigned n=form.width;
            if(!n||n!=e_.boundary.width||
               e_.boundary.address%n||!mapped(c,{e_.boundary.address,n})||e_.target<e_.root||
               std::any_of(e_.path.begin(),e_.path.end(),[&](auto x){return x.pc==e_.target;}))return fail(1);
        }
        for(auto a:e_.accesses)if(!a.width||a.width>128u||(a.write&&!a.stack)||
            (a.expected_value&&(a.write||(a.width!=1u&&a.width!=2u&&a.width!=4u)))||
            std::count_if(e_.path.begin(),e_.path.end(),[&](auto x){return x.pc==a.pc;})!=1||
            std::count_if(e_.accesses.begin(),e_.accesses.end(),[&](auto x){return x.pc==a.pc;})!=1)return fail(1);
        for(unsigned i=0;i<frame_.size;++i)shadow_.push_back(c.mmu.read8(frame_.base+i));
        written_.resize(frame_.size);cpu_=&c;gp_=incoming_=c.gpr;gqr_=c.gqr;msr_=c.msr;
        cr_=pack(c);lr_=c.lr;ctr_=c.ctr;xer_=c.xer;srr0_=c.srr0;srr1_=c.srr1;last_=c.inst_count;stage_=1;return true;
    }
    template<class C>bool poll(C& c,bool held){
        if(stage_!=1u||c.inst_count!=last_)return fail(2);
        if(!visits_&&!initial_poll_&&c.pc==e_.root&&common(c,held)){
            initial_poll_=true;return true;
        }
        // NWiiRecomp polls at the source PC of a local backward branch
        // after its instruction tick, but BEFORE CTR decrement or branch.
        if(!back_poll_due_||c.pc!=poll_pc_||!common(c,held,true))return fail(2);
        back_poll_due_=false;++back_polls_;return true;
    }
    template<class C>bool entry(C& c,uint32_t pc,bool held){
        if(stage_!=1u||back_poll_due_||!common(c,held)||c.pc!=pc)return fail(3);
        if(!visits_){
            if(!initial_poll_||entry_seen_||pc!=e_.root||c.inst_count-last_!=1u)return fail(3);
            entry_seen_=true;return true;
        }
        if(e_.boundary.width||!due_||pc!=e_.target||c.inst_count!=last_||!word(c,pc,e_.target_word)||!abi(c))return fail(3);
        stage_=2;return true;
    }
    template<class C>bool before(C& c,uint32_t pc,uint32_t w,bool held){
        if(stage_!=1u||!common(c,held)||due_||back_poll_due_||visits_>=e_.path.size()||
           c.inst_count-last_!=(visits_?1u:2u)||(!visits_&&(!initial_poll_||!entry_seen_||c.pc!=pc))||
           e_.path[visits_].pc!=pc||e_.path[visits_].word!=w||!word(c,pc,w))return fail(4);
        ++visits_;last_=c.inst_count;uint32_t next=pc+4u;
        const unsigned op=w>>26,rs=(w>>21)&31u,ra=(w>>16)&31u,rb=(w>>11)&31u,xo=(w>>1)&1023u;
        const uint32_t imm=uint32_t(int32_t((w&0xffffu)^0x8000u)-0x8000);
        const uint32_t ea=(ra?gp_[ra]:0u)+imm;
        if(op==37u&&rs==1u&&ra==1u){
            if(stores_||gp_[1]!=incoming_[1]||ea!=frame_.base||!access(pc,ea,4,true)||!store(ea,4,gp_[1]))return fail(5);
            ++stores_;gp_[1]=ea;
        }else if(op==36u||op==38u||op==44u||op==47u||op==37u||op==39u||op==45u){
            const unsigned n=op==36u||op==37u||op==47u?4u:op==38u||op==39u?1u:2u,count=op==47u?32u-rs:1u;
            if(gp_[1]!=frame_.base||!access(pc,ea,n*count,true))return fail(5);
            for(unsigned i=0;i<count;++i)if(!store(ea+n*i,n,gp_[rs+i]))return fail(5);
            ++stores_;
            if(op==37u||op==39u||op==45u){if(!ra||ra==1u)return fail(5);gp_[ra]=ea;}
        }else if(op==31u&&(xo==151u||xo==183u||xo==215u||xo==247u||xo==407u||xo==439u)){
            const unsigned n=xo==151u||xo==183u?4u:xo==215u||xo==247u?1u:2u;
            const uint32_t a=(ra?gp_[ra]:0u)+gp_[rb];
            if(gp_[1]!=frame_.base||!access(pc,a,n,true)||!store(a,n,gp_[rs]))return fail(5);
            ++stores_;
            if(xo==183u||xo==247u||xo==439u){if(!ra||ra==1u)return fail(5);gp_[ra]=a;}
        }else if(const auto form=decode_load(w);form.width){
            const unsigned n=form.width;
            const uint32_t a=(ra?gp_[ra]:0u)+(form.indexed?gp_[rb]:imm);
            if(!access(pc,a,n,false)||!mapped(c,{a,n})||(a%n))return fail(5);
            uint32_t v=0;for(unsigned i=0;i<n;++i)v=(v<<8)|c.mmu.read8(a+i);
            const auto site=std::find_if(e_.accesses.begin(),e_.accesses.end(),[&](auto x){return x.pc==pc;});
            if(site->expected_value){
                if(v!=*site->expected_value)return fail(5);
                ++authenticated_loads_;
            }
            gp_[rs]=form.sign&&(v&0x8000u)?v|0xffff0000u:v;++loads_;
            if(form.update)gp_[ra]=a;
        }else if(op==31u&&xo==339u&&(ra|(rb<<5))==8u&&rs!=1u)gp_[rs]=lr_;
        else if(op==31u&&xo==467u&&(ra|(rb<<5))==9u)ctr_=gp_[rs];
        else if((op==14u||op==15u)&&rs!=1u)gp_[rs]=(ra?gp_[ra]:0u)+(op==15u?imm<<16u:imm);
        else if(op==10u||op==11u){
            if(w&0x00200000u)return fail(6);
            const uint32_t a=gp_[ra],b=op==10u?w&0xffffu:imm;
            compare((w>>23)&7u,op==10u?a<b:std::bit_cast<int32_t>(a)<std::bit_cast<int32_t>(b),a==b);
        }else if(op==31u&&(xo==0u||xo==32u)){
            if(w&0x00200000u)return fail(6);
            const uint32_t a=gp_[ra],b=gp_[rb];
            compare((w>>23)&7u,xo==32u?a<b:std::bit_cast<int32_t>(a)<std::bit_cast<int32_t>(b),a==b);
        }else if(op==31u&&xo==444u&&rs==rb&&ra!=1u){
            gp_[ra]=gp_[rs];if(w&1u)record(gp_[ra]);
        }else if(op==31u&&(xo==922u||xo==954u)&&ra!=1u){
            const uint32_t m=xo==922u?0xffffu:0xffu,s=xo==922u?0x8000u:0x80u;
            gp_[ra]=((gp_[rs]&m)^s)-s;if(w&1u)record(gp_[ra]);
        }else if((op==20u||op==21u||op==23u)&&ra!=1u){
            const unsigned sh=op==23u?gp_[rb]&31u:rb,mb=(w>>6)&31u,me=(w>>1)&31u;
            const uint32_t m=mask(mb,me),v=std::rotl(gp_[rs],int(sh))&m;
            gp_[ra]=op==20u?(gp_[ra]&~m)|v:v;if(w&1u)record(gp_[ra]);
        }else if(op>=24u&&op<=29u&&ra!=1u){
            const uint32_t n=(w&0xffffu)<<((op&1u)?16u:0u);
            gp_[ra]=op<26u?gp_[rs]|n:op<28u?gp_[rs]^n:gp_[rs]&n;if(op>=28u)record(gp_[ra]);
        }else if(op==31u&&(xo==266u||xo==40u)&&rs!=1u){
            gp_[rs]=xo==266u?gp_[ra]+gp_[rb]:gp_[rb]-gp_[ra];if(w&1u)record(gp_[rs]);
        }else if(op==18u&&(w&3u)==1u){
            if(e_.boundary.width||visits_!=e_.path.size()||target(pc,w)!=e_.target||!abi(c))return fail(6);
            lr_=pc+4u;due_=true;return true;
        }else if(op==16u||op==18u){
            if(w&3u)return fail(6);
            const auto dst=target(pc,w);
            if(dst>=e_.root&&dst<=pc){
                back_poll_due_=true;poll_pc_=pc;poll_ctr_=ctr_;
            }
            const unsigned bo=(w>>21)&31u,bi=(w>>16)&31u;bool ct=true;
            if(op==16u&&!(bo&4u)){--ctr_;ct=bool(ctr_)!=bool(bo&2u);}
            if(op==18u||(ct&&((bo&16u)||bool((cr_>>(31u-bi))&1u)==bool(bo&8u))))next=target(pc,w);
        }else return fail(6);
        if(visits_==e_.path.size()&&e_.boundary.width){
            if(next!=e_.target)return fail(6);
            boundary_due_=true;return true;
        }
        if(visits_>=e_.path.size()||e_.path[visits_].pc!=next)return fail(6);
        return true;
    }
    // The instrumented label ticks, then stops before the native load body.
    // Unlike a direct call entry, ctx.pc need not track every local label.
    template<class C>bool stop_before_load(C& c,uint32_t pc,uint32_t w,bool held){
        if(stage_!=1u||!e_.boundary.width||!boundary_due_||back_poll_due_||due_||
           visits_!=e_.path.size()||pc!=e_.target||w!=e_.target_word||
           c.inst_count-last_!=1u||!common(c,held)||!word(c,pc,w)||!abi(c))return fail(6);
        const auto form=decode_load(w);
        const unsigned ra=(w>>16)&31u,rb=(w>>11)&31u;
        const uint32_t imm=uint32_t(int32_t((w&0xffffu)^0x8000u)-0x8000);
        if(!form.width||form.width!=e_.boundary.width||
           (ra?gp_[ra]:0u)+(form.indexed?gp_[rb]:imm)!=e_.boundary.address||
           !mapped(c,{e_.boundary.address,e_.boundary.width}))return fail(6);
        last_=c.inst_count;stage_=2;return true;
    }
    template<class C>bool reached_load_boundary(C& c,bool held)const{
        return stage_==2u&&boundary_due_&&!due_&&!back_poll_due_&&common(c,held)&&
            c.inst_count==last_&&abi(c)&&word(c,e_.target,e_.target_word);
    }
    template<class C>bool reached(C& c,bool held)const{
        return stage_==2u&&!e_.boundary.width&&due_&&common(c,held)&&c.pc==e_.target&&c.inst_count==last_&&abi(c);
    }
    // A frameless descendant may change volatile registers but must not
    // alter any byte of this completed formatter prologue frame.
    template<class C>bool frame_held(C& c,bool held)const{
        if(stage_!=2u||error_||!held||cpu_!=&c||!safe(c)||c.gpr[1]!=frame_.base||
           c.inst_count<last_||c.inst_count-last_>128u||!mapped(c,frame_))return false;
        for(unsigned i=0;i<shadow_.size();++i)if(c.mmu.read8(frame_.base+i)!=shadow_[i])return false;
        return true;
    }
    // One bounded 48-byte nested frame may use the ABI's linkage word.
    // The child's own shadow supplies the expected current linkage value.
    template<class C>bool child_frame_held(C& c,bool held,uint32_t child_sp,uint32_t child_link)const{
        if(stage_!=2u||!due_||error_||!held||cpu_!=&c||!safe(c)||c.gpr[1]!=child_sp||
           (child_sp!=frame_.base&&child_sp!=frame_.base-48u)||c.inst_count<last_||
           c.inst_count-last_>128u||!mapped(c,frame_))return false;
        for(unsigned i=0;i<shadow_.size();++i){
            if(i>=4u&&i<8u&&written_[i])return false;
            const auto v=(i>=4u&&i<8u)?uint8_t(child_link>>(24u-8u*(i-4u))):shadow_[i];
            if(c.mmu.read8(frame_.base+i)!=v)return false;
        }
        return true;
    }
private:
    struct LoadForm {unsigned width=0;bool indexed=false,update=false,sign=false;};
    static LoadForm decode_load(uint32_t w){
        const unsigned op=w>>26,rt=(w>>21)&31u,ra=(w>>16)&31u,xo=(w>>1)&1023u;
        LoadForm f;
        if((op>=32u&&op<=35u)||(op>=40u&&op<=43u)){
            f={op<=33u?4u:op<=35u?1u:2u,false,bool(op&1u),op>=42u};
        }else if(op==31u&&!(w&1u)){
            switch(xo){
            case 23:case 55:f={4,true,xo==55,false};break;
            case 87:case 119:f={1,true,xo==119,false};break;
            case 279:case 311:case 343:case 375:f={2,true,xo==311||xo==375,xo==343||xo==375};break;
            default:return {};
            }
        }
        if(rt==1u||(f.update&&(!ra||ra==rt||ra==1u)))return {};
        return f;
    }
    ScFormatterExpectation e_;const void* cpu_=nullptr;AllocatorRange frame_{};
    std::array<uint32_t,32> gp_{},incoming_{};std::array<uint32_t,8> gqr_{};
    std::vector<uint8_t> shadow_,written_;
    uint32_t msr_=0,cr_=0,lr_=0,ctr_=0,xer_=0,srr0_=0,srr1_=0;
    uint64_t last_=0;unsigned stage_=0,error_=0,visits_=0,stores_=0,loads_=0,authenticated_loads_=0,seen_=0;
    bool initial_poll_=false,entry_seen_=false,due_=false,back_poll_due_=false,boundary_due_=false;
    uint32_t poll_pc_=0,poll_ctr_=0;unsigned back_polls_=0;
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    static uint32_t mask(unsigned mb,unsigned me){
        uint32_t v=0;for(unsigned i=0;i<32u;++i)if(mb<=me?(i>=mb&&i<=me):(i>=mb||i<=me))v|=1u<<(31u-i);return v;
    }
    void compare(unsigned f,bool lt,bool eq){
        const unsigned sh=28u-4u*f;
        cr_=(cr_&~(15u<<sh))|(((lt?8u:eq?2u:4u)|((xer_>>31)&1u))<<sh);
    }
    void record(uint32_t v){compare(0u,(v&0x80000000u)!=0u,v==0u);}
    static uint32_t target(uint32_t pc,uint32_t w){
        const bool bc=w>>26==16u;const uint32_t m=bc?0xfffcu:0x03fffffcu,s=bc?0x8000u:0x02000000u;
        return pc+(((w&m)^s)-s);
    }
    bool access(uint32_t pc,uint32_t a,unsigned n,bool wr){
        const auto x=std::find_if(e_.accesses.begin(),e_.accesses.end(),[&](auto v){return v.pc==pc;});
        if(x==e_.accesses.end()||x->width!=n||x->write!=wr)return false;
        const int64_t expected=x->stack?int64_t(incoming_[1])+x->address:x->address;
        if(expected<0||expected>0xffffffffll||a!=uint32_t(expected))return false;
        const auto i=unsigned(x-e_.accesses.begin());if(seen_&(1u<<i))return false;seen_|=1u<<i;return true;
    }
    bool store(uint32_t a,unsigned n,uint32_t v){
        if(!frame_.contains(a,n)||(a%n)||(a>=incoming_[1]&&(a!=incoming_[1]+4u||n!=4u||v!=e_.entry_lr)))return false;
        for(unsigned i=0;i<n;++i){const auto j=a-frame_.base+i;if(written_[j])return false;written_[j]=1;
            shadow_[j]=uint8_t(v>>(8u*(n-i-1u)));}
        return true;
    }
    template<class C>bool abi(C& c)const{
        if(stores_+loads_!=e_.accesses.size()||authenticated_loads_!=unsigned(std::count_if(e_.accesses.begin(),e_.accesses.end(),[](auto a){return a.expected_value.has_value();}))||
           gp_[1]!=frame_.base||c.mmu.read32(frame_.base)!=incoming_[1]||
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
    template<class C>bool common(C& c,bool held,bool pre_branch=false)const{
        if(error_||!held||cpu_!=&c||!safe(c)||c.gpr!=gp_||c.gqr!=gqr_||c.msr!=msr_||
           pack(c)!=cr_||c.lr!=lr_||c.ctr!=(pre_branch?poll_ctr_:ctr_)||c.xer!=xer_||c.srr0!=srr0_||c.srr1!=srr1_||!mapped(c,frame_))return false;
        for(unsigned i=0;i<shadow_.size();++i)if(c.mmu.read8(frame_.base+i)!=shadow_[i])return false;
        return true;
    }
};
}
