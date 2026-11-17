// Source-only continuous Wii V53 original EXI mask/MMIO maintenance-loop dispatcher. No owner code shipped.
// All owner DOL bytes and generated game C++ remain private.
#include "loader/loader.h"
#include "analyzer/analyzer.h"
#include "recompiler/recompiler.h"
#include <array>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <set>
#include <stdexcept>
#include <string>
#include <vector>
namespace {
constexpr uint32_t START=0x8000403c,INIT=0x80004238,REGS=0x800041a8,HW=0x800042e0;
constexpr uint32_t DBINIT=0x804e5020,OSINIT=0x80520670,DBPRINTF=0x804e50b8;
constexpr uint32_t OSTIME=0x8052a844,GETTIME=0x8052a824,DISABLE=0x805265ac,RESTORE=0x805265d4,EXEC=0x80523b1c,PERF=0x804b7964;
constexpr uint32_t MFHID0=0x804b7920,MTHID0=0x804b7928,SPEC=0x804b7a00,NONIEEE=0x804b7a28,HID4=0x804b7a30,REPORT=0x80522f00;
constexpr uint32_t SAVE20=0x805450e8,ALTERNATIVE=0x80520bdc;
constexpr uint32_t STOP=0x80004160, PS=0x80520fb4, FPR=0x8051fbb0, CACHE=0x80522540;
constexpr uint32_t ERR=0x805230b8,ARENA_LO=0x80521d60,ARENA_HI=0x80521d48;
constexpr uint32_t MEM2_LO=0x80521d68,MEM2_HI=0x80521d50,IPC=0x8052ae80;
constexpr uint32_t EXCEPTION=0x80520bf4,EXC_STOP=0x80520e58,RESTGPR=0x80545134,OS_RET_STOP=0x805208c8, EXI=0x804ef9bcu, EXI_STOP=0x804efa34u,MASK=0x8052693cu,SYSCALL=0x805290c8,SYSCALL_SOURCE=0x805290a8,EXC_FIRST_STOP=0x80520cdc,EXC_SECOND_DEBUG=0x80520d08,EXC_DEBUG_STOP=0x80520c44;
constexpr uint32_t MARK=0x804e50a0;
constexpr uint32_t EXC_SOURCE_WORD=0x80520f28;
constexpr uint32_t VECTOR_COPY_CALL=0x80520d98, COPY=0x80004338, VECTOR_DEST=0x80000100;
constexpr uint32_t DCFLUSH=0x80522320,ICINVALID=0x80522378;
constexpr uint32_t ALARM=0x805210cc,GETEXC=0x80520eb0,SETEXC=0x80520e9c,SHUTDOWN=0x80527b4c,MODULE=0x80526d30;
constexpr uint32_t IRQ=0x8052661cu,IRQ_MEMSET_CALL=0x80526648u,IRQ_STOP=0x805266E0u,IRQ_MEMSET=0x8000443cu,IRQ_FILL=0x80004388u;
constexpr uint32_t SETMASK=0x805266e0u,SETMASK_CALL=0x805266a0u,SETMASK_END=0x8052693cu;
constexpr uint32_t CONTEXT=0x80522eb8u,CONTEXT_END=0x80522f00u;
constexpr uint32_t ORACLE_GUEST=0x90050000u,ORACLE_SIZE=0x98u;
void require(bool v,const std::string& msg){if(!v)throw std::runtime_error(msg);}
uint32_t be32(const uint8_t* data){return (uint32_t(data[0])<<24)|(uint32_t(data[1])<<16)|(uint32_t(data[2])<<8)|data[3];}
uint32_t branch(uint32_t ins,uint32_t pc){
 require((ins>>26)==18 && (ins&3)==1,"expected absolute-free PPC BL");
 uint32_t imm=ins&0x03fffffc;
 if(imm&0x02000000)imm|=0xfc000000;
 return pc+imm;
}
void verify_file(const std::filesystem::path& path,bool owner){
 std::ifstream in(path,std::ios::binary|std::ios::ate);
 require(bool(in),"failed opening private test DOL");
 const auto bytes=in.tellg();
 require(bytes>=0x100 && bytes<=128*1024*1024,"malformed DOL file size");
 in.seekg(0);std::array<uint8_t,256> header{};
 require(bool(in.read(reinterpret_cast<char*>(header.data()),header.size())),"short DOL header");
 std::vector<std::pair<uint64_t,uint64_t>> file_regions,guest_regions;
 unsigned sections=0;
 for(unsigned data=0;data<2;++data){
  for(unsigned i=0;i<(data?11u:7u);++i){
   uint32_t off=be32(header.data()+(data?0x1c:0)+4*i);
   uint32_t addr=be32(header.data()+(data?0x64:0x48)+4*i);
   uint32_t n=be32(header.data()+(data?0xac:0x90)+4*i);
   if(off==0 && n==0)continue;
   require(off>=256 && n && ((off|addr)&3u)==0,"invalid DOL section offset/alignment");
   require(uint64_t(off)+n<=static_cast<uint64_t>(bytes),"DOL section exceeds file");
   uint64_t end=uint64_t(addr)+n;
   require((addr>=0x80000000u && end<=0x81800000ull)||
           (addr>=0x90000000u && end<=0x94000000ull),"DOL section outside guest RAM");
   for(const auto& [start,stop]:file_regions)
    require(off>=stop || uint64_t(off)+n<=start,"overlapping DOL file sections");
   for(const auto& [start,stop]:guest_regions)
    require(addr>=stop || end<=start,"overlapping DOL guest sections");
   file_regions.emplace_back(off,uint64_t(off)+n);
   guest_regions.emplace_back(addr,end);
   ++sections;
  }
 }
 require(sections==(owner?9u:8u),
         "V38 requires seven text sections plus one startup-data and one private template-oracle section");
 if(owner){
   require(be32(header.data()+0x64)==0x80006420u &&
           be32(header.data()+0xac)==0xB0u,
           "original __init_data relocator table changed");
   require(be32(header.data()+0x20)>=256u &&
           be32(header.data()+0x68)==ORACLE_GUEST &&
           be32(header.data()+0xb0)==ORACLE_SIZE,
           "missing exact private original handler template data section");
 }
 require(be32(header.data()+0xe0)==START,"wrong DOL entry");
}
}
int main(int argc,char** argv)try{
 require(argc==4,"Usage: generator PRIVATE.DOL EMPTY_DIR owner|synthetic");
 const std::string mode=argv[3];
 require(mode=="owner"||mode=="synthetic","unknown V25 mode");
 const bool owner=mode=="owner";
 const std::filesystem::path output=argv[2];
 require(std::filesystem::is_directory(output)&&std::filesystem::is_empty(output),
         "output directory must exist and be empty");
 verify_file(argv[1],owner);
 nwii::loader::Executable exe;
 require(exe.load_dol(argv[1]),"private test image load failed");
 nwii::analyzer::Analyzer analyzer(exe);
 analyzer.analyze({FPR,CACHE,REPORT});
 const auto& funcs=analyzer.get_functions();
 require(owner ? (funcs.size()>=62u && funcs.size()<=136u) : funcs.size()==24u,
          "unexpected V30 analyzed function count: "+std::to_string(funcs.size()));
 for(uint32_t pc:{START,REGS,HW,INIT,PS,FPR,CACHE,DBINIT,DBPRINTF,OSINIT,ERR,OSTIME,SAVE20})
  require(funcs.count(pc)==1,"missing expected PPC function");
 const auto& start=funcs.at(START).instructions;
 require(start.size()==(owner?74u:10u),"startup entry function size changed");
 require(branch(start.at(0).opcode,START)==REGS && branch(start.at(1).opcode,START+4)==HW,
         "original entry register/hardware calls changed");
 require(branch(start.at(6).opcode,START+24)==INIT,"original third startup call changed");
 if(owner){
  require(start.at(7).opcode==0x38000000u,"expected original post-data LI zero");
  for(const auto& [at,target] : std::array<std::pair<uint32_t,uint32_t>,2>{{{0x80004158u,DBINIT},{0x8000415cu,OSINIT}}}){
   bool found=false;
   for(const auto& ins:start)if(ins.address==at){require(branch(ins.opcode,at)==target,"original DB/OS startup call target changed");found=true;}
   require(found,"original DB/OS startup call missing");
  }
  for(uint32_t pc:{0x800040c8u,0x800040dcu}){
   const auto idx=(pc-START)/4;
   require(start.at(idx).opcode==0x44000002u,"alternative boot branch must be test-only guarded");
  }
  require(start.back().address==STOP && start.back().opcode==0x4e800020u,
          "missing synthetic stop continuation BLR");
  const auto& db=funcs.at(DBINIT).instructions;
  require(db.size()==10 && db.back().opcode==0x4e800020u,"original DBInit incomplete");
  require(db.at(5).opcode>>26==36 && db.at(7).opcode>>26==36 && db.at(8).opcode>>26==36,
          "original DBInit guest stores changed");
 }else{
  const auto& db=funcs.at(DBINIT).instructions;
  require(db.size()==4 && db.back().opcode==0x4e800020u, "synthetic DBInit incomplete");
  require(db[0].opcode==0x3d208003u && db[1].opcode==0x394055aau &&
          db[2].opcode==0x91497000u, "synthetic DBInit body does not match test fixture");
  require(branch(start.at(7).opcode,0x80004058u)==DBINIT &&
          branch(start.at(8).opcode,0x8000405cu)==OSINIT,"synthetic DBInit/OSInit calls missing");
 }
 const auto& os=funcs.at(OSINIT).instructions;
 
 require(os.size()==(owner?154u:10u),"bounded original OSInit + interrupt entry incomplete");
 if(owner){
  require(os[15].opcode>>26==36 && os[16].opcode>>26==36,
          "original 64-bit OS timestamp stores changed");
  require(os[17].address==0x805206b4u &&
          branch(os[17].opcode,0x805206b4u)==DISABLE,
          "real original OSInit B4 interrupt-disable call missing");
  require(os[18].address==0x805206b8u && os[18].opcode>>26==14,
          "original post-disable OSInit fallthrough changed");
  require(os[19].address==0x805206bcu &&
          branch(os[19].opcode,0x805206bcu)==EXEC,
          "original OSInit __OSGetExecParams call is missing");
  for(unsigned i=0;i<6;++i){
    const auto li=20u+2u*i, call=li+1u;
    require(os[li].address==0x805206c0u+8u*i && os[li].opcode>>26==14,
            "original performance helper argument initialization missing");
    require(os[call].address==0x805206c4u+8u*i &&
            branch(os[call].opcode,0x805206c4u+8u*i)==PERF+8u*i,
            "original MMCR/PMC call edge missing");
  }
  for(const auto& [at,callee] : std::array<std::pair<uint32_t,uint32_t>,3>{{
      {0x805206f4u,HID4},{0x805206f8u,SPEC},{0x805206fcu,NONIEEE}}}){
    require(os.at((at-OSINIT)/4).address==at &&
            branch(os.at((at-OSINIT)/4).opcode,at)==callee,
            "original HID4/speculation/FPSCR call edge changed");
  }
  for(unsigned i=36;i<66;++i)
    require(os[i].address==0x80520700u+(i-36u)*4u &&
            os[i].opcode!=0x44000002u,
            "original Wii low-memory code truncated by test boundary");
  require(os[65].opcode>>26==32,
          "final original low-memory arena-hint read changed");
  for(unsigned i=66;i<106;++i)
    require(os[i].address==0x80520778u+(i-66u)*4u &&
            os[i].opcode!=0x44000002u,
            "original Wii MEM1 decision block contains unexpected test-only opcode");
  require(branch(os[(0x805207e8u-OSINIT)/4].opcode,0x805207e8u)==ARENA_LO &&
          branch(os[(0x80520814u-OSINIT)/4].opcode,0x80520814u)==ARENA_HI,
          "original MEM1 low/high setter call edges changed");
  for(unsigned i=106;i<141;++i)
    require(os[i].address==0x80520818u+(i-106u)*4u &&
            os[i].opcode!=0x44000002u,
            "original Wii MEM2 selection block truncated or changed");
  require(branch(os[(0x8052088cu-OSINIT)/4u].opcode,0x8052088cu)==MEM2_LO &&
          branch(os[(0x805208a0u-OSINIT)/4u].opcode,0x805208a0u)==MEM2_HI,
          "original Wii MEM2 arena low/high BL callsites changed");
  require(os[141].address==0x805208a4u &&
          branch(os[141].opcode,0x805208a4u)==IPC,
          "original OSInit IPC-buffer helper call target changed");
  require(os[142].address==0x805208a8u &&
          branch(os[142].opcode,0x805208a8u)==EXCEPTION,
          "original OSExceptionInit BL call target changed");
  require(os[143].address==0x805208acu &&
          branch(os[143].opcode,0x805208acu)==SYSCALL &&
          os[144].address==0x805208b0u &&
          branch(os[144].opcode,0x805208b0u)==ALARM &&
          os[145].address==0x805208b4u &&
          branch(os[145].opcode,0x805208b4u)==MODULE &&
          os[146].address==0x805208b8u &&
          branch(os[146].opcode,0x805208b8u)==IRQ &&
          os[147].address==0x805208bcu &&
          branch(os[147].opcode,0x805208bcu)==CONTEXT &&
          os[148].address==0x805208c0u &&
          branch(os[148].opcode,0x805208c0u)==CACHE &&
          os[149].address==0x805208c4u && branch(os[149].opcode,0x805208c4u)==EXI &&
          os[150].address==OS_RET_STOP && os[150].opcode==0x44000002u &&
          os[151].opcode==0x4e800020u,
          "original OSInit IRQ/context BL or bounded next OS stop missing");
 }else require(os[9].opcode==0x4e800020u,
               "synthetic OSInit prefix missing boundary");
 if(owner){require(os[152].address==ALTERNATIVE && os[152].opcode==0x44000002u && os[153].opcode==0x4e800020u,
   "unimplemented repeat-OSInit branch not explicitly stopped");}
 if(owner){
   require(funcs.count(EXI)==1,"original EXI entry missing from continuous native dispatch");
   const auto& exi=funcs.at(EXI).instructions;
   require(exi.size()==32u && exi.front().address==EXI && exi.front().opcode==0x9421ffe0u &&
           exi[30].address==EXI_STOP && exi[30].opcode==0x44000002u &&
           exi[31].opcode==0x4e800020u,"EXI mask/MMIO original prefix or explicit stop incomplete");
   require(branch(exi[22].opcode,0x804efa14u)==MASK,
           "authentic EXI interrupt-mask helper call was not restored");
   require(funcs.count(MASK)==1,"original Wii __OSMaskInterrupts body missing");
   const auto& mask=funcs.at(MASK).instructions;
   require(mask.size()==32u && mask.front().address==MASK &&
           (mask.front().opcode>>26)==37u &&
           mask.back().opcode==0x4e800020u,
           "original Wii __OSMaskInterrupts prologue or epilogue differs");
   for(const auto& edge:std::array<std::pair<uint32_t,uint32_t>,3>{{
         {0x80526958u,0x805265acu},
         {0x80526988u,SETMASK},
         {0x80526998u,0x805265d4u}}}){
      bool found=false;
      for(const auto& ins:mask)if(ins.address==edge.first){
         require(branch(ins.opcode,ins.address)==edge.second,
                 "original Wii __OSMaskInterrupts nested branch changed");
         found=true;
      }
      require(found,"original Wii __OSMaskInterrupts nested callsite missing");
   }
   for(uint32_t pc:{0x804efa20u,0x804efa24u,0x804efa28u,0x804efa30u}){
      bool found=false;
      for(const auto& ins:exi)if(ins.address==pc){
          require(ins.opcode>>26==36u,"original EXIInit MMIO store opcode changed");
          found=true;
      }
      require(found,"authentic EXI channel MMIO write missing");
   }
   for(uint32_t pc:{0x804ef9dcu,0x804ef9ecu,0x804ef9fcu}){
      bool found=false;
      for(const auto& ins:exi)if(ins.address==pc&&ins.opcode>>26==32u)found=true;
      require(found,"authentic EXI channel status LWZ missing");
   }
 }
 std::vector<uint32_t> stops{DBPRINTF,ERR};
 if(!owner)stops.push_back(OSTIME);
 for(uint32_t stop:stops){
  const auto& f=funcs.at(stop).instructions;
  require(f.size()==2 && f[0].opcode==0x44000002u && f[1].opcode==0x4e800020u,
          "unimplemented service missing explicit synthetic stop");
 }
 const auto& saver=funcs.at(SAVE20).instructions;
 require(saver.size()==(owner?13u:2u)&&saver.back().opcode==0x4e800020u,
         "GPR save helper incomplete");
 if(owner){
  require(os[0].opcode==0x9421ffb0u&&os[1].opcode==0x7c0802a6u,
          "original OSInit prologue changed");
  require(os[2].opcode==0x90010054u && os[3].opcode==0x39610050u,
          "original OSInit stack frame or LR save changed");
  require(branch(os[4].opcode,OSINIT+0x10)==SAVE20,
          "original register-save call changed");
  require(os[12].opcode==0x38000001u&&os[13].opcode==0x900df21cu,
          "original OS init-once store changed");
  require(branch(os[14].opcode,OSINIT+0x38)==OSTIME,
          "original OS time call changed");
  for(size_t i=0;i<12;++i)
   require(saver[i].opcode>>26==36,"original nonvolatile GPR save opcode changed");
 }else{
  require(os[0].opcode==0x9421ffa0u && os[7].opcode==0x91497004u,
          "independent synthetic OS prefix changed");
  require(branch(os[4].opcode,OSINIT+0x10)==SAVE20 &&
          branch(os[8].opcode,OSINIT+0x20)==OSTIME,
          "synthetic helper/time calls changed");
  require(saver[0].opcode==0x930bffd0u,"synthetic GPR save changed");
 }
 nwii::recomp::RecompilerConfig config;
 config.output_dir=output.string();config.split_output=false;
 nwii::recomp::Recompiler generator(analyzer,nullptr,config);
 auto files=generator.generate_cpp(START);
 require(files.size()==1 && files[0]=="output.cpp","unexpected output configuration");
 if(owner){
  for(uint32_t pc:{GETTIME,DISABLE,RESTORE,EXEC})
    require(funcs.count(pc)==1,"missing original PowerPC time/interrupt/execparams function");
  const auto& exec=funcs.at(EXEC).instructions;
  require(exec.size()==9u && exec.front().address==EXEC &&
          exec.back().address==EXEC+32,
          "authentic __OSGetExecParams body incomplete");
  for(unsigned i=0;i<6;++i){
    const auto pc=PERF+8u*i;
    require(funcs.count(pc)==1,"missing authentic original MMCR/PMC helper");
    const auto& instructions=funcs.at(pc).instructions;
    require(instructions.size()==2u &&
            instructions.front().address==pc &&
            ((instructions.front().opcode>>1)&1023u)==467u &&
            instructions.back().opcode==0x4e800020u,
            "incomplete translated native performance helper");
  }
  for(const auto& [pc,count] : std::array<std::pair<uint32_t,size_t>,5>{{
      {MTHID0,2u},{SPEC,10u},{NONIEEE,2u},{HID4,20u},{REPORT,2u}}}){
    require(funcs.count(pc)==1,"missing original or guarded Wii HID4 function");
    const auto& instructions=funcs.at(pc).instructions;
    require(instructions.size()==count && instructions.front().address==pc &&
            instructions.back().address==pc+4u*(count-1u),
            "incomplete native HID4/FP function body");
  }
  for(const auto& [pc,disp] : std::array<std::pair<uint32_t,int32_t>,2>{{
      {ARENA_LO,-16400},{ARENA_HI,-3472}}}){
    require(funcs.count(pc)==1,"original Wii arena setter not translated");
    const auto& setter=funcs.at(pc).instructions;
    require(setter.size()==2u &&
            setter.front().address==pc &&
            setter.front().opcode>>26==36u &&
            (setter.front().opcode>>21 &31u)==3u &&
            (setter.front().opcode>>16 &31u)==13u &&
            static_cast<int16_t>(setter.front().opcode&0xFFFFu)==disp &&
            setter.back().opcode==0x4e800020u,
            "original Wii arena global setter PPC body is incomplete");
  }
  for(const auto& [pc,disp] : std::array<std::pair<uint32_t,int32_t>,2>{{
      {MEM2_LO,-16396},{MEM2_HI,-3468}}}){
    require(funcs.count(pc)==1,"original Wii MEM2 arena setter not translated");
    const auto& body=funcs.at(pc).instructions;
    require(body.size()==2u &&
            body.front().address==pc &&
            body.front().opcode>>26==36u &&
            ((body.front().opcode>>21)&31u)==3u &&
            ((body.front().opcode>>16)&31u)==13u &&
            static_cast<int16_t>(body.front().opcode&0xffffu)==disp &&
            body.back().opcode==0x4e800020u,
            "original MEM2 arena global setter PPC instructions differ");
  }
  require(funcs.count(IPC)==1,"genuine Wii IPC-buffer original function missing");
  const auto& ipc=funcs.at(IPC).instructions;
  require(ipc.size()==6u && ipc.front().address==IPC &&
          ipc.back().address==IPC+20u && ipc.back().opcode==0x4e800020u,
          "original IPC-buffer initializer incomplete");
  require(ipc.at(0).opcode>>26==15u &&
          ipc.at(1).opcode>>26==32u &&
          ipc.at(2).opcode>>26==36u &&
          ipc.at(3).opcode>>26==32u &&
          ipc.at(4).opcode>>26==36u,
          "original IPC-buffer guest memory access instructions changed");
  require(funcs.count(EXCEPTION)==1,"original Wii OSExceptionInit not translated");
  const auto& exc=funcs.at(EXCEPTION).instructions;
  require(!exc.empty() && exc.front().address==EXCEPTION &&
          exc.front().opcode==0x9421ffc0u,
          "original OSExceptionInit stack frame prologue incomplete");
  require(branch(exc.at(4).opcode,EXCEPTION+0x10u)==SAVE20,
          "original exception nonvolatile GPR save helper not called");
  bool reached_stop=false,reached_debug_stop=false,reached_first_stop=false,reached_second_debug=false;
  for(const auto& ins:exc){
    if(ins.address==EXC_STOP){
      require(branch(ins.opcode,EXC_STOP)==DBPRINTF,
              "original exception terminal debug BL target changed");
      reached_stop=true;
    }
    if(ins.address==EXC_DEBUG_STOP){
      require(ins.opcode==0x44000002u,"exception unimplemented DBPrintf not guarded");
      reached_debug_stop=true;
    }
    if(ins.address==EXC_FIRST_STOP){
      require(ins.opcode==0x44000002u,"exception first debug-service boundary unguarded");
      reached_first_stop=true;
    }
    if(ins.address==EXC_SECOND_DEBUG){
      require(ins.opcode==0x44000002u,"exception second debug-service boundary unguarded");
      reached_second_debug=true;
    }
  }
  require(reached_stop&&reached_debug_stop&&reached_first_stop&&reached_second_debug,
          "original exception/guarded debug branches not analyzed");
  bool restore_bl=false,return_blr=false;
  for(const auto& ins:exc){
    if(ins.address==0x80520e60u){
      require(branch(ins.opcode,ins.address)==RESTGPR,
              "original exception epilogue restore BL target changed");
      restore_bl=true;
    }
    if(ins.address==0x80520e70u){
      require(ins.opcode==0x4e800020u,
              "original OSExceptionInit epilogue does not return");
      return_blr=true;
    }
  }
  require(restore_bl&&return_blr,"original Wii exception return/restore not translated");
  require(funcs.count(RESTGPR)==1,"authentic Wii _restgpr_20 missing");
  const auto& rest=funcs.at(RESTGPR).instructions;
  require(rest.size()==13u && rest.front().address==RESTGPR &&
          rest.back().address==RESTGPR+48u && rest.back().opcode==0x4e800020u,
          "original _restgpr_20 thunk is incomplete");
  require(os[143].address==0x805208acu &&
          branch(os[143].opcode,0x805208acu)==SYSCALL &&
          os[144].address==0x805208b0u &&
          branch(os[144].opcode,0x805208b0u)==ALARM &&
          os[145].address==0x805208b4u &&
          branch(os[145].opcode,0x805208b4u)==MODULE &&
          os[146].address==0x805208b8u &&
          branch(os[146].opcode,0x805208b8u)==IRQ &&
          os[147].address==0x805208bcu &&
          branch(os[147].opcode,0x805208bcu)==CONTEXT &&
          os[148].address==0x805208c0u &&
          branch(os[148].opcode,0x805208c0u)==CACHE &&
          os[149].address==0x805208c4u && branch(os[149].opcode,0x805208c4u)==EXI &&
          os[150].address==OS_RET_STOP && os[150].opcode==0x44000002u,
          "original OSInit IRQ/context native BL and bounded stop changed");
  // __OSCacheInit was already authentically translated and executed from
   // __start. The same function must serve the second original OSInit BL.
   const auto& cache_code=funcs.at(CACHE).instructions;
   require(cache_code.size()==78u && cache_code.front().address==CACHE &&
           cache_code.back().opcode==0x4e800020u,
           "original Wii __OSCacheInit body not available for second call");
   require(funcs.count(CONTEXT)==1,
          "owner-original __OSContextInit not translated");
  const auto& context=funcs.at(CONTEXT).instructions;
  require(context.size()==18u && context.front().address==CONTEXT &&
          context.back().address==CONTEXT_END-4u &&
          context.back().opcode==0x4e800020u,
          "original Wii context initializer body incomplete");
  bool handler=false,debug=false;
  for(const auto& ins:context){
    if(ins.address==CONTEXT+0x18u){
      require(branch(ins.opcode,ins.address)==SETEXC,
              "original Wii context exception-handler BL changed");
      handler=true;
    }
    if(ins.address==CONTEXT+0x34u){
      require(branch(ins.opcode,ins.address)==DBPRINTF,
              "original Wii context debug BL changed");
      debug=true;
    }
  }
  require(handler&&debug,
          "original __OSContextInit handler/debug native call graph incomplete");
  require(funcs.count(SYSCALL)==1,
          "owner original __OSInitSystemCall function not translated");
  for(uint32_t pc:{ALARM,GETEXC,SETEXC,SHUTDOWN,MODULE})
    require(funcs.count(pc)==1,"genuine Wii alarm/shutdown/module native function missing");
  const auto& module=funcs.at(MODULE).instructions;
  require(module.size()==6u && module.front().address==MODULE &&
          module.back().opcode==0x4e800020u,
          "authentic original Wii __OSModuleInit PPC function incomplete");
  const auto& alarm=funcs.at(ALARM).instructions;
  const auto& get=funcs.at(GETEXC).instructions;
  const auto& set=funcs.at(SETEXC).instructions;
  const auto& shutdown=funcs.at(SHUTDOWN).instructions;
  require(alarm.size()==22u && alarm.front().opcode==0x9421fff0u &&
          alarm.back().opcode==0x4e800020u,
          "original Wii __OSInitAlarm body not completely translated");
  require(get.size()==4u && set.size()==5u && shutdown.size()==34u &&
          shutdown.back().opcode==0x4e800020u,
          "original exception handler accessors/shutdown register function incomplete");
  for(const auto& [site,destination]:std::array<std::pair<uint32_t,uint32_t>,3>{{
      {ALARM+0x10u,GETEXC},{ALARM+0x38u,SETEXC},
      {ALARM+0x44u,SHUTDOWN}}}){
    bool matched=false;
    for(const auto& ins:alarm)if(ins.address==site){
      require(branch(ins.opcode,site)==destination,
              "original Wii alarm helper BL edge changed");
      matched=true;
    }
    require(matched,"original Wii alarm helper BL callsite missing");
  }
  for(uint32_t pc:{IRQ,IRQ_MEMSET,IRQ_FILL})
     require(funcs.count(pc)==1,"original Wii interrupt and memset/fill helper missing");
   const auto& irq=funcs.at(IRQ).instructions;
   const auto& memset_func=funcs.at(IRQ_MEMSET).instructions;
   const auto& fill_func=funcs.at(IRQ_FILL).instructions;
   require(irq.size()==49u && irq.front().address==IRQ &&
           irq.front().opcode==0x9421ffe0u &&
           irq.back().address==IRQ_STOP-4u &&
           irq.back().opcode==0x4e800020u,
           "original Wii __OSInterruptInit return epilogue missing");
   bool restore_called=false,handler_called=false;
   for(const auto& ins:irq){
     if(ins.address==0x805266b0u){
       require(branch(ins.opcode,ins.address)==RESTORE,
               "genuine Wii IRQ OSRestoreInterrupts BL edge changed");
       restore_called=true;
     }
     if(ins.address==0x805266c0u){
       require(branch(ins.opcode,ins.address)==SETEXC,
               "genuine Wii IRQ __OSSetExceptionHandler BL edge changed");
       handler_called=true;
     }
   }
   require(restore_called&&handler_called,
           "original Wii IRQ epilogue helper BL graph incomplete");
   require(funcs.count(SETMASK)==1,"owner-original SetInterruptMask missing");
   const auto& setmask=funcs.at(SETMASK).instructions;
   require(setmask.size()==151u && setmask.front().address==SETMASK &&
           setmask.back().address==SETMASK_END-4u &&
           setmask.back().opcode==0x4e800020u,
           "full 151-instruction original SetInterruptMask body incomplete");
   bool setmask_called=false;
   for(const auto& ins:irq)if(ins.address==SETMASK_CALL){
     require(branch(ins.opcode,SETMASK_CALL)==SETMASK,
             "original IRQ native SetInterruptMask BL target changed");
     setmask_called=true;
   }
   require(setmask_called,"original IRQ SetInterruptMask BL not analyzed");
   for(uint32_t address:{0x80526708u,0x80526778u,0x805267b8u,
          0x805267e4u,0x80526828u,0x8052686cu,
          0x805268a0u,0x80526938u}){
     const size_t offset=(address-SETMASK)/4u;
     require(offset<setmask.size() && setmask[offset].address==address &&
             setmask[offset].opcode==0x4e800020u,
             "SetInterruptMask multi-return original PPC graph differs");
   }
   auto is_stw=[](uint32_t ins,uint32_t src,uint32_t base,uint32_t offset){
     return (ins>>26)==36u && ((ins>>21)&31u)==src &&
            ((ins>>16)&31u)==base && (ins&0xffffu)==offset;
   };
   require(irq[20].address==0x8052666cu &&
           is_stw(irq[20].opcode,5u,4u,0x3004u) &&
           irq[21].address==0x80526670u &&
           is_stw(irq[21].opcode,0u,3u,0x34u),
           "authentic interrupt-controller MMIO store instruction encoding changed");
   require(irq[22].address==0x80526674u &&
           branch(irq[22].opcode,0x80526674u)==DISABLE,
           "original Wii interrupt-disable call missing from native IRQ prefix");
   require(irq[28].address==0x8052668cu &&
           is_stw(irq[28].opcode,30u,31u,0x00c4u),
           "original Wii interrupt-mask state store encoding changed");
   require(memset_func.size()==12u && fill_func.size()==45u &&
           memset_func.back().opcode==0x4e800020u &&
           fill_func.back().opcode==0x4e800020u,
           "original Wii memset/__fill_mem helper bodies missing");
   bool irq_memset_call=false,memset_fill_call=false;
   for(const auto& ins:irq)if(ins.address==IRQ_MEMSET_CALL){
     require(branch(ins.opcode,IRQ_MEMSET_CALL)==IRQ_MEMSET,
             "original __OSInterruptInit BL into memset changed");
     irq_memset_call=true;
   }
   for(const auto& ins:memset_func)if(ins.address==0x80004450u){
     require(branch(ins.opcode,0x80004450u)==IRQ_FILL,
             "original memset BL into __fill_mem changed");
     memset_fill_call=true;
   }
   require(irq_memset_call&&memset_fill_call,
           "native Wii interrupt memory initialization helper graph incomplete");
   const auto& sys=funcs.at(SYSCALL).instructions;
  require(sys.size()==24u && sys.front().address==SYSCALL &&
          sys.front().opcode==0x9421fff0u &&
          sys.back().opcode==0x4e800020u,
          "original __OSInitSystemCall function is incomplete");
  for(const auto& [site,destination] : std::array<std::pair<uint32_t,uint32_t>,3>{{
       {SYSCALL+0x2cu,COPY},{SYSCALL+0x38u,DCFLUSH},
       {SYSCALL+0x48u,ICINVALID}}}){
    bool matched=false;
    for(const auto& ins:sys)if(ins.address==site){
      require(branch(ins.opcode,site)==destination,
              "original __OSInitSystemCall native helper branch changed");
      matched=true;
    }
    require(matched,"original __OSInitSystemCall guest callsite absent");
  }
  bool vector_copy_call=false;
  for(const auto& ins:exc)if(ins.address==VECTOR_COPY_CALL){
    require(branch(ins.opcode,VECTOR_COPY_CALL)==COPY,
            "original exception memcpy helper BL callsite changed");
    vector_copy_call=true;
  }
  require(vector_copy_call,
          "authentic original exception vector-copy helper not analyzed");
  for(const auto& [site,callee] : std::array<std::pair<uint32_t,uint32_t>,2>{{
      {0x80520da4u,DCFLUSH},{0x80520db4u,ICINVALID}}}){
    bool found=false;
    for(const auto& ins:exc)if(ins.address==site){
      require(branch(ins.opcode,site)==callee,
              "original Wii exception cache service BL edge differs");
      found=true;
    }
    require(found,"authentic Wii cache service callsite missing");
  }
  for(const auto& [pc,length] : std::array<std::pair<uint32_t,size_t>,2>{{
      {DCFLUSH,11u},{ICINVALID,13u}}}){
    require(funcs.count(pc)==1,"original Wii cache service not translated");
    const auto& code=funcs.at(pc).instructions;
    require(code.size()==length && code.front().address==pc &&
            code.back().opcode==0x4e800020u,
            "original Wii cache service BLR/body incomplete");
    require((code.at(7).opcode>>26)==31u,
            "original PPC cache-line instruction changed");
  }
  for(const auto& [site,op] : std::array<std::pair<uint32_t,uint32_t>,3>{{ 
       {0x80520d20u,0x28150000u},{0x80520d64u,0x4200ffdcu},
       {0x80520d7cu,0x4200fff8u}}}){
    bool found=false;
    for(const auto& ins:exc)if(ins.address==site){
      require(ins.opcode==op,"original PPC template-clearing loop instruction differs");
      found=true;
    }
    require(found,"original PPC loop instruction missing");
  }
  // Original fifteen-vector loopback and terminal setup before DBPrintf.
  for(const auto& [site,op] : std::array<std::pair<uint32_t,uint32_t>,5>{{
      {0x80520db8u,0x3bbd0001u},{0x80520dbcu,0x281d000fu},
      {0x80520dc0u,0x4180fee8u},{0x80520e50u,0x937c0000u},
      {0x80520e54u,0x4cc63182u}}}){
    bool found=false;
    for(const auto& ins:exc)if(ins.address==site){
      require(ins.opcode==op,"original Wii 15-vector installation opcode changed");
      found=true;
    }
    require(found,"original Wii 15-vector loop setup not analyzed");
  }
  for(uint32_t site:{0x80520cc4u,0x80520cf0u}){
    bool found=false;
    for(const auto& ins:exc)if(ins.address==site){
      require(branch(ins.opcode,site)==MARK,
              "original __DBIsExceptionMarked guest call changed");
      found=true;
    }
    require(found,"original exception marker callsite not analyzed");
  }
  require(funcs.count(MARK)==1,
          "genuine original __DBIsExceptionMarked not translated");
  const auto& marker=funcs.at(MARK).instructions;
  require(marker.size()==6u && marker.front().address==MARK &&
          marker.front().opcode==0x808defc0u &&
          marker.at(4).opcode==0x7c630038u &&
          marker.back().opcode==0x4e800020u,
          "original exception marker PPC bitmask function changed");
  const auto& report=funcs.at(REPORT).instructions;
  require(report.front().opcode==0x44000002u &&
          report.back().opcode==0x4e800020u,
          "original OSReport branch must remain an explicit test-only boundary");
  const auto& t=funcs.at(OSTIME).instructions;
  require(t.size()==25 && t.back().opcode==0x4e800020u,
          "original __OSGetSystemTime body incomplete");
  require(branch(t[6].opcode,0x8052a85cu)==DISABLE &&
          branch(t[8].opcode,0x8052a864u)==GETTIME &&
          branch(t[15].opcode,0x8052a880u)==RESTORE,
          "original time/interrupt inter-function call graph changed");
  require(funcs.at(GETTIME).instructions.size()==6 &&
          funcs.at(DISABLE).instructions.size()==5 &&
          funcs.at(RESTORE).instructions.size()==9,
          "original PowerPC helper body length changed");
 }
 std::cout<<"PASS: V53 recovered continuous original Wii EXI-mask native dispatcher, mode="<<mode
          <<" functions="<<funcs.size()<<" original_OSInit_prefix="<<owner<<"\n";
 return 0;
}catch(const std::exception& e){std::cerr<<"V25 generator: "<<e.what()<<"\n";return 1;}
