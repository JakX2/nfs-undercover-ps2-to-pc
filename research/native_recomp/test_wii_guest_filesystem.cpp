#include "wii_ios_bus.h"
#include <array>
#include <cassert>
#include <iostream>
#include <memory>
#include <string_view>
using namespace undercover::wii;
using B=IosBus;using M=IpcMailbox;using H=HollywoodIrq;using S=StmIos;
struct Ram final:IosMemory{
    std::array<uint8_t,4096> data{};
    bool valid(uint32_t a,uint32_t n)const override{return uint64_t(a)+n<=data.size();}
    uint8_t read8(uint32_t a)const override{return data.at(a);}
    void write8(uint32_t a,uint8_t v)override{data.at(a)=v;}
    void string(uint32_t a,std::string_view v){for(char c:v)write8(a++,uint8_t(c));write8(a,0);}
};
int main(){
    Ram ram;B bus(ram);
    constexpr uint32_t request=0x100,event=0x180,path=0x300,out=0x400,eventout=0x500;
    constexpr uint32_t en=M::IY1|M::IY2;
    auto wr=[&](uint32_t a,uint32_t v){assert(bus.write32(a,v));};
    auto rd=[&](uint32_t a){return bus.read32(a).value();};
    auto clear=[&](uint32_t bit){
        assert(bus.external_irq_level());
        wr(B::IPC+M::PPCCTRL,en|bit);assert(bus.tick()==S::Pump::Busy);
        wr(B::IPC+H::PPC_FLAG,H::IPC_PPC);assert(!bus.external_irq_level());
    };
    auto submit=[&](uint32_t slot,uint32_t cmd,uint32_t fd,uint32_t a=0,uint32_t b=0,
                    uint32_t c=0,uint32_t d=0,uint32_t e=0){
        const std::array<uint32_t,8> words{cmd,0xdeadbeef,fd,a,b,c,d,e};
        for(unsigned i=0;i<words.size();++i)ram.write32(slot+4u*i,words[i]);
        wr(B::IPC+M::PPCMSG,slot);wr(B::IPC+M::PPCCTRL,en|M::X1);
    };
    auto ack=[&](S::Pump p){assert(bus.tick()==p);clear(M::Y2);};
    auto reply=[&](uint32_t slot,uint32_t cmd,int32_t result){
        assert(bus.tick()==S::Pump::Replied&&rd(B::IPC+M::ARMMSG)==slot);
        assert(ram.read32(slot)==S::Reply&&ram.read32(slot+4u)==uint32_t(result)&&ram.read32(slot+8u)==cmd);
        clear(M::Y1);assert(bus.tick()==S::Pump::Idle);
    };
    auto call=[&](uint32_t cmd,uint32_t fd,int32_t result,uint32_t a=0,uint32_t b=0,
                  uint32_t c=0,uint32_t d=0,uint32_t e=0){
        submit(request,cmd,fd,a,b,c,d,e);ack(S::Pump::Ack);reply(request,cmd,result);
    };
    auto open=[&](std::string_view p,uint32_t mode,int32_t expected){
        ram.string(path,p);call(S::Open,0,expected,path,mode);
    };
    wr(B::IPC+H::PPC_MASK,H::IPC_PPC);wr(B::PI_MASK,H::PI_HOLLYWOOD);
    open("/dev/fs",0,S::NotFound); // explicit backend required
    auto files=std::make_shared<GuestFiles>();
    assert(files->add("/shared2/sys/example.bin",{0x10,0x20,0x30,0x40,0x50}));
    assert(files->add("/tmp/empty",{}));
    assert(!files->add("/shared2/sys/example.bin",{0xff}));
    for(const auto p:{"","/","relative","/dev/fs","/dev","/tmp/../other","/tmp/./file",
                      "/tmp//file","/tmp/","/tmp/C:","/tmp/win\\file","/a/b/c/d/e/f/g/h/i"})
        assert(!files->add(p,{1}));
    assert(bus.services().mount_filesystem(files));
    open("/dev/stm/immediate",0,0);open("/dev/stm/eventhook",0,1);
    ram.write32(eventout,0xaabbccddu);submit(event,S::Ioctl,1,S::EventHook,0,0,eventout,4);
    ack(S::Pump::Deferred);assert(bus.services().event_pending());
    open("/dev/fs",0,2);assert(bus.services().is_open(2,S::Device::Fs));
    open("/shared2/sys/example.bin",2,S::FsAccess);
    open("/tmp/missing",1,S::FsMissing);
    open("/tmp/../other",1,S::FsInvalid);
    open("/shared2/sys/example.bin",1,3);open("/shared2/sys/example.bin",1,4);
    // IOS_OpenAsync and IOS_ReadAsync share the ordinary IOS wire request
    // format. Run independent request slots while the STM event remains
    // outstanding, without synthesizing a guest callback or scheduler.
    constexpr uint32_t async_request=0x200;
    ram.string(path,"/shared2/sys/example.bin");
    submit(async_request,S::Open,0,path,1);
    ack(S::Pump::Ack);
    assert(bus.services().event_pending()&&ram.read32(event)==S::Ioctl);
    reply(async_request,S::Open,5);
    assert(bus.services().is_open(5,S::Device::File));
    submit(async_request,S::Read,5,out+24,3);
    ack(S::Pump::Ack);
    reply(async_request,S::Read,3);
    assert(ram.read8(out+24)==0x10u&&ram.read8(out+25)==0x20u&&
           ram.read8(out+26)==0x30u);
    submit(async_request,S::Ioctl,5,S::FileStats,0,0,out+40,8);
    ack(S::Pump::Ack);
    reply(async_request,S::Ioctl,0);
    assert(ram.read32(out+40)==5u&&ram.read32(out+44)==3u);
    submit(async_request,S::Close,5);
    ack(S::Pump::Ack);
    reply(async_request,S::Close,0);
    assert(!bus.services().is_open(5,S::Device::File));
    ram.string(path,"/shared2/sys/not-mounted.bin");
    submit(async_request,S::Open,0,path,1);
    ack(S::Pump::Ack);
    reply(async_request,S::Open,S::FsMissing);
    // System Configuration is an ordinary read-only IOS file, never a
    // special success-only shortcut. A guest-supplied fixture is required.
    ram.string(path,"/shared2/sys/SYSCONF");
    submit(async_request,S::Open,0,path,1);
    ack(S::Pump::Ack);reply(async_request,S::Open,S::FsMissing);
    assert(files->add("/shared2/sys/SYSCONF",{0x53,0x43,0x66,0x67,0x10}));
    submit(async_request,S::Open,0,path,1);
    ack(S::Pump::Ack);reply(async_request,S::Open,5);
    assert(bus.services().is_open(5,S::Device::File));
    submit(async_request,S::Read,5,out+64,8);
    ack(S::Pump::Ack);reply(async_request,S::Read,5);
    constexpr std::array<uint8_t,5> sc_expected{{0x53,0x43,0x66,0x67,0x10}};
    for(unsigned i=0;i<sc_expected.size();++i)
        assert(ram.read8(out+64+i)==sc_expected[i]);
    submit(async_request,S::Close,5);
    ack(S::Pump::Ack);reply(async_request,S::Close,0);
    assert(!bus.services().is_open(5,S::Device::File));
    assert(bus.services().event_pending()&&ram.read32(event)==S::Ioctl&&
           ram.read32(eventout)==0xaabbccddu&&
           bus.services().queued_replies()==0u);
    assert(!bus.services().mount_filesystem({}));
    ram.write32(out,0xa5a5a5a5u);ram.write32(out+4,0x12345678u);
    call(S::Read,3,3,out,3);assert(ram.read32(out)==0x102030a5u);
    call(S::Ioctl,3,0,S::FileStats,0,0,out+8,8);
    assert(ram.read32(out+8)==5u&&ram.read32(out+12)==3u);
    call(S::Read,4,1,out+1,1);assert(ram.read8(out+1)==0x10);
    call(S::Seek,3,1,uint32_t(-2),1);call(S::Read,3,4,out,8);
    assert(ram.read32(out)==0x20304050u&&ram.read32(out+4)==0x12345678u);
    call(S::Read,3,0,out,4);call(S::Read,3,0,0,0);
    call(S::Seek,3,S::FsInvalid,1,2);call(S::Seek,3,S::FsInvalid,uint32_t(-6),2);
    call(S::Seek,3,0,0,0);call(S::Read,3,S::FsInvalid,request+4,2);
    call(S::Read,3,S::FsInvalid,event+4,2);
    call(S::Read,3,S::FsInvalid,eventout,4);
    call(S::Ioctl,3,S::FsInvalid,S::FileStats,0,0,eventout-4,8);
    call(S::Ioctl,0,S::Invalid,S::GetState,0,0,eventout,4);
    call(S::Read,3,S::FsInvalid,4095,2);
    call(S::Read,3,S::FsInvalid,out,0xffffffffu);
    call(S::Ioctl,3,S::FsInvalid,S::FileStats,0,0,request+60,8);
    call(S::Write,3,S::FsAccess,out,1);
    call(S::Ioctl,2,S::FsInvalid,0x9999);
    assert(bus.services().event_pending()&&ram.read32(eventout)==0xaabbccddu);
    for(uint32_t fd=5;fd<18;++fd)open("/tmp/empty",1,int32_t(fd));
    open("/tmp/empty",1,S::FsFull);
    for(uint32_t fd=2;fd<18;++fd)call(S::Close,fd,0);
    assert(bus.services().mount_filesystem({}));open("/dev/fs",0,S::NotFound);
    assert(bus.services().signal_event(0x20000u));reply(event,S::Ioctl,0);
    assert(ram.read32(eventout)==0x20000u&&bus.services().is_open(0,S::Device::Immediate)&&
           bus.services().is_open(1,S::Device::Event));
    bus.reset();assert(!bus.services().is_open(0,S::Device::Immediate));
    std::cout<<"PASS: mounted read-only native guest filesystem, descriptor isolation, file reads, seeks, stats, errors and persistent STM event transport\n";
}
