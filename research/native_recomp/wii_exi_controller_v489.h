#pragma once
#include "wii_irq_banks_v480.h"
#include <optional>
#include <limits>
namespace undercover::wii {
// Native EXI register/controller state, independent of any device protocol.
// https://wiibrew.org/wiki/Hardware/External_Interface
// No endpoint is attached by default. A transfer never invents a reply or
// marks itself complete merely because a guest polls CR.
class ExiController {
public:
    struct Request{uint64_t token;unsigned channel,device,length,direction;uint32_t tx;};
    explicit ExiController(WiiIrqBanks& banks):banks_(banks){}
    ExiController(const ExiController&)=delete;
    ExiController& operator=(const ExiController&)=delete;
    void attach(unsigned ch,unsigned dev,bool connected){
        auto& s=channel(ch);if(dev>=3||s.pending)throw std::invalid_argument("EXI endpoint change");
        s.attached[dev]=connected;
    }
    uint32_t read(unsigned ch,unsigned offset)const{
        const auto& s=channel(ch);
        switch(offset){
            case 0:return banks_.exi_csr(ch)|(ch==0?romdis_:0u);
            case 4:return s.mar;
            case 8:return s.length;
            case 12:return s.control;
            case 16:return s.data;
            default:throw std::out_of_range("EXI register");
        }
    }
    void write(unsigned ch,unsigned offset,uint32_t value){
        auto& s=channel(ch);
        if(s.pending)throw std::runtime_error("EXI transfer in progress");
        switch(offset){
            case 0:{
                // Latch the observed ROMDIS bit without claiming Wii ROM
                // remapping semantics. Other channels do not own the bit.
                const uint32_t rom=ch==0?value&0x2000u:0;
                banks_.write_exi_csr(ch,value&~rom);
                if(ch==0)romdis_=rom;
                break;
            }
            case 4:s.mar=value&~31u;break;
            case 8:s.length=value&~31u;break;
            case 12:control(ch,s,value);break;
            case 16:s.data=value;break;
            default:throw std::out_of_range("EXI register");
        }
    }
    std::optional<Request> pending(unsigned ch)const{return channel(ch).pending;}
    void complete_immediate(unsigned ch,uint64_t token,uint32_t response){
        auto& s=channel(ch);
        if(!s.pending||s.pending->token!=token)throw std::runtime_error("EXI completion token");
        const auto req=*s.pending;
        // Immediate data is left aligned; bytes not clocked are preserved.
        if(req.direction!=1){
            const unsigned unused=(4u-req.length)*8u;
            const uint32_t mask=0xffffffffu<<unused;
            s.data=(s.data&~mask)|(response&mask);
        }
        s.control&=~1u;s.pending.reset();
        banks_.raise_exi(ch,WiiIrqBanks::TC_INT);
    }
private:
    struct Channel{
        uint32_t mar=0,length=0,control=0,data=0;
        std::array<bool,3> attached{};
        std::optional<Request> pending;
    };
    WiiIrqBanks& banks_;std::array<Channel,3> channels_{};
    uint32_t romdis_=0;uint64_t sequence_=0;
    Channel& channel(unsigned ch){if(ch>=3)throw std::out_of_range("EXI channel");return channels_[ch];}
    const Channel& channel(unsigned ch)const{if(ch>=3)throw std::out_of_range("EXI channel");return channels_[ch];}
    void control(unsigned ch,Channel& s,uint32_t value){
        if(value&~0x3fu)throw std::runtime_error("EXI reserved control");
        const unsigned direction=(value>>2)&3u;
        if(direction==3)throw std::runtime_error("EXI direction");
        if(!(value&1u)){s.control=value;return;}
        // DMA requires an explicit RAM/endpoint adapter. It is not emulated
        // by this immediate controller and must not be silently completed.
        if(value&2u)throw std::runtime_error("EXI DMA backend missing");
        const unsigned cs=(banks_.exi_csr(ch)>>7)&7u;
        if(cs!=1&&cs!=2&&cs!=4)throw std::runtime_error("EXI selection");
        const unsigned dev=cs==1?0u:cs==2?1u:2u;
        if(!s.attached[dev]||sequence_==std::numeric_limits<uint64_t>::max())
            throw std::runtime_error("EXI endpoint unavailable");
        const unsigned length=((value>>4)&3u)+1u;
        s.pending=Request{++sequence_,ch,dev,length,direction,s.data};
        s.control=value;
    }
};
}
