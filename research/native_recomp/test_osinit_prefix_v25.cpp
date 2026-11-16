// Original-free native contract: authentic __start -> __init_data -> DBInit -> OSInit test boundary.
// Runs private original DOL code only when caller explicitly supplies it.
#include "runtime/cpu_context.h"
#include "loader/loader.h"
#include <algorithm>
#include <array>
#include <cstdint>
#include <cstring>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>
#include <vector>
namespace {
constexpr uint32_t START=0x8000403cu, POST=0x8052a844u, OS_RET_OWNER=0x805206acu, OS_RET_SYNTH=0x80520694u;
constexpr uint32_t OSINIT=0x80520670u, SAVE20=0x805450e8u;
constexpr uint32_t START_OS_RET_OWNER=0x80004160u, START_OS_RET_SYNTH=0x80004060u;
constexpr uint32_t OS_INIT_FLAG=0x8070dafcu, SYNTH_OS_MARKER=0x80037004u;
constexpr uint32_t DATA_RETURN=0x80004058u,DBINIT=0x804e5020u;
constexpr uint32_t TABLE=0x80006420u, INIT=0x80004238u;
constexpr uint32_t FLUSH=0x80004304u, COPY=0x80004338u,FILL=0x80004388u,SET=0x8000443cu;
constexpr uint32_t CACHE=0x80522540u,ERR=0x805230b8u,DBG=0x804e50b8u;
constexpr uint32_t L2_READ=0x804b7930u,L2_WRITE=0x804b7938u;
constexpr uint32_t ICE=0x805223bcu,DCE=0x80522280u;
constexpr uint32_t ORIGINAL_SP=0x80751cb8u,SYNTH_SP=0x80060000u;
uint64_t checks=0;
void check(bool result,const char*why){if(!result)throw std::runtime_error(why);++checks;}
uint32_t random32(uint32_t&state){state^=state<<13;state^=state>>17;state^=state<<5;return state;}
struct Span {uint32_t start,size;};
std::vector<Span> zero_table(nwii::runtime::CPUContext&ctx){
  std::vector<Span> v;
  for(unsigned i=0;i<4;++i){
    const uint32_t at=TABLE+0x90+8*i;
    const uint32_t address=ctx.mmu.read32(at),size=ctx.mmu.read32(at+4);
    if(size==0)break;
    check(address>=0x80000000u&&size<=1024*1024u,"BSS table range outside test limit");
    v.push_back({address,size});
  }
  return v;
}
}
namespace nwii::runtime {
bool g_trace_calls=true;
uint32_t g_watch_addr=0;
static std::array<uint64_t,5> data_calls{};
static uint64_t l2_reads=0,l2_writes=0,ic_calls=0,dc_calls=0,cache_calls=0;
static uint64_t post_stops=0,db_entries=0,os_entries=0,save_entries=0,unknown_calls=0,interpreter_calls=0;
static std::array<uint64_t,2> external_stubs{};
void trace_call(uint32_t addr, CPUContext&ctx){
  constexpr std::array<uint32_t,5> data{INIT,FLUSH,COPY,FILL,SET};
  const auto it=std::find(data.begin(),data.end(),addr);
  if(it!=data.end())++data_calls[static_cast<size_t>(it-data.begin())];
  else if(addr==CACHE){++cache_calls;check(ctx.lr==0x800042fcu,"cache entered from wrong guest LR");}
  else if(addr==L2_READ)++l2_reads;
  else if(addr==L2_WRITE)++l2_writes;
  else if(addr==ICE)++ic_calls;
  else if(addr==DCE)++dc_calls;
  else if(addr==OSINIT){++os_entries;}
  else if(addr==SAVE20){++save_entries;}
  else if(addr==DBINIT){
    ++db_entries;
    check(ctx.lr==0x8000415cu || ctx.lr==0x8000405cu, "DBInit guest LR mismatch");
  }
}
bool handle_syscall(CPUContext&ctx){
  if(ctx.pc==POST){
    const bool own=ctx.mmu.read32(0x80000048u)==0x004e5090u;
    check(ctx.lr==(own?OS_RET_OWNER:OS_RET_SYNTH),"wrong guest LR at synthetic OS time boundary");
    check(ctx.gpr[1]==(own?ORIGINAL_SP-8u-80u:SYNTH_SP-8u-96u),
          "wrong guest SP in original/synthetic OSInit prologue");
    ++post_stops;ctx.is_running=false;return true;}
  if(ctx.pc==DBG){++external_stubs[0];return true;}
  if(ctx.pc==ERR){
    check(ctx.gpr[3]==1u,"OSSetErrorHandler exception index differs");
    ++external_stubs[1];return true;
  }
  ++unknown_calls;throw std::runtime_error("unexpected syscall/native Wii service");
}
void interpret_step(CPUContext&){++interpreter_calls;throw std::runtime_error("interpreter fallback");}
bool process_pending_callbacks(CPUContext&){return false;}
void watch_hit(uint32_t,uint32_t,int){}
void GX_WGPIPE_Write8(uint8_t){}
void GX_WGPIPE_Write16(uint16_t){}
void GX_WGPIPE_Write32(uint32_t){}
void GX_WGPIPE_WriteF32(float){}
void GX_WGPIPE_WriteF64(double){}
uint16_t HW_Reg_Read16(uint32_t){return 0;}
uint32_t HW_Reg_Read32(uint32_t){return 0;}
void HW_Reg_Write16(uint32_t,uint16_t){}
void HW_Reg_Write32(uint32_t,uint32_t){}
}
extern "C" void run_game(nwii::runtime::CPUContext&);
int main(int argc,char**argv){
  if(argc!=3)return 2;
  const bool owner=std::string(argv[2])=="owner";
  if(!owner&&std::string(argv[2])!="synthetic")return 2;
  nwii::loader::Executable exe;
  check(exe.load_dol(argv[1]),"test DOL load failed");
  check(exe.entry_point==START&&exe.sections.size()==8,"unexpected DOL image layout");
  auto ctx=std::make_unique<nwii::runtime::CPUContext>();
  unsigned table_count=0;
  for(const auto&sec:exe.sections){
    if(!sec.is_bss&&!sec.is_text&&sec.address==TABLE){
      check(sec.size==0xb0u,"invalid copied relocation table");
      for(size_t i=0;i<sec.data.size();++i)ctx->mmu.write8(TABLE+uint32_t(i),sec.data[i]);
      ++table_count;
    }
  }
  check(table_count==1,"required DOL data table missing");
  const auto zero=zero_table(*ctx);
  check(zero.size()==(owner?3u:2u),"wrong zero-table mode/count");
  if(owner){
    check(zero[0].start==0x8061e900u&&zero[0].size==950236,"wrong owner BSS range 0");
    check(zero[1].start==0x8070ab60u&&zero[1].size==13164,"wrong owner BSS range 1");
    check(zero[2].start==0x80711c80u&&zero[2].size==56,"wrong owner BSS range 2");
  }
  uint32_t seed=0x9e3779b9u;
  const unsigned trials=owner?16u:16u;
  for(unsigned trial=0;trial<trials;++trial){
    auto&c=*ctx;
    for(auto&g:c.gpr)g=random32(seed);
    const bool ic_on=(trial&4u)==0,dc_on=(trial&2u)==0,l2_on=(trial&1u)==0;
    const uint32_t msr0=random32(seed)&~0x2000u;
    c.msr=msr0;
    c.hid0=(random32(seed)&0x00ff0000u)|(ic_on?0x8000u:0u)|(dc_on?0x4000u:0u);
    const uint32_t expected_hid0=c.hid0|0xc800u;
    c.hid2=random32(seed)&~0xa0000000u;
    const uint32_t expected_hid2=c.hid2|0xa0000000u;
    for(auto&q:c.gqr)q=0xffffffffu;
    const uint32_t old_l2=(random32(seed)&0xff00u)|(l2_on?0x80000000u:0);
    c.l2cr=old_l2;c.l2cr_busy_polls=0;
    const uint32_t ps_addr=owner?0x8070db08u:0x80034000u;
    const uint32_t fp_addr=owner?0x8070db10u:0x80034100u;
    const float expected_ps=static_cast<float>(-3.25-(trial%13)*.25);
    c.mmu.write_f32(ps_addr,1.5f+float(trial%11)*.125f);
    c.mmu.write_f32(ps_addr+4,expected_ps);
    const uint32_t fpscr=random32(seed);
    const uint64_t fpbits=0x3ff0000000000000ull|fpscr;
    c.mmu.write64(fp_addr,fpbits);
    c.mmu.write64(0x80034110u,fpbits);
    double expected_scalar=0;
    std::memcpy(&expected_scalar,&fpbits,sizeof(fpbits));
    for(unsigned k=0;k<32;++k){c.fpr[k]=0;c.ps1[k]=0;}
    c.fpscr=0xffffffffu;
    if(owner){
      for(const auto&span:zero){
        auto*ptr=c.mmu.get_ptr(span.start);
        check(ptr!=nullptr,"original BSS span outside MMU");
        std::memset(ptr,0x35+trial,span.size);
        c.mmu.write8(span.start-1,0xB5);
        c.mmu.write8(span.start+span.size,0xC5);
      }
      // Seed FP memory AFTER poisoning BSS, as FPR seed belongs to BSS.
      c.mmu.write_f32(ps_addr,1.5f+float(trial%11)*.125f);
      c.mmu.write_f32(ps_addr+4,expected_ps);
      c.mmu.write64(fp_addr,fpbits);
    } else {
      c.mmu.write32(0x80036000u,0xDEADBEEFu);
      c.mmu.write32(0x80036004u,0xDEADBEEFu);
    }
    const uint32_t sp=owner?ORIGINAL_SP:SYNTH_SP;
    c.gpr[1]=sp;
    c.pc=START;c.lr=0x80009998u;c.is_running=true;
    const auto before_data=nwii::runtime::data_calls;
    const auto before_ic=nwii::runtime::ic_calls, before_dc=nwii::runtime::dc_calls;
    const auto before_cache=nwii::runtime::cache_calls;
    const auto before_stubs=nwii::runtime::external_stubs;
    const auto before_stop=nwii::runtime::post_stops;
    const auto before_db=nwii::runtime::db_entries;
    const auto before_os=nwii::runtime::os_entries;
    const auto before_save=nwii::runtime::save_entries;
    c.mmu.write32(0x800000f4u,0);
    c.mmu.write32(0x80000034u,0);
    c.mmu.write32(0x80000044u,0xbadc0ffeu);
    c.mmu.write32(0x80000048u,0xaabbccddu);
    c.mmu.write32(0x80037000u,0xbaadf00du);
    c.mmu.write32(SYNTH_OS_MARKER,0xbaadf00du);
    c.mmu.write32(OS_INIT_FLAG,0u);
    const auto before_inst=c.inst_count;
    run_game(c);
    if(c.pc!=(owner?OS_RET_OWNER:OS_RET_SYNTH) || c.is_running){std::cerr<<std::hex<<"V25 TRACE PC="<<c.pc<<" LR="<<c.lr<<" r1="<<c.gpr[1]<<" r5="<<c.gpr[5]<<" r6="<<c.gpr[6]<<" r7="<<c.gpr[7]<<" r14="<<c.gpr[14]<<" r15="<<c.gpr[15]<<" running="<<c.is_running<<std::dec<<" dbentries="<<nwii::runtime::db_entries<<" stops="<<nwii::runtime::post_stops<<" inst="<<c.inst_count<<"\n";}
    check(!c.is_running&&c.pc==(owner?OS_RET_OWNER:OS_RET_SYNTH),"native guest did not stop at synthetic OS time service");
    check(c.lr==(owner?OS_RET_OWNER:OS_RET_SYNTH),"guest LR at time-service boundary changed");
    check(nwii::runtime::db_entries==before_db+1,"translated DBInit not entered exactly once");
    check(nwii::runtime::os_entries==before_os+1,"translated OSInit prefix never entered");
    check(nwii::runtime::save_entries==before_save+1,"translated register-save helper not invoked once");
    check(c.mmu.read32(sp-4)==(owner?START_OS_RET_OWNER:START_OS_RET_SYNTH),
          "OSInit prologue failed to save caller LR");
    const auto os_frame=sp-8u-(owner?80u:96u);
    check(c.gpr[1]==os_frame,"OSInit guest frame pointer changed");
    if(owner){
      check(c.mmu.read32(OS_INIT_FLAG)==1u,"original OS init-once guard flag not set");
      check(c.gpr[30]==0x806f4f00u&&c.gpr[31]==0x8060b7a8u,
            "original OSInit nonvolatile globals changed");
      for(unsigned reg=20;reg<32;++reg){
        const auto spill=c.mmu.read32((sp-8u)-48u+(reg-20u)*4u);
        check(spill==(reg==31?0x80004044u:0u),
              "original _savegpr_20 spilled unexpected preserved GPR state");
      }
      check(c.mmu.read32(0x80000044u)==0,"original startup low-memory clear failed");
      check(c.mmu.read32(0x80000048u)==0x004e5090u,"original DBInit OS debug pointer wrong");
      check(c.mmu.read32(0x8070d8a0u)==0x80000040u,"original DBInit low-memory base wrong");
      check(c.mmu.read32(0x8070d8a4u)==1,"original DBInit initialized flag wrong");
    } else {
      check(c.mmu.read32(0x80037000u)==0x55aau,"synthetic DBInit guest store wrong");
      check(c.mmu.read32(SYNTH_OS_MARKER)==0x707u,"synthetic OSInit guest marker missing");
      check(c.mmu.read32(sp-8u-48u)==c.gpr[24],"synthetic helper spill missing");
      check(c.mmu.read32(0x80000048u)==0xaabbccddu,"synthetic DBInit corrupted low-memory pointer");
    }
    check(c.mmu.read32(sp-8)==0xffffffffu,
          "__start stack backchain corruption");
    check(c.msr==(msr0|0x2000u),"hardware MSR state changed");
    check(c.hid0==expected_hid0&&c.hid2==expected_hid2,"cache/HID state changed");
    check(c.fpscr==fpscr,"original FPR initializer FPSCR differs");
    for(unsigned i=0;i<32;++i){
      check(c.fpr[i]==expected_scalar,"scalar FPR state changed");
      check(c.ps1[i]==expected_ps,"paired-single PS1 state changed");
      check(c.gqr[i%8]==0,"GQR not zeroed");
    }
    check(nwii::runtime::cache_calls==before_cache+1,"cache initializer not entered");
    check(nwii::runtime::ic_calls==before_ic+(owner?(ic_on?0u:1u):1u),"ICEnable branch count differs");
    check(nwii::runtime::dc_calls==before_dc+(owner?(dc_on?0u:1u):1u),"DCEnable branch count differs");
    check(nwii::runtime::external_stubs[1]==before_stubs[1]+1,"error-handler fixture was not invoked");
    check(nwii::runtime::post_stops==before_stop+1,"no bounded OSInit stop");
    check(nwii::runtime::data_calls[0]==before_data[0]+1,"native __init_data not entered");
    check(c.inst_count>before_inst+100,"too few guest instructions executed");
    if(owner){
      const std::array<uint64_t,5> expected{1,0,0,3,3};
      for(unsigned i=0;i<5;++i)
        check(nwii::runtime::data_calls[i]-before_data[i]==expected[i],"unexpected data helper call count");
      for(const auto&span:zero){
        const auto*ptr=c.mmu.get_ptr(span.start);
        for(uint32_t i=0;i<span.size;++i){
          const uint32_t address=span.start+i;
          const bool db_global=address>=0x8070d8a0u && address<0x8070d8a8u;
          const bool os_global=address>=OS_INIT_FLAG && address<OS_INIT_FLAG+4u;
          if(!db_global&&!os_global)check(ptr[i]==0,"original BSS byte not zero");
        }
        check(c.mmu.read8(span.start-1)==0xB5,"BSS underrun canary clobbered");
        check(c.mmu.read8(span.start+span.size)==0xC5,"BSS overrun canary clobbered");
      }
    } else {
      check(c.mmu.read32(0x80036000u)==0,"synthetic translated store did not run");
      check(c.mmu.read32(0x80036004u)==0xDEADBEEFu,"synthetic store overran neighboring word");
    }
  }
  check(nwii::runtime::unknown_calls==0&&nwii::runtime::interpreter_calls==0,"unexpected syscall/interpreter fallback");
  std::cout<<std::dec<<"PASS: "<<checks<<" V25 continuous original __start->DBInit->OSInit prefix->OS time boundary assertions; mode="
           <<(owner?"owner":"synthetic")<<" trials="<<trials<<" stop=0x"<<std::hex<<POST<<std::dec<<"\n";
}
