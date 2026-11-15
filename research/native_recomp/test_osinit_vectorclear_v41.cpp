// Source-only assertions for genuine original Wii OSInit prefix under AOT native dispatch.
// Private extracted code and original DOL stay off GitHub and out of test source.
#include "runtime/cpu_context.h"
#include "loader/loader.h"
#include <array>
#include <cstdint>
#include <iostream>
#include <memory>
#include <stdexcept>

namespace {
constexpr uint32_t OSINIT=0x80520670u,STOP=0x80520D80u,FIRSTSTOP=0x80520CDCu,SECONDDEBUG=0x80520D08u,MARK=0x804E50A0u,IPC=0x8052AE80u,EXCEPTION=0x80520BF4u,DEBUGSTOP=0x80520C44u,
   EXC_SOURCE_WORD=0x80520F28u, ALT=0x80520BDCu,REPORT=0x80522F00u;
constexpr uint32_t TIME=0x8052A844u,GETTIME=0x8052A824u,DISABLE=0x805265ACu;
constexpr uint32_t RESTORE=0x805265D4u,EXEC=0x80523B1Cu,SAVE=0x805450E8u,COPY=0x80004338u,PERF=0x804B7964u,
                   MFHID0=0x804B7920u,MTHID0=0x804B7928u,
                   SPEC=0x804B7A00u,NONIEEE=0x804B7A28u,HID4=0x804B7A30u,ARENA_LO=0x80521D60u,ARENA_HI=0x80521D48u,MEM2_LO=0x80521D68u,MEM2_HI=0x80521D50u;
constexpr uint32_t SP=0x80082000u, R13=0x8070E8E0u, INITFLAG=0x8070DAFCu;
constexpr uint32_t DEST=0x806F4F00u,SOURCE=0x80038000u,TIMEHI=0x8070DB30u;
// Boot-state globals are indexed from the original guest r13 small-data pointer.
constexpr uint32_t BOOT_BASE=R13-3512u, BOOT_RECORD=R13-3516u;
constexpr uint32_t BOOT_FALLBACK=R13-3520u, BOOT_MODE=R13-16864u;
constexpr uint32_t BOOT_FIELD=R13-3216u, BOOT_HINT=0x8000310cu;
constexpr uint32_t BOOT_SOURCE=0x8003D000u;
constexpr uint32_t LO_GLOBAL=R13-16400u,HI_GLOBAL=R13-3472u;
constexpr uint32_t MEM1_HI_HINT=0x80003110u;
constexpr uint32_t MEM2_LO_HINT=0x80003124u,MEM2_HI_HINT=0x80003128u;
constexpr uint32_t MEM2_LO_GLOBAL=R13-16396u,MEM2_HI_GLOBAL=R13-3468u;
constexpr uint32_t IPC_LO_HINT=0x80003130u,IPC_HI_HINT=0x80003134u;
constexpr uint32_t IPC_LO_GLOBAL=R13-16336u,IPC_HI_GLOBAL=R13-3352u;
struct ReportStop {};
struct NativeStop {};
struct FirstMarkStop {};
struct SecondDebugStop {};
struct DebugStop {};
uint64_t assertions=0;
void check(bool b,const char* text){if(!b)throw std::runtime_error(text);++assertions;}
}
namespace nwii::runtime {
bool g_trace_calls=true;
uint32_t g_watch_addr=0;
static uint32_t stops=0,forbidden=0;
static uint32_t expected_stop=STOP;
static uint64_t target_time=0;
static uint32_t call_counts[32]{};
void trace_call(uint32_t pc,CPUContext& ctx){
 constexpr uint32_t symbols[32]={OSINIT,TIME,GETTIME,DISABLE,RESTORE,EXEC,SAVE,COPY,ALT,
  PERF,PERF+8,PERF+16,PERF+24,PERF+32,PERF+40,MFHID0,MTHID0,SPEC,NONIEEE,HID4,REPORT,ARENA_LO,ARENA_HI,MEM2_LO,MEM2_HI,IPC,EXCEPTION,0x80520E98u,0x80520E9Cu,0x80520EC0u,0x80520F58u,MARK};
 for(size_t i=0;i<32;++i)if(pc==symbols[i]){
   ++call_counts[i];
   // Deterministic test-only virtual-clock start; not a production runtime override.
   if(pc==GETTIME)ctx.inst_count=target_time;
   return;
 }
 throw std::runtime_error("unplanned original Wii function entered");
}
bool handle_syscall(CPUContext& ctx){
 if(ctx.pc!=expected_stop){++forbidden;throw std::runtime_error("unexpected guest syscall stop at "+std::to_string(ctx.pc)+" expected "+std::to_string(expected_stop));}
 ++stops;ctx.is_running=false;
 if(ctx.pc==STOP)throw NativeStop{};
 if(ctx.pc==FIRSTSTOP)throw FirstMarkStop{};
 if(ctx.pc==SECONDDEBUG)throw SecondDebugStop{};
 if(ctx.pc==DEBUGSTOP)throw DebugStop{};
 if(ctx.pc==REPORT)throw ReportStop{}; // stop before original OSReport can return
 return true;
}
void interpret_step(CPUContext&){++forbidden;throw std::runtime_error("PPC interpreter fallback");}
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
int main(int argc,char**argv)try{
 check(argc==2,"usage: original-native-test PRIVATE_DOL");
 nwii::loader::Executable exe;
 check(exe.load_dol(argv[1])&&exe.entry_point==OSINIT,"wrong bounded OSInit DOL");
 auto ctx=std::make_unique<nwii::runtime::CPUContext>();
 // The original exception prologue reads a text-resident handler template
 // through lwzu. The test loader currently does not automatically install
 // all original DOL sections into MMU RAM: seed this owner-private word from
 // the private slice, without embedding copyrighted bytes in the test source.
 bool found_template=false;
 uint32_t template_word=0;
 for(const auto& sec:exe.sections){
   if(sec.address<=EXC_SOURCE_WORD &&
      uint64_t(EXC_SOURCE_WORD)+4<=uint64_t(sec.address)+sec.data.size()){
     const size_t pos=EXC_SOURCE_WORD-sec.address;
     template_word=uint32_t(sec.data[pos])<<24 | uint32_t(sec.data[pos+1])<<16 |
         uint32_t(sec.data[pos+2])<<8 | uint32_t(sec.data[pos+3]);
     found_template=true;
   }
 }
 check(found_template,"missing owner-private exception code-data literal");
 constexpr std::array<uint32_t,6> source{0u,0x7fffffffu,SOURCE,0x80000000u,0u,0x7fffffffu};
 constexpr std::array<uint64_t,6> clocks{0x0000000000100000ull,0x00000001fffffffcull,
       0x00000000fffffff0ull,0x0000000200000004ull,0x0000000300000001ull,0x0000000100001234ull};
 constexpr std::array<uint64_t,6> offsets{0x0000000000000000ull,0x0000000200000050ull,
       0x00000003ffffffe0ull,0x00000001fffffffdull,0x0000000000000300ull,0x00000000ffffff00ull};
 for(size_t run=0;run<source.size();++run){
  const uint32_t ptr=source[run];const bool copied=ptr>=0x80000000u;
  const uint32_t msr=(run&1)?0x2000u:0xA000u;
  constexpr uint32_t SAVED_LR=0x8000BEEFu;
  ctx->mmu.write32(INITFLAG,0);
  ctx->mmu.write32(0x80000060u,0x00000001u+uint32_t(run)); // skip unimplemented DBPrintf/vector-copy path
  ctx->mmu.write32(EXC_SOURCE_WORD,template_word);
  ctx->mmu.write32(0x80000100u,0x0DD0D0D0u);
  for(unsigned k=0;k<12;++k)ctx->mmu.write32(SP-128u+k*4,0xC0C0C0C0u);
  ctx->mmu.write32(0x800030F0u,ptr);
  // Six startup shapes: neither boot source, legacy fallback,
  // explicit boot-info record, and a boot record overriding fallback flags.
  const uint32_t boot=run<2?0u:BOOT_SOURCE+static_cast<uint32_t>((run-2)*0x100u);
  const bool legacy=(run&1u)!=0;
  const uint8_t legacy_byte0=uint8_t(0x65u+run),legacy_byte1=uint8_t(0x85u+run);
  const uint32_t boot_word0=(run==2?1u:0xABCD1200u+uint32_t(run*11+9));
  const uint32_t boot_word1=0xCAFE5600u+uint32_t(run*13+0x42);
  const uint32_t arena_hint=(run==0||run==2||run==4||run==5)?0u:0x80102000u+uint32_t(run*0x100u);
  const uint32_t high_hint=(run==3)?0x81720000u:((run==5)?0x81760000u:0u);
  const uint32_t expected_lo=arena_hint?arena_hint:(run==2?0x80751CC0u:((run==5)?0x80001234u:0x80753CC0u));
  const uint32_t expected_hi=high_hint?high_hint:(legacy?1u:0x81700000u);
  constexpr std::array<uint32_t,6> mem2_lows{0u,0x90000000u,0x900007ffu,
                                              0x90000800u,0x90010000u,0x80004000u};
  constexpr std::array<uint32_t,6> mem2_highs{0u,0x93400000u,0u,
                                               0x93a00000u,0x93f00000u,0x93b00000u};
  const uint32_t mem2_lo=mem2_lows[run],mem2_hi=mem2_highs[run];
  const uint32_t expected_mem2_lo=mem2_lo?((mem2_lo>=0x90000000u&&mem2_lo<0x90000800u)?0x90000800u:mem2_lo):0xA5A5A5A5u;
  const uint32_t expected_mem2_hi=mem2_hi?mem2_hi:0xB5B5B5B5u;
  // 0x80000030 controls the original alternate aligned-heap path.
  ctx->mmu.write32(0x80000030u,run==5?0x80001234u:0u);
  ctx->mmu.write32(MEM1_HI_HINT,high_hint);
  ctx->mmu.write32(MEM2_LO_HINT,mem2_lo);
  ctx->mmu.write32(MEM2_HI_HINT,mem2_hi);
  const uint32_t ipc_lo=run==0?0u:(0x90000100u+uint32_t(run*0x100u));
  const uint32_t ipc_hi=run==1?0u:(0x93FFF000u-uint32_t(run*0x1000u));
  ctx->mmu.write32(IPC_LO_HINT,ipc_lo);
  ctx->mmu.write32(IPC_HI_HINT,ipc_hi);
  ctx->mmu.write32(IPC_LO_GLOBAL,0xFAFA1616u);
  ctx->mmu.write32(IPC_HI_GLOBAL,0xBEBE2929u);
  ctx->mmu.write32(IPC_LO_GLOBAL-4u,0xDEADC0DEu);
  ctx->mmu.write32(IPC_HI_GLOBAL+4u,0xFACECAFEu);
  ctx->mmu.write32(0x800000F4u,boot);
  ctx->mmu.write32(0x80000034u,legacy?1u:0u);
  ctx->mmu.write8(0x800030E8u,legacy_byte0);
  ctx->mmu.write8(0x800030E9u,legacy_byte1);
  ctx->mmu.write32(BOOT_HINT,arena_hint);
  if(boot){
    ctx->mmu.write32(boot+12u,boot_word0);
    ctx->mmu.write32(boot+36u,boot_word1);
    ctx->mmu.write8(boot+8u,0xDAu);
    ctx->mmu.write8(boot+40u,0xDBu);
  }
  ctx->mmu.write32(BOOT_BASE,0x6F6F6F6Fu);
  ctx->mmu.write32(BOOT_RECORD,0x6E6E6E6Eu);
  ctx->mmu.write32(BOOT_FALLBACK,0x6D6D6D6Du);
  ctx->mmu.write32(BOOT_FIELD,0x6C6C6C6Cu);
  ctx->mmu.write32(BOOT_MODE,0x6B6B6B6Bu);
  ctx->mmu.write32(LO_GLOBAL,0xA1A1A1A1u);
  ctx->mmu.write32(HI_GLOBAL,0xB2B2B2B2u);
  ctx->mmu.write32(LO_GLOBAL-4u,0xC3C3C3C3u);
  // V32 used adjacent MEM2 globals as canaries; V37 now seeds actual outputs.
  ctx->mmu.write32(HI_GLOBAL+4u,0xB5B5B5B5u);
  ctx->mmu.write32(LO_GLOBAL+4u,0xA5A5A5A5u);
  ctx->mmu.write32(MEM2_LO_GLOBAL+4u,0xC5C5C5C5u);
  ctx->mmu.write32(MEM2_HI_GLOBAL+4u,0xD5D5D5D5u);

  ctx->mmu.write32(0x800030D8u,uint32_t(offsets[run]>>32));
  ctx->mmu.write32(0x800030DCu,uint32_t(offsets[run]));
  ctx->mmu.write32(TIMEHI,0xA0A0A0A0u);
  ctx->mmu.write32(TIMEHI+4,0xBBBBBBBBu);
  ctx->mmu.write8(DEST-1,0xAC);
  for(uint32_t i=0;i<32;++i){
    ctx->mmu.write8(DEST+i,0xAA);
    if(copied)ctx->mmu.write8(ptr+i,uint8_t((run*43+i*17+9)&255));
  }
  ctx->mmu.write8(DEST+28,0xC9);
  ctx->mmu.write8(DEST+29,0xD9);
  for(unsigned i=20;i<=31;++i){
   ctx->gpr[i]=0x1CA00000u+(uint32_t(run)<<16)+i;
   ctx->mmu.write32(SP-48u+4u*(i-20u),0xFAFAFAFAu);
  }
  ctx->hid0=0x05000000u + uint32_t(run);
  ctx->hid4=0x00012345u + uint32_t(run);
  ctx->fpscr=0xA0000000u + uint32_t(run);
  const uint32_t initial_hid0=ctx->hid0;
  const uint32_t initial_fpscr=ctx->fpscr;
  ctx->mmcr0=0xFFFF0001u+uint32_t(run);
  ctx->mmcr1=0x0000FFFFu+uint32_t(run);
  for(size_t i=0;i<4;++i)ctx->pmc[i]=0xBEEFAA01u+uint32_t(run*4+i);
  ctx->gpr[13]=R13;
  ctx->gpr[1]=SP;ctx->lr=SAVED_LR;ctx->pc=OSINIT;ctx->msr=msr;
  ctx->is_running=true;
  nwii::runtime::target_time=clocks[run];
  // Genuine __DBIsExceptionMarked uses this r13-relative pointer to a debug
  // structure with a mark-bit mask at +4. Seed only independently authored data.
  constexpr uint32_t DB_GLOBAL=R13-4160u, DB_STRUCT=0x80045000u;
  const uint32_t dbmask=(run&1u)?0xFFFFFFFFu:0u;
  ctx->mmu.write32(DB_GLOBAL,DB_STRUCT);
  ctx->mmu.write32(DB_STRUCT,0x19283746u);
  ctx->mmu.write32(DB_STRUCT+4u,dbmask);
  const uint32_t stops=nwii::runtime::stops;
  std::array<uint32_t,32> before{};
  for(size_t i=0;i<before.size();++i)before[i]=nwii::runtime::call_counts[i];
  const bool marked_first=(run==1u || run>=3u);
  const bool debug_branch=(dbmask&1u)!=0u;
  constexpr uint32_t VECTOR_TEMPLATE=0x80520F18u;
  ctx->mmu.write32(VECTOR_TEMPLATE-4u,0x42434342u);
  ctx->mmu.write32(VECTOR_TEMPLATE,0x11224488u);
  ctx->mmu.write32(VECTOR_TEMPLATE+4u,0x47494947u);
  nwii::runtime::expected_stop=debug_branch?FIRSTSTOP:STOP;
  bool exact_stop=false;
  try{run_game(*ctx);}
  catch(const NativeStop&){if(!debug_branch)exact_stop=true;}
  catch(const FirstMarkStop&){if(debug_branch)exact_stop=true;}
  check(exact_stop,"original OSInit missing expected exception-mark terminal syscall");
  check(!ctx->is_running&&ctx->pc==(debug_branch?FIRSTSTOP:STOP),
        "wrong original exception-mark guest syscall boundary");
  check(nwii::runtime::stops==stops+1,"missing original OSInit continuation stop");
  check(ctx->gpr[1]==SP-144,"original OSInit+exception nested stack frame incorrect");
  check(ctx->mmu.read32(SP-76u)==0x805208ACu,"original exception saved return LR incorrectly");
  check(ctx->mmu.read32(0x80000060u)==0x00000001u+uint32_t(run),"exception changed low-memory branch flag");
  check(ctx->mmu.read32(0x80000100u)==0x0DD0D0D0u,
        "unverified exception vector write executed before boundary");
  check(ctx->gpr[28]==EXC_SOURCE_WORD && ctx->gpr[27]==template_word,
        "original exception template LWZU did not read owner text word");
  check(ctx->gpr[25]==0x98u&&ctx->gpr[21]==4u&&ctx->gpr[23]==0x60000000u,
        "original exception setup arithmetic differs");
  for(unsigned k=0;k<10;++k)
    check(ctx->mmu.read32(SP-128u+k*4)==0x1CA00000u+(uint32_t(run)<<16)+20u+k,
          "original exception _savegpr_20 stored wrong nonvolatile register");
  check(ctx->mmu.read32(SP-88u)==0x806F4F00u && ctx->mmu.read32(SP-84u)==0x8060B7A8u,
        "exception _savegpr_20 saved original OSInit r30/r31 incorrectly");
  check(ctx->mmu.read32(SP+4)==SAVED_LR,"original caller LR was not saved");
  check(ctx->mmu.read32(INITFLAG)==1,"OSInit one-time global not set");
  check((ctx->msr&0x8000u)==0,"original second interrupt disable not executed");
  check((ctx->msr&~0x8000u)==(msr&~0x8000u),"original OSInit corrupted other MSR bits");
  check(ctx->gpr[13]==R13,"OSInit guest small-data pointer changed");
  check(ctx->gpr[3]==(debug_branch?0x8060BC38u:1u),
        "original marker result or template-clear loop register differs");
  check(ctx->mmu.read32(VECTOR_TEMPLATE-4u)==0x42434342u &&
        ctx->mmu.read32(VECTOR_TEMPLATE+4u)==0x47494947u,
        "original template-clear loop overran its four-byte test buffer");
  check(ctx->mmu.read32(VECTOR_TEMPLATE)==(debug_branch?0x11224488u:0x60000000u),
        "original exception template loop did not clear precisely one word");
  if(!debug_branch)check(ctx->ctr==0u,"original bdnz template-clear loop did not exhaust CTR");
  check(ctx->mmu.read32(DB_GLOBAL)==DB_STRUCT&&ctx->mmu.read32(DB_STRUCT+4)==dbmask,
        "debug mark inputs modified by original exception check");
  check(ctx->mmu.read32(EXC_SOURCE_WORD)==template_word,
        "original exception-template word unexpectedly modified");
  check(ctx->mmu.read32(IPC_LO_GLOBAL)==ipc_lo && ctx->mmu.read32(IPC_HI_GLOBAL)==ipc_hi,
        "original IPC globals not initialized from low memory");
  check(ctx->mmu.read32(IPC_LO_HINT)==ipc_lo && ctx->mmu.read32(IPC_HI_HINT)==ipc_hi,
        "original IPC source values were modified");
  check(ctx->mmu.read32(IPC_LO_GLOBAL-4u)==0xDEADC0DEu &&
        ctx->mmu.read32(IPC_HI_GLOBAL+4u)==0xFACECAFEu,
        "original IPC initialization overwrote adjacent memory");
  check(ctx->mmu.read32(BOOT_HINT)==arena_hint&&ctx->mmu.read32(MEM1_HI_HINT)==high_hint,
        "original arena hint inputs changed");
  check(ctx->mmu.read32(LO_GLOBAL)==expected_lo,"original MEM1 low setter result differs");
  check(ctx->mmu.read32(HI_GLOBAL)==expected_hi,"original MEM1 high setter result differs");
  check(ctx->mmu.read32(LO_GLOBAL-4u)==0xC3C3C3C3u&&
        ctx->mmu.read32(MEM2_HI_GLOBAL+4u)==0xD5D5D5D5u,
        "MEM2 setter overwrote outer global canary");
  check(ctx->mmu.read32(MEM2_LO_HINT)==mem2_lo&&ctx->mmu.read32(MEM2_HI_HINT)==mem2_hi,
        "original MEM2 arena hints changed");
  check(ctx->mmu.read32(MEM2_LO_GLOBAL)==expected_mem2_lo,
        "original MEM2 low arena result differs");
  check(ctx->mmu.read32(MEM2_HI_GLOBAL)==expected_mem2_hi,
        "original MEM2 high arena result differs");
  check(ctx->mmu.read32(BOOT_BASE)==0x80000000u,"original OS boot base pointer changed");
  check(ctx->mmu.read32(BOOT_MODE)==1u,"original OS boot mode flag should be one");
  check(ctx->mmu.read32(0x800000F4u)==boot,"low-memory boot pointer modified");
  check(ctx->mmu.read32(0x80000034u)==(legacy?1u:0u),"low-memory legacy flag modified");
  if(boot){
    check(ctx->mmu.read32(BOOT_RECORD)==boot+12u,"original OS boot-info pointer wrong");
    check(ctx->mmu.read32(BOOT_FIELD)==boot_word1,"original boot-info secondary word wrong");
    check(ctx->mmu.read32(BOOT_FALLBACK)==0x6D6D6D6Du,"boot-info path touched fallback word");
    check(ctx->mmu.read8(0x800030E8u)==uint8_t(boot_word0),"boot-info first flag byte wrong");
    check(ctx->mmu.read8(0x800030E9u)==uint8_t(boot_word1),"boot-info second flag byte wrong");
    check(ctx->mmu.read32(boot+12u)==boot_word0&&ctx->mmu.read32(boot+36u)==boot_word1,
          "source boot-info words changed");
    check(ctx->mmu.read8(boot+8u)==0xDAu&&ctx->mmu.read8(boot+40u)==0xDBu,
          "source boot-info guards changed");
  } else if(legacy){
    check(ctx->mmu.read32(BOOT_RECORD)==BOOT_FALLBACK,"fallback boot pointer wrong");
    check(ctx->mmu.read32(BOOT_FIELD)==legacy_byte1,"fallback secondary boot byte wrong");
    check(ctx->mmu.read32(BOOT_FALLBACK)==legacy_byte0,"fallback primary boot byte wrong");
    check(ctx->mmu.read8(0x800030E8u)==legacy_byte0&&ctx->mmu.read8(0x800030E9u)==legacy_byte1,
          "fallback changed original low-memory bytes");
  } else {
    check(ctx->mmu.read32(BOOT_RECORD)==0u,"empty boot record pointer not cleared");
    check(ctx->mmu.read32(BOOT_FIELD)==0x6C6C6C6Cu,"empty boot path modified field");
    check(ctx->mmu.read32(BOOT_FALLBACK)==0x6D6D6D6Du,"empty boot path modified fallback");
    check(ctx->mmu.read8(0x800030E8u)==legacy_byte0&&ctx->mmu.read8(0x800030E9u)==legacy_byte1,
          "empty boot path modified low-memory bytes");
  }

  check(ctx->mmcr0==0&&ctx->mmcr1==0,"original MMCR0/MMCR1 zeroing failed");
  check(ctx->hid4==0x83900000u,"genuine original HID4 init write failed");
  check(ctx->hid0==(initial_hid0|0x200u),"original PPCDisableSpeculation HID0 bit preservation failed");
  check(ctx->fpscr==(initial_fpscr|0x4u),"original mtfsb1(29) FPSCR bit mapping failed");
  for(size_t i=0;i<4;++i)check(ctx->pmc[i]==0,"original PMC register zeroing failed");
  const uint64_t stamp=(uint64_t(ctx->mmu.read32(TIMEHI))<<32)|ctx->mmu.read32(TIMEHI+4);
  const uint64_t low=clocks[run]+offsets[run];
  check(stamp>=low+1 && stamp<=low+48,"OSInit timestamp outside original timebase window");
  const uint32_t expected_entries[32]={1,1,1,2,1,1,2,(copied?1u:0u),0,1,1,1,1,1,1,1,1,1,1,1,0,1,1,(mem2_lo?1u:0u),(mem2_hi?1u:0u),1u,1u,0,0,0,0,(marked_first&&!debug_branch?2u:1u)};
  for(size_t i=0;i<32;++i)
    check(nwii::runtime::call_counts[i]-before[i]==expected_entries[i],
      "wrong number of original guest function dispatches");
  for(unsigned i=20;i<=31;++i)
    check(ctx->mmu.read32(SP-48u+4u*(i-20u))==0x1CA00000u+(uint32_t(run)<<16)+i,
      "original _savegpr_20 guest stack slot wrong");
  check(ctx->mmu.read8(DEST-1)==0xAC && ctx->mmu.read8(DEST+28)==0xC9 &&
        ctx->mmu.read8(DEST+29)==0xD9,"execparams destination guard changed");
  for(uint32_t i=0;i<28;++i){
    const uint8_t expected=copied?uint8_t((run*43+i*17+9)&255):(i<4?0u:0xAA);
    check(ctx->mmu.read8(DEST+i)==expected,"OSInit original exec-params copy/zero wrong");
  }
 }
 // The original exception branch checks low memory at 0x80000060.
 // A zero value enters an OS debug/copy path we have not implemented. The
 // fixture substitutes a strict test-only syscall before the real DBPrintf;
 // no original exception-vector copy/flush is claimed or allowed to run.
 nwii::runtime::expected_stop=DEBUGSTOP;
 ctx->mmu.write32(0x80000060u,0u);
 ctx->mmu.write32(EXC_SOURCE_WORD,template_word);
 ctx->mmu.write32(0x80000100u,0x0DD0D0D0u);
 ctx->gpr[1]=SP-80u;ctx->gpr[13]=R13;
 ctx->lr=0x805208ACu;ctx->pc=EXCEPTION;ctx->is_running=true;
 const uint32_t before_exception=nwii::runtime::call_counts[26];
 const uint32_t before_debug=nwii::runtime::stops;
 bool stopped_at_debug=false;
 try{run_game(*ctx);}catch(const DebugStop&){stopped_at_debug=true;}
 check(stopped_at_debug,"zero low-memory exception path escaped the DBPrintf boundary");
 check(ctx->pc==DEBUGSTOP&&!ctx->is_running,"unexpected debug branch syscall PC");
 check(nwii::runtime::call_counts[26]==before_exception+1u&&
       nwii::runtime::stops==before_debug+1u,"original exception debug path not traced");
 check(ctx->gpr[1]==SP-144u && ctx->mmu.read32(SP-76u)==0x805208ACu,
       "original exception debug branch stack or LR incorrect");
 check(ctx->mmu.read32(0x80000100u)==0x0DD0D0D0u,
       "unimplemented exception vector copy unexpectedly modified memory");
 // Exercise the *second* original __DBIsExceptionMarked call when the first
 // boot-record check falls through and the debug mask is set. The real
 // DBPrintf service is rejected at its instruction address, not HLE-returned.
 nwii::runtime::expected_stop=SECONDDEBUG;
 ctx->mmu.write32(0x80000060u,1u);
 ctx->mmu.write32(BOOT_RECORD,0u);
 ctx->mmu.write32(R13-4160u,0x80045000u);
 ctx->mmu.write32(0x80045004u,1u);
 ctx->gpr[1]=SP-80u;ctx->gpr[13]=R13;
 ctx->lr=0x805208ACu;ctx->pc=EXCEPTION;ctx->is_running=true;
 const uint32_t second_before=nwii::runtime::stops;
 const uint64_t mark_before=nwii::runtime::call_counts[31];
 bool rejected_second=false;
 try {run_game(*ctx);}catch(const SecondDebugStop&){rejected_second=true;}
 check(rejected_second&&!ctx->is_running&&ctx->pc==SECONDDEBUG,
       "second marked-exception path bypassed DBPrintf fail-closed stop");
 check(nwii::runtime::stops==second_before+1u&&
       nwii::runtime::call_counts[31]==mark_before+1u,
       "original second exception-mark helper not dispatched");
 nwii::runtime::expected_stop=ALT;
 // Independent direct calls prove both original arena-setter functions preserve
 // the input value, do not alias one another, and return through the guest LR.
 nwii::runtime::expected_stop=ALT;
 for(const auto& [entry,global,other]:std::array<std::array<uint32_t,3>,4>{{
       {{ARENA_LO,LO_GLOBAL,HI_GLOBAL}},{{ARENA_HI,HI_GLOBAL,LO_GLOBAL}},
       {{MEM2_LO,MEM2_LO_GLOBAL,LO_GLOBAL}},{{MEM2_HI,MEM2_HI_GLOBAL,HI_GLOBAL}}}}){
  const uint32_t value=(entry==ARENA_LO||entry==MEM2_LO)?0x900BA120u:0x93EABCD0u;
  ctx->mmu.write32(global,0u);
  ctx->mmu.write32(other,0xE7E7E7E7u);
  ctx->gpr[3]=value;ctx->pc=entry;ctx->lr=ALT;
  ctx->gpr[1]=SP;ctx->gpr[13]=R13;ctx->is_running=true;
  const size_t count_idx=entry==ARENA_LO?21u:entry==ARENA_HI?22u:entry==MEM2_LO?23u:24u;
  const auto before_call=nwii::runtime::call_counts[count_idx];
  run_game(*ctx);
  check(!ctx->is_running&&ctx->pc==ALT,"direct original MEM1/MEM2 setter failed to return");
  check(ctx->mmu.read32(global)==value,"original MEM1/MEM2 setter discarded operand");
  check(ctx->mmu.read32(other)==0xE7E7E7E7u,"MEM1/MEM2 setter clobbered other global");
  check(ctx->gpr[3]==value&&ctx->gpr[1]==SP&&ctx->lr==ALT,
        "original MEM1/MEM2 setter damaged guest call convention");
  check(nwii::runtime::call_counts[count_idx]==before_call+1u,
        "missing original MEM1/MEM2 setter native entry");
 }
 // Direct original IPC init must preserve arbitrary pointer words, including zeros.
 nwii::runtime::expected_stop=ALT;
 for(uint32_t seed:{0u,0x90000000u,0x93FFFFF0u}){
  const uint32_t high=seed^0xA5A55A5Au;
  ctx->mmu.write32(IPC_LO_HINT,seed);
  ctx->mmu.write32(IPC_HI_HINT,high);
  ctx->mmu.write32(IPC_LO_GLOBAL,0x11112222u);
  ctx->mmu.write32(IPC_HI_GLOBAL,0x33334444u);
  ctx->gpr[1]=SP;ctx->gpr[13]=R13;ctx->lr=ALT;ctx->pc=IPC;
  ctx->is_running=true;
  const auto called=nwii::runtime::call_counts[25];
  run_game(*ctx);
  check(!ctx->is_running && ctx->pc==ALT,"direct original IPC function failed to return");
  check(ctx->mmu.read32(IPC_LO_GLOBAL)==seed && ctx->mmu.read32(IPC_HI_GLOBAL)==high,
        "direct original IPC pointer copy differs");
  check(ctx->gpr[1]==SP && ctx->gpr[13]==R13 && ctx->lr==ALT,
        "direct IPC helper corrupted guest calling convention");
  check(nwii::runtime::call_counts[25]==called+1u,"direct original IPC helper not dispatched");
 }
 // Independent direct calls exercise the original PowerPC slw/and mask
 // at indices 0, 1, 7, 31, 32, and 63. The Wii slw returns zero for
 // shift counts >=32 rather than using a modulo-32 host shift.
 nwii::runtime::expected_stop=ALT;
 for(uint32_t index:{0u,1u,7u,31u,32u,63u}){
  for(uint32_t mask:{0u,0xFFFFFFFFu,0x80000081u}){
   ctx->mmu.write32(R13-4160u,0x80045000u);
   ctx->mmu.write32(0x80045004u,mask);
   ctx->gpr[1]=SP;ctx->gpr[13]=R13;ctx->gpr[3]=index;
   ctx->lr=ALT;ctx->pc=MARK;ctx->is_running=true;
   const auto before_mark=nwii::runtime::call_counts[31];
   run_game(*ctx);
   const uint32_t bit=index>=32u?0u:(1u<<index);
   check(!ctx->is_running&&ctx->pc==ALT,"direct original DBIsExceptionMarked did not return");
   check(ctx->gpr[3]==(mask&bit),"original PPC exception bit mask differs");
   check(ctx->gpr[1]==SP&&ctx->lr==ALT&&ctx->gpr[13]==R13,
         "original exception marker did not preserve guest ABI");
   check(nwii::runtime::call_counts[31]==before_mark+1u,
         "original marker was not natively dispatched");
  }
 }
 // Direct calls into each authentic two-instruction PPC helper use nonzero
 // operands. This proves value storage (not unconditional zeroing or no-op).
 nwii::runtime::expected_stop=ALT;
 constexpr std::array<uint32_t,6> perf_addr{PERF,PERF+8,PERF+16,PERF+24,PERF+32,PERF+40};
 for(size_t i=0;i<perf_addr.size();++i){
  ctx->mmcr0=0xACDC1234u;ctx->mmcr1=0xBADA0001u;
  ctx->pmc={0x11111111u,0x22222222u,0x33333333u,0x44444444u};
  const std::array<uint32_t,6> previous{ctx->mmcr0,ctx->mmcr1,
      ctx->pmc[0],ctx->pmc[1],ctx->pmc[2],ctx->pmc[3]};
  const uint32_t value=0xDEAD1001u+uint32_t(i*37);
  ctx->gpr[3]=value;
  ctx->pc=perf_addr[i];ctx->lr=ALT;ctx->is_running=true;
  const uint32_t old_stops=nwii::runtime::stops;
  const uint32_t old_helper_calls=nwii::runtime::call_counts[9+i];
  run_game(*ctx);
  check(!ctx->is_running && ctx->pc==ALT,"direct original mtspr did not reach ALT stop");
  check(nwii::runtime::stops==old_stops+1,"direct original mtspr stop missing");
  check(nwii::runtime::call_counts[9+i]==old_helper_calls+1,"helper dispatched incorrectly");
  check(ctx->gpr[3]==value,"original mtspr corrupted source operand");
  const std::array<uint32_t,6> after{ctx->mmcr0,ctx->mmcr1,
      ctx->pmc[0],ctx->pmc[1],ctx->pmc[2],ctx->pmc[3]};
  for(size_t n=0;n<after.size();++n)
    check(after[n]==(n==i?value:previous[n]),"performance SPR alias or mapping wrong");
 }
 // Original HID4 helper with sign bit set: no OSReport and correct 32-bit write.
 nwii::runtime::expected_stop=ALT;
 ctx->hid4=0x13572468u;
 ctx->gpr[3]=0xBEEF4567u;ctx->gpr[31]=0xDA1E0FAFu;
 ctx->gpr[1]=SP;ctx->lr=ALT;ctx->pc=HID4;ctx->is_running=true;
 const uint32_t first_stop=nwii::runtime::stops;
 const uint32_t first_hid=nwii::runtime::call_counts[19];
 run_game(*ctx);
 check(!ctx->is_running && ctx->pc==ALT,"direct original HID4 did not return to synthetic ALT");
 check(ctx->hid4==0xBEEF4567u,"direct original HID4 nonzero value lost");
 check(ctx->gpr[3]==0xBEEF4567u&&ctx->gpr[31]==0xDA1E0FAFu,"HID4 callee register corruption");
 check(ctx->gpr[1]==SP&&ctx->lr==ALT,"original HID4 direct stack/LR mismatch");
 check(nwii::runtime::stops==first_stop+1&&nwii::runtime::call_counts[19]==first_hid+1,
       "direct original HID4 call tracing mismatch");
 // HID4 bit31 clear must take the original OSReport branch. We stop there
 // deliberately rather than invent a successful host OSReport implementation.
 nwii::runtime::expected_stop=REPORT;
 ctx->hid4=0x55667788u;ctx->gpr[3]=0x00000505u;
 ctx->gpr[1]=SP;ctx->lr=ALT;ctx->pc=HID4;ctx->is_running=true;
 const uint32_t report_before=nwii::runtime::call_counts[20];
 bool stopped_at_report=false;
 try { run_game(*ctx); } catch(const ReportStop&) { stopped_at_report=true; }
 check(stopped_at_report,"HID4 bit31-clear branch returned from synthetic OSReport stop");
 check(!ctx->is_running&&ctx->pc==REPORT,"HID4 MSB-clear path did not reach OSReport boundary");
 check(ctx->hid4==0x55667788u,"HID4 register changed before OSReport returned");
 check(nwii::runtime::call_counts[20]==report_before+1,"unverified OSReport branch not traced");
 // Independent direct original speculation control preserves all other HID0 bits.
 nwii::runtime::expected_stop=ALT;
 for(uint32_t seed:{0u,0x40000000u,0xFFFFFFFFu}){
  ctx->hid0=seed;ctx->gpr[1]=SP;ctx->lr=ALT;ctx->pc=SPEC;ctx->is_running=true;
  run_game(*ctx);
  check(ctx->pc==ALT && !ctx->is_running,"PPCDisableSpeculation did not return normally");
  check(ctx->hid0==(seed|0x200u),"PPCDisableSpeculation damaged other HID0 bits");
  check(ctx->gpr[1]==SP&&ctx->lr==ALT,"PPCDisableSpeculation guest ABI damaged");
 }
 // The original FP mode helper ORs FPSCR bit 2 (PowerPC bit number 29).
 for(uint32_t seed:{0u,0xFFFFFFFFu,0x01230000u}){
  ctx->fpscr=seed;ctx->lr=ALT;ctx->pc=NONIEEE;ctx->is_running=true;
  run_game(*ctx);
  check(!ctx->is_running&&ctx->pc==ALT,"PPCSetFpNonIEEEMode did not return");
  check(ctx->fpscr==(seed|0x4u),"mtfsb1 29 changed unrelated FPSCR bits");
 }
 check(nwii::runtime::forbidden==0,"interpreter or unexpected syscall reached");
 std::cout << std::dec << "PASS: " << assertions << " V41 original OSInit exception-template clearing native assertions, 6 OSInit paths + direct helpers, no interpreter fallback\n";
 return 0;
}catch(const std::exception& e){std::cerr<<"V41 original test failed: "<<e.what()<<'\n';return 1;}
