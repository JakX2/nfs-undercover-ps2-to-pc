// Original-free V23 emitter: genuine start -> __init_data, preserving V21 IC/DC functions. The owner's original PPC stays in
// temporary DOL file and private generated output.cpp, never Git/public ZIP.
#include "loader/loader.h"
#include "analyzer/analyzer.h"
#include "recompiler/recompiler.h"
#include <array>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>
#include <unordered_set>

namespace {
constexpr uint32_t ENTRY=0x8000403cu, REGS=0x800041a8u, HW=0x800042e0u;
constexpr uint32_t INIT=0x80004238u, FLUSH=0x80004304u, COPY=0x80004338u,
                   FILL=0x80004388u, SET=0x8000443cu, TABLE=0x80006420u,
                   POST_INIT=0x80004058u;
constexpr uint32_t PS=0x80520fb4u, FPR=0x8051fbb0u, CACHE=0x80522540u;
constexpr uint32_t HIDR=0x804b79dcu,HIDW=0x804b79e4u,IC=0x805223acu;
constexpr uint32_t HID0R=0x804b7920u,MSRR=0x804b7910u,MSRW=0x804b7918u;
constexpr uint32_t L2R=0x804b7930u,L2W=0x804b7938u;
constexpr uint32_t DCE=0x80522280u,ICE=0x805223bcu,DBG=0x804e50b8u,ERR=0x805230b8u;
constexpr std::array<uint32_t,18> functions{ENTRY,REGS,HW,PS,FPR,CACHE,HIDR,HIDW,IC,HID0R,MSRR,MSRW,L2R,L2W,DCE,ICE,DBG,ERR};
void ck(bool v,const std::string& msg);
// Defense-in-depth for upstream DOL loader versions without the V12 bounds
// patch. Reject truncated, aliased, oversized and out-of-memory sections
// BEFORE invoking Executable::load_dol or NWiiRecomp code generation.
void verify_file_ranges(const std::filesystem::path& path){
  std::ifstream in(path,std::ios::binary|std::ios::ate);
  ck(bool(in),"failed opening private DOL");
  const auto bytes=in.tellg();
  ck(bytes>=0x100 && bytes<=128*1024*1024,"private DOL size not supported");
  in.seekg(0);
  std::array<unsigned char,0x100> header{};
  ck(bool(in.read(reinterpret_cast<char*>(header.data()),header.size())),"short DOL header");
  auto be32=[&](unsigned pos)->uint32_t {
    return (uint32_t(header[pos])<<24)|(uint32_t(header[pos+1])<<16)|
           (uint32_t(header[pos+2])<<8)|uint32_t(header[pos+3]);
  };
  unsigned count=0;
  std::vector<std::pair<uint64_t,uint64_t>> ranges;
  for(unsigned data=0;data<2;++data){
    const unsigned n=data?11:7;
    for(unsigned i=0;i<n;++i){
      const uint32_t off=be32((data?0x1c:0)+4*i),
          guest=be32((data?0x64:0x48)+4*i),
          len=be32((data?0xac:0x90)+4*i);
      if(off==0 && len==0)continue;
      ck(off>=0x100 && len!=0 && ((off|guest)&3u)==0,
         "DOL section missing offset, length or alignment");
      ck(uint64_t(off)+len<=static_cast<uint64_t>(bytes),"DOL section exceeds file");
      const uint64_t finish=uint64_t(guest)+len;
      ck((guest>=0x80000000u&&finish<=0x81800000ull)||
         (guest>=0x90000000u&&finish<=0x94000000ull),
         "DOL section exceeds guest RAM");
      for(const auto& [old_begin,old_end]:ranges)
        ck(uint64_t(off)>=old_end || uint64_t(off)+len<=old_begin,
           "overlapping DOL file regions");
      ranges.emplace_back(off,uint64_t(off)+len);
      ++count;
    }
  }
  ck(count==8,"V23 image needs seven text and one data region");
}
void ck(bool v,const std::string& msg){if(!v)throw std::runtime_error(msg);}
uint32_t bl_target(const nwii::analyzer::Instruction& ins){
  const uint32_t w=ins.opcode;
  ck((w>>26)==18 && (w&3)==1,"expected PPC BL");
  uint32_t x=w&0x03fffffcu;
  if(x&0x02000000u)x|=0xfc000000u;
  return ins.address+x;
}
uint32_t spr(uint32_t w){return (((w>>11)&31u)<<5)|((w>>16)&31u);}
}
int main(int argc,char**argv)try{
  ck(argc==4,"usage: generate_start_to_data_v23 PRIVATE_DOL EMPTY_DIR owner|synthetic");
  const std::string mode=argv[3];
  ck(mode=="owner"||mode=="synthetic","unknown test mode");
  const bool owner=mode=="owner";
  const std::filesystem::path out=argv[2];
  ck(std::filesystem::is_directory(out)&&std::filesystem::is_empty(out),"private output directory must exist and be empty");
  verify_file_ranges(argv[1]);
  nwii::loader::Executable dol;
  ck(dol.load_dol(argv[1]),"invalid DOL");
  ck(dol.entry_point==ENTRY&&dol.sections.size()==8,"wrong DOL entry or section count");
  bool table_found=false;
  for(const auto& sec:dol.sections)if(!sec.is_text&&!sec.is_bss&&sec.address==TABLE&&sec.data.size()==0xb0u)
    table_found=true;
  ck(table_found,"missing owner/synthetic initialization table");
  nwii::analyzer::Analyzer a(dol);
  a.analyze({FPR,CACHE});
  const auto& fs=a.get_functions();
  ck(fs.size()==functions.size()+(owner?5u:1u),"unexpected native function count " +std::to_string(fs.size()));
  for(auto pc:functions)ck(fs.count(pc)==1,"missing selected function at "+std::to_string(pc));
  const auto& start=fs.at(ENTRY).instructions;
  ck(start.size()==9&&bl_target(start.at(0))==REGS&&bl_target(start.at(1))==HW&&
     bl_target(start.at(6))==INIT&&start.at(7).opcode==0x44000002u &&
     start.at(8).opcode==0x4e800020u,"unexpected start->data third-call boundary");
  ck(fs.count(INIT)==1,"missing __init_data from full native dispatcher");
  // Verify the original-free structural ABI: the startup prologue stores two
  // 0xFFFFFFFF words after stwu r1,-8 before the third direct BL.
  // These are generic PPC instruction forms, not game-derived C++ bodies.
  const auto& prefix=start;
  ck(prefix[2].opcode==0x3800ffffu && prefix[3].opcode==0x9421fff8u &&
     prefix[4].opcode==0x90010004u && prefix[5].opcode==0x90010000u,
     "startup linkage stack prologue is not the expected PPC ABI");
  if(owner){
    const auto& f=fs.at(INIT).instructions;
    ck(f.size()==42 && f.back().opcode==0x4e800020u,"original data initializer not complete");
    for(auto [pc, size] : std::array<std::array<uint32_t,2>,4>{
      std::array<uint32_t,2>{FLUSH,13},std::array<uint32_t,2>{COPY,20},
      std::array<uint32_t,2>{FILL,45},std::array<uint32_t,2>{SET,12}}){
      ck(fs.count(pc)==1 && fs.at(pc).instructions.size()==size,"missing original data helper");
    }
    const std::array<std::array<uint32_t,2>,4> expected_edges{{
      {0x80004280u,COPY},{0x8000428cu,FLUSH},{0x800042b8u,SET},{0x80004450u,FILL}}};
    for(auto [pc,target]:expected_edges){
      const auto& f2=fs.at(pc>=SET?SET:INIT).instructions;
      bool found=false;
      for(const auto& ins:f2)if(ins.address==pc){ck(bl_target(ins)==target,"data helper BL target wrong");found=true;}
      ck(found,"missing original data helper BL");
    }
  } else {
    const auto& init=fs.at(INIT).instructions;
    ck(init.size()==4 && init[0].opcode==0x3d008003u &&
       init[1].opcode==0x38000000u && init[2].opcode==0x90086000u &&
       init[3].opcode==0x4e800020u,
       "synthetic guest init must zero exactly one test memory word and return");
  }
  const auto& hw=fs.at(HW).instructions;
  ck(hw.size()==9&&bl_target(hw.at(4))==PS&&bl_target(hw.at(5))==FPR&&
     bl_target(hw.at(6))==CACHE,"hardware calls not genuine");
  const auto& cache=fs.at(CACHE).instructions;
  ck(cache.size()==(owner?78u:21u),"unexpected cache body size");
  ck(cache.back().opcode==0x4e800020u,"cache initializer must return through blr");
  const auto& lr=fs.at(L2R).instructions;
  const auto& lw=fs.at(L2W).instructions;
  ck(lr.size()==2&&lw.size()==2,"L2CR wrappers incomplete");
  ck((lr[0].opcode>>26)==31 && ((lr[0].opcode>>1)&1023)==339 &&
    spr(lr[0].opcode)==1017,"L2 read wrapper wrong SPR1017");
  ck((lw[0].opcode>>26)==31 && ((lw[0].opcode>>1)&1023)==467 &&
    spr(lw[0].opcode)==1017,"L2 write wrapper wrong SPR1017");
  for (auto [addr,xo,n] : std::array<std::array<uint32_t,3>,3>{
         std::array<uint32_t,3>{HID0R,339,1008},
         std::array<uint32_t,3>{L2R,339,1017},
         std::array<uint32_t,3>{L2W,467,1017}}){
    const auto& instructions=fs.at(addr).instructions;
    ck(instructions.size()==2 && instructions.back().opcode==0x4e800020u,
       "hardware SPR wrapper must be a complete leaf");
    const uint32_t w=instructions[0].opcode;
    ck(w>>26==31 && ((w>>1)&1023u)==xo && spr(w)==n && ((w>>21)&31u)==3u,
       "hardware SPR wrapper opcode/register changed");
  }
  for (auto [addr,xo] : std::array<std::array<uint32_t,2>,2>{
         std::array<uint32_t,2>{MSRR,83},std::array<uint32_t,2>{MSRW,146}}){
    const auto& instructions=fs.at(addr).instructions;
    ck(instructions.size()==2 && instructions.back().opcode==0x4e800020u,
       "MSR wrapper must be a complete leaf");
    const uint32_t w=instructions[0].opcode;
    ck(w>>26==31 && ((w>>1)&1023u)==xo && ((w>>21)&31u)==3u,
       "MSR helper opcode/register changed");
  }
  for(auto pc:{DBG,ERR}){
    const auto& stub=fs.at(pc).instructions;
    ck(stub.size()==2&&stub[0].opcode==0x44000002u &&stub[1].opcode==0x4e800020u,
       "OS adapter must remain synthetic sc/blr fixture");
  }
  // Two original Wii cache-enable bodies, no synthetic syscall endpoint.
  for (const auto& [pc, barrier, mask] : std::array<std::array<uint32_t,3>,2>{
         std::array<uint32_t,3>{DCE,0x7c0004acu,0x4000u},
         std::array<uint32_t,3>{ICE,0x4c00012cu,0x8000u}}) {
    const auto& ins=fs.at(pc).instructions;
    ck(ins.size()==5,"IC/DC enable must have exactly five PPC instructions");
    ck(ins[0].opcode==barrier&&ins[4].opcode==0x4e800020u,
       "IC/DC enable missing sync/isync or blr");
    const uint32_t rd=ins[1].opcode,op=ins[2].opcode,wr=ins[3].opcode;
    ck((rd>>26)==31 && ((rd>>1)&1023u)==339u && spr(rd)==1008u,
       "IC/DC enable HID0 read missing");
    ck((wr>>26)==31 && ((wr>>1)&1023u)==467u && spr(wr)==1008u,
       "IC/DC enable HID0 write missing");
    const uint32_t r=(rd>>21)&31u;
    ck(((wr>>21)&31u)==r && (op>>26)==24u && ((op>>21)&31u)==r &&
       ((op>>16)&31u)==r && (op&0xffffu)==mask,
       "IC/DC enable must OR the correct HID0 bit using the same register");
  }
  if(owner){
    unsigned bls=0,bc=0,syncs=0;
    for(const auto& ins:cache){
      const uint32_t w=ins.opcode;
      if((w>>26)==18&&(w&1u))++bls;
      if((w>>26)==16)++bc;
      if((w>>26)==31&&((w>>1)&1023)==598)++syncs;
    }
    ck(bls==26&&bc==5&&syncs==6,"original cache call/branch/sync census changed");
  }
  nwii::recomp::RecompilerConfig cfg;
  cfg.output_dir=out.string();cfg.split_output=false;
  nwii::recomp::Recompiler recomp(a,nullptr,cfg);
  const auto outputs=recomp.generate_cpp(ENTRY);
  ck(outputs.size()==1&&outputs.at(0)=="output.cpp","wrong dispatcher output");
  std::cout<<"PASS: emitted V23 native start->data dispatcher for "<<fs.size()<<" functions, mode="<<mode<<"\n";
}catch(const std::exception& e){
  std::cerr<<"V21 generator failed: "<<e.what()<<'\n';return 1;
}
