#pragma once
#include <array>
#include <cstdint>
namespace undercover::wii {
struct CallbackReturnExpectation {
    uint32_t call,root,caller;
    std::array<uint32_t,7> restore;
    std::array<uint32_t,4> tail;
    uint32_t caller_word;
};
// Read-only verifier of authenticated restore loads, LR reload and stack unwind.
class CallbackReturnWitness {
public:
    explicit CallbackReturnWitness(CallbackReturnExpectation e):e_(e){}
    unsigned stage()const{return stage_;}
    unsigned failure()const{return error_;}
    unsigned visits()const{return visits_;}
    template<class C> bool start(C& c,uint32_t pc,uint32_t w,const std::array<uint32_t,32>& original,uint32_t cr,bool held){
        if(stage_||error_||!held||!safe(c)||pc!=e_.call||w>>26!=18u||(w&3u)!=1u||
           pc+(((w&0x03fffffcu)^0x02000000u)-0x02000000u)!=e_.root||
           !match(c,pc,w)||!match(c,e_.caller,e_.caller_word)||c.inst_count>UINT64_MAX-16u||
           original[1]<0x80000400u||original[1]>0x817fff00u||(original[1]&3u)||
           e_.restore.back()!=0x4e800020u||e_.tail.back()!=0x4e800020u)return fail(1);
        for(unsigned i=0;i<7;++i)if(!match(c,e_.root+4u*i,e_.restore[i]))return fail(1);
        for(unsigned i=0;i<4;++i)if(!match(c,e_.call+4u+4u*i,e_.tail[i]))return fail(1);
        cpu_=&c;original_=original;gp_=c.gpr;cr_=pack(c);original_cr_=cr;
        lr_=e_.call+4u;msr_=c.msr;srr0_=c.srr0;srr1_=c.srr1;last_=c.inst_count;next_=e_.root;
        stage_=1;return true;
    }
    template<class C> bool entry(C& c,uint32_t pc,bool held){
        if(stage_!=1||!common(c,held)||pc!=e_.root||c.pc!=pc||c.inst_count!=last_||!state(c))return fail(2);
        stage_=2;return true;
    }
    template<class C> bool before(C& c,uint32_t pc,uint32_t w,bool held){
        if(stage_<2||stage_>4||!common(c,held)||pc!=next_||c.inst_count-last_!=1u||!state(c)||!match(c,pc,w))return fail(3);
        last_=c.inst_count;++visits_;
        if(stage_==4){
            if(pc!=e_.caller||c.pc!=pc||c.lr!=pc||w!=e_.caller_word||c.gpr[1]!=original_[1]||
               c.gpr[2]!=original_[2]||c.gpr[13]!=original_[13]||(pack(c)&0x00fff000u)!=(original_cr_&0x00fff000u))return fail(5);
            for(unsigned i=14;i<32;++i)if(c.gpr[i]!=original_[i])return fail(5);
            if(visits_!=12u)return fail(5);
            stage_=5;return true;
        }
        if(stage_==2){
            if(index_>=7u||pc!=e_.root+4u*index_||w!=e_.restore[index_])return fail(3);
            if(index_==6u){
                if(w!=0x4e800020u||c.lr!=e_.call+4u)return fail(4);
                stage_=3;index_=0;next_=lr_;return true;
            }
            const unsigned rd=(w>>21)&31u,ra=(w>>16)&31u;
            if(w>>26!=32u||rd!=26u+index_||(ra!=1u&&ra!=11u)||!load(c,w,original_[rd]))return fail(4);
        }else{
            if(index_>=4u||pc!=e_.call+4u+4u*index_||w!=e_.tail[index_]||(!index_&&c.pc!=pc))return fail(3);
            const unsigned op=w>>26,rd=(w>>21)&31u,ra=(w>>16)&31u,rb=(w>>11)&31u;
            if(index_==3u){
                if(w!=0x4e800020u||lr_!=e_.caller||gp_[1]!=original_[1])return fail(4);
                stage_=4;next_=lr_;return true;
            }
            if(op==32u&&ra==1u&&rd==0u){if(!load(c,w,e_.caller))return fail(4);}
            else if(op==14u&&rd==1u&&ra==1u&&disp(w)>0u&&disp(w)<0x8000u){gp_[1]+=disp(w);if(gp_[1]!=original_[1])return fail(4);}
            else if(op==31u&&((w>>1)&1023u)==467u&&(ra|(rb<<5))==8u&&rd==0u&&!(w&1u)){lr_=gp_[0];if(lr_!=e_.caller)return fail(4);}
            else return fail(4);
        }
        ++index_;next_=pc+4u;return true;
    }
private:
    CallbackReturnExpectation e_;const void* cpu_=nullptr;
    std::array<uint32_t,32> gp_{},original_{};
    unsigned stage_=0,error_=0,index_=0,visits_=0;
    uint32_t lr_=0,cr_=0,original_cr_=0,msr_=0,srr0_=0,srr1_=0,next_=0;
    uint64_t last_=0;
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    static uint32_t disp(uint32_t w){return ((w&0xffffu)^0x8000u)-0x8000u;}
    template<class C>static bool safe(C& c){return c.is_running&&!c.in_callback&&!c.dispatch_saved_ctx&&!(c.msr&0x8000u);}
    template<class C>bool common(C& c,bool held)const{return !error_&&held&&cpu_==&c&&safe(c)&&c.msr==msr_&&c.srr0==srr0_&&c.srr1==srr1_;}
    template<class C>static uint32_t pack(C& c){uint32_t v=0;for(auto f:c.cr)v=(v<<4)|(unsigned(f.lt)<<3)|(unsigned(f.gt)<<2)|(unsigned(f.eq)<<1)|unsigned(f.so);return v;}
    template<class C>bool state(C& c)const{return c.gpr==gp_&&c.lr==lr_&&pack(c)==cr_;}
    template<class C>static bool match(C& c,uint32_t a,uint32_t w){
        return !(a&3u)&&a>=0x80000000u&&a<=0x817ffffcu&&c.mmu.get_ptr(a)&&c.mmu.get_ptr(a+3u)&&c.mmu.read32(a)==w;
    }
    template<class C>bool load(C& c,uint32_t w,uint32_t value){
        const unsigned rd=(w>>21)&31u,ra=(w>>16)&31u;
        const uint32_t a=gp_[ra]+disp(w);
        if(a<original_[1]-0x400u||uint64_t(a)+4u>uint64_t(original_[1])+0x100u||!match(c,a,value))return false;
        gp_[rd]=value;return true;
    }
};
}
