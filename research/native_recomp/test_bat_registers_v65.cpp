#include "runtime/cpu_context.h"
#include <cassert>
#include <iostream>
#include <memory>
int main(){
  auto c=std::make_unique<nwii::runtime::CPUContext>();
  for(unsigned i=0;i<32;++i){
    unsigned spr=i<16?528+i:560+i-16;
    assert(c->bat_index(spr)==i);c->write_bat(spr,0xbad00000u+i);
    assert(c->read_bat(spr)==0xbad00000u+i);
    assert(c->bat_write_sprs[i]==spr&&c->bat_write_values[i]==0xbad00000u+i);
  }
  for(unsigned i=0;i<40;++i)c->write_bat(528,i);
  assert(c->bat_write_count==72&&c->read_bat(528)==39&&c->bat_write_values[63]==31);
  std::cout<<"PASS: 32 independent BAT SPR values and bounded ordered-write trace\n";
}
