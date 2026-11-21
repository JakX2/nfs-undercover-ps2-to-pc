#include "wii_stm_ios.h"
#include <cassert>
#include <iostream>
#include <string_view>
using namespace undercover::wii;
using M=IpcMailbox;
using S=StmIos;
constexpr auto P=M::Side::Broadway,A=M::Side::Starlet;
struct Ram final:IosMemory{
    std::array<uint8_t,8192> bytes{};
    bool valid(uint32_t a,uint32_t n)const override{return uint64_t(a)+n<=bytes.size();}
    uint8_t read8(uint32_t a)const override{return bytes.at(a);}
    void write8(uint32_t a,uint8_t v)override{bytes.at(a)=v;}
    void string(uint32_t a,std::string_view s){for(char c:s)write8(a++,uint8_t(c));write8(a,0);}
};
int main(){
    Ram mem;M m;S ios(m,mem);
    constexpr uint32_t req=0x100,event=0x180,path=0x400,buf=0x600;
    constexpr auto enables=M::IY1|M::IY2;
    auto clear=[&](uint32_t bit){m.write(P,M::PPCCTRL,enables|bit);};
    auto submit=[&](uint32_t addr,uint32_t cmd,uint32_t fd,uint32_t a=0,uint32_t b=0,
                    uint32_t c=0,uint32_t d=0,uint32_t e=0){
        for(unsigned i=0;i<8;++i)mem.write32(addr+4*i,std::array<uint32_t,8>{cmd,0xdeadbeef,fd,a,b,c,d,e}[i]);
        m.write(P,M::PPCMSG,addr);m.write(P,M::PPCCTRL,enables|M::X1);
    };
    auto ack=[&](bool deferred=false){
        assert(ios.pump()==(deferred?S::Pump::Deferred:S::Pump::Ack));
        assert(!m.request_pending()&&(m.read(P,M::PPCCTRL)&M::Y2));
        assert(m.broadway_irq_level()&&ios.pump()==S::Pump::Busy);
        clear(M::Y2);assert(!m.broadway_irq_level());
    };
    auto reply=[&](uint32_t addr,uint32_t cmd,int32_t result){
        assert(ios.pump()==S::Pump::Replied);
        assert(m.read(P,M::ARMMSG)==addr&&m.reply_pending()&&m.broadway_irq_level());
        assert(mem.read32(addr)==S::Reply&&mem.read32(addr+4)==uint32_t(result)&&mem.read32(addr+8)==cmd);
        assert(ios.pump()==S::Pump::Busy);clear(M::Y1);assert(!m.broadway_irq_level());
    };
    m.write(P,M::PPCCTRL,enables);m.write(A,M::ARMCTRL,M::IX1);
    mem.string(path,"/dev/stm/immediate");submit(req,S::Open,0,path,0);ack();reply(req,S::Open,0);
    assert(ios.is_open(0,S::Device::Immediate));
    mem.string(path,"/dev/stm/eventhook");submit(req,S::Open,0,path,0);ack();reply(req,S::Open,1);
    assert(ios.is_open(1,S::Device::Event));
    mem.write32(buf,0xaabbccdd);mem.write32(buf+4,0xa1b2c3d4);
    submit(event,S::Ioctl,1,S::EventHook,0,0,buf,32);ack(true);
    assert(ios.event_pending()&&ios.pump()==S::Pump::Idle&&mem.read32(event)==S::Ioctl);
    assert(mem.read32(buf)==0xaabbccdd);
    // Attempt overlapping live request slots without writing the guest
    // message itself; the broker must reject before ACK or dispatch.
    for(uint32_t a:{event-32u,event,event+32u,buf}){
        m.write(P,M::PPCMSG,a);m.write(P,M::PPCCTRL,enables|M::X1);
        assert(ios.pump()==S::Pump::InvalidAddress&&m.request_pending());
        assert(!m.ios_request_queued());
        m.write(P,M::PPCCTRL,enables);
        assert(ios.event_pending()&&mem.read32(event)==S::Ioctl&&mem.read32(buf)==0xaabbccdd);
    }
    submit(req,S::Ioctl,1,S::EventHook,0,0,buf,32);ack();reply(req,S::Ioctl,S::Invalid);
    assert(ios.signal_event(0x20000));assert(!ios.event_pending());
    reply(event,S::Ioctl,0);assert(mem.read32(buf)==0x20000&&mem.read32(buf+4)==0xa1b2c3d4);
    submit(event,S::Ioctl,1,S::EventHook,0,0,buf,4);ack(true);
    submit(req,S::Ioctl,0,S::Release);ack();
    reply(event,S::Ioctl,0);reply(req,S::Ioctl,0);assert(mem.read32(buf)==0);
    for(bool idle:{false,true}){
        ios.set_idle(idle);submit(req,S::Ioctl,0,S::GetState,0,0,buf,4);ack();reply(req,S::Ioctl,0);
        assert(mem.read32(buf)==uint32_t(idle));
    }
    for(uint32_t a:{0u,req+4u,req+32u,req+60u,0xfffffffdu,8190u}){
        submit(req,S::Ioctl,0,S::GetState,0,0,a,4);ack();reply(req,S::Ioctl,S::Invalid);
    }
    mem.string(path,"/dev/unknown");submit(req,S::Open,0,path,0);ack();reply(req,S::Open,S::NotFound);
    submit(req,S::Ioctl,0,0x2003);ack();reply(req,S::Ioctl,S::Invalid);
    submit(req,S::Close,1);ack();reply(req,S::Close,0);
    submit(req,S::Close,1);ack();reply(req,S::Close,S::Invalid);
    mem.string(path,"/dev/stm/eventhook");
    for(unsigned i=1;i<S::DescriptorCount;++i){submit(req,S::Open,0,path,0);ack();reply(req,S::Open,int32_t(i));}
    submit(req,S::Open,0,path,0);ack();reply(req,S::Open,S::QueueFull);
    for(uint32_t a:{0u,1u,8160u,8192u,0xffffffe0u}){
        m.write(P,M::PPCMSG,a);m.write(P,M::PPCCTRL,enables|M::X1);
        assert(ios.pump()==S::Pump::InvalidAddress&&m.request_pending());
        assert(!m.ios_request_queued());
        m.write(P,M::PPCCTRL,enables);
    }
    ios.reset();m.reset();assert(!ios.is_open(0,S::Device::Immediate)&&ios.queued_replies()==0&&!ios.event_pending());
    std::cout<<"PASS: native STM open/close, deferred eventhook, release, state, descriptor limits and mailbox transport\n";
}
