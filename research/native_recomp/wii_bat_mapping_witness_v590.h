#pragma once
#include "wii_exception_vector_witness_v457.h"
#include <array>
#include <utility>
namespace undercover::wii {
struct BatMappingExpectations {
    VectorEdge mapper;
    std::array<VectorEdge,2> trampoline;
    std::array<uint32_t,2> entry_word,return_word;
};
// The expected register sequence was independently exercised by the V65
// owner harness. This witness checks native register state, not access
// translation or actual Broadway permission enforcement.
class BatMappingWitness {
public:
    static constexpr std::array<uint32_t,2> Entry{0x805270c4u,0x80527144u};
    static constexpr std::array<uint32_t,2> Resume{0x805275d0u,0x80527600u};
    static constexpr std::array<std::pair<uint32_t,uint32_t>,32> Writes{{
        {536,0},{537,2},{536,0x800001ffu},{528,0},{529,2},{528,0x800001ffu},
        {540,0},{541,0x01000002u},{540,0x810000ffu},{532,0},{533,0x01000002u},{532,0x810000ffu},
        {568,0},{569,0x10000002u},{568,0x900003ffu},{560,0},{561,0},
        {570,0},{571,0x1000002au},{570,0xd00007ffu},{562,0},{563,0},
        {572,0},{573,0x12000002u},{572,0x920001ffu},{564,0},{565,0},
        {574,0},{575,0x13000002u},{574,0x9300007fu},{566,0},{567,0}
    }};
    explicit BatMappingWitness(const BatMappingExpectations& e):e_(e){}
    unsigned stage()const noexcept{return stage_;}
    unsigned failure()const noexcept{return error_;}
    template<class Cpu>bool begin(Cpu& c,bool mi_ready){
        if(stage_||error_||!mi_ready||!c.is_running||!matches(c,e_.mapper)||
           c.gpr[3]!=0x000ba2cfu||(c.msr&0x8000u)||(c.msr&0x30u)!=0x30u||
           c.dispatch_saved_ctx||!equal(c,0x80003100u,0x01800000u)||
           !equal(c,0x80003104u,0x01800000u)||!equal(c,0x8000311cu,0x04000000u)||
           !equal(c,0x80003120u,0x93400000u)||
           uint64_t(c.bat_write_count)+Writes.size()>c.bat_write_sprs.size()||
           c.bat_write_sprs.size()!=c.bat_write_values.size())return fail(1);
        base_=c.bat_write_count;initial_=c.bat_registers;
        sp_=c.gpr[1];r2_=c.gpr[2];r13_=c.gpr[13];msr_=c.msr;last_=c.inst_count;
        stage_=1;return true;
    }
    template<class Cpu>bool observe(uint32_t addr,Cpu& c){
        if(error_||stage_<1||stage_>6||!c.is_running||c.pc!=addr||c.dispatch_saved_ctx||
           c.gpr[2]!=r2_||c.gpr[13]!=r13_||c.inst_count<=last_||
           c.inst_count-last_>100000u)return fail(2);
        const unsigned lane=(stage_-1)/3,phase=(stage_-1)%3;
        const unsigned before=lane?12u:0u,after=lane?32u:12u;
        if(phase==0){
            if(!matches(c,e_.trampoline[lane])||c.gpr[3]!=Entry[lane]||
               c.lr!=Resume[lane]||c.msr!=msr_||!registers(c,before)||
               c.gpr[1]>sp_||sp_-c.gpr[1]>256u)return fail(3);
            map_sp_=c.gpr[1];
        }else if(phase==1){
            if(addr!=Entry[lane]||c.lr!=Resume[lane]||c.gpr[1]!=map_sp_||
               c.srr0!=(Entry[lane]&0x3fffffffu)||(c.msr&0x30u)||
               c.msr!=c.srr1||(c.msr&0x8000u)||
               !equal(c,addr,e_.entry_word[lane])||!registers(c,before))return fail(4);
        }else{
            if(addr!=Resume[lane]||c.lr!=addr||c.gpr[1]!=map_sp_||
               c.srr0!=addr||c.srr1!=msr_||c.msr!=msr_||
               !equal(c,addr,e_.return_word[lane])||!registers(c,after))return fail(5);
        }
        ++stage_;last_=c.inst_count;return true;
    }
    template<class Cpu>bool final_state(Cpu& c){
        if(error_||stage_!=7||!c.is_running||c.msr!=msr_||
           c.gpr[2]!=r2_||c.gpr[13]!=r13_||!registers(c,32))return fail(6);
        return true;
    }
private:
    BatMappingExpectations e_;
    unsigned stage_=0,error_=0,base_=0;
    uint32_t sp_=0,map_sp_=0,r2_=0,r13_=0,msr_=0;uint64_t last_=0;
    std::array<uint32_t,32> initial_{};
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    template<class Cpu>bool registers(Cpu& c,unsigned n)const{
        if(uint64_t(c.bat_write_count)!=uint64_t(base_)+n)return false;
        auto expected=initial_;
        for(unsigned i=0;i<n;++i){
            auto [spr,value]=Writes[i];
            if(c.bat_write_sprs[base_+i]!=spr||c.bat_write_values[base_+i]!=value)return false;
            const unsigned index=spr<=543?spr-528:16+spr-560;
            expected[index]=value;
        }
        return c.bat_registers==expected;
    }
    template<class Cpu>static bool equal(Cpu& c,uint32_t a,uint32_t w){
        return !(a&3u)&&a>=0x80000000u&&a<=0x817ffffcu&&c.mmu.get_ptr(a)&&c.mmu.get_ptr(a+3u)&&c.mmu.read32(a)==w;
    }
    template<class Cpu>static bool matches(Cpu& c,const VectorEdge& e){
        return c.pc==e.pc&&c.lr==e.lr&&equal(c,e.pc,e.entry_word)&&equal(c,e.lr-4,e.branch_word);
    }
};
}
