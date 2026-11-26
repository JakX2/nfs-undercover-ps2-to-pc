#pragma once
#include "wii_post_stm_sc_restore.h"
namespace undercover::wii {
struct ScVersionByte {uint32_t addr;uint8_t value;};
struct ScVersionExpectation {
    uint32_t root,start,version,report,report_word,pointer_cell,version_ptr,format_ptr;
    std::span<const IpcDispatchWord> words;
    std::span<const ScVersionByte> data;
};
// The caller loads the original initialized pointer, calls the version
// thunk, and the thunk tail-branches to the diagnostic routine. Stop at
// that original entry: no simulated report or report return in this lane.
class ScVersionWitness {
public:
    explicit ScVersionWitness(ScVersionExpectation e):e_(e){}
    unsigned stage()const{return stage_;} unsigned failure()const{return error_;}
    unsigned visits()const{return visits_;} unsigned ordinal()const{return ordinal_;}
    template<class C>bool begin(C& c,bool held){
        if(stage_||error_||!held||!safe(c)||!(c.msr&0x8000u)||c.pc!=e_.start||c.lr!=e_.start||
           e_.words.size()<5u||e_.words.size()>10u||e_.data.size()<8u||e_.data.size()>516u||
           !known(c,e_.root,e_.start)||!known(c,e_.version,e_.version)||
           !word(c,e_.report,e_.report_word)||!word(c,e_.pointer_cell,e_.version_ptr)||!data(c))return fail(1);
        for(auto x:e_.data)if(std::count_if(e_.data.begin(),e_.data.end(),[&](auto y){return x.addr==y.addr;})!=1)return fail(1);
        if(!string(c,e_.version_ptr)||!string(c,e_.format_ptr))return fail(1);
        cpu_=&c;gp_=c.gpr;gqr_=c.gqr;msr_=c.msr;cr_=pack(c);lr_=c.lr;ctr_=c.ctr;xer_=c.xer;
        srr0_=c.srr0;srr1_=c.srr1;last_=c.inst_count;next_=e_.start;owner_=e_.root;stage_=1;return true;
    }
    template<class C>bool poll(C& c,bool held){
        if(stage_!=1u||!common(c,held)||c.inst_count!=last_)return fail(2);
        if(!visits_&&!initial_poll_&&c.pc==e_.start){initial_poll_=true;return true;}
        if(!tail_due_||c.pc!=e_.report||c.lr!=e_.start+8u||c.gpr[3]!=e_.format_ptr||c.gpr[4]!=e_.version_ptr||
           !word(c,e_.report,e_.report_word)||visits_!=e_.words.size())return fail(2);
        stage_=2;return true;
    }
    template<class C>bool entry(C& c,uint32_t pc,bool held){
        if(stage_!=1u||!common(c,held)||c.pc!=pc)return fail(3);
        if(!visits_){
            if(!initial_poll_||entry_seen_||pc!=e_.start||c.inst_count-last_!=1u)return fail(3);
            entry_seen_=true;return true;
        }
        if(!call_due_||pc!=e_.version||c.inst_count!=last_||c.lr!=e_.start+8u||c.gpr[3]!=e_.version_ptr)return fail(3);
        call_due_=false;owner_=e_.version;version_entry_=true;return true;
    }
    template<class C>bool before(C& c,uint32_t pc,uint32_t w,bool held){
        if(stage_!=1u||!common(c,held)||call_due_||tail_due_||pc!=next_||
           c.inst_count-last_!=(visits_?1u:2u)||(!visits_&&(!initial_poll_||c.pc!=pc))||
           !known(c,owner_,pc,w)||++visits_>e_.words.size())return fail(4);
        ordinal_=visits_;last_=c.inst_count;next_=pc+4u;
        const unsigned op=w>>26,rs=(w>>21)&31u,ra=(w>>16)&31u,rb=(w>>11)&31u,xo=(w>>1)&1023u;
        const uint32_t imm=uint32_t(int32_t((w&0xffffu)^0x8000u)-0x8000);
        if(owner_==e_.root){
            if(visits_==1u&&op==32u&&rs==3u&&(ra==2u||ra==13u)&&gp_[ra]+imm==e_.pointer_cell&&word(c,e_.pointer_cell,e_.version_ptr)){
                gp_[3]=e_.version_ptr;
            }else if(visits_==2u&&op==18u&&(w&3u)==1u&&target(pc,w)==e_.version&&gp_[3]==e_.version_ptr){
                lr_=pc+4u;next_=e_.version;call_due_=true;return true;
            }else return fail(5);
        }else if(owner_==e_.version&&version_entry_){
            if(op==14u&&volatile_reg(rs))gp_[rs]=(ra?gp_[ra]:0u)+imm;
            else if(op==31u&&xo==444u&&!(w&1u)&&rs==rb&&volatile_reg(ra))gp_[ra]=gp_[rs];
            else if(op==18u&&!(w&3u)&&target(pc,w)==e_.report&&visits_==e_.words.size()&&
                    gp_[3]==e_.format_ptr&&gp_[4]==e_.version_ptr&&lr_==e_.start+8u){
                next_=e_.report;tail_due_=true;return true;
            }else return fail(5);
        }else return fail(5);
        if(!known(c,owner_,next_))return fail(5);
        return true;
    }
    template<class C>bool reached(C& c,bool held)const{
        return stage_==2u&&tail_due_&&version_entry_&&common(c,held)&&c.pc==e_.report&&
            c.inst_count==last_&&c.lr==e_.start+8u&&c.gpr[3]==e_.format_ptr&&c.gpr[4]==e_.version_ptr;
    }
    template<class C>bool data_held(C& c,bool held)const{return stage_==2u&&!error_&&cpu_==&c&&held&&safe(c)&&data(c);}
private:
    ScVersionExpectation e_;const void* cpu_=nullptr;
    std::array<uint32_t,32> gp_{};std::array<uint32_t,8> gqr_{};
    uint32_t msr_=0,cr_=0,lr_=0,ctr_=0,xer_=0,srr0_=0,srr1_=0,next_=0,owner_=0;
    uint64_t last_=0;unsigned stage_=0,error_=0,visits_=0,ordinal_=0;
    bool initial_poll_=false,entry_seen_=false,version_entry_=false,call_due_=false,tail_due_=false;
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    static bool volatile_reg(unsigned r){return r==0u||(r>=3u&&r<=12u);}
    static uint32_t target(uint32_t pc,uint32_t w){return pc+(((w&0x03fffffcu)^0x02000000u)-0x02000000u);}
    template<class C>static bool safe(C& c){return c.is_running&&!c.in_callback&&!c.dispatch_saved_ctx;}
    template<class C>static uint32_t pack(C& c){uint32_t v=0;for(auto f:c.cr)v=(v<<4)|(unsigned(f.lt)<<3)|(unsigned(f.gt)<<2)|(unsigned(f.eq)<<1)|unsigned(f.so);return v;}
    template<class C>bool common(C& c,bool held)const{
        return !error_&&held&&cpu_==&c&&safe(c)&&c.gpr==gp_&&c.gqr==gqr_&&c.msr==msr_&&
            pack(c)==cr_&&c.lr==lr_&&c.ctr==ctr_&&c.xer==xer_&&c.srr0==srr0_&&c.srr1==srr1_&&data(c);
    }
    template<class C>static bool word(C& c,uint32_t a,uint32_t w){
        if((a&3u)||a<0x80000000u||a>0x817ffffcu)return false;
        auto p=c.mmu.get_ptr(a),q=c.mmu.get_ptr(a+3u);
        return p&&q&&reinterpret_cast<uintptr_t>(q)==reinterpret_cast<uintptr_t>(p)+3u&&c.mmu.read32(a)==w;
    }
    template<class C>bool data(C& c)const{
        for(auto x:e_.data)if(x.addr<0x80000000u||x.addr>=0x81800000u||!c.mmu.get_ptr(x.addr)||c.mmu.read8(x.addr)!=x.value)return false;
        return true;
    }
    template<class C>bool string(C& c,uint32_t a)const{
        for(unsigned i=0;i<256;++i){
            if(a>0xffffffffu-i||!c.mmu.get_ptr(a+i))return false;
            auto p=std::find_if(e_.data.begin(),e_.data.end(),[&](auto x){return x.addr==a+i;});
            if(p==e_.data.end())return false;
            if(!p->value)return i>0;
        }
        return false;
    }
    template<class C>bool known(C& c,uint32_t owner,uint32_t pc)const{
        return std::count_if(e_.words.begin(),e_.words.end(),
            [&](auto x){return x.owner==owner&&x.pc==pc&&word(c,pc,x.word);})==1;
    }
    template<class C>bool known(C& c,uint32_t owner,uint32_t pc,uint32_t w)const{return known(c,owner,pc)&&word(c,pc,w);}
};
}
