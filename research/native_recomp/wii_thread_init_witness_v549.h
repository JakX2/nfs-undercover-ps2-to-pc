#pragma once
#include "wii_sram_read_witness_v534.h"
namespace undercover::wii {
struct ThreadInitExpectations {
    VectorEdge thread,clear_main,current,callback,getsp,clear_idle;
    uint32_t return_word;
};
// Original thread creation, not a host scheduler or context-switch HLE.
// The complete-image SRAM predecessor must finish before this observer starts.
class ThreadInitWitness {
public:
    static constexpr uint32_t Thread=0x806f5318u,Idle=Thread+1048u,
        StackTop=0x80751cb8u,StackBottom=0x80711cb8u,
        CallbackPtr=0x8070a908u,Return=0x805208d4u;
    explicit ThreadInitWitness(const ThreadInitExpectations& expected):e_(expected){}
    unsigned stage()const noexcept{return stage_;}
    unsigned failure()const noexcept{return error_;}
    template<class Cpu>bool begin(Cpu& c){
        if(stage_||error_||!c.is_running||c.pc!=e_.thread.lr-4u||
           !equal(c,c.pc,e_.thread.branch_word)||c.gpr[1]!=StackTop-88u||
           (c.msr&0x8000u)||!equal(c,0x800000d8u,0)||
           !equal(c,SramGuest+72u,0)||!equal(c,SramGuest+76u,1)||
           !equal(c,CallbackPtr,e_.callback.pc)||!mapped(c,Thread,1472))return fail(1);
        for(unsigned i=0;i<1472;++i)if(c.mmu.read8(Thread+i))return fail(1);
        sp_=c.gpr[1];r2_=c.gpr[2];r13_=c.gpr[13];msr_=c.msr;last_=c.inst_count;
        for(unsigned i=0;i<18;++i)nv_[i]=c.gpr[i+14];
        stage_=1;return true;
    }
    template<class Cpu>bool observe(uint32_t addr,Cpu& c){
        if(error_||stage_<1||stage_>7||!c.is_running||c.pc!=addr||
           c.inst_count<last_||c.inst_count-last_>5000000u||
           c.gpr[2]!=r2_||c.gpr[13]!=r13_||(c.msr&0x8000u)||
           !equal(c,CallbackPtr,e_.callback.pc)||!equal(c,SramGuest+76,1))return fail(2);
        if(addr==Return){
            if(stage_!=7||!equal(c,Return,e_.return_word)||c.lr!=Return||c.gpr[1]!=sp_||
               !context_mode(c)||!equal(c,0x800000d8u,0)||!equal(c,0x800000d4u,Thread)||
               !equal(c,0x800000dcu,Thread)||!equal(c,0x800000e0u,Thread)||
               !equal(c,0x800000e4u,Thread)||!equal(c,0x800000c0u,Thread&0x3fffffffu)||
               !equal(c,StackBottom,0xdeadbabeu)||!equal(c,sp_-32u,sp_))return fail(6);
            for(unsigned i=0;i<18;++i)if(c.gpr[i+14]!=nv_[i])return fail(6);
            if(!mapped(c,Thread,1048)||!mapped(c,StackBottom,sp_-32u-StackBottom))return fail(6);
            for(unsigned off=0;off<1048;off+=4){
                uint32_t expected=0;
                switch(off){case 712:expected=0x00020001u;break;case 720:case 724:expected=16;break;
                    case 728:expected=0xffffffffu;break;case 772:expected=StackTop;break;
                    case 776:expected=StackBottom;break;default:break;}
                if(!equal(c,Thread+off,expected))return fail(6);
            }
            for(uint32_t a=StackBottom+4u;a<sp_-32u;a+=4)if(c.mmu.read32(a))return fail(6);
            stage_=8;return true;
        }
        const std::array<VectorEdge,6> edges{e_.thread,e_.clear_main,e_.current,e_.callback,e_.getsp,e_.clear_idle};
        if(stage_<7&&matches(c,edges[stage_-1])){
            if(c.gpr[1]!=(stage_==1?sp_:sp_-32u))return fail(3);
            if(stage_<=3&&c.msr!=msr_)return fail(3);
            if(stage_>=4&&!context_mode(c))return fail(3);
            switch(stage_){
            case 1:break;
            case 2:
                if(c.gpr[3]!=Thread||!equal(c,0x800000d8u,Thread)||!equal(c,Thread+712,0x00020001u))return fail(4);
                break;
            case 3:
                if(c.gpr[3]!=Thread||!equal(c,0x800000d8u,0))return fail(4);
                break;
            case 4:
                if(c.ctr!=e_.callback.pc||c.gpr[12]!=e_.callback.pc||c.gpr[3]!=0||c.gpr[4]!=Thread||
                   !equal(c,0x800000d4u,Thread)||!equal(c,0x800000c0u,Thread&0x3fffffffu)||
                   !equal(c,Thread+772,StackTop)||!equal(c,Thread+776,StackBottom)||
                   !equal(c,StackBottom,0xdeadbabeu))return fail(5);
                break;
            case 5:
                if(!equal(c,0x800000e4u,Thread))return fail(5);
                break;
            case 6:if(c.gpr[3]!=Idle)return fail(5);break;
            }
            ++stage_;last_=c.inst_count;return true;
        }
        if(addr&3u||!mapped(c,addr,4)||++extra_>512u||addr==e_.thread.pc||addr==e_.callback.pc||
           addr==0x80531b34u||addr==0x805327f8u)return fail(7);
        for(auto e:edges)if(addr==e.pc&&c.lr==e.lr)return fail(7);
        return true;
    }
private:
    ThreadInitExpectations e_;unsigned stage_=0,error_=0,extra_=0;
    uint32_t sp_=0,r2_=0,r13_=0,msr_=0;uint64_t last_=0;std::array<uint32_t,18> nv_{};
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    template<class Cpu>static bool mapped(Cpu& c,uint32_t a,unsigned n){
        return n&&a>=0x80000000u&&uint64_t(a)+n<=0x81800000ull&&c.mmu.get_ptr(a)&&c.mmu.get_ptr(a+n-1u);
    }
    template<class Cpu>static bool equal(Cpu& c,uint32_t a,uint32_t w){return !(a&3u)&&mapped(c,a,4)&&c.mmu.read32(a)==w;}
    template<class Cpu>static bool matches(Cpu& c,const VectorEdge& e){return c.pc==e.pc&&c.lr==e.lr&&equal(c,e.pc,e.entry_word)&&equal(c,e.lr-4,e.branch_word);}
    template<class Cpu>static bool context_mode(Cpu& c){return (c.msr&0x2002u)==2u;}
};
}
