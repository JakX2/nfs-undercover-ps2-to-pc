#include "wii_full_start_witness.h"
#include <iostream>
#include <map>
#include <stdexcept>
using namespace undercover::wii;
using R=FullStartResult;
static void need(bool v,const char* why){if(!v)throw std::runtime_error(why);}
struct Mmu {
    std::map<uint32_t,uint32_t> memory;
    uint32_t* get_ptr(uint32_t a){auto it=memory.find(a&~3u);return it==memory.end()?nullptr:&it->second;}
    uint32_t read32(uint32_t a){return memory.at(a);}
};
struct Cpu {
    Mmu mmu;std::array<uint32_t,32> gpr{};
    uint32_t pc=0,lr=0;uint64_t inst_count=0;bool is_running=true;
};
int main(){
    FullStartExpectations e{0x80004000u,0x80004100u,0x80004200u,{1u,2u},{},{},{}};
    e.register_words.fill(0x60000000u);e.register_words.back()=0x4e800020u;
    e.hardware_words.fill(0x60000000u);e.register_result[1]=0x80001000u;e.register_result[13]=0x80002000u;
    const auto prepare=[&](){Cpu c;const auto load=[&](uint32_t a,const auto& words){for(std::size_t i=0;i<words.size();++i)c.mmu.memory[a+uint32_t(i*4u)]=words[i];};load(e.entry,e.entry_words);load(e.register_init,e.register_words);load(e.hardware_init,e.hardware_words);c.pc=e.entry;return c;};
    const auto enter_reg=[&](Cpu& c){c.pc=e.register_init;c.lr=e.entry+4u;c.inst_count=2;};
    const auto enter_hw=[&](Cpu& c){c.pc=e.hardware_init;c.lr=e.entry+8u;c.inst_count=40;c.gpr=e.register_result;};
    {auto c=prepare();FullStartWitness w(e);need(w.observe(c.pc,c)==R::Accepted&&w.stage()==1,"entry rejected");enter_reg(c);need(w.observe(c.pc,c)==R::Accepted&&w.stage()==2,"reg init rejected");enter_hw(c);need(w.observe(c.pc,c)==R::Complete&&w.stage()==3,"hardware boundary rejected");need(w.observe(c.pc,c)==R::Invalid,"duplicate completion");}
    {auto c=prepare();FullStartWitness w(e);c.mmu.memory.erase(e.entry+4u);need(w.observe(c.pc,c)==R::Invalid&&w.stage()==0,"missing entry word accepted");}
    {auto c=prepare();FullStartWitness w(e);need(w.observe(c.pc,c)==R::Accepted,"entry");enter_reg(c);c.lr=0;need(w.observe(c.pc,c)==R::Invalid,"wrong BL return accepted");}
    {auto c=prepare();FullStartWitness w(e);need(w.observe(c.pc,c)==R::Accepted,"entry");enter_reg(c);c.mmu.memory[e.register_init+8u]^=1u;need(w.observe(c.pc,c)==R::Invalid,"wrong register body accepted");}
    {auto c=prepare();FullStartWitness w(e);need(w.observe(c.pc,c)==R::Accepted,"entry");enter_reg(c);need(w.observe(c.pc,c)==R::Accepted,"reg");enter_hw(c);c.gpr[3]=1;need(w.observe(c.pc,c)==R::Invalid,"register mismatch accepted");}
    {auto c=prepare();FullStartWitness w(e);need(w.observe(c.pc,c)==R::Accepted,"entry");enter_reg(c);need(w.observe(c.pc,c)==R::Accepted,"reg");enter_hw(c);c.inst_count=37;need(w.observe(c.pc,c)==R::Invalid,"insufficient instruction progress accepted");}
    {auto c=prepare();FullStartWitness w(e);enter_reg(c);need(w.observe(c.pc,c)==R::Invalid,"skipped startup accepted");c=prepare();need(w.observe(c.pc,c)==R::Invalid,"failed witness reused");}
    std::cout<<"PASS: full-image entry, original branch LR and all GPR witness; negative controls\n";
}
