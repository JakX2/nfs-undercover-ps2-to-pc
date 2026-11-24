#pragma once
#include "wii_irq_banks_v480.h"
#include <optional>
#include <limits>
#include <span>
#include <vector>
#include "wii_ios_memory.h"
namespace undercover::wii {
// Native EXI register/controller state, independent of any device protocol.
// https://wiibrew.org/wiki/Hardware/External_Interface
// No endpoint is attached by default. A transfer never invents a reply or
// marks itself complete merely because a guest polls CR.
class ExiController {
public:
    struct Request{uint64_t token;unsigned channel,device,length,direction;uint32_t tx;bool dma=false;uint32_t physical=0;};
    explicit ExiController(WiiIrqBanks& banks,IosMemory* ram=nullptr):banks_(banks),ram_(ram){}
    ExiController(const ExiController&)=delete;
    ExiController& operator=(const ExiController&)=delete;
    bool bound_to(const WiiIrqBanks& banks)const noexcept{return &banks==&banks_;}
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
                const bool changed=((banks_.exi_csr(ch)^value)&0x380u)!=0;
                if(changed&&s.selection_epoch==std::numeric_limits<uint64_t>::max())throw std::runtime_error("EXI select epoch overflow");
                banks_.write_exi_csr(ch,value&~rom);
                if(changed)++s.selection_epoch;
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
    uint64_t selection_epoch(unsigned ch)const{return channel(ch).selection_epoch;}
    void complete_immediate(unsigned ch,uint64_t token,uint32_t response){
        auto& s=channel(ch);
        if(!s.pending||s.pending->token!=token||s.pending->dma)throw std::runtime_error("EXI immediate completion token");
        const auto req=*s.pending;
        // Immediate data is left aligned; bytes not clocked are preserved.
        if(req.direction!=1){
            const unsigned unused=(4u-req.length)*8u;
            const uint32_t mask=0xffffffffu<<unused;
            s.data=(s.data&~mask)|(response&mask);
        }
        finish(ch,s);
    }
    // DMA requests are serviced explicitly, just like immediate transfers.
    // Validate the complete RAM span before any endpoint or memory mutation.
    std::vector<uint8_t> dma_tx(unsigned ch,uint64_t token)const{
        const auto& req=dma_request(ch,token);
        if(req.direction!=1)throw std::runtime_error("EXI DMA write direction");
        std::vector<uint8_t> data(req.length);
        for(unsigned i=0;i<req.length;++i)data[i]=ram_->read8(req.physical+i);
        return data;
    }
    void complete_dma(unsigned ch,uint64_t token,std::span<const uint8_t> response){
        const auto req=dma_request(ch,token);
        if(response.size()!=(req.direction==0?req.length:0u))
            throw std::runtime_error("EXI DMA response size");
        for(unsigned i=0;i<response.size();++i)ram_->write8(req.physical+i,response[i]);
        finish(ch,channel(ch));
    }
private:
    struct Channel{
        uint32_t mar=0,length=0,control=0,data=0;
        uint64_t selection_epoch=0;
        std::array<bool,3> attached{};
        std::optional<Request> pending;
    };
    WiiIrqBanks& banks_;IosMemory* ram_;std::array<Channel,3> channels_{};
    uint32_t romdis_=0;uint64_t sequence_=0;
    Channel& channel(unsigned ch){if(ch>=3)throw std::out_of_range("EXI channel");return channels_[ch];}
    const Channel& channel(unsigned ch)const{if(ch>=3)throw std::out_of_range("EXI channel");return channels_[ch];}
    void finish(unsigned ch,Channel& s){
        s.control&=~1u;s.pending.reset();banks_.raise_exi(ch,WiiIrqBanks::TC_INT);
    }
    const Request& dma_request(unsigned ch,uint64_t token)const{
        const auto& s=channel(ch);
        if(!ram_||!s.pending||s.pending->token!=token||!s.pending->dma||
           !ram_->valid(s.pending->physical,s.pending->length))
            throw std::runtime_error("EXI DMA completion token/range");
        return *s.pending;
    }
    void control(unsigned ch,Channel& s,uint32_t value){
        if(value&~0x3fu)throw std::runtime_error("EXI reserved control");
        const unsigned direction=(value>>2)&3u;
        if(direction==3)throw std::runtime_error("EXI direction");
        if(!(value&1u)){s.control=value;return;}
        const bool dma=(value&2u)!=0;
        // Original guest code may pass a cached or uncached RAM address to
        // MAR. Translate only the normal Broadway RAM aliases; no MMIO or
        // wraparound. Keep the programmed MAR itself for register readback.
        const uint32_t physical=s.mar&0x3fffffffu;
        if(dma&&(!ram_||direction>1u||!s.length||s.length>16u*1024u*1024u||
                (s.mar&0xc0000000u)==0x40000000u||!ram_->valid(physical,s.length)))
            throw std::runtime_error("EXI DMA backend/range");
        const unsigned cs=(banks_.exi_csr(ch)>>7)&7u;
        if(cs!=1&&cs!=2&&cs!=4)throw std::runtime_error("EXI selection");
        const unsigned dev=cs==1?0u:cs==2?1u:2u;
        if(!s.attached[dev]||sequence_==std::numeric_limits<uint64_t>::max())
            throw std::runtime_error("EXI endpoint unavailable");
        const unsigned length=dma?s.length:((value>>4)&3u)+1u;
        s.pending=Request{++sequence_,ch,dev,length,direction,s.data,dma,dma?physical:0u};
        s.control=value;
    }
};
}
