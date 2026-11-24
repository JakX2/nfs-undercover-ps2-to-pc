#pragma once
#include "wii_exi_absent_witness_v510.h"
namespace undercover::wii {
struct SiEntryExpectations {
    VectorEdge exi_version,si_entry,si_version,rate;
    uint32_t report_tail_word,exi_version_pointer,si_version_pointer;
};
// Observe the real version tail and subsequent original SI call edges.
// Do not emulate OSReport, write guest state, or synthesize a return.
class SiEntryWitness {
public:
    explicit SiEntryWitness(const SiEntryExpectations& e):e_(e){}
    unsigned stage()const{return stage_;}
    unsigned failure()const{return error_;}
    template<class Cpu>bool begin(Cpu& c){
        if(stage_||error_||!c.is_running||!matches(c,e_.exi_version)||
           c.gpr[3]!=e_.exi_version_pointer||!equal(c,0x8070a748u,e_.exi_version_pointer)||
           !equal(c,c.gpr[13]-3824u,exi_id_completion.id())||c.gpr[1]<0x80000100u)return fail(1);
        sp_=c.gpr[1];r2_=c.gpr[2];r13_=c.gpr[13];msr_=c.msr;last_=c.inst_count;
        for(unsigned i=0;i<32;++i){if(!mapped(c,0x80003040u+4*i,4))return fail(1);
            irq_[i]=c.mmu.read32(0x80003040u+4*i);}
        stage_=1;return true;
    }
    template<class Cpu>bool observe(uint32_t addr,Cpu& c){
        if(error_||stage_<1||stage_>5||!c.is_running||c.inst_count<last_||
           c.inst_count-last_>2000000u||c.gpr[2]!=r2_||c.gpr[13]!=r13_||
           !equal(c,r13_-3824u,exi_id_completion.id()))return fail(2);
        if(addr==0x80521024u){
            const bool exi=stage_==1;
            if((!exi&&stage_!=4)||!equal(c,addr,e_.report_tail_word)||
               c.lr!=(exi?e_.exi_version.lr:e_.si_version.lr)||
               c.gpr[1]!=(exi?sp_:sp_+16u)||c.msr!=msr_||
               c.gpr[3]!=r13_-16436u||c.gpr[4]!=(exi?e_.exi_version_pointer:e_.si_version_pointer))
                return fail(3);
            ++stage_;last_=c.inst_count;return true;
        }
        if(addr==e_.si_entry.pc){
            if(stage_!=2||!matches(c,e_.si_entry)||c.gpr[1]!=sp_+32u||c.msr!=msr_||
               !equal(c,r13_-3148u,0)||!equal(c,0x806f156cu,0)||
               !equal(c,0x800030c0u,0)||!equal(c,0x800030c4u,0))return fail(4);
            ++stage_;last_=c.inst_count;return true;
        }
        if(addr==e_.si_version.pc&&c.lr==e_.si_version.lr){
            if(stage_!=3||!matches(c,e_.si_version)||c.gpr[1]!=sp_+16u||c.msr!=msr_||
               c.gpr[3]!=e_.si_version_pointer||!equal(c,0x8070aa70u,e_.si_version_pointer)||
               !mapped(c,e_.si_version_pointer,1))return fail(5);
            ++stage_;last_=c.inst_count;return true;
        }
        if(addr==e_.rate.pc){
            if(stage_!=5||!matches(c,e_.rate)||c.gpr[1]!=sp_+16u||c.msr!=msr_||
               c.gpr[3]!=0||!equal(c,0x80619a64u,0))return fail(6);
            for(unsigned i=0;i<4;++i)if(!equal(c,0x806fe340u+32*i,0xffffffffu))return fail(6);
            for(unsigned i=0;i<32;++i)if(!equal(c,0x80003040u+4*i,irq_[i]))return fail(6);
            stage_=6;return true;
        }
        // Original report implementation and save/restore helpers may be
        // visited. A trace at the report entry is not used to infer return.
        if(addr!=c.pc||addr&3u||!mapped(c,addr,4)||++extra_>512u||
           addr==e_.exi_version.pc||addr==0x804ef9bcu||addr==0x804efd7cu||
           addr==0x804ef09cu||addr==0x805269bcu||addr==0x8053238cu)return fail(7);
        return true;
    }
private:
    SiEntryExpectations e_;unsigned stage_=0,error_=0,extra_=0;
    uint32_t sp_=0,r2_=0,r13_=0,msr_=0;uint64_t last_=0;std::array<uint32_t,32> irq_{};
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    template<class Cpu>static bool mapped(Cpu& c,uint32_t a,unsigned n){
        return n&&a>=0x80000000u&&uint64_t(a)+n<=0x81800000ull&&c.mmu.get_ptr(a)&&c.mmu.get_ptr(a+n-1u);
    }
    template<class Cpu>static bool equal(Cpu& c,uint32_t a,uint32_t w){return !(a&3u)&&mapped(c,a,4)&&c.mmu.read32(a)==w;}
    template<class Cpu>static bool matches(Cpu& c,const VectorEdge& e){return c.pc==e.pc&&c.lr==e.lr&&equal(c,e.pc,e.entry_word)&&equal(c,e.lr-4,e.branch_word);}
};
}
