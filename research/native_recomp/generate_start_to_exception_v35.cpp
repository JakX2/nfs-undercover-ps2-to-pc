// Source-only continuous Wii V35 original exception prologue dispatcher. No owner code shipped.
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
constexpr uint32_t EXCEPTION=0x80520bf4,EXC_STOP=0x80520ca8,EXC_DEBUG_STOP=0x80520c44;
constexpr uint32_t EXC_SOURCE_WORD=0x80520f28;
void require(bool v,const std::string& msg){if(!v)throw std::runtime_error(msg);}
uint32_t be32(const uint8_t* data){return (uint32_t(data[0])<<24)|(uint32_t(data[1])<<16)|(uint32_t(data[2])<<8)|data[3];}
uint32_t branch(uint32_t ins,uint32_t pc){
 require((ins>>26)==18 && (ins&3)==1,"expected absolute-free PPC BL");
 uint32_t imm=ins&0x03fffffc;
 if(imm&0x02000000)imm|=0xfc000000;
 return pc+imm;
}
void verify_file(const std::filesystem::path& path){
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
 require(sections==8,"V25 expects seven code sections and one table");
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
 verify_file(argv[1]);
 nwii::loader::Executable exe;
 require(exe.load_dol(argv[1]),"private test image load failed");
 nwii::analyzer::Analyzer analyzer(exe);
 analyzer.analyze({FPR,CACHE,REPORT});
 const auto& funcs=analyzer.get_functions();
 require(owner ? (funcs.size()>=51u && funcs.size()<=72u) : funcs.size()==24u,
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
 
 require(os.size()==(owner?147u:10u),"bounded original OSInit exception setup incomplete");
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
  require(os[143].address==0x805208acu && os[143].opcode==0x44000002u &&
          os[144].opcode==0x4e800020u,
          "test-only guard before __OSInitSystemCall is missing");
 }else require(os[9].opcode==0x4e800020u,
               "synthetic OSInit prefix missing boundary");
 if(owner){require(os[145].address==ALTERNATIVE && os[145].opcode==0x44000002u && os[146].opcode==0x4e800020u,
   "unimplemented repeat-OSInit branch not explicitly stopped");}
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
  bool reached_stop=false,reached_debug_stop=false;
  for(const auto& ins:exc){
    if(ins.address==EXC_STOP){
      require(ins.opcode==0x44000002u,"exception vector-copy boundary missing");
      reached_stop=true;
    }
    if(ins.address==EXC_DEBUG_STOP){
      require(ins.opcode==0x44000002u,"exception unimplemented DBPrintf not guarded");
      reached_debug_stop=true;
    }
  }
  require(reached_stop&&reached_debug_stop,
          "original exception fast/debug branches lack explicit syscall stops");
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
 std::cout<<"PASS: V35 recovered continuous exception prologue native dispatcher, mode="<<mode
          <<" functions="<<funcs.size()<<" original_OSInit_prefix="<<owner<<"\n";
 return 0;
}catch(const std::exception& e){std::cerr<<"V25 generator: "<<e.what()<<"\n";return 1;}
