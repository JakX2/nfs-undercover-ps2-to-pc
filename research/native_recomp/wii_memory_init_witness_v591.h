#pragma once
#include "wii_bat_mapping_witness_v590.h"
#include "wii_irq_bank_binding_v481.h"
#include "wii_thread_init_witness_v549.h"
#include <vector>
namespace undercover::wii {
struct MemoryInitExpectations {
    std::array<VectorEdge,12> edges;
    BatMappingExpectations bat;
    uint32_t entry_word,return_word;
    std::vector<VectorEdge> helpers;
};
class MemoryInitWitness {
public:
    static constexpr uint32_t Begin=0x805208d8u,Return=0x805208f4u,
        Node=0x8060d030u,AlarmNode=0x8060bcb8u,Handler=0x8052707cu,IrqTable=0x80003040u;
    explicit MemoryInitWitness(const MemoryInitExpectations& e):e_(e),bat_(e.bat){}
    unsigned stage()const noexcept{return stage_;}
    unsigned failure()const noexcept{return error_;}
    template<class Cpu>bool begin(Cpu& c){
        if(stage_||error_||!c.is_running||c.pc!=Begin||c.lr!=Begin||
           c.gpr[1]!=ThreadInitWitness::StackTop-88u||(c.msr&0x8000u)||
           !equal(c,Begin,e_.entry_word)||!IrqBankBinding::active()||
           !equal(c,0x800000e4u,ThreadInitWitness::Thread))return fail(1);
        sp_=c.gpr[1];r2_=c.gpr[2];r13_=c.gpr[13];msr_=c.msr;hid_=c.hid2;start_=c.inst_count;
        if(!equal(c,r13_-3400u,0)||!equal(c,r13_-3376u,AlarmNode)||
           !equal(c,r13_-3372u,AlarmNode)||!equal(c,Node,0x80527040u)||
           !equal(c,Node+4,127)||!equal(c,Node+8,0)||!equal(c,Node+12,0))return fail(1);
        guards_={c.mmu.read32(Node-4),c.mmu.read32(Node+16)};
        stage_=1;return true;
    }
    template<class Cpu>bool observe(uint32_t addr,Cpu& c){
        if(error_||stage_<1||stage_>19||!c.is_running||c.pc!=addr||
           c.gpr[2]!=r2_||c.gpr[13]!=r13_||c.inst_count<start_||
           c.inst_count-start_>2000000u||c.gpr[1]>sp_||sp_-c.gpr[1]>1024||
           !equal(c,0x800000e4u,ThreadInitWitness::Thread))return fail(2);
        if(stage_>=12&&stage_<=17){
            if(!bat_.observe(addr,c))return fail(3);
            ++stage_;return true;
        }
        if(c.msr!=msr_)return fail(2);
        if(stage_==19&&addr==Return){
            if(c.lr!=Return||c.gpr[1]!=sp_||!equal(c,Return,e_.return_word)||
               !equal(c,r13_-3400u,1)||!links(c)||!handlers(c,5)||
               !IrqBankBinding::mi_boot_complete()||!bat_.final_state(c)||
               !equal(c,ThreadInitWitness::StackBottom,0xdeadbabeu))return fail(6);
            stage_=20;return true;
        }
        const unsigned index=stage_==18?11u:stage_-1u;
        if(index<e_.edges.size()&&matches(c,e_.edges[index])){
            switch(stage_){
            case 1:if(c.gpr[1]!=sp_||c.hid2!=hid_)return fail(4);break;
            case 2:if(c.gpr[1]!=sp_||c.gpr[3]!=(hid_&~0x40000000u))return fail(4);break;
            case 3:
                if(c.gpr[1]!=sp_||c.hid2!=(hid_&~0x40000000u)||!equal(c,r13_-3400u,0))return fail(4);
                try{IrqBankBinding::enable_mi_boot();}catch(const std::exception&){return fail(4);}
                break;
            case 4:
                if(c.gpr[3]!=0xf0000000u||!IrqBankBinding::mi_boot_ready())return fail(4);
                break;
            case 5:case 6:case 7:case 8:case 9:{
                const unsigned n=stage_-5;
                if(c.gpr[3]!=n||c.gpr[4]!=Handler||!handlers(c,n)||
                   !equal(c,IrqTable+4*n,0))return fail(4);
                break;
            }
            case 10:if(c.gpr[3]!=Node||!handlers(c,5))return fail(4);break;
            case 11:if(!links(c)||!handlers(c,5)||!bat_.begin(c,IrqBankBinding::mi_boot_ready()))return fail(4);break;
            case 18:if(c.gpr[3]!=0x08000000u||!bat_.final_state(c))return fail(4);break;
            default:return fail(4);
            }
            ++stage_;return true;
        }
        // Only authenticated direct helper edges within the MI mask/unmask
        // and shutdown registration routines may interleave the main route.
        if(stage_<5||stage_==12||stage_>19||++extra_>128)return fail(5);
        for(auto e:e_.edges)if(addr==e.pc&&c.lr==e.lr)return fail(5);
        for(auto e:e_.helpers)if(matches(c,e))return true;
        return fail(5);
    }
private:
    MemoryInitExpectations e_;BatMappingWitness bat_;
    unsigned stage_=0,error_=0,extra_=0;
    uint32_t sp_=0,r2_=0,r13_=0,msr_=0,hid_=0;uint64_t start_=0;
    std::array<uint32_t,2> guards_{};
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    template<class Cpu>static bool equal(Cpu& c,uint32_t a,uint32_t w){
        return !(a&3u)&&a>=0x80000000u&&a<=0x817ffffcu&&c.mmu.get_ptr(a)&&c.mmu.get_ptr(a+3u)&&c.mmu.read32(a)==w;
    }
    template<class Cpu>static bool matches(Cpu& c,const VectorEdge& e){
        return c.pc==e.pc&&c.lr==e.lr&&equal(c,e.pc,e.entry_word)&&equal(c,e.lr-4,e.branch_word);
    }
    template<class Cpu>static bool handlers(Cpu& c,unsigned n){
        for(unsigned i=0;i<n;++i)if(!equal(c,IrqTable+4*i,Handler))return false;
        return true;
    }
    template<class Cpu>bool links(Cpu& c){
        return equal(c,r13_-3376u,AlarmNode)&&equal(c,r13_-3372u,Node)&&
            equal(c,AlarmNode+8,Node)&&equal(c,Node,0x80527040u)&&equal(c,Node+4,127)&&
            equal(c,Node+8,0)&&equal(c,Node+12,AlarmNode)&&
            equal(c,Node-4,guards_[0])&&equal(c,Node+16,guards_[1]);
    }
};
}
