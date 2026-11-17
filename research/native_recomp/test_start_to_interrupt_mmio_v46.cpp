// Recovered V46 native contract: continuous __start executes original DC/IC cache loops.
// Runs private original DOL code only when caller explicitly supplies it.
#include "runtime/cpu_context.h"
#include "loader/loader.h"
#include <algorithm>
#include <array>
#include <cstdint>
#include <cstring>
#include <iostream>
#include <fstream>
#include <memory>
#include <stdexcept>
#include <string>
#include <vector>
namespace {
constexpr uint32_t START=0x8000403cu, POST_OWNER=0x80526674u, POST_SYNTH=0x8052a844u;
constexpr uint32_t OS_RET_OWNER=0x8052664cu, OS_RET_SYNTH=0x80520694u;
constexpr uint32_t OSINIT=0x80520670u, SAVE20=0x805450e8u;
constexpr uint32_t TIME=0x8052a844u, GETTIME=0x8052a824u;
constexpr uint32_t INT_DISABLE=0x805265acu, INT_RESTORE=0x805265d4u, EXEC=0x80523b1cu, PERF=0x804b7964u;
constexpr uint32_t MFHID0=0x804b7920u,MTHID0=0x804b7928u,SPEC=0x804b7a00u,NONIEEE=0x804b7a28u,HID4=0x804b7a30u,REPORT=0x80522f00u;
constexpr uint32_t START_OS_RET_OWNER=0x80004160u, START_OS_RET_SYNTH=0x80004060u;
constexpr uint32_t OS_INIT_FLAG=0x8070dafcu, SYNTH_OS_MARKER=0x80037004u;
constexpr uint32_t DATA_RETURN=0x80004058u,DBINIT=0x804e5020u;
constexpr uint32_t TABLE=0x80006420u, INIT=0x80004238u;
constexpr uint32_t FLUSH=0x80004304u, COPY=0x80004338u,FILL=0x80004388u,SET=0x8000443cu;
constexpr uint32_t CACHE=0x80522540u,ERR=0x805230b8u,DBG=0x804e50b8u;
constexpr uint32_t L2_READ=0x804b7930u,L2_WRITE=0x804b7938u;
constexpr uint32_t ICE=0x805223bcu,DCE=0x80522280u;
constexpr uint32_t ORIGINAL_SP=0x80751cb8u,SYNTH_SP=0x80060000u;
constexpr uint32_t R13=0x8070e8e0u,BOOT_BASE=R13-3512u,BOOT_RECORD=R13-3516u;
constexpr uint32_t ARENA_LO=0x80521d60u,ARENA_HI=0x80521d48u;
constexpr uint32_t MEM2_LO=0x80521d68u,MEM2_HI=0x80521d50u,IPC=0x8052ae80u;
constexpr uint32_t EXCEPTION=0x80520bf4u,EXC_SOURCE_WORD=0x80520f28u;
constexpr uint32_t DCFLUSH=0x80522320u,ICINVALID=0x80522378u;
constexpr uint32_t MARK=0x804e50a0u,EXC_TEMPLATE_DST=0x80520f18u;
constexpr uint32_t SOURCE_TEMPLATE=0x80520ec0u,ORACLE_GUEST=0x90050000u;
constexpr uint32_t SYSCALL=0x805290c8u,SYSCALL_SOURCE=0x805290a8u;
constexpr uint32_t SYSCALL_DEST=0x80000c00u,SYSCALL_LEN=28u;
constexpr uint32_t ALARM=0x805210ccu,GETEXC=0x80520eb0u,
    SETEXC=0x80520e9cu,SHUTDOWN=0x80527b4cu;
constexpr uint32_t ALARM_HANDLER=0x805217bcu,SHUTDOWN_NODE=0x8060bcb8u;
constexpr uint32_t INTERRUPT=0x8052661cu,IRQ_STOP=0x8052664cu;
constexpr uint32_t IRQ_TABLE=0x80003040u,IRQ_GLOBAL=R13-3408u;
constexpr uint32_t LOW_MASK_PRE=0x800000c0u,LOW_MASK_A=0x800000c4u,
  LOW_MASK_B=0x800000c8u,LOW_MASK_POST=0x800000ccu;
constexpr uint32_t MODULE=0x80526d30u,MODULE_PRE=0x800030c4u,
    MODULE_LO=0x800030c8u,MODULE_MID=0x800030ccu,
    MODULE_HI=0x800030d0u,MODULE_POST=0x800030d4u;
constexpr uint32_t ALARM_HEAD=R13-3496u,SHUTDOWN_HEAD=R13-3376u,
    SHUTDOWN_TAIL=R13-3372u;
constexpr uint32_t VECTOR_DEST=0x80000100u,VECTOR_LEN=0x98u;
constexpr uint32_t MEM2_LO_HINT=0x80003124u,MEM2_HI_HINT=0x80003128u;
constexpr uint32_t MEM2_LO_GLOBAL=R13-16396u,MEM2_HI_GLOBAL=R13-3468u;
constexpr uint32_t IPC_LO_GLOBAL=R13-16336u,IPC_HI_GLOBAL=R13-3352u;
constexpr uint32_t IPC_LO_INPUT=0x80003130u,IPC_HI_INPUT=0x80003134u;
constexpr uint32_t LO_GLOBAL=R13-16400u,HI_GLOBAL=R13-3472u;
constexpr uint32_t BOOT_FALLBACK=R13-3520u,BOOT_FIELD=R13-3216u;
constexpr uint32_t BOOT_MODE=R13-16864u,BOOT_HINT=0x8000310cu;
struct ExceptionStop {};
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
static uint64_t time_entries=0, gettime_entries=0, disable_entries=0, restore_entries=0;
static uint32_t observed_stop_pc=0;
static uint64_t time_global_checks=0;
static uint64_t exec_entries=0;
static std::array<uint64_t,6> perf_entries{};
static std::array<uint64_t,5> hardware_entries{};
static std::array<uint64_t,2> arena_entries{};
static std::array<uint64_t,2> mem2_entries{};
static uint64_t ipc_entries=0;
static uint64_t exception_entries=0;
static uint64_t marker_entries=0;
static uint64_t dcflush_entries=0,icinvalid_entries=0;
static uint64_t syscall_entries=0;
static uint64_t alarm_entries=0,alarm_get_entries=0,
    alarm_set_entries=0,shutdown_entries=0,module_entries=0;
static uint64_t irq_entries=0,irq_memset_entries=0,irq_fill_entries=0;
static uint64_t unexpected_mmio=0;
static std::vector<std::pair<uint32_t,uint32_t>> mmio_writes;
static uint64_t exception_restore_entries=0;
static uint64_t exception_epilogue_debug_entries=0;
static uint32_t cache_sync_entry=0,cache_isync_entry=0;
void trace_call(uint32_t addr, CPUContext&ctx){
  constexpr std::array<uint32_t,5> data{INIT,FLUSH,COPY,FILL,SET};
  const auto it=std::find(data.begin(),data.end(),addr);
  if(it!=data.end()){
    ++data_calls[static_cast<size_t>(it-data.begin())];
    if(addr==SET && ctx.lr==IRQ_STOP){
      check(ctx.gpr[3]==IRQ_TABLE && ctx.gpr[4]==0u && ctx.gpr[5]==128u,
            "original IRQ memset received incorrect destination/zero/count");
      ++irq_memset_entries;
    }
    if(addr==FILL && ctx.gpr[3]==IRQ_TABLE){
      check(ctx.lr==0x80004454u,
            "original IRQ __fill_mem reached via incorrect guest BL return");
      ++irq_fill_entries;
    }
  }
  else if(addr==CACHE){++cache_calls;check(ctx.lr==0x800042fcu,"cache entered from wrong guest LR");}
  else if(addr==L2_READ)++l2_reads;
  else if(addr==L2_WRITE)++l2_writes;
  else if(addr==ICE)++ic_calls;
  else if(addr==DCE)++dc_calls;
  else if(addr==OSINIT){++os_entries;}
  else if(addr==SAVE20){++save_entries;}
  else if(addr==TIME){++time_entries;}
  else if(addr==GETTIME){++gettime_entries;}
  else if(addr==INT_DISABLE){
    ++disable_entries;
    // This entry is the *second* disable call, from original OSInit at B4.
    // The authentic system-time return registers must have been stored by
    // original PPC at AC and B0 before the helper receives control.
    if(ctx.lr==0x805206b8u){
      check(ctx.mmu.read32(0x8070db30u)==ctx.gpr[3],
            "original system time high word differs before second interrupt disable");
      check(ctx.mmu.read32(0x8070db34u)==ctx.gpr[4],
            "original system time low word differs before second interrupt disable");
      ++time_global_checks;
    }
  }
  else if(addr==INT_RESTORE){++restore_entries;}
  else if(addr==EXEC){
    check(ctx.lr==0x805206c0u, "original execparams called with wrong return LR");
    ++exec_entries;
  }
  else if(addr>=PERF && addr<PERF+48 && (addr-PERF)%8==0){
    const unsigned i=(addr-PERF)/8;
    check(ctx.lr==0x805206c8u+8u*i,
          "original perf helper guest BL return address changed");
    check(ctx.gpr[3]==0u,
          "original MMCR/PMC helper argument is not zero");
    ++perf_entries[i];
  }
  else if(addr==HID4){
    check(ctx.lr==0x805206f8u && ctx.gpr[3]==0x83900000u,
          "original HID4 call did not receive authentic OSInit argument");
    ++hardware_entries[0];
  }
  else if(addr==SPEC){
    check(ctx.lr==0x805206fcu,
          "original speculation call has incorrect guest return LR");
    ++hardware_entries[1];
  }
  else if(addr==NONIEEE){
    check(ctx.lr==0x80520700u,
          "original non-IEEE FP helper has incorrect guest return LR");
    ++hardware_entries[2];
  }
  else if(addr==MFHID0 && ctx.lr==0x804b7a10u){
    ++hardware_entries[3];
  }
  else if(addr==MTHID0 && ctx.lr==0x804b7a18u){
    ++hardware_entries[4];
  }
  else if(addr==ARENA_LO){
    check(ctx.lr==0x805207ecu,"original OSSetMEM1ArenaLo return LR incorrect");
    ++arena_entries[0];
  }
  else if(addr==ARENA_HI){
    check(ctx.lr==0x80520818u,"original OSSetMEM1ArenaHi return LR incorrect");
    ++arena_entries[1];
  }
  else if(addr==MEM2_LO){
    check(ctx.lr==0x80520890u,
          "original OSSetMEM2ArenaLo return LR incorrect");
    ++mem2_entries[0];
  }
  else if(addr==MEM2_HI){
    check(ctx.lr==0x805208a4u,
          "original OSSetMEM2ArenaHi return LR incorrect");
    ++mem2_entries[1];
  }
  else if(addr==IPC){
    check(ctx.lr==0x805208a8u,"genuine original IPC-buffer return LR changed");
    ++ipc_entries;
  }
  else if(addr==EXCEPTION){
    check(ctx.lr==0x805208acu,
          "original OSExceptionInit call did not preserve guest return LR");
    ++exception_entries;
  }
  else if(addr==MARK){
    check(ctx.lr==0x80520cf4u,
          "authentic original exception-mark BL guest return LR changed");
    // Each original exception-vector iteration probes its own index.
    // The zero-mask fast path reaches this helper once per vector.
    check(ctx.gpr[3]==uint32_t(marker_entries%15u),
          "original Wii exception mark helper vector index is out of sequence");
    ++marker_entries;
  }
  else if(addr==SYSCALL){
    check(ctx.lr==0x805208b0u,
          "original OSInit __OSInitSystemCall native call LR incorrect");
    check(ctx.gpr[1]==ORIGINAL_SP-8u-80u,
          "original syscall installer entered with wrong OSInit frame");
    ++syscall_entries;
  }
  else if(addr==ALARM){
    check(ctx.lr==0x805208b4u && ctx.gpr[1]==ORIGINAL_SP-8u-80u,
          "original OSInit->__OSInitAlarm guest LR or stack frame differs");
    ++alarm_entries;
  }
  else if(addr==GETEXC){
    check(ctx.lr==ALARM+0x14u,
          "original __OSGetExceptionHandler callsite LR incorrect");
    ++alarm_get_entries;
  }
  else if(addr==SETEXC){
    check(ctx.lr==ALARM+0x3cu,
          "original __OSSetExceptionHandler callsite LR incorrect");
    ++alarm_set_entries;
  }
  else if(addr==SHUTDOWN){
    check(ctx.lr==ALARM+0x48u,
          "original shutdown registration callsite LR incorrect");
    ++shutdown_entries;
  }
  else if(addr==MODULE){
    check(ctx.lr==0x805208b8u && ctx.gpr[1]==ORIGINAL_SP-8u-80u,
          "original __OSModuleInit native entry LR/OSInit frame incorrect");
    ++module_entries;
  }
  else if(addr==INTERRUPT){
    check(ctx.lr==0x805208bcu && ctx.gpr[1]==ORIGINAL_SP-8u-80u,
          "native original __OSInterruptInit entry LR/OSInit SP incorrect");
    ++irq_entries;
  }
  else if(addr==DCFLUSH){
    check(ctx.lr==(dcflush_entries%16u==15u?0x80529104u:0x80520da8u),
          "original exception/syscall DCFlushRangeNoSync BL return LR changed");
    // One cumulative cache-ordering baseline, taken at the first handler.
    if(ctx.guest_flush_count==0u){
      cache_sync_entry=ctx.guest_sync_count;
      cache_isync_entry=ctx.guest_isync_count;
    }
    ++dcflush_entries;
  }
  else if(addr==ICINVALID){
    check(ctx.lr==(icinvalid_entries%16u==15u?0x80529114u:0x80520db8u),
          "original exception/syscall ICInvalidateRange BL return LR changed");
    ++icinvalid_entries;
  }
  else if(addr==0x80545134u){
    check(ctx.lr==0x80520e64u,
          "original Wii _restgpr_20 did not receive epilogue BL return LR");
    check(ctx.gpr[29]==15u && ctx.gpr[28]==EXC_SOURCE_WORD,
          "original Wii completed exception loop not observed at restore entry");
    check(ctx.gpr[1]==ORIGINAL_SP-8u-80u-64u,
          "original Wii exception stack pointer incorrect before _restgpr_20");
    ++exception_restore_entries;
  }
  else if(addr==DBINIT){
    ++db_entries;
    check(ctx.lr==0x8000415cu || ctx.lr==0x8000405cu, "DBInit guest LR mismatch");
  }
}
bool handle_syscall(CPUContext&ctx){
  const bool own=ctx.mmu.read32(0x80000048u)==0x004e5090u;
  if(ctx.pc==(own?POST_OWNER:POST_SYNTH)){
    check(ctx.lr==(own?OS_RET_OWNER:OS_RET_SYNTH),"wrong guest LR at V26 owner or synthetic stop");
    check(ctx.gpr[1]==(own?ORIGINAL_SP-8u-80u-32u:SYNTH_SP-8u-96u),
          "original interrupt prefix did not allocate authentic nested stack frame");
    observed_stop_pc=ctx.pc;
    ++post_stops;ctx.is_running=false;
    if(own)throw ExceptionStop{};  // prevent synthetic BLR after exact guest PC
    return true;}
  if(ctx.pc==DBG){
    ++external_stubs[0];
    // Count the authentic terminal OSExceptionInit BL at 0x80520E58
    // separately from other bounded debug-service invocations in __start.
    if(ctx.lr==0x80520e5cu)++exception_epilogue_debug_entries;
    return true;
  }
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
uint16_t HW_Reg_Read16(uint32_t){
 ++unexpected_mmio;throw std::runtime_error("unexpected Wii MMIO read16");
}
uint32_t HW_Reg_Read32(uint32_t){
 ++unexpected_mmio;throw std::runtime_error("unexpected Wii MMIO read32");
}
void HW_Reg_Write16(uint32_t,uint16_t){
 ++unexpected_mmio;throw std::runtime_error("unexpected Wii MMIO write16");
}
void HW_Reg_Write32(uint32_t addr,uint32_t value){
 // Test-only original guest MMIO observation, NOT a production PI/IOS model.
 if(addr!=0x0c003004u && addr!=0x0d000034u){
   ++unexpected_mmio;
   throw std::runtime_error("unexpected Wii MMIO write32 address");
 }
 mmio_writes.emplace_back(addr,value);
}
}
extern "C" void run_game(nwii::runtime::CPUContext&);
int main(int argc,char**argv){
  if(argc!=3)return 2;
  const bool owner=std::string(argv[2])=="owner";
  if(!owner&&std::string(argv[2])!="synthetic")return 2;
  nwii::loader::Executable exe;
  check(exe.load_dol(argv[1]),"test DOL load failed");
  check(exe.entry_point==START&&exe.sections.size()==(owner?9u:8u),"unexpected DOL image layout");
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
  std::vector<uint8_t> original_handler;
  if(owner){
    unsigned handlers=0;
    for(const auto&sec:exe.sections){
      if(!sec.is_bss&&!sec.is_text&&sec.address==ORACLE_GUEST){
        check(sec.size==VECTOR_LEN && sec.data.size()==VECTOR_LEN,
              "private original exception-vector template oracle has invalid size");
        original_handler.assign(sec.data.begin(),sec.data.end());
        ++handlers;
      }
    }
    check(handlers==1 && original_handler.size()==VECTOR_LEN,
          "missing unique owner-original handler template in private DOL");
  }
  // Source-backed original exception template word from the PRIVATE fixture.
  // NWiiRuntime's minimal test MMU does not automatically map all PPC text.
  uint32_t exception_word=0;
  if(owner){
    unsigned matches=0;
    for(const auto& sec:exe.sections){
      if(!sec.is_bss && sec.address<=EXC_SOURCE_WORD &&
         uint64_t(EXC_SOURCE_WORD)+4u<=uint64_t(sec.address)+sec.size){
        const size_t off=EXC_SOURCE_WORD-sec.address;
        check(off+4<=sec.data.size(),
              "original exception literal not in private DOL memory span");
        exception_word=(uint32_t(sec.data[off])<<24)|
                       (uint32_t(sec.data[off+1])<<16)|
                       (uint32_t(sec.data[off+2])<<8)|
                        uint32_t(sec.data[off+3]);
        ++matches;
      }
    }
    check(matches==1,"original exception template word missing/ambiguous");
  }
  std::array<uint8_t,SYSCALL_LEN> original_syscall{};
  if(owner){
    unsigned sources=0;
    for(const auto& section:exe.sections){
      if(!section.is_bss && section.address<=SYSCALL_SOURCE &&
         uint64_t(SYSCALL_SOURCE)+SYSCALL_LEN<=
           uint64_t(section.address)+section.data.size()){
        const size_t off=SYSCALL_SOURCE-section.address;
        for(size_t i=0;i<original_syscall.size();++i)
          original_syscall[i]=section.data[off+i];
        ++sources;
      }
    }
    check(sources==1,
          "V46 private owner syscall handler source is not mapped uniquely");
  }
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
    c.mmcr0=0x12345678u; c.mmcr1=0x9abcdef0u;
    c.hid4=random32(seed);
    for(unsigned k=0;k<4;++k)c.pmc[k]=0x10000u+k;
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
    const auto before_terminal_debug=nwii::runtime::exception_epilogue_debug_entries;
    const auto before_stop=nwii::runtime::post_stops;
    const auto before_db=nwii::runtime::db_entries;
    const auto before_os=nwii::runtime::os_entries;
    const auto before_save=nwii::runtime::save_entries;
    const auto before_time=nwii::runtime::time_entries;
    const auto before_gettime=nwii::runtime::gettime_entries;
    const auto before_disable=nwii::runtime::disable_entries;
    const auto before_restore=nwii::runtime::restore_entries;
    const auto before_time_global=nwii::runtime::time_global_checks;
    const auto before_hardware=nwii::runtime::hardware_entries;
    const auto before_arena=nwii::runtime::arena_entries;
    const auto before_mem2=nwii::runtime::mem2_entries;
    const auto before_ipc=nwii::runtime::ipc_entries;
    const auto before_exception=nwii::runtime::exception_entries;
    const auto before_marker=nwii::runtime::marker_entries;
    const auto before_exception_restore=nwii::runtime::exception_restore_entries;
    const auto before_exec=nwii::runtime::exec_entries;
    const auto before_perf=nwii::runtime::perf_entries;
    // Diagnostics are reset per trial; they do not affect guest cache state.
    c.guest_flush_count=0;c.guest_invalidate_count=0;
    c.guest_sync_count=0;c.guest_isync_count=0;
    const auto before_dcflush=nwii::runtime::dcflush_entries;
    const auto before_icinvalid=nwii::runtime::icinvalid_entries;
    const auto before_syscall=nwii::runtime::syscall_entries;
    const auto before_alarm=nwii::runtime::alarm_entries;
    const auto before_alarm_get=nwii::runtime::alarm_get_entries;
    const auto before_alarm_set=nwii::runtime::alarm_set_entries;
    const auto before_shutdown=nwii::runtime::shutdown_entries;
    const auto before_module=nwii::runtime::module_entries;
    const auto before_irq=nwii::runtime::irq_entries;
    const auto before_irq_memset=nwii::runtime::irq_memset_entries;
    const auto before_irq_fill=nwii::runtime::irq_fill_entries;
    const auto before_mmio=nwii::runtime::mmio_writes.size();
    c.mmu.write32(0x800000f4u,0);
    const uint32_t arena_hint=0x80102000u+(trial*0x100u);
    c.mmu.write32(BOOT_HINT,arena_hint);
    c.mmu.write32(0x80003110u,0u); // no MEM1 arena-high hint
    const uint32_t mem2_low_hint=0x90002000u+trial*0x100u;
    const uint32_t mem2_high_hint=0x93500000u+trial*0x100u;
    c.mmu.write32(MEM2_LO_HINT,mem2_low_hint);
    c.mmu.write32(MEM2_HI_HINT,mem2_high_hint);
    const uint32_t ipc_lo=0x90003000u+trial*0x120u;
    const uint32_t ipc_hi=0x93600000u+trial*0x120u;
    c.mmu.write32(IPC_LO_INPUT,ipc_lo);
    c.mmu.write32(IPC_HI_INPUT,ipc_hi);
    c.mmu.write32(IPC_LO_INPUT-4u,0xD13ACAFEu);
    c.mmu.write32(IPC_HI_INPUT+4u,0xBABE1234u);
    if(owner){
      c.mmu.write32(0x80000060u,1u+trial); // original exception fast path
      for(uint32_t i=0;i<VECTOR_LEN;++i)
        c.mmu.write8(SOURCE_TEMPLATE+i,original_handler[i]);
      c.mmu.write32(EXC_SOURCE_WORD,exception_word);
      c.mmu.write32(EXC_TEMPLATE_DST,0xDADAC0DEu);
      c.mmu.write32(EXC_TEMPLATE_DST-4u,0x42434342u);
      c.mmu.write32(EXC_TEMPLATE_DST+4u,0x47494947u);
      // This MMU test has no original game's vector offset .data mapped.
      // Provide synthetic offsets and adjacent canaries for all fifteen
      // guest vectors; their payloads still come from the owner's DOL.
      for(uint32_t vector=0;vector<15u;++vector){
        const uint32_t dest=VECTOR_DEST+vector*0x100u;
        c.mmu.write32(0x8060bbe0u+4u*vector,0x100u+vector*0x100u);
        c.mmu.write8(dest-1u,0xB6u);
        for(uint32_t i=0;i<VECTOR_LEN;++i)c.mmu.write8(dest+i,0xD3u);
        c.mmu.write8(dest+VECTOR_LEN,0xB7u);
        c.mmu.write32(0x80003000u+4u*vector,0xBEEA0000u+vector);
      }
      c.mmu.write32(0x8000303cu,0xDEADBEEFu);
      // The synthetic MMU maps text-as-data only when explicitly seeded.
      // Use the owner-original, SHA-authenticated 28-byte syscall stub.
      for(uint32_t i=0;i<SYSCALL_LEN;++i)
        c.mmu.write8(SYSCALL_SOURCE+i,original_syscall[i]);
      c.mmu.write8(SYSCALL_SOURCE-1u,0xABu);
      c.mmu.write8(SYSCALL_SOURCE+SYSCALL_LEN,0xBCu);
      // Independently authored alarm and shutdown-list test inputs.
      // __init_data clears BSS during native continuous __start as normal.
      c.mmu.write32(ALARM_HEAD,0x11112222u+trial);
      c.mmu.write32(ALARM_HEAD+4u,0x33334444u+trial);
      c.mmu.write32(SHUTDOWN_HEAD,0u);
      c.mmu.write32(SHUTDOWN_TAIL,0u);
      c.mmu.write32(SHUTDOWN_NODE,0xFACA0000u+trial);
      c.mmu.write32(SHUTDOWN_NODE+4u,100u+trial);
      c.mmu.write32(SHUTDOWN_NODE+8u,0xAACA0000u+trial);
      c.mmu.write32(SHUTDOWN_NODE+12u,0xBBCA0000u+trial);
      c.mmu.write32(SHUTDOWN_NODE+16u,0xCCCA0000u+trial);
      // Authored per-trial module globals/canaries, verifying the exact
      // three-word owner-original low-memory zeroing without overrun.
      c.mmu.write32(MODULE_PRE,0x6A6A6A6Au);
      c.mmu.write32(MODULE_LO,0xB0000001u+trial*0x101u);
      c.mmu.write32(MODULE_MID,0xB0000002u+trial*0x101u);
      c.mmu.write32(MODULE_HI,0xB0000003u+trial*0x101u);
      c.mmu.write32(MODULE_POST,0x7B7B7B7Bu);
      // Table begins immediately after the existing 15 exception pointers.
      for(uint32_t i=0;i<128u;++i)
        c.mmu.write8(IRQ_TABLE+i,uint8_t((trial*0x13u+i*7u+3u)&0xffu));
      c.mmu.write8(IRQ_TABLE+128u,0xC5u);
      c.mmu.write32(LOW_MASK_PRE,0x1952A052u);
      c.mmu.write32(LOW_MASK_A,0xAC000001u+trial);
      c.mmu.write32(LOW_MASK_B,0xAC000101u+trial);
      c.mmu.write32(LOW_MASK_POST,0x4952A052u);
    }
    c.mmu.write32(0x80000030u,0u); // no alternate heap override
    c.mmu.write32(0x80000034u,0);
    c.mmu.write32(0x80000044u,0xbadc0ffeu);
    c.mmu.write32(0x80000048u,0xaabbccddu);
    c.mmu.write32(0x80037000u,0xbaadf00du);
    c.mmu.write32(SYNTH_OS_MARKER,0xbaadf00du);
    c.mmu.write32(OS_INIT_FLAG,0u);
    const auto before_inst=c.inst_count;
    bool exception_stop=false;
    if(owner){
      try{run_game(c);}catch(const ExceptionStop&){exception_stop=true;}
      check(exception_stop,"exception initialization did not reach exact test-only syscall");
    }else run_game(c);
    if(nwii::runtime::observed_stop_pc!=(owner?POST_OWNER:POST_SYNTH) || c.is_running){std::cerr<<std::hex<<"V26 TRACE PC="<<c.pc<<" LR="<<c.lr<<" r1="<<c.gpr[1]<<" r5="<<c.gpr[5]<<" r6="<<c.gpr[6]<<" r7="<<c.gpr[7]<<" r14="<<c.gpr[14]<<" r15="<<c.gpr[15]<<" running="<<c.is_running<<std::dec<<" dbentries="<<nwii::runtime::db_entries<<" stops="<<nwii::runtime::post_stops<<" inst="<<c.inst_count<<"\n";}
    check(!c.is_running && nwii::runtime::observed_stop_pc==(owner?POST_OWNER:POST_SYNTH),
          "native syscall callback did not observe exact test-only PowerPC instruction PC");
    check(c.lr==(owner?OS_RET_OWNER:OS_RET_SYNTH),"guest LR after original time/interrupt service changed");
    check(nwii::runtime::db_entries==before_db+1,"translated DBInit not entered exactly once");
    check(nwii::runtime::os_entries==before_os+1,"translated OSInit prefix never entered");
    check(nwii::runtime::save_entries==before_save+(owner?2u:1u),"original nested GPR-save helper call count differs");
    check(c.mmu.read32(sp-4)==(owner?START_OS_RET_OWNER:START_OS_RET_SYNTH),
          "OSInit prologue failed to save caller LR");
    // Original OSExceptionInit has returned after restoring its own 64-byte
    // frame. The OSInit frame itself is still live at this bounded checkpoint.
    const auto current_frame=sp-8u-(owner?80u+32u:96u);
    check(c.gpr[1]==current_frame,"OSInit guest frame pointer changed");
    if(owner){
      check(nwii::runtime::time_entries==before_time+1, "original OS time service was not called");
      check(nwii::runtime::gettime_entries==before_gettime+1, "original OS timebase helper missing");
      check(nwii::runtime::disable_entries==before_disable+2, "original post-time interrupt disable helper missing");
      check(nwii::runtime::restore_entries==before_restore+1, "original time interrupt restoration missing");
      check(nwii::runtime::time_global_checks==before_time_global+1,
            "original time was not stored before the second interrupt call");
      check(nwii::runtime::exec_entries==before_exec+1,
            "original __OSGetExecParams function was not entered");
      for(unsigned i=0;i<before_hardware.size();++i)
        check(nwii::runtime::hardware_entries[i]==before_hardware[i]+1,
              "original HID4/speculation/FP helper execution count changed");
      check(c.hid4==0x83900000u,"authentic OSInit HID4 value was not written");
      check(c.gpr[13]==R13,"original continuous startup r13 small-data base differs");
      // r3 is a PowerPC caller-saved register. The cache helpers may
      // overwrite it; verify their actual line operations and memory bounds
      // below instead of asserting a post-call register value.
      check(nwii::runtime::syscall_entries==before_syscall+1u,
            "original __OSInitSystemCall was not dispatched exactly once");
      check(nwii::runtime::alarm_entries==before_alarm+1u &&
            nwii::runtime::alarm_get_entries==before_alarm_get+1u &&
            nwii::runtime::alarm_set_entries==before_alarm_set+1u &&
            nwii::runtime::shutdown_entries==before_shutdown+1u,
            "original Wii alarm/exception/shutdown native function dispatch count differs");
      check(nwii::runtime::module_entries==before_module+1u,
            "genuine Wii __OSModuleInit native dispatch not observed exactly once");
      check(nwii::runtime::irq_entries==before_irq+1u &&
            nwii::runtime::irq_memset_entries==before_irq_memset+1u &&
            nwii::runtime::irq_fill_entries==before_irq_fill+1u,
            "native __OSInterruptInit/memset/__fill_mem dispatch counts differ");
      check(c.mmu.read32(IRQ_GLOBAL)==IRQ_TABLE,
            "original Wii __OSInterruptInit failed to install IRQ table pointer");
      check(c.gpr[3]==0xCD000000u && c.gpr[4]==0xCC000000u &&
            c.gpr[5]==0xF0u && c.gpr[6]==0u &&
            c.gpr[0]==0x40000000u,
            "original Wii interrupt MMIO register operands differ");
      check(c.mmu.read32(LOW_MASK_A)==0u &&
            c.mmu.read32(LOW_MASK_B)==0u,
            "original interrupt low-memory mask zeroing failed");
      check(c.mmu.read32(LOW_MASK_PRE)==0x1952A052u &&
            c.mmu.read32(LOW_MASK_POST)==0x4952A052u,
            "original interrupt low-memory masking overran surrounding canaries");
      check(nwii::runtime::mmio_writes.size()==before_mmio+2u,
            "original Wii interrupt MMIO write count differs");
      check(nwii::runtime::mmio_writes.at(before_mmio)==
            std::make_pair(0x0c003004u,0xF0u) &&
            nwii::runtime::mmio_writes.at(before_mmio+1u)==
            std::make_pair(0x0d000034u,0x40000000u),
            "native Wii MMIO destination/value/order differs");
      check(nwii::runtime::unexpected_mmio==0u,
            "unplanned Wii MMIO access occurred during startup");
      check(c.mmu.read32(0x8000303cu)==0xDEADBEEFu &&
            c.mmu.read8(IRQ_TABLE+128u)==0xC5u,
            "native IRQ memset clobbered table boundary canaries");
      for(uint32_t i=0;i<128u;++i)
        check(c.mmu.read8(IRQ_TABLE+i)==0u,
              "native original Wii memset/__fill_mem failed to zero IRQ table");
      check(c.mmu.read32(MODULE_LO)==0u &&
            c.mmu.read32(MODULE_MID)==0u &&
            c.mmu.read32(MODULE_HI)==0u,
            "original Wii module initializer failed to clear three low-memory globals");
      check(c.mmu.read32(MODULE_PRE)==0x6A6A6A6Au &&
            c.mmu.read32(MODULE_POST)==0x7B7B7B7Bu,
            "original Wii module initializer corrupted neighboring low memory");
      check(nwii::runtime::dcflush_entries==before_dcflush+16u,
            "original exception/syscall DCFlushRangeNoSync not dispatched sixteen times");
      check(nwii::runtime::icinvalid_entries==before_icinvalid+16u,
            "original exception/syscall ICInvalidateRange not dispatched sixteen times");
      check(c.guest_flush_count==83u && c.guest_invalidate_count==83u,
            "original exception/syscall guest cache-operation counts differ");
      check(c.guest_sync_count-nwii::runtime::cache_sync_entry==32u &&
            c.guest_isync_count-nwii::runtime::cache_isync_entry==16u,
            "original exception/syscall PPC sync/isync ordering differs");
      check(c.guest_flush_lines.size()>=83u &&
            c.guest_invalidate_lines.size()>=83u,
            "native guest cache trace cannot hold 83 original lines");
      for(uint32_t i=0;i<75u;++i){
        const uint32_t vector=i/5u,line=i%5u;
        const uint32_t pc=VECTOR_DEST+vector*0x100u+line*32u;
        check(c.guest_flush_lines[i]==pc,
              "original Wii 15-vector data-cache line ordering incorrect");
        check(c.guest_invalidate_lines[i]==pc,
              "original Wii 15-vector instruction-cache ordering incorrect");
      }
      for(uint32_t line=0;line<8u;++line){
        const uint32_t addr=SYSCALL_DEST+32u*line;
        check(c.guest_flush_lines[75u+line]==addr,
              "original syscall data-cache flush line ordering incorrect");
        check(c.guest_invalidate_lines[75u+line]==addr,
              "original syscall instruction-cache line ordering incorrect");
      }
      check(c.guest_last_flush==SYSCALL_DEST+0xe0u &&
            c.guest_last_invalidate==SYSCALL_DEST+0xe0u,
            "original Wii last syscall cache-maintenance line differs");
      check(c.ctr==0u,
            "original PowerPC bdnz template loop did not exhaust CTR");
      check(nwii::runtime::marker_entries==before_marker+15u,
            "authentic __DBIsExceptionMarked not dispatched for every vector");
      check(nwii::runtime::exception_restore_entries==before_exception_restore+1u,
            "original Wii _restgpr_20 was not executed exactly once");
      check(c.gpr[29]==0u,
            "original Wii exception-vector loop failed to restore caller r29");
      check(c.gpr[31]==0x80000000u,
            "original Wii MMIO prefix lost r31 MEM1 base before IRQ epilogue");
      check(c.mmu.read32(R13-3552u)==0x80003000u,
            "original Wii exception handler-table global was not installed");
      check(c.mmu.read32(0x8070d8a0u)==0x80000040u &&
            c.mmu.read32(0x80000044u)==0u,
            "original debug marker pointer or zero mask changed");
      check(c.mmu.read32(EXC_TEMPLATE_DST)==0x60000000u,
            "original PPC template clearing loop did not store exactly one NOP");
      check(c.mmu.read32(EXC_TEMPLATE_DST-4u)==0x42434342u &&
            c.mmu.read32(EXC_TEMPLATE_DST+4u)==0x47494947u,
            "original PPC template-clearing loop corrupted neighboring canaries");
      check(nwii::runtime::exception_entries==before_exception+1,
            "genuine OSExceptionInit original entry not reached exactly once");
      check(nwii::runtime::exception_epilogue_debug_entries==before_terminal_debug+1u,
            "V46 original OSExceptionInit terminal DBPrintf BL callback not observed once");
      check(nwii::runtime::external_stubs[0]>=before_stubs[0]+1u,
            "V46 no bounded DBPrintf callback observed during native startup");
      check(c.gpr[28]==0u && c.gpr[27]==0u,
            "original Wii _restgpr_20 did not restore caller r27/r28");
      check(c.mmu.read32(0x80000060u)==1u+trial,
            "exception source low-memory branch flag changed");
      std::vector<uint8_t> expected_handler=original_handler;
      auto expected_word=[&](uint32_t pc,uint32_t value){
        check(pc>=SOURCE_TEMPLATE && uint64_t(pc)+4u<=uint64_t(SOURCE_TEMPLATE)+VECTOR_LEN,
              "original handler test oracle word outside private template");
        const uint32_t offset=pc-SOURCE_TEMPLATE;
        for(unsigned j=0;j<4;++j)
          expected_handler[offset+j]=uint8_t(value>>(24u-8u*j));
      };
      expected_word(EXC_TEMPLATE_DST-4u,0x42434342u);
      expected_word(EXC_TEMPLATE_DST,0x60000000u);
      expected_word(EXC_TEMPLATE_DST+4u,0x47494947u);
      check(c.mmu.read8(VECTOR_DEST-1u)==0xB6u &&
            c.mmu.read8(VECTOR_DEST+VECTOR_LEN)==0xB7u,
            "original exception-vector memcpy overwrote neighboring guest memory");
      for(uint32_t i=0;i<VECTOR_LEN;++i)
        check(c.mmu.read8(SOURCE_TEMPLATE+i)==expected_handler[i],
              "original Wii handler source template changed across vector loop");
      check(c.mmu.read32(EXC_SOURCE_WORD)==exception_word,
            "original exception-vector template word not restored after loop");
      for(uint32_t vector=0;vector<15u;++vector){
        const uint32_t dest=VECTOR_DEST+vector*0x100u;
        check(c.mmu.read32(0x8060bbe0u+4u*vector)==0x100u+vector*0x100u,
              "original exception vector offset test inputs were overwritten");
        check(c.mmu.read8(dest-1u)==0xB6u &&
              c.mmu.read8(dest+VECTOR_LEN)==0xB7u,
              "original Wii exception-vector copy crossed canary memory");
        check(c.mmu.read32(0x80003000u+vector*4u)==
                (vector==8u?ALARM_HANDLER:0x80520f5cu),
              "original __OSInitAlarm exception-vector dispatch table entry incorrect");
        for(uint32_t i=0;i<VECTOR_LEN;++i){
          uint8_t expected=expected_handler[i];
          constexpr uint32_t MARK_OFFSET=EXC_SOURCE_WORD-SOURCE_TEMPLATE;
          if(i>=MARK_OFFSET && i<MARK_OFFSET+4u)
            expected=uint8_t((exception_word|vector)>>(24u-8u*(i-MARK_OFFSET)));
          if(vector==11u && i<SYSCALL_LEN)
            expected=original_syscall[i]; // original syscall vector overlays handler 11
          check(c.mmu.read8(dest+i)==expected,
                "native original Wii vector differs from owner-original handler template");
        }
      }
      check(c.mmu.read32(0x8000303cu)==0xDEADBEEFu,
            "original Wii exception handler table wrote a sixteenth entry");
      check(c.mmu.read32(ALARM_HEAD)==0u &&
            c.mmu.read32(ALARM_HEAD+4u)==0u,
            "original __OSInitAlarm failed to reset its alarm list head");
      check(c.mmu.read32(SHUTDOWN_HEAD)==SHUTDOWN_NODE &&
            c.mmu.read32(SHUTDOWN_TAIL)==SHUTDOWN_NODE,
            "original Wii alarm shutdown callback was not registered");
      check(c.mmu.read32(SHUTDOWN_NODE+8u)==0u &&
            c.mmu.read32(SHUTDOWN_NODE+12u)==0u &&
            c.mmu.read32(SHUTDOWN_NODE+4u)==100u+trial,
            "original Wii shutdown-list node links/priority incorrect");
      check(c.mmu.read32(SHUTDOWN_NODE)==0xFACA0000u+trial &&
            c.mmu.read32(SHUTDOWN_NODE+16u)==0xCCCA0000u+trial,
            "original shutdown registration overwrote adjacent fields");
      for(uint32_t i=0;i<SYSCALL_LEN;++i){
        check(c.mmu.read8(SYSCALL_DEST+i)==original_syscall[i],
              "native Wii syscall vector byte differs from private owner original");
        check(c.mmu.read8(SYSCALL_SOURCE+i)==original_syscall[i],
              "native Wii syscall-vector source was changed");
      }
      check(c.mmu.read8(SYSCALL_SOURCE-1u)==0xABu &&
            c.mmu.read8(SYSCALL_SOURCE+SYSCALL_LEN)==0xBCu,
            "original syscall handler copy changed adjacent source bytes");
      check(c.mmu.read8(SYSCALL_DEST+VECTOR_LEN)==0xB7u,
            "original syscall handler copy clobbered handler neighbor");
      // After OSExceptionInit returned, the original syscall initializer
      // legitimately reuses this formerly exception-owned LR stack slot.
      // The direct-entry V46 ABI test independently verifies this reuse.
      // The original alarm initializer reuses the 16-byte syscall stack
      // frame and saves the newer OSInit BL return at the same LR slot.
      check(c.mmu.read32((sp-8u)-76u)==0x805208bcu,
            "original interrupt prologue stored incorrect OSInit return LR");
      check(c.mmu.read32((sp-8u)-88u)==0x806f4f00u &&
            c.mmu.read32((sp-8u)-84u)==0x8060b7a8u,
            "original exception save helper corrupted OSInit r30/r31");
      check(nwii::runtime::ipc_entries==before_ipc+1,
            "authentic original IPC-buffer initializer not entered exactly once");
      check(c.mmu.read32(IPC_LO_GLOBAL)==ipc_lo &&
            c.mmu.read32(IPC_HI_GLOBAL)==ipc_hi,
            "original IPC-buffer low-memory pointers not copied into OS globals");
      check(c.mmu.read32(IPC_LO_INPUT)==ipc_lo &&
            c.mmu.read32(IPC_HI_INPUT)==ipc_hi,
            "original IPC-buffer initializer changed its input pointer words");
      check(c.mmu.read32(IPC_LO_INPUT-4u)==0xD13ACAFEu &&
            c.mmu.read32(IPC_HI_INPUT+4u)==0xBABE1234u,
            "original IPC helper corrupted adjacent low-memory canaries");
      check(nwii::runtime::arena_entries[0]==before_arena[0]+1 &&
            nwii::runtime::arena_entries[1]==before_arena[1]+1,
            "original MEM1 low/high arena setters were not both executed");
      check(nwii::runtime::mem2_entries[0]==before_mem2[0]+1 &&
            nwii::runtime::mem2_entries[1]==before_mem2[1]+1,
            "authentic MEM2 low/high arena setter entry counts changed");
      check(c.mmu.read32(MEM2_LO_GLOBAL)==mem2_low_hint,
            "original MEM2 low arena global differs");
      check(c.mmu.read32(MEM2_HI_GLOBAL)==mem2_high_hint,
            "original MEM2 high arena global differs");
      check(c.mmu.read32(MEM2_LO_HINT)==mem2_low_hint &&
            c.mmu.read32(MEM2_HI_HINT)==mem2_high_hint,
            "original MEM2 low/high hints were modified");
      check(c.mmu.read32(LO_GLOBAL)==arena_hint,
            "original MEM1 low arena setter ignored low-memory hint");
      check(c.mmu.read32(HI_GLOBAL)==0x81700000u,
            "original MEM1 high arena setter ignored expected fallback");
      check(c.mmu.read32(BOOT_HINT)==arena_hint &&
            c.mmu.read32(0x80003110u)==0u,
            "original low-memory MEM1 arena input hints modified");
      check(c.mmu.read32(BOOT_BASE)==0x80000000u,
            "original low-memory boot base global differs");
      check(c.mmu.read32(BOOT_RECORD)==0u,
            "empty original OS boot info pointer was not cleared");
      check(c.mmu.read32(BOOT_MODE)==1u,
            "original OS boot mode initialized incorrectly");
      check(c.mmu.read32(BOOT_FALLBACK)==0u,
            "empty OS boot fallback global changed");
      check(c.mmu.read32(BOOT_FIELD)==0u,
            "empty OS boot field changed");
      check(c.mmu.read32(0x800000f4u)==0u &&
            c.mmu.read32(0x80000034u)==0u,
            "original low-memory boot input flags changed");
      check((c.hid0 & 0x200u)!=0,"original speculation-disable HID0 bit not set");
      for(unsigned k=0;k<6;++k)
        check(nwii::runtime::perf_entries[k]==before_perf[k]+1,
              "original MMCR/PMC helper was not called exactly once");
      check(c.mmcr0==0u && c.mmcr1==0u,
            "authentic MMCR0/MMCR1 register writes did not execute");
      for(auto reg:c.pmc)
        check(reg==0u, "authentic performance counter write did not execute");
      // Read the two original store instructions from the *private* test DOL,
      // without embedding their instruction words in public source.
      // High/low time-store assertions were checked *before* the B4
      // interrupt helper overwrote r3 and potentially other volatile GPRs.
      check(c.mmu.read32(OS_INIT_FLAG)==1u,"original OS init-once guard flag not set");
      check(c.gpr[25]==0u && c.gpr[21]==0u && c.gpr[23]==0u,
            "original Wii _restgpr_20 did not restore caller r21/r23/r25");
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
    check(c.msr==(owner?((msr0|0x2000u)&~0x8000u):(msr0|0x2000u)),
          "original interrupt-disable MSR.EE side effect changed");
    check(c.hid0==(owner?(expected_hid0|0x200u):expected_hid0) &&
          c.hid2==expected_hid2,"cache/HID0/HID2 state changed");
    check(c.fpscr==(owner?(fpscr|0x4u):fpscr),"original non-IEEE FP FPSCR bit differed");
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
      const std::array<uint64_t,5> expected{1,0,16,4,4};
      for(unsigned i=0;i<5;++i)
        check(nwii::runtime::data_calls[i]-before_data[i]==expected[i],"unexpected data helper call count");
      for(const auto&span:zero){
        const auto*ptr=c.mmu.get_ptr(span.start);
        for(uint32_t i=0;i<span.size;++i){
          const uint32_t address=span.start+i;
          const bool db_global=address>=0x8070d8a0u && address<0x8070d8a8u;
          const bool os_global=address>=OS_INIT_FLAG && address<OS_INIT_FLAG+4u;
          const bool time_global=address>=0x8070db30u && address<0x8070db38u;
          const bool boot_global=address>=BOOT_BASE && address<BOOT_BASE+4u;
          const bool arena_global=address>=HI_GLOBAL && address<HI_GLOBAL+4u;
          const bool mem2_high_global=address>=MEM2_HI_GLOBAL && address<MEM2_HI_GLOBAL+4u;
          const bool ipc_high_global=address>=IPC_HI_GLOBAL && address<IPC_HI_GLOBAL+4u;
          const bool exception_table_global=address>=R13-3552u && address<R13-3552u+4u;
          const bool shutdown_global=address>=SHUTDOWN_HEAD && address<SHUTDOWN_TAIL+4u;
           const bool irq_global=address>=IRQ_GLOBAL && address<IRQ_GLOBAL+4u;
          if(!db_global&&!os_global&&!time_global&&!boot_global&&!arena_global&&!mem2_high_global&&!ipc_high_global&&!exception_table_global&&!shutdown_global&&!irq_global)
            check(ptr[i]==0,"original BSS byte not zero");
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
  std::cout<<std::dec<<"PASS: "<<checks<<" V46 recovered continuous original __start->OSInterruptInit MMIO assertions; mode="
           <<(owner?"owner":"synthetic")<<" trials="<<trials<<" stop=0x"<<std::hex<<(owner?POST_OWNER:POST_SYNTH)<<std::dec<<"\n";
}
