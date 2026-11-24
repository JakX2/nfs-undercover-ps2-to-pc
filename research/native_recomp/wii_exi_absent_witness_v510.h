#pragma once
#include "wii_exi_id_witness_v504.h"
namespace undercover::wii {
// Both removable slots are absent. A sticky transfer-complete status
// from the prior device ID is legitimate; presence is a different bit.
class ExiAbsentTrace {
public:
    bool begin() noexcept{if(active_||bad_||reads_)return false;active_=true;return true;}
    void mmio(bool write,unsigned offset,uint32_t value)noexcept{
        if(!active_)return;
        if(write||reads_>=2||offset!=20u*reads_||(value&~WiiIrqBanks::TC_INT)){bad_=true;return;}
        ++reads_;
    }
    void completion()noexcept{if(active_)bad_=true;}
    unsigned reads()const{return reads_;}
    bool finish()noexcept{const bool ok=active_&&!bad_&&reads_==2;active_=false;return ok;}
private:unsigned reads_=0;bool active_=false,bad_=false;
};
inline thread_local ExiAbsentTrace exi_absent_trace{};
struct ExiAbsentExpectations{
    std::array<VectorEdge,5> edges; // two ID entries, shared Probe, disable/restore
    VectorEdge version;
    uint32_t first_return,returns[2],version_pointer;
};
class ExiAbsentWitness {
public:
    explicit ExiAbsentWitness(const ExiAbsentExpectations& e):e_(e){}
    unsigned stage()const{return stage_;}
    unsigned failure()const{return error_;}
    template<class Cpu>bool begin(Cpu& c){
        if(stage_||error_||!c.is_running||!equal(c,0x804efab0u,e_.first_return)||
           c.gpr[3]!=1||!equal(c,c.gpr[13]-3824u,exi_id_completion.id())||
           !equal(c,0x806f156cu,0)||!exi_absent_trace.begin())return fail(1);
        sp_=c.gpr[1];r2_=c.gpr[2];r13_=c.gpr[13];msr_=c.msr;last_=c.inst_count;
        for(unsigned i=0;i<32;++i){
            if(!mapped(c,0x80003040u+i*4,4))return fail(1);
            irq_[i]=c.mmu.read32(0x80003040u+i*4);
        }
        stage_=1;return true;
    }
    template<class Cpu>bool observe(uint32_t addr,Cpu& c){
        if(error_||stage_<1||stage_>7||!c.is_running||c.inst_count<last_||
           c.inst_count-last_>1000000u||c.gpr[2]!=r2_||c.gpr[13]!=r13_||
           !equal(c,r13_-3824u,exi_id_completion.id()))return fail(2);
        const unsigned ch=stage_<=3?0u:1u;
        if(stage_==1||stage_==4){
            if(matches(c,e_.edges[ch])){
                if(c.gpr[1]!=sp_||c.gpr[3]!=ch||c.gpr[4]!=0||c.gpr[5]!=sp_+8u||
                   c.msr!=msr_||exi_absent_trace.reads()!=ch)return fail(3);
                ++stage_;last_=c.inst_count;return true;
            }
        }else if(stage_==2||stage_==5){
            if(matches(c,e_.edges[2])){
                if(c.gpr[1]!=sp_-64u||c.gpr[3]!=ch||c.msr!=msr_||exi_absent_trace.reads()!=ch)return fail(4);
                ++stage_;last_=c.inst_count;return true;
            }
        }else if(stage_==3||stage_==6){
            const uint32_t ret=ch?0x804efb34u:0x804efafcu;
            if(addr==ret){
                if(!equal(c,ret,e_.returns[ch])||c.gpr[1]!=sp_||c.gpr[3]!=0||
                   c.msr!=msr_||exi_absent_trace.reads()!=ch+1u||
                   !equal(c,0x800030c0u+ch*4,0))return fail(5);
                ++stage_;last_=c.inst_count;return true;
            }
        }else if(stage_==7&&matches(c,e_.version)){
            if(c.gpr[1]!=sp_||c.msr!=msr_||c.gpr[3]!=e_.version_pointer||
               !equal(c,0x8070a748u,e_.version_pointer)||!mapped(c,e_.version_pointer,1)||
               !equal(c,0x800030c0u,0)||!equal(c,0x800030c4u,0)||
               !equal(c,0x806f156cu,0)||!exi_absent_trace.finish())return fail(6);
            for(unsigned i=0;i<32;++i)if(!equal(c,0x80003040u+i*4,irq_[i]))return fail(6);
            stage_=8;return true;
        }
        // Save/restore helpers and exact original Probe interrupt calls can
        // execute within the two bounded ID frames. Never force a return.
        if(addr!=c.pc||addr&3u||!mapped(c,addr,4)||++extra_>128u||
           addr==0x804f02a0u||c.lr==0x804ef164u||c.lr==0x804ef170u||
           addr==0x804efb80u||addr==0x804ef3ecu||addr==0x804ee984u||addr==0x804eed9cu||
           addr==0x804efd7cu||addr==0x804ef09cu||addr==0x80521018u||
           addr==0x804efafcu||addr==0x804efb34u)return fail(7);
        for(unsigned i=3;i<5;++i)if(addr==e_.edges[i].pc&&c.lr==e_.edges[i].lr){
            if((stage_!=3&&stage_!=6)||!matches(c,e_.edges[i]))return fail(7);
        }
        return true;
    }
private:
    ExiAbsentExpectations e_;unsigned stage_=0,error_=0,extra_=0;
    uint32_t sp_=0,r2_=0,r13_=0,msr_=0;uint64_t last_=0;std::array<uint32_t,32> irq_{};
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    template<class Cpu>static bool mapped(Cpu& c,uint32_t a,unsigned n){
        return n&&a>=0x80000000u&&uint64_t(a)+n<=0x81800000ull&&c.mmu.get_ptr(a)&&c.mmu.get_ptr(a+n-1u);
    }
    template<class Cpu>static bool equal(Cpu& c,uint32_t a,uint32_t w){return !(a&3u)&&mapped(c,a,4)&&c.mmu.read32(a)==w;}
    template<class Cpu>static bool matches(Cpu& c,const VectorEdge& e){return c.pc==e.pc&&c.lr==e.lr&&equal(c,e.pc,e.entry_word)&&equal(c,e.lr-4,e.branch_word);}
};
}
