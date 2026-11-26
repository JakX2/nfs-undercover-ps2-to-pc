#pragma once
#include "wii_post_stm_sc_disable.h"
#include <bit>
namespace undercover::wii {
struct ScDecisionCell {uint32_t pc,address,width;AllocatorRange object;};
struct ScDecisionExpectation {
    uint32_t root,start,restore,restore_word,cold_call;
    ScDecisionCell load;
    std::span<const ScDecisionCell> stores;
    std::span<const IpcDispatchWord> words;
};
// Observe the original cold branch. No initialization, register writes,
// branch selection or store is performed by this witness.
class ScDecisionWitness {
public:
    explicit ScDecisionWitness(ScDecisionExpectation e):e_(e){}
    unsigned stage()const{return stage_;} unsigned failure()const{return error_;}
    unsigned visits()const{return visits_;} unsigned loads()const{return loads_;}
    unsigned stores()const{return stores_;} unsigned ordinal()const{return ordinal_;}
    uint32_t expected_msr()const{return msr_;}
    template<class C>bool begin(C& c,bool held){
        if(stage_||error_||!held||!safe(c)||(c.msr&0x8000u)||c.pc!=e_.start||c.lr!=e_.start||
           c.gpr[3]!=1u||e_.words.size()!=8u||e_.stores.size()!=2u||
           !known(c,e_.start)||!known(c,e_.cold_call)||!word(c,e_.restore,e_.restore_word)||
           !cell(c,e_.load,false)||value(c,e_.load)!=0u)return fail(1);
        for(auto s:e_.stores)if(!cell(c,s,true))return fail(1);
        if(overlap(e_.stores[0].object,e_.stores[1].object)||
           std::count_if(e_.stores.begin(),e_.stores.end(),[&](auto s){return s.address==e_.load.address&&s.width==e_.load.width;})!=1)
            return fail(1);
        for(unsigned j=0;j<2;++j){
            objects_[j]=e_.stores[j].object;
            for(unsigned i=0;i<objects_[j].size;++i)shadow_[j].push_back(c.mmu.read8(objects_[j].base+i));
        }
        cpu_=&c;gp_=c.gpr;gqr_=c.gqr;msr_=c.msr;cr_=pack(c);lr_=c.lr;ctr_=c.ctr;xer_=c.xer;
        srr0_=c.srr0;srr1_=c.srr1;last_=c.inst_count;next_=e_.start;stage_=1;return true;
    }
    template<class C>bool poll(C& c,bool held){
        if(stage_!=1u||!common(c,held)||visits_||initial_poll_||c.pc!=e_.start||c.inst_count!=last_)return fail(2);
        initial_poll_=true;return true;
    }
    template<class C>bool entry(C& c,uint32_t pc,bool held){
        if(stage_!=1u||!common(c,held)||c.pc!=pc)return fail(3);
        if(!visits_){
            if(!initial_poll_||entry_seen_||pc!=e_.start||c.inst_count-last_!=1u)return fail(3);
            entry_seen_=true;return true;
        }
        if(!due_||pc!=e_.restore||c.inst_count!=last_||c.lr!=e_.cold_call+4u||
           c.gpr[3]!=1u||loads_!=1u||stores_!=2u||seen_stores_!=3u||value(c,e_.load)!=1u||
           !word(c,e_.restore,e_.restore_word))return fail(3);
        stage_=2;return true;
    }
    template<class C>bool before(C& c,uint32_t pc,uint32_t w,bool held){
        if(stage_!=1u||!common(c,held)||due_||pc!=next_||
           c.inst_count-last_!=(visits_?1u:2u)||(!visits_&&(!initial_poll_||c.pc!=pc))||
           !known(c,pc,w)||++visits_>e_.words.size())return fail(4);
        ordinal_=(pc-e_.start)/4u+1u;last_=c.inst_count;next_=pc+4u;
        const unsigned op=w>>26,rs=(w>>21)&31u,ra=(w>>16)&31u,rb=(w>>11)&31u,xo=(w>>1)&1023u;
        const uint32_t imm=uint32_t(int32_t((w&0xffffu)^0x8000u)-0x8000);
        const uint32_t ea=gp_[ra]+imm;
        if(op==32u||op==34u||op==40u){
            if(loads_||pc!=e_.load.pc||ea!=e_.load.address||!writable(rs)||!cell(c,e_.load,false))return fail(5);
            gp_[rs]=value(c,e_.load);if(gp_[rs])return fail(5);++loads_;
        }else if(op==36u||op==38u||op==44u){
            unsigned j=0;while(j<2&&e_.stores[j].pc!=pc)++j;
            if(j==2||(seen_stores_&(1u<<j))||!loads_||ea!=e_.stores[j].address||!cell(c,e_.stores[j],true))return fail(5);
            const auto s=e_.stores[j];const uint32_t v=gp_[rs];
            if(s.address==e_.load.address&&v!=1u)return fail(5);
            for(unsigned i=0;i<s.width;++i)shadow_[j][s.address-s.object.base+i]=uint8_t(v>>(8u*(s.width-i-1u)));
            seen_stores_|=1u<<j;++stores_;
        }else if(op==10u||op==11u){
            if(w&0x00200000u)return fail(6);
            const uint32_t a=gp_[ra],b=op==10u?w&0xffffu:imm;
            const bool lt=op==10u?a<b:std::bit_cast<int32_t>(a)<std::bit_cast<int32_t>(b);
            compare((w>>23)&7u,lt,a==b);
        }else if(op==14u||op==15u){
            if(!writable(rs))return fail(6);
            gp_[rs]=(ra?gp_[ra]:0u)+(op==15u?imm<<16:imm);
        }else if(op==24u||op==25u){
            if(!writable(ra))return fail(6);
            gp_[ra]=gp_[rs]|((w&0xffffu)<<(op==25u?16u:0u));
        }else if(op==31u&&xo==444u&&!(w&1u)&&writable(ra)){
            gp_[ra]=gp_[rs]|gp_[rb];
        }else if(op==18u&&(w&3u)==1u){
            if(pc!=e_.cold_call||target(pc,w)!=e_.restore||loads_!=1u||stores_!=2u||gp_[3]!=1u||value(c,e_.load)!=1u)return fail(6);
            lr_=pc+4u;next_=e_.restore;due_=true;return true;
        }else if(op==16u||op==18u){
            if(w&3u||target(pc,w)<=pc||(op==16u&&!((w>>21)&4u)))return fail(6);
            if(op==18u||taken(w))next_=target(pc,w);
        }else return fail(6);
        if(!known(c,next_))return fail(6);
        return true;
    }
    template<class C>bool reached(C& c,bool held)const{
        return stage_==2u&&due_&&common(c,held)&&c.pc==e_.restore&&c.inst_count==last_&&
            loads_==1u&&stores_==2u&&value(c,e_.load)==1u;
    }
    template<class C>bool objects_held(C& c,bool held)const{
        return stage_==2u&&!error_&&cpu_==&c&&held&&safe(c)&&settled(c);
    }
private:
    ScDecisionExpectation e_;const void* cpu_=nullptr;
    std::array<uint32_t,32> gp_{};std::array<uint32_t,8> gqr_{};
    std::array<AllocatorRange,2> objects_{};std::array<std::vector<uint8_t>,2> shadow_{};
    uint32_t msr_=0,cr_=0,lr_=0,ctr_=0,xer_=0,srr0_=0,srr1_=0,next_=0;
    uint64_t last_=0;unsigned stage_=0,error_=0,visits_=0,loads_=0,stores_=0,seen_stores_=0,ordinal_=0;
    bool initial_poll_=false,entry_seen_=false,due_=false;
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    static bool writable(unsigned r){return r==0u||(r>=3u&&r<=12u)||r>=14u;}
    static bool overlap(AllocatorRange a,AllocatorRange b){return a.base<b.end()&&b.base<a.end();}
    template<class C>static bool safe(C& c){return c.is_running&&!c.in_callback&&!c.dispatch_saved_ctx;}
    template<class C>static uint32_t pack(C& c){uint32_t v=0;for(auto f:c.cr)v=(v<<4)|(unsigned(f.lt)<<3)|(unsigned(f.gt)<<2)|(unsigned(f.eq)<<1)|unsigned(f.so);return v;}
    void compare(unsigned field,bool lt,bool eq){
        const unsigned shift=28u-4u*field;
        const uint32_t v=(lt?8u:eq?2u:4u)|((xer_>>31)&1u);
        cr_=(cr_&~(15u<<shift))|(v<<shift);
    }
    bool taken(uint32_t w)const{
        const unsigned bo=(w>>21)&31u,bi=(w>>16)&31u;
        return (bo&16u)||bool((cr_>>(31u-bi))&1u)==bool(bo&8u);
    }
    static uint32_t target(uint32_t pc,uint32_t w){const bool bc=w>>26==16u;const uint32_t m=bc?0xfffcu:0x03fffffcu,s=bc?0x8000u:0x02000000u;return pc+(((w&m)^s)-s);}
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
    template<class C>bool cell(C& c,ScDecisionCell s,bool store)const{
        if(!known(c,s.pc)||!s.width||s.width>4u||s.address%s.width||s.object.size>4096u||
           !s.object.contains(s.address,s.width)||!mapped(c,s.object))return false;
        const auto w=c.mmu.read32(s.pc);const unsigned op=w>>26,ra=(w>>16)&31u;
        const unsigned n=store?(op==36u?4u:op==38u?1u:op==44u?2u:0u):(op==32u?4u:op==34u?1u:op==40u?2u:0u);
        return n==s.width&&(ra==2u||ra==13u)&&
            c.gpr[ra]+uint32_t(int32_t((w&0xffffu)^0x8000u)-0x8000)==s.address;
    }
    template<class C>static uint32_t value(C& c,ScDecisionCell s){
        uint32_t v=0;for(unsigned i=0;i<s.width;++i)v=(v<<8)|c.mmu.read8(s.address+i);return v;
    }
    template<class C>bool settled(C& c)const{
        for(unsigned j=0;j<2;++j){
            if(!mapped(c,objects_[j]))return false;
            for(unsigned i=0;i<shadow_[j].size();++i)if(c.mmu.read8(objects_[j].base+i)!=shadow_[j][i])return false;
        }
        return true;
    }
    template<class C>bool common(C& c,bool held)const{
        return !error_&&held&&cpu_==&c&&safe(c)&&c.gpr==gp_&&c.gqr==gqr_&&c.msr==msr_&&
            pack(c)==cr_&&c.lr==lr_&&c.ctr==ctr_&&c.xer==xer_&&c.srr0==srr0_&&c.srr1==srr1_&&settled(c);
    }
};
}
