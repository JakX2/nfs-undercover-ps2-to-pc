// Independent, original-byte-free semantic tests for native Wii SetInterruptMask.
#include "runtime/cpu_context.h"
#include "loader/loader.h"
#include <array>
#include <cstdint>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <vector>
namespace {
constexpr uint32_t ENTRY=0x805266e0u, STOP=0x8052693cu, SP=0x80082000u;
struct Terminal{};
struct IO{bool read;unsigned width;uint32_t addr,val;};
std::vector<IO> actual;
uint32_t readback=0;
unsigned stops=0, entry_count=0, forbidden=0, interpreter=0;
uint64_t assertions=0;
void expect(bool ok,const char* reason){if(!ok)throw std::runtime_error(reason);++assertions;}
uint32_t bit(unsigned index){return uint32_t(0x80000000u)>>index;}
uint32_t reference(uint32_t select,uint32_t mask,uint32_t initial,uint32_t&write_addr,unsigned&width,bool&has_read,bool&has_write){
 // Independent semantic model for each original Wii interrupt-controller bank.
 // PPC bit indices count from the most significant bit; not C/C++ LSB indices.
 has_read=false;has_write=true;width=32;
 const unsigned group=__builtin_clz(select);
 if(group<5){write_addr=0x0c00401cu;width=16;
   uint32_t result=0;for(unsigned i=0;i<5;++i)if(!(mask&bit(i)))result|=1u<<i;return result;}
 if(group<8){write_addr=0x0c00500au;width=16;has_read=true;
   uint32_t result=initial&~0x1f8u;
   if(!(mask&bit(5)))result|=0x10u;
   if(!(mask&bit(6)))result|=0x40u;
   if(!(mask&bit(7)))result|=0x100u;
   return result&0xffffu;}
 if(group==8){write_addr=0x0d006c00u;has_read=true;
   return (initial&0xffffffd3u)|(!(mask&bit(8))?4u:0u);}
 if(group<12){write_addr=0x0d006800u;has_read=true;
   return (initial&0xffffd3f0u)|(!(mask&bit(9))?1u:0u)|(!(mask&bit(10))?4u:0u)|(!(mask&bit(11))?0x400u:0u);}
 if(group<15){write_addr=0x0d006814u;has_read=true;
   return (initial&0xfffff3f0u)|(!(mask&bit(12))?1u:0u)|(!(mask&bit(13))?4u:0u)|(!(mask&bit(14))?0x400u:0u);}
 if(group<17){write_addr=0x0d006828u;has_read=true;
   return (initial&0xfffffff0u)|(!(mask&bit(15))?1u:0u)|(!(mask&bit(16))?4u:0u);}
 if(group<28){write_addr=0x0c003004u;
   uint32_t result=0xf0u;
   constexpr unsigned ppc_indices[11]={17,20,21,22,23,24,25,18,19,26,27};
   constexpr uint32_t bits[11]={0x800u,8u,4u,2u,1u,0x100u,0x1000u,0x200u,0x400u,0x2000u,0x4000u};
   for(unsigned i=0;i<11;++i)if(!(mask&bit(ppc_indices[i])))result|=bits[i];
   return result;}
 has_write=false;return 0;
}
}
namespace nwii::runtime {
bool g_trace_calls=true;uint32_t g_watch_addr=0;
void trace_call(uint32_t pc,CPUContext&){if(pc==ENTRY){++entry_count;return;}if(pc==STOP)return;++forbidden;throw std::runtime_error("unexpected original guest dispatch");}
bool handle_syscall(CPUContext&ctx){if(ctx.pc!=STOP){++forbidden;throw std::runtime_error("unexpected guest syscall");}++stops;ctx.is_running=false;throw Terminal{};}
void interpret_step(CPUContext&){++interpreter;throw std::runtime_error("interpreter fallback");}
bool process_pending_callbacks(CPUContext&){return false;}
void watch_hit(uint32_t,uint32_t,int){}
void GX_WGPIPE_Write8(uint8_t){} void GX_WGPIPE_Write16(uint16_t){} void GX_WGPIPE_Write32(uint32_t){}
void GX_WGPIPE_WriteF32(float){} void GX_WGPIPE_WriteF64(double){}
uint16_t HW_Reg_Read16(uint32_t addr){actual.push_back({true,16,addr,readback&0xffff});return uint16_t(readback);}
uint32_t HW_Reg_Read32(uint32_t addr){actual.push_back({true,32,addr,readback});return readback;}
void HW_Reg_Write16(uint32_t addr,uint16_t value){actual.push_back({false,16,addr,value});}
void HW_Reg_Write32(uint32_t addr,uint32_t value){actual.push_back({false,32,addr,value});}
}
extern "C" void run_game(nwii::runtime::CPUContext&);
int main(int argc,char**argv)try{
 expect(argc==2,"usage: native_setmask_test PRIVATE_DOL");
 nwii::loader::Executable exe;
 expect(exe.load_dol(argv[1])&&exe.entry_point==ENTRY,"private original Wii SetInterruptMask image invalid");
 auto ctx=std::make_unique<nwii::runtime::CPUContext>();
 constexpr std::array<unsigned,10> groups{0,3,5,7,8,9,12,15,17,27};
 unsigned trial=0;
 for(unsigned index:groups){
  for(uint32_t mask:{0u,0xffffffffu,0xa55a6996u}){
   const uint32_t select=bit(index);
   const uint32_t initial=0xa5c33c5au + 0x10001u*trial;
   uint32_t addr=0;unsigned width=0;bool has_read=false,has_write=false;
   uint32_t write=reference(select,mask,initial,addr,width,has_read,has_write);
   readback=initial;actual.clear();
   ctx->pc=ENTRY;ctx->lr=STOP;ctx->gpr[1]=SP;ctx->gpr[3]=select;ctx->gpr[4]=mask;
   ctx->gpr[13]=0x8070e8e0u;ctx->gpr[29]=0x12345678u;ctx->gpr[30]=0x76543210u;
   ctx->is_running=true;
   const auto before_stop=stops, before_entry=entry_count; const auto before_inst=ctx->inst_count;
   bool terminal=false;try{run_game(*ctx);}catch(const Terminal&){terminal=true;}
   expect(terminal&&!ctx->is_running&&ctx->pc==STOP,"original helper did not return through synthetic stop");
   expect(stops==before_stop+1&&entry_count==before_entry+1,"original helper dispatch/stops mismatch");
   expect(ctx->inst_count>before_inst+3,"original helper executed too few instructions");
   expect(ctx->lr==STOP&&ctx->gpr[1]==SP,"original helper corrupted guest stack or LR");
   expect(ctx->gpr[13]==0x8070e8e0u&&ctx->gpr[29]==0x12345678u&&ctx->gpr[30]==0x76543210u,"original helper corrupted preserved registers");
   uint32_t expected_remaining=select;
   if(index<5)expected_remaining&=0x07ffffffu;
   else if(index<8)expected_remaining&=~0x07000000u;
   else if(index==8)expected_remaining&=~bit(8);
   else if(index<12)expected_remaining&=~(bit(9)|bit(10)|bit(11));
   else if(index<15)expected_remaining&=~(bit(12)|bit(13)|bit(14));
   else if(index<17)expected_remaining&=~(bit(15)|bit(16));
   else if(index<28)expected_remaining&=~0x00007ff0u; // PPC bits 17..27
   expect(ctx->gpr[3]==expected_remaining,"original interrupt mask did not clear selected bank bits");
   unsigned expected_io=unsigned(has_read)+unsigned(has_write);
   expect(actual.size()==expected_io,"unexpected MMIO read/write count");
   if(has_read){expect(actual[0].read&&actual[0].width==width&&actual[0].addr==addr&&actual[0].val==(initial&(width==16?0xffffu:0xffffffffu)),"original MMIO read mismatch");}
   if(has_write){const auto&out=actual[has_read?1:0];if(out.read||out.width!=width||out.addr!=addr||out.val!=write){std::cerr<<std::hex<<"trial="<<trial<<" index="<<index<<" mask="<<mask<<" want="<<write<<" got="<<out.val<<" addr="<<out.addr<<" expectedaddr="<<addr<<std::dec<<"\n";throw std::runtime_error("original MMIO write mismatch");}++assertions;}
   ++trial;
  }
 }
 // Native guest-call chain for the precise seven-bank mask sequence V53
 // leaves in r3. Each invocation is still a direct original function entry,
 // not a claim of integration into __OSInterruptInit or real interrupt hardware.
 constexpr std::array<uint32_t,8> sequence{0xfffffff0u,0x07fffff0u,
     0x00fffff0u,0x007ffff0u,0x000ffff0u,0x0001fff0u,0x00007ff0u,0u};
 for(uint32_t mask:{0u,0xffffffffu,0xa55a6996u}){
   for(size_t stage=0;stage+1<sequence.size();++stage){
     uint32_t initial=0x76543210u+uint32_t(stage)*0x10101u;
     uint32_t addr=0;unsigned width=0;bool has_read=false,has_write=false;
     uint32_t write=reference(sequence[stage],mask,initial,addr,width,has_read,has_write);
     actual.clear();readback=initial;
     ctx->pc=ENTRY;ctx->lr=STOP;ctx->gpr[1]=SP;ctx->gpr[3]=sequence[stage];
     ctx->gpr[4]=mask;ctx->is_running=true;
     const unsigned start=stops;
     bool terminal=false;try{run_game(*ctx);}catch(const Terminal&){terminal=true;}
     expect(terminal&&ctx->pc==STOP&&stops==start+1,"seven-bank native SetInterruptMask chain did not return");
     expect(ctx->gpr[3]==sequence[stage+1],"seven-bank original interrupt mask progression differs");
     expect(actual.size()==unsigned(has_read)+unsigned(has_write),"seven-bank original MMIO count differs");
     if(has_read){const auto&rd=actual.front();
       expect(rd.read&&rd.width==width&&rd.addr==addr&&rd.val==(initial&(width==16?0xffffu:0xffffffffu)),
           "seven-bank original MMIO read mismatch");}
     if(has_write){const auto&wr=actual[has_read?1:0];
       expect(!wr.read&&wr.width==width&&wr.addr==addr&&wr.val==write,"seven-bank original MMIO write mismatch");}
   }
 }
 // Early return instructions for no remaining interrupt group (bits 28..31 or zero).
 for(uint32_t select:{0x00000008u,0x00000001u,0u}){
   actual.clear();ctx->pc=ENTRY;ctx->lr=STOP;ctx->gpr[1]=SP;ctx->gpr[3]=select;ctx->gpr[4]=0u;ctx->is_running=true;
   bool terminal=false;try{run_game(*ctx);}catch(const Terminal&){terminal=true;}
   expect(terminal&&ctx->pc==STOP,"early-return path did not reach stop");
   expect(ctx->gpr[3]==select&&actual.empty(),"terminal mask must not access MMIO or change unhandled bits");
 }
 expect(forbidden==0&&interpreter==0,"unexpected interpreter or guest dispatch");
 std::cout<<"PASS: "<<assertions<<" V54 original Wii SetInterruptMask assertions across "<<trial+3+21<<" branch cases; zero interpreter fallback\n";
}catch(const std::exception&e){std::cerr<<"V54 native semantics: "<<e.what()<<"\n";return 1;}
