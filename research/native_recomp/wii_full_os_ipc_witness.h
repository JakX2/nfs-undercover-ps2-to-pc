#pragma once
#include <array>
#include <cstdint>

namespace undercover::wii {
struct IpcEdge {uint32_t pc,lr,branch_word,entry_word;};
struct OsIpcExpectations {std::array<IpcEdge,4> edges;};
// Complete-image lane requires valid runtime-owned MEM2/IPC metadata.
// The guest's own setters and IPC-copy routine remain authoritative.
class FullOsIpcWitness {
public:
    explicit FullOsIpcWitness(OsIpcExpectations e):e_(e){}
    unsigned stage() const{return stage_;}
    unsigned failure() const{return failure_;}
    bool active() const{return begun_&&stage_<4&&!failure_;}
    bool clamped() const{return lo_!=selected_;}
    template<class Cpu> bool begin(Cpu& c){
        if(begun_||failure_||!c.is_running||c.pc!=0x80520818u||c.lr!=c.pc||c.gpr[13]!=Sda||(c.msr&0x8000u))return fail(1);
        for(auto a:Inputs)if(!mapped(c,a))return fail(1);
        for(auto a:Globals)if(!mapped(c,a))return fail(1);
        for(auto a:Guards)if(!mapped(c,a))return fail(1);
        for(unsigned i=0;i<4;++i){inputs_[i]=c.mmu.read32(Inputs[i]);old_[i]=c.mmu.read32(Globals[i]);}
        for(unsigned i=0;i<Guards.size();++i)guards_[i]=c.mmu.read32(Guards[i]);
        lo_=inputs_[0];selected_=lo_<0x90000800u?0x90000800u:lo_;
        // The upper bound is exclusive; IPC may end exactly at MEM2 end.
        if(lo_<0x90000000u||selected_>=inputs_[1]||inputs_[1]>inputs_[2]||inputs_[2]>=inputs_[3]||inputs_[3]>0x94000000u)return fail(2);
        if((lo_|inputs_[1]|inputs_[2]|inputs_[3])&3u)return fail(2);
        sp_=c.gpr[1];r2_=c.gpr[2];msr_=c.msr;last_=c.inst_count;
        begun_=true;return true;
    }
    template<class Cpu> bool observe(uint32_t addr,Cpu& c){
        if(!active()||!c.is_running||c.pc!=addr||c.inst_count<=last_||c.gpr[1]!=sp_||c.gpr[2]!=r2_||c.gpr[13]!=Sda||c.msr!=msr_)return fail(3);
        const auto& e=e_.edges[stage_];
        if(addr!=e.pc||c.lr!=e.lr||!equal(c,addr,e.entry_word)||!equal(c,e.lr-4u,e.branch_word))return fail(4);
        for(unsigned i=0;i<4;++i)if(!equal(c,Inputs[i],inputs_[i]))return fail(5);
        for(unsigned i=0;i<Guards.size();++i)if(!equal(c,Guards[i],guards_[i]))return fail(6);
        const std::array<uint32_t,4> wanted{selected_,inputs_[1],inputs_[2],inputs_[3]};
        for(unsigned i=0;i<4;++i){const unsigned complete=i<2?i+1:3;if(!equal(c,Globals[i],stage_>=complete?wanted[i]:old_[i]))return fail(7);}
        if((stage_==0&&c.gpr[3]!=selected_)||(stage_==1&&c.gpr[3]!=inputs_[1]))return fail(8);
        ++stage_;last_=c.inst_count;return true;
    }
private:
    static constexpr uint32_t Sda=0x8070e8e0u;
    static constexpr std::array<uint32_t,4> Inputs{0x80003124u,0x80003128u,0x80003130u,0x80003134u};
    static constexpr std::array<uint32_t,4> Globals{Sda-16396u,Sda-3468u,Sda-16336u,Sda-3352u};
    static constexpr std::array<uint32_t,6> Guards{Sda-16400u,Sda-3472u,Sda-16392u,Sda-3464u,Sda-16340u,Sda-3348u};
    OsIpcExpectations e_;unsigned stage_=0,failure_=0;bool begun_=false;
    uint32_t sp_=0,r2_=0,msr_=0,lo_=0,selected_=0;uint64_t last_=0;
    std::array<uint32_t,4> inputs_{},old_{};std::array<uint32_t,6> guards_{};
    bool fail(unsigned r){if(!failure_)failure_=r;return false;}
    template<class Cpu> static bool mapped(Cpu& c,uint32_t a){return !(a&3u)&&a>=0x80000000u&&a<=0x817ffffcu&&c.mmu.get_ptr(a)&&c.mmu.get_ptr(a+3u);}
    template<class Cpu> static bool equal(Cpu& c,uint32_t a,uint32_t v){return mapped(c,a)&&c.mmu.read32(a)==v;}
};
}
