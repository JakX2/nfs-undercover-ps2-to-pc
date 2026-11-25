#include "runtime/cpu_context.h"
#include "undercover/wii_postack_os_leaf_v703.h"
#include "leaf_test.h"
#include <cstdlib>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>
#include <source_location>
using namespace undercover::wii;
#include "owner_leaf_input.h"
static PostAckOsLeaf leaves[]={PostAckOsLeaf({H,D,D+4u*uint32_t(disable_words.size()),caller[0],1}),
    PostAckOsLeaf({H+4,T,T+4u*uint32_t(time_words.size()),caller[1],2}),
    PostAckOsLeaf({H+12,R,R+4u*uint32_t(restore_words.size()),caller[3],3})};
static unsigned leaf_index=0;static bool started=false;static unsigned outer_polls=0;
static uint64_t time_first=0,time_last=0;
static unsigned time_reads=0;
static std::string mode;
static unsigned pending_reg=32;
static uint32_t expected_word=0;
static void need(bool ok,const std::source_location loc=std::source_location::current()){
    if(ok)return;
    const auto i=leaf_index<3?leaf_index:2u;
    std::cout<<"V715_OWNER_LEAF_ASSERT line="<<loc.line()<<" ordinal="<<i+1
        <<" stage="<<leaves[i].stage()<<" witness="<<leaves[i].failure()
        <<" time_reads="<<time_reads<<std::endl;
    std::_Exit(126);
}
[[noreturn]]static void fault(unsigned kind){
    const auto i=leaf_index<3?leaf_index:2u;
    std::cout<<"V716_OWNER_LEAF_FAULT kind="<<kind<<" ordinal="<<i+1
        <<" stage="<<leaves[i].stage()<<" witness="<<leaves[i].failure()
        <<" time_reads="<<time_reads<<" outer_polls="<<outer_polls<<std::endl;
    std::_Exit(126);
}
namespace leaf_test{
void before(nwii::runtime::CPUContext& c,uint32_t pc,uint32_t word){
    if(pending_reg<32){need(c.gpr[pending_reg]==expected_word);pending_reg=32;}
    if(pc>=H&&pc<H+24){
        if(started){
            if(mode=="corrupt"&&leaf_index==0)c.gpr[14]^=1u;
            const bool ok=leaves[leaf_index].returned(c,pc);
            if(mode=="corrupt"&&leaf_index==0){need(!ok&&leaves[leaf_index].failure()==4);std::cout<<"V714_REFUSAL reason=4"<<std::endl;std::_Exit(126);}
            need(ok);
            if(leaf_index==1){
                const uint64_t value=(uint64_t(c.gpr[3])<<32)|c.gpr[4];
                need(time_reads>=3&&value>=time_first&&value<=time_last&&leaves[leaf_index].polls()>=1);
            }
            ++leaf_index;started=false;
        }
        if(pc==H+8){need(leaf_index==2);return;}
        if(pc==H+16){
            need(leaf_index==3&&outer_polls==1&&c.msr==0x32u&&c.gpr[3]==0&&c.srr0==0x80009000u&&c.srr1==0x8032u);
            need(leaves[0].msr_writes()==1&&leaves[1].msr_writes()==0&&leaves[2].msr_writes()==1);
            std::cout<<"V715_OWNER_TIMEBASE rollover_retry="<<unsigned(time_reads>3)<<std::endl;
            std::cout<<"V714_LEAF_AOT roots=3 mtmsr=2 timebase=1 masked_loop_poll=1 native_return=3 fallback=0"<<std::endl;std::_Exit(0);
        }
        need(leaf_index<3&&leaves[leaf_index].start(c,pc,word));started=true;return;
    }
    need(started&&leaf_index<3);
    need(leaves[leaf_index].before(c,pc,word));
    const unsigned xo=(word>>1)&1023u,spr=((word>>11)&31u)*32u+((word>>16)&31u);
    if(leaf_index==1&&(word>>26)==31u&&(xo==371u||xo==339u)&&(spr==268u||spr==269u)){
        const uint64_t sample=c.read_timebase();
        if(!time_reads)time_first=sample;
        time_last=sample;++time_reads;
        pending_reg=(word>>21)&31u;
        expected_word=uint32_t(spr==269u?sample>>32:sample);
    }
}}
namespace nwii::runtime{
bool g_trace_calls=true;uint32_t g_watch_addr=0;
void trace_call(uint32_t pc,CPUContext& c){
    if(pc==H)return;
    need(started&&leaf_index<3&&leaves[leaf_index].entry(pc,c));
}
bool process_pending_callbacks(CPUContext& c){
    if(started){if(!leaves[leaf_index].poll(c))fault(1);return false;}
    ++outer_polls;return false;
}
bool handle_syscall(CPUContext&){fault(2);}
void interpret_step(CPUContext&){fault(3);}
void micro_interpret(CPUContext&,uint32_t,uint32_t){fault(4);}
void note_null_call(uint32_t,uint32_t){fault(5);}
void watch_hit(uint32_t,uint32_t,int){}
void GX_WGPIPE_Write8(uint8_t){fault(7);}void GX_WGPIPE_Write16(uint16_t){fault(7);}void GX_WGPIPE_Write32(uint32_t){fault(7);}
void GX_WGPIPE_WriteF32(float){fault(7);}void GX_WGPIPE_WriteF64(double){fault(7);}
uint16_t HW_Reg_Read16(uint32_t){fault(6);}
uint32_t HW_Reg_Read32(uint32_t){fault(6);}
void HW_Reg_Write16(uint32_t,uint16_t){fault(6);}
void HW_Reg_Write32(uint32_t,uint32_t){fault(6);}
}
extern "C" void run_game(nwii::runtime::CPUContext&);
int main(int argc,char**argv)try{
    need(argc==3);mode=argv[1];auto cpu=std::make_unique<nwii::runtime::CPUContext>();auto& c=*cpu;
    auto put=[&](uint32_t a,const auto& w){for(auto x:w){c.mmu.write32(a,x);a+=4;}};
    put(H,caller);put(D,disable_words);put(T,time_words);put(R,restore_words);
    for(unsigned r=0;r<32;++r)c.gpr[r]=0x12340000u+r;
    c.gpr[1]=0x80011000u;c.pc=H;c.lr=0x80008000u;c.msr=0x32u;c.srr0=0x80009000u;c.srr1=0x8032u;
    c.is_running=true;c.dispatch_saved_ctx=0;c.inst_count=std::stoull(argv[2],nullptr,0);run_game(c);fault(8);
}catch(const std::out_of_range&){fault(9);}
 catch(const std::logic_error&){fault(10);}
 catch(const std::runtime_error&){fault(11);}
 catch(const std::exception&){fault(12);}
 catch(...){fault(13);}
