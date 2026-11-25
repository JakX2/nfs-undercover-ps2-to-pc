#include "wii_si_ack_binding_v672.h"
#include "wii_si_type_scheduler_v514.h"
#include <map>
#include <string>
using namespace undercover::wii;
using namespace nwii::runtime::hw;
constexpr uint32_t H=0x80004000u,A=0x80005000u,B=0x80006000u,
    Nop=0x60000000u,Blr=0x4e800020u,Store=0x90030000u,
    FirstCall=0x48001001u,SecondCall=0x48001ffdu,Other=0x100u;
struct Mmu{
    std::map<uint32_t,uint32_t> words;uint8_t byte=0;
    uint8_t* get_ptr(uint32_t a){return (a>=H&&a<H+32)||(a>=A&&a<A+8)||(a>=B&&a<B+16)?&byte:nullptr;}
    uint32_t read32(uint32_t a){return words.at(a);}
};
struct Cpu{
    Mmu mmu;std::array<uint32_t,32> gpr{};uint64_t inst_count=100;
    uint32_t pc=H,lr=0x80007000u,msr=0x32,dispatch_saved_ctx=0;
    bool is_running=true,in_callback=false;
};
static void need(bool ok){if(!ok)throw std::runtime_error("V689 integration assertion");}
int main(int argc,char** argv){
    need(argc==2);std::string mode=argv[1];
    pi_intsr=Other;pi_intmr=SiController::PI_SI;
    SiController ctl(pi_intsr);SiBinding binding(ctl);
    using Port=SiTypeScheduler::Port;
    SiTypeScheduler sched(ctl,{Port::absent(),Port::absent(),Port::absent(),Port::absent()},8);
    need(SiBinding::write32(0xcd006434u,0xc0010301u));sched.advance(1);sched.advance(9);
    Cpu c;c.mmu.words={{H,FirstCall},{H+4,SecondCall},{H+8,Store},{H+12,Nop},{A,Nop},{A+4,Blr},{B,Store},{B+4,Blr},{B+8,Nop}};
    v672::begin(c);
    if(mode=="out-of-order"){
        ++c.inst_count;v672::before(c,H+4,SecondCall,2,1);
        throw std::runtime_error("second helper escaped order guard");
    }
    ++c.inst_count;v672::before(c,H,FirstCall,1,1);
    c.pc=A;c.lr=H+4;v672::observe(A,c);
    ++c.inst_count;v680::before(c,A,Nop);
    ++c.inst_count;v680::before(c,A+4,Blr);
    c.pc=H+4;++c.inst_count;v672::before(c,H+4,SecondCall,2,1);
    c.pc=B;c.lr=mode=="wrong-lr"?H+4:H+8;v672::observe(B,c);
    if(mode=="gap")++c.inst_count;
    uint32_t word=mode=="nested"?0x48000101u:Store;
    c.mmu.words[B]=word;++c.inst_count;
    v688::before(c,B,word,mode=="nested"?1u:0u,mode=="nested"?1u:0u);
    if(mode.rfind("post-",0)==0){
        need(SiBinding::write32(0xcd006434u,0xe0010300u));
        c.mmu.words[B+4]=mode=="post-branch"?Blr:Store;
        ++c.inst_count;v688::before(c,B+4,c.mmu.words[B+4],0,0);
        need(si_completion_ack_trace.phase()==SiCompletionAckTrace::Phase::PostAck);
        if(mode=="post-start")SiBinding::write32(0xcd006434u,0xc0010303u);
        if(mode=="post-bad-length")SiBinding::write32(0xcd006434u,0xc0020305u);
        if(mode=="post-config")SiBinding::write32(0xcd006434u,0x40010300u);
        if(mode=="post-stale")++c.inst_count;
        need(SiBinding::write32(0xcd006438u,0x08000000u));
        need(ctl.read(SiController::Status)==0&&pi_intsr==Other&&!ctl.pending());
        c.mmu.words[B+8]=Store;++c.inst_count;v688::before(c,B+8,Store,0,0);
        need(SiBinding::write32(0xcd006480u,0x12345678u));
        need(ctl.read(SiController::Buffer)==0x12345678u);
        c.mmu.words[B+12]=Blr;
        if(mode=="post-cause")pi_intsr.fetch_or(SiController::PI_SI);
        ++c.inst_count;v688::before(c,B+12,Blr,0,0);
        c.pc=H+8;if(mode=="post-abi")c.gpr[14]^=1u;
        ++c.inst_count;v672::before(c,H+8,Store,0,0);
        throw std::runtime_error("post-ACK return escaped");
    }
    if(mode=="inside"||mode=="wrong-next"||mode=="stale"||mode=="unsupported"){
        if(mode=="stale")++c.inst_count;
        need(SiBinding::write32(0xcd006434u,mode=="unsupported"?0x80010300u:0xe0010300u));
        need(pi_intsr==Other&&pi_intmr==SiController::PI_SI);
        ++c.inst_count;
        v688::before(c,mode=="wrong-next"?B+8:B+4,mode=="wrong-next"?Nop:Blr,0,0);
        throw std::runtime_error("helper ACK escaped completion guard");
    }
    ++c.inst_count;v688::before(c,B+4,Blr,0,0);
    c.pc=H+8;if(mode=="abi")c.gpr[14]^=1u;
    ++c.inst_count;v672::before(c,H+8,Store,0,0);
    need(SiBinding::write32(0xcd806434u,0xe0010300u));
    need(pi_intsr==Other&&pi_intmr==SiController::PI_SI);
    ++c.inst_count;v672::before(c,H+12,Nop,0,0);
    throw std::runtime_error("handler ACK escaped completion guard");
}
