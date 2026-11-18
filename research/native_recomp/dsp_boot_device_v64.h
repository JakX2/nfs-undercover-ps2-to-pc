#pragma once
// Bounded DSP bootstrap test device. The mailbox completion is synthetic;
// no claim of DSP ISA execution. ARAM DMA copies real guest data.
#include <array>
#include <cstdint>
#include <stdexcept>
struct DspBootDevice {
    static constexpr uint32_t CONTROL=0x0c00500a,INFO=0x0c005012,
        CPU_MAIL=0x0c005000,MAIL_H=0x0c005004,MAIL_L=0x0c005006,
        DMA_SOURCE=0x0c005020,DMA_DEST=0x0c005024,DMA_COUNT=0x0c005028;
    enum class Phase {idle,info,reset_config,reset_prepare,reset_trigger,reset_poll,
        cpu_mail,drain_high,drain_low,dma_source,dma_dest,dma_count,dma_poll,dma_ack,
        init_read,init_write,init_poll,halt_read,halt_clear,mail_wait,mail_low,
        halt_restore_read,halt_restore,done};
    Phase phase=Phase::idle;
    unsigned resets=0,transfers=0,acks=0;
    unsigned reset_busy=0,reset2_busy=0,dma_busy=0,dma2_busy=0,init_busy=0,mail_busy=0;
    bool initial_mail=false,last_mail_pending=false;
    uint32_t source=0,dest=0;
    static void need(bool c,const char*msg){if(!c)throw std::runtime_error(msg);}
    void reset(unsigned trial){
        *this=DspBootDevice{};
        reset_busy=trial%4u;reset2_busy=(trial/4u)%4u;
        dma_busy=(trial/4u)%4u;dma2_busy=trial%4u;
        init_busy=trial%4u;mail_busy=(trial/4u)%4u;
        initial_mail=(trial&1u)!=0;
    }
    void begin(){need(phase==Phase::idle,"DSP boot already active");phase=Phase::info;}
    bool active()const{return phase!=Phase::idle;}
    bool complete()const{return phase==Phase::done&&resets==2&&transfers==2&&acks==2;}
    void write16(uint32_t reg,uint16_t value){
        switch(phase){
        case Phase::info:need(reg==INFO&&value==0x43,"DSP ARAM info setup differs");phase=Phase::reset_config;return;
        case Phase::reset_config:
            need(reg==CONTROL&&value==0x8ac,"DSP reset mode/status clear differs");phase=Phase::reset_prepare;return;
        case Phase::reset_trigger:
            need(reg==CONTROL&&value==0x805,"DSP reset start differs");++resets;phase=Phase::reset_poll;return;
        case Phase::cpu_mail:
            need(reg==CPU_MAIL&&value==0,"DSP CPU mailbox clear differs");phase=Phase::drain_high;return;
        case Phase::dma_ack:
            need(reg==CONTROL&&value==0x824,"DSP ARAM DMA W1C completion differs");++acks;
            phase=acks==1?Phase::dma_source:Phase::init_read;return;
        case Phase::init_write:
            need(reg==CONTROL&&value==4,"DSP reset boot/init mode clear differs");phase=Phase::init_poll;return;
        case Phase::halt_clear:
            need(reg==CONTROL&&value==0,"DSP halt clear differs");phase=Phase::mail_wait;return;
        case Phase::halt_restore:
            need(reg==CONTROL&&value==4,"DSP halt restore differs");phase=Phase::reset_config;return;
        default:throw std::runtime_error("unexpected DSP boot write16");
        }
    }
    void write32(uint32_t reg,uint32_t value){
        switch(phase){
        case Phase::dma_source:need(reg==DMA_SOURCE&&value==0x01000000u,"DSP ARAM DMA source invalid");
            source=value;phase=Phase::dma_dest;return;
        case Phase::dma_dest:need(reg==DMA_DEST&&value==0u,"DSP ARAM DMA destination invalid");
            dest=value;phase=Phase::dma_count;return;
        case Phase::dma_count:need(reg==DMA_COUNT&&value==32u,"DSP ARAM DMA count/direction invalid");
            phase=Phase::dma_poll;return;
        default:throw std::runtime_error("unexpected DSP boot write32");
        }
    }
    template<class Copy> uint16_t read16(uint32_t reg,Copy copy){
        switch(phase){
        case Phase::reset_prepare:need(reg==CONTROL,"DSP reset control read differs");
            phase=Phase::reset_trigger;return 0x804;
        case Phase::reset_poll:{
            need(reg==CONTROL,"DSP reset poll differs");auto& busy=resets==1?reset_busy:reset2_busy;
            if(busy){--busy;return 0x805;}
            phase=resets==1?Phase::cpu_mail:Phase::done;return 0x804;}
        case Phase::drain_high:need(reg==MAIL_H,"DSP initial mailbox high read differs");
            last_mail_pending=initial_mail;phase=Phase::drain_low;return initial_mail?0x8000:0;
        case Phase::drain_low:need(reg==MAIL_L,"DSP initial mailbox low read differs");
            initial_mail=false;phase=last_mail_pending?Phase::drain_high:Phase::dma_source;return 0;
        case Phase::dma_poll:{
            need(reg==CONTROL,"DSP ARAM DMA poll differs");auto& busy=transfers==0?dma_busy:dma2_busy;
            if(busy){--busy;return 0xa04;}
            copy(source,dest,32u);++transfers;phase=Phase::dma_ack;return 0x824;}
        case Phase::init_read:need(reg==CONTROL,"DSP init mode read differs");
            phase=Phase::init_write;return 0x804;
        case Phase::init_poll:need(reg==CONTROL,"DSP init poll differs");
            if(init_busy){--init_busy;return 0x404;}
            phase=Phase::halt_read;return 4;
        case Phase::halt_read:need(reg==CONTROL,"DSP halt status read differs");
            phase=Phase::halt_clear;return 4;
        case Phase::mail_wait:need(reg==MAIL_H,"DSP boot completion mailbox poll differs");
            if(mail_busy){--mail_busy;return 0;}
            phase=Phase::mail_low;return 0x8123;
        case Phase::mail_low:need(reg==MAIL_L,"DSP boot completion mailbox low read differs");
            phase=Phase::halt_restore_read;return 0x4567;
        case Phase::halt_restore_read:need(reg==CONTROL,"DSP halt restore status read differs");
            phase=Phase::halt_restore;return 0;
        default:throw std::runtime_error("unexpected DSP boot read16");
        }
    }
};
