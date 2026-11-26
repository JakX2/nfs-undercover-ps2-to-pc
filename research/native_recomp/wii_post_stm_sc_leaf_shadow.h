#pragma once
#include "wii_post_stm_sc_report_helper.h"
#include <bit>
namespace undercover::wii {
// Independent integer leaf instruction shadow. It never writes guest
// registers or memory. A caller supplies the only writable object and
// verifies actual native effects on each subsequent instruction boundary.
struct ScLeafAccess {uint32_t pc,offset,width;bool write;};
struct ScLeafExpectation {
    uint32_t root,caller,caller_word;
    std::span<const IpcDispatchWord> words;
    std::span<const ScLeafAccess> accesses;
};
class ScLeafShadow {
public:
    explicit ScLeafShadow(ScLeafExpectation e):e_(e){}
    unsigned stage()const{return stage_;} unsigned failure()const{return error_;}
    unsigned visits()const{return visits_;} unsigned loads()const{return loads_;} unsigned stores()const{return stores_;}
    uint32_t expected_sp()const{return gp_[1];}
    uint32_t object_base()const{return object_.base;}
    std::span<const uint8_t> expected_bytes()const{return shadow_;}
    template<class C>bool begin(C& c,AllocatorRange object,bool held){
        if(stage_||error_||!held||!safe(c)||!(c.msr&0x8000u)||c.pc!=e_.root||c.lr!=e_.caller||
           e_.words.empty()||e_.words.size()>128u||e_.accesses.size()>8u||
           !object.size||object.size>4096u||!mapped(c,object)||!known(c,e_.root)||!word(c,e_.caller,e_.caller_word))return fail(1);
        for(auto x:e_.words)if(x.owner!=e_.root||!word(c,x.pc,x.word)||
            std::count_if(e_.words.begin(),e_.words.end(),[&](auto y){return x.pc==y.pc;})!=1)return fail(1);
        for(auto a:e_.accesses)if((a.width!=1u&&a.width!=2u&&a.width!=4u)||a.offset>object.size||
           a.width>object.size-a.offset||!known(c,a.pc)||
           std::count_if(e_.accesses.begin(),e_.accesses.end(),[&](auto x){return x.pc==a.pc;})!=1)return fail(1);
        object_=object;
        for(unsigned i=0;i<object.size;++i)shadow_.push_back(c.mmu.read8(object.base+i));
        cpu_=&c;gp_=c.gpr;gqr_=c.gqr;msr_=c.msr;cr_=pack(c);lr_=c.lr;ctr_=c.ctr;xer_=c.xer;
        srr0_=c.srr0;srr1_=c.srr1;last_=c.inst_count;next_=e_.root;stage_=1;return true;
    }
    template<class C>bool poll(C& c,bool held){
        if(stage_!=1u||!common(c,held)||c.inst_count!=last_)return fail(2);
        if(!visits_&&!initial_poll_&&c.pc==e_.root){initial_poll_=true;return true;}
        if(!due_||c.pc!=e_.caller||c.lr!=e_.caller||!word(c,e_.caller,e_.caller_word))return fail(2);
        stage_=2;return true;
    }
    template<class C>bool entry(C& c,uint32_t pc,bool held){
        if(stage_!=1u||!common(c,held)||visits_||!initial_poll_||entry_seen_||
           pc!=e_.root||c.pc!=pc||c.inst_count-last_!=1u)return fail(3);
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
            if(lr_!=e_.caller)return fail(5);
            next_=e_.caller;due_=true;return true;
        }
        if(op==10u||op==11u){
            if(w&0x00200000u)return fail(5);
            const uint32_t a=gp_[ra],b=op==10u?w&0xffffu:imm;
            compare((w>>23)&7u,op==10u?a<b:std::bit_cast<int32_t>(a)<std::bit_cast<int32_t>(b),a==b);
        }else if(op==14u||op==15u){
            if(!vol(rs))return fail(5);
            gp_[rs]=(ra?gp_[ra]:0u)+(op==15u?imm<<16u:imm);
        }else if(op>=24u&&op<=29u){
            if(!vol(ra))return fail(5);
            const uint32_t n=(w&0xffffu)<<((op&1u)?16u:0u);
            gp_[ra]=op<26u?gp_[rs]|n:op<28u?gp_[rs]^n:gp_[rs]&n;
            if(op>=28u)record(gp_[ra]);
        }else if(op==20u||op==21u||op==23u){
            if(!vol(ra))return fail(5);
            const unsigned sh=op==23u?gp_[rb]&31u:rb,mb=(w>>6)&31u,me=(w>>1)&31u;
            const uint32_t m=mask(mb,me),v=std::rotl(gp_[rs],int(sh))&m;
            gp_[ra]=op==20u?(gp_[ra]&~m)|v:v;
            if(w&1u)record(gp_[ra]);
        }else if(op==31u&&(xo==0u||xo==32u)){
            if(w&0x00200000u)return fail(5);
            const auto a=gp_[ra],b=gp_[rb];
            compare((w>>23)&7u,xo==32u?a<b:std::bit_cast<int32_t>(a)<std::bit_cast<int32_t>(b),a==b);
        }else if(op==31u&&(xo==444u||xo==28u||xo==316u||xo==24u||xo==536u)){
            if(!vol(ra))return fail(5);
            const auto a=gp_[rs],b=gp_[rb];const unsigned sh=b&63u;
            gp_[ra]=xo==444u?a|b:xo==28u?a&b:xo==316u?a^b:sh>=32u?0u:xo==24u?a<<sh:a>>sh;
            if(w&1u)record(gp_[ra]);
        }else if(op==31u&&(xo==266u||xo==40u)){
            if(!vol(rs))return fail(5);
            gp_[rs]=xo==266u?gp_[ra]+gp_[rb]:gp_[rb]-gp_[ra];
            if(w&1u)record(gp_[rs]);
        }else if(op==32u||op==34u||op==40u||op==42u||op==36u||op==38u||op==44u){
            const bool wr=op==36u||op==38u||op==44u;
            const unsigned n=op==32u||op==36u?4u:op==34u||op==38u?1u:2u;
            const uint32_t a=(ra?gp_[ra]:0u)+imm;
            auto p=std::find_if(e_.accesses.begin(),e_.accesses.end(),[&](auto x){return x.pc==pc;});
            if(p==e_.accesses.end()||p->write!=wr||p->width!=n||a!=object_.base+p->offset||
               !object_.contains(a,n)||(a%n)||(!wr&&!vol(rs)))return fail(6);
            const auto i=unsigned(p-e_.accesses.begin());if(seen_&(1u<<i))return fail(6);seen_|=1u<<i;
            if(wr){for(unsigned j=0;j<n;++j)shadow_[p->offset+j]=uint8_t(gp_[rs]>>(8u*(n-j-1u)));++stores_;}
            else {uint32_t v=0;for(unsigned j=0;j<n;++j)v=(v<<8)|shadow_[p->offset+j];
                gp_[rs]=op==42u&&v&0x8000u?v|0xffff0000u:v;++loads_;}
        }else if(op==16u||op==18u){
            if(w&3u||(op==16u&&!((w>>21)&4u)))return fail(5);
            const unsigned bo=(w>>21)&31u,bi=(w>>16)&31u;
            if(op==18u||(bo&16u)||bool((cr_>>(31u-bi))&1u)==bool(bo&8u))next_=target(pc,w);
        }else return fail(5);
        if(next_<=pc||!known(c,next_))return fail(5);
        return true;
    }
    template<class C>bool reached(C& c,bool held)const{
        return stage_==2u&&due_&&common(c,held)&&c.pc==e_.caller&&c.inst_count==last_;
    }
    template<class C>bool object_held(C& c,bool held)const{
        if(stage_!=2u||error_||!held||cpu_!=&c||!safe(c)||!mapped(c,object_))return false;
        for(unsigned i=0;i<shadow_.size();++i)if(c.mmu.read8(object_.base+i)!=shadow_[i])return false;
        return true;
    }
private:
    ScLeafExpectation e_;const void* cpu_=nullptr;AllocatorRange object_{};
    std::array<uint32_t,32> gp_{};std::array<uint32_t,8> gqr_{};
    std::vector<uint8_t> shadow_;
    uint32_t msr_=0,cr_=0,lr_=0,ctr_=0,xer_=0,srr0_=0,srr1_=0,next_=0;
    uint64_t last_=0;unsigned stage_=0,error_=0,visits_=0,loads_=0,stores_=0,seen_=0;
    bool initial_poll_=false,entry_seen_=false,due_=false;
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    static bool vol(unsigned r){return r==0u||(r>=3u&&r<=12u);}
    static uint32_t mask(unsigned mb,unsigned me){
        uint32_t v=0;for(unsigned i=0;i<32u;++i)
            if(mb<=me?(i>=mb&&i<=me):(i>=mb||i<=me))v|=1u<<(31u-i);
        return v;
    }
    void compare(unsigned field,bool lt,bool eq){
        const unsigned sh=28u-4u*field;
        cr_=(cr_&~(15u<<sh))|(((lt?8u:eq?2u:4u)|((xer_>>31)&1u))<<sh);
    }
    void record(uint32_t v){compare(0u,(v&0x80000000u)!=0u,v==0u);}
    static uint32_t target(uint32_t pc,uint32_t w){
        const bool bc=w>>26==16u;const uint32_t m=bc?0xfffcu:0x03fffffcu,s=bc?0x8000u:0x02000000u;
        return pc+(((w&m)^s)-s);
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
           pack(c)!=cr_||c.lr!=lr_||c.ctr!=ctr_||c.xer!=xer_||c.srr0!=srr0_||c.srr1!=srr1_||!mapped(c,object_))return false;
        for(unsigned i=0;i<shadow_.size();++i)if(c.mmu.read8(object_.base+i)!=shadow_[i])return false;
        return true;
    }
};
}
