// Independent synthetic PPC switch, not an extracted game function.
#include "analyzer/analyzer.h"
#include <algorithm>
#include <cstdint>
#include <iostream>
#include <stdexcept>
#include <vector>

static void need(bool condition,const char*why){
  if(!condition) throw std::runtime_error(why);
}
static std::vector<uint8_t> be(std::initializer_list<uint32_t> words){
  std::vector<uint8_t> data;
  for(auto w:words)for(unsigned shift:{24u,16u,8u,0u})
    data.push_back(uint8_t(w>>shift));
  return data;
}
int main(){
  constexpr uint32_t entry=0x80010000u,table=0x80020000u;
  nwii::loader::Executable exe;
  exe.entry_point=entry;
  // lis/addi establish table; index is an input byte offset.
  // lwzx r6,r5,r3; mtctr r6; bctr. Two distinct local return blocks.
  auto text=be({(15u<<26)|(5u<<21)|(table>>16),
                (14u<<26)|(5u<<21)|(5u<<16)|(table&0xffffu),
                (31u<<26)|(6u<<21)|(5u<<16)|(3u<<11)|(23u<<1),
                (31u<<26)|(6u<<21)|((9u<<5)<<11)|(467u<<1),
                (19u<<26)|(20u<<21)|(528u<<1),
                (14u<<26)|(3u<<21)|11u,0x4e800020u,
                (14u<<26)|(3u<<21)|22u,0x4e800020u});
  const auto first=entry+20u,second=entry+28u;
  auto data=be({first,second,first,0u});
  exe.sections.push_back({entry,uint32_t(text.size()),text,true,false});
  exe.sections.push_back({table,uint32_t(data.size()),data,false,false});
  nwii::analyzer::Analyzer a(exe);
  a.analyze();
  const auto& functions=a.get_functions();
  need(functions.count(entry)&&functions.count(first)&&functions.count(second),
       "data pointer roots not discovered");
  const auto& parent=functions.at(entry);
  need(parent.jump_table_targets==std::set<uint32_t>{first,second},
       "computed switch destinations lost when also seeded as roots");
  for(uint32_t pc:{first,first+4u,second,second+4u})
    need(std::any_of(parent.instructions.begin(),parent.instructions.end(),
       [pc](const auto& inst){return inst.address==pc;}),"local switch code missing");
  std::cout<<"PASS: synthetic PPC jump table retains data-seeded target blocks\n";
}
