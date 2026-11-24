#pragma once
#include "wii_physical_ram.h"
#include <array>
#include <atomic>
#include <limits>
#include <stdexcept>
namespace undercover::wii {
// Wii ARAM DMA subset: MEM1 <-> MEM2, 32-byte bursts, explicit tick profile.
// References: WiiBrew Hardware/DSP and Memory map; PI interrupt bit 6.
// No address mirroring, DSP ISA, reset/mailbox protocol or audio playback.
// Reject unimplemented modes rather than allowing silent legacy fallback.
class AramDma {
public:
    static constexpr uint16_t ArInt=0x20u,ArMask=0x40u,Busy=0x200u;
    static constexpr uint32_t PiDsp=1u<<6,Reverse=0x80000000u,
        MaxTransfer=65536u;
    AramDma(WiiPhysicalRam& ram,std::atomic<uint32_t>& pi,uint64_t ticks_per_block)
        :ram_(ram),pi_(pi),latency_(ticks_per_block){
        if(!latency_)throw std::invalid_argument("ARAM tick profile");
        refresh();
    }
    ~AramDma(){pi_.fetch_and(~PiDsp,std::memory_order_relaxed);}
    AramDma(const AramDma&)=delete;
    AramDma& operator=(const AramDma&)=delete;
    uint16_t info()const noexcept{return info_;}
    uint32_t main_address()const noexcept{return main_;}
    uint32_t aram_address()const noexcept{return aram_;}
    uint32_t count()const noexcept{return count_|direction_;}
    uint16_t control_bits()const noexcept{return (pending_?Busy:0u)|(irq_?ArInt:0u)|mask_;}
    uint64_t completed()const noexcept{return completed_;}
    void set_info(uint16_t v){
        idle();
        // Only observed Wii bootstrap's mode 3, with explicit control bits.
        if(v!=0x43u)throw std::runtime_error("unsupported ARAM info mode");
        info_=v;
    }
    void set_main_address(uint32_t v){
        idle();if(v&31u||v>=WiiPhysicalRam::MEM1_SIZE)throw std::out_of_range("ARAM MEM1 address");
        main_=v;
    }
    void set_aram_address(uint32_t v){
        idle();if(v&31u||v>=WiiPhysicalRam::MEM2_SIZE)throw std::out_of_range("ARAM MEM2 offset");
        aram_=v;
    }
    void start(uint32_t v){
        idle();const auto n=v&~Reverse;
        if(info_!=0x43u||!n||(n&31u)||n>MaxTransfer||
           !ram_.valid(main_,n)||!ram_.valid(WiiPhysicalRam::MEM2_BASE+aram_,n)||
           uint64_t(main_)+n>WiiPhysicalRam::MEM1_SIZE||
           uint64_t(aram_)+n>WiiPhysicalRam::MEM2_SIZE)
            throw std::runtime_error("unsupported ARAM DMA geometry");
        // No mutation on an unrepresentable deadline.
        if(uint64_t(n/32)>std::numeric_limits<uint64_t>::max()/latency_||
           last_>std::numeric_limits<uint64_t>::max()-uint64_t(n/32)*latency_)
            throw std::overflow_error("ARAM deadline");
        count_=n;direction_=v&Reverse;pending_=true;armed_=false;
    }
    // Update only ARAM's W1C/mask subfields. A future DSP register owner
    // must merge other DSP status/mask sources separately.
    void write_irq_control(uint16_t v){
        if(v&~(ArInt|ArMask))throw std::runtime_error("unsupported ARAM control");
        mask_=v&ArMask;if(v&ArInt)irq_=false;refresh();
    }
    void refresh()noexcept{
        const uint32_t desired=irq_&&mask_?PiDsp:0u;
        auto cur=pi_.load(std::memory_order_relaxed);
        while(!pi_.compare_exchange_weak(cur,(cur&~PiDsp)|desired,std::memory_order_relaxed,std::memory_order_relaxed)){}
    }
    // Explicit CPU-thread boundary. The first post-command visit arms the
    // deadline. Each elapsed block is copied exactly once. Polls are inert.
    void advance(uint64_t tick){
        if(tick<last_)throw std::logic_error("ARAM time reversal");
        if(!pending_){last_=tick;return;}
        if(!armed_){
            const uint64_t duration=uint64_t(count_/32)*latency_;
            if(tick>std::numeric_limits<uint64_t>::max()-duration)throw std::overflow_error("ARAM deadline");
            due_=tick+latency_;armed_=true;last_=tick;return;
        }
        last_=tick;
        while(pending_&&tick>=due_){
            const uint32_t ext=WiiPhysicalRam::MEM2_BASE+aram_;
            const uint32_t src=direction_?ext:main_,dst=direction_?main_:ext;
            std::array<uint8_t,32> bytes{};
            for(unsigned i=0;i<32;++i)bytes[i]=ram_.read8(src+i);
            for(unsigned i=0;i<32;++i)ram_.write8(dst+i,bytes[i]);
            main_+=32;aram_+=32;count_-=32;
            if(count_)due_+=latency_;
            else {pending_=false;armed_=false;++completed_;irq_=true;refresh();}
        }
    }
private:
    WiiPhysicalRam& ram_;std::atomic<uint32_t>& pi_;const uint64_t latency_;
    uint16_t info_=0,mask_=0;uint32_t main_=0,aram_=0,count_=0,direction_=0;
    uint64_t last_=0,due_=0,completed_=0;bool pending_=false,armed_=false,irq_=false;
    void idle()const{if(pending_)throw std::logic_error("ARAM DMA busy");}
};
}
