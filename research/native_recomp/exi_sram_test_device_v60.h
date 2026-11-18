#pragma once
// Independently authored, bounded test device for a 64-byte SRAM DMA read.
// Not a complete EXI controller or a persistent SRAM implementation.
#include <cstdint>
#include <array>
#include <stdexcept>
struct ExiSramTestDevice {
  static constexpr uint32_t CSR=0x0d006800u,MAR=CSR+4,LEN=CSR+8,CR=CSR+12,DATA=CSR+16,REV=0x0d006024u;
  enum Phase { idle, ready, selecting, selected, command, writing, written, command_synced,
               addressed, sized, reading, received, synced, deselecting, done };
  Phase phase=idle;
  uint32_t address=0,expected_address=0;
  unsigned write_busy=0,dma_busy=0,polls=0;
  std::array<uint8_t,64> bytes{};
  static void need(bool c,const char*msg){if(!c)throw std::runtime_error(msg);}
  void reset(uint32_t dest,unsigned trial){
    *this=ExiSramTestDevice{};
    expected_address=dest;write_busy=trial%4u;dma_busy=(trial/4u)%4u;
    for(unsigned i=0;i<bytes.size();++i)bytes[i]=uint8_t(17u*i+trial*13u+7u);
    // A non-reserved GBS configuration exercises the no-write path.
    bytes[60]=0x12u;bytes[61]=uint8_t(trial&0x3fu);
  }
  void begin(){need(phase==idle,"SRAM device already active");phase=ready;}
  bool active()const{return phase!=idle;}
  bool complete()const{return phase==done;}
  template<class Copy> uint32_t read(uint32_t reg,Copy copy){
    if(reg==CSR&&phase==ready){phase=selecting;return 0;}
    if(reg==CSR&&phase==synced){phase=deselecting;return 0x130;}
    if(reg==REV&&phase==written){phase=command_synced;return 1;}
    if(reg==REV&&phase==received){phase=synced;return 1;}
    if(reg==CR&&phase==writing){
      need(++polls<=8,"unbounded SRAM command busy");if(write_busy){--write_busy;return 0x35;}
      phase=written;return 0x34;
    }
    if(reg==CR&&phase==reading){
      need(++polls<=8,"unbounded SRAM DMA busy");if(dma_busy){--dma_busy;return 3;}
      copy(address,bytes);phase=received;return 2;
    }
    throw std::runtime_error("unexpected SRAM device read");
  }
  void write(uint32_t reg,uint32_t value){
    if(phase==selecting&&reg==CSR&&value==0x130){phase=selected;return;}
    if(phase==selected&&reg==DATA&&value==0x20000100u){phase=command;return;}
    if(phase==command&&reg==CR&&value==0x35){phase=writing;return;}
    if(phase==command_synced&&reg==MAR&&value==expected_address&&!(value&31u)){
      address=value;phase=addressed;return;}
    if(phase==addressed&&reg==LEN&&value==64){phase=sized;return;}
    if(phase==sized&&reg==CR&&value==3){phase=reading;return;}
    if(phase==deselecting&&reg==CSR&&value==0){phase=done;return;}
    throw std::runtime_error("unexpected SRAM device write");
  }
};
