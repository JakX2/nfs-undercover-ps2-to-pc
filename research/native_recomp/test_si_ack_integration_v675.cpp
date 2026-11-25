#include "wii_si_ack_binding_v672.h"
#include "wii_si_type_scheduler_v514.h"
#include <map>
#include <stdexcept>
#include <string>
using namespace undercover::wii;
using namespace nwii::runtime::hw;
constexpr uint32_t First=v672::handler_first,Store=0x90030000u,Nop=0x60000000u,Other=0x100u;
struct Mmu{
    std::map<uint32_t,uint32_t> words;uint8_t byte=0;
    uint8_t* get_ptr(uint32_t a){return a>=First&&a<v672::handler_end?&byte:nullptr;}
    uint32_t read32(uint32_t a){return words.at(a);}
};
struct Cpu{
    Mmu mmu;uint64_t inst_count=100;uint32_t pc=First,msr=0x32,dispatch_saved_ctx=0;
    bool is_running=true,in_callback=false;
};
static void need(bool ok){if(!ok)throw std::runtime_error("V675 fixture assertion");}
int main(int argc,char** argv){
    need(argc==2);const std::string mode=argv[1];
    pi_intsr=Other;pi_intmr=SiController::PI_SI;
    SiController ctl(pi_intsr);SiBinding binding(ctl);
    using Port=SiTypeScheduler::Port;
    SiTypeScheduler sched(ctl,{Port::absent(),Port::absent(),Port::absent(),Port::absent()},8);
    // Native binding is pass-through when the bounded witness is inactive.
    need(SiBinding::write32(0xcd006480u,0x12345678u));
    need(SiBinding::read32(0xcd806480u)==0x12345678u);
    // The type-discovery command is byte zero, not the RAM control pattern.
    need(SiBinding::write32(0xcd006480u,0u));
    Cpu c;c.mmu.words={{First,Store},{First+4,Nop},{First+8,Nop}};
    v672::before(c,First,Store,0,0);need(!v672::active());
    need(SiBinding::write32(0xcd006434u,0xc0010301u));sched.advance(1);sched.advance(9);
    need(ctl.read(SiController::Control)==0xe0010300u&&pi_intsr==(Other|SiController::PI_SI));
    if(mode=="idle"){
        need(SiBinding::write32(0xcd006434u,0xe0010300u));need(pi_intsr==Other&&!v672::active());
        std::cout<<"V675_IDLE passed=1"<<std::endl;return 0;
    }
    if(mode=="masked")c.msr|=0x8000u;
    v672::begin(c);need(v672::active());need(!v672::poll(c));++c.inst_count;
    if(mode=="direct"||mode=="indirect"||mode=="unknown"){
        const uint32_t w=mode=="direct"?0x48000009u:mode=="indirect"?0x4e800421u:0x4e800021u;
        c.mmu.words[First]=w;
        v672::before(c,First,w,mode=="unknown"?0u:1u,mode=="direct"?1u:mode=="indirect"?2u:0u);
        throw std::runtime_error("helper escaped call gate");
    }
    if(mode=="tamper")c.mmu.words[First]=Nop;
    if(mode=="pre-gap")++c.inst_count;
    v672::before(c,First,Store,0,0);
    if(mode=="stale"){++c.inst_count;}
    need(SiBinding::write32(mode=="mirror"?0xcd806434u:0xcd006434u,mode=="unsupported"?0x80010300u:0xe0010300u));
    need(pi_intsr==Other&&pi_intmr==SiController::PI_SI&&ctl.read(SiController::Status)==0x08000000u);
    c.inst_count+=mode=="gap"?2:1;
    const uint32_t next=mode=="wrong-next"?First+8:First+4;
    v672::before(c,next,Nop,0,0);
    throw std::runtime_error("ACK observer failed to stop");
}
