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
    void string(uint32_t a,std::string_view v){for(char ch:v)write8(a++,uint8_t(ch));write8(a,0);}
};
int main(){
    Ram ram;B bus(ram);
    constexpr uint32_t req=0x100,event=0x180,path=0x300,vec=0x400,input=0x440,out=0x480,eventout=0x500;
    constexpr uint32_t en=M::IY1|M::IY2;
    constexpr uint64_t title=0x0001000041424344ull;
    auto wr=[&](uint32_t a,uint32_t v){assert(bus.write32(a,v));};
    auto clear=[&](uint32_t bit){
        assert(bus.external_irq_level());
        wr(B::IPC+M::PPCCTRL,en|bit);
        assert(bus.tick()==S::Pump::Busy);
        wr(B::IPC+H::PPC_FLAG,H::IPC_PPC);assert(!bus.external_irq_level());
    };
    auto submit=[&](uint32_t addr,uint32_t cmd,uint32_t fd,uint32_t a=0,uint32_t b=0,
                    uint32_t c=0,uint32_t d=0,uint32_t e=0){
        const std::array<uint32_t,8> words{cmd,0xdeadbeef,fd,a,b,c,d,e};
        for(unsigned i=0;i<words.size();++i)ram.write32(addr+4u*i,words[i]);
        wr(B::IPC+M::PPCMSG,addr);wr(B::IPC+M::PPCCTRL,en|M::X1);
    };
    auto reply=[&](uint32_t addr,uint32_t cmd,int32_t expected){
        assert(bus.tick()==S::Pump::Replied);
        assert(bus.read32(B::IPC+M::ARMMSG)==addr&&ram.read32(addr)==S::Reply&&
               ram.read32(addr+4)==uint32_t(expected)&&ram.read32(addr+8)==cmd);
        clear(M::Y1);assert(bus.tick()==S::Pump::Idle);
    };
    auto call=[&](uint32_t cmd,uint32_t fd,int32_t expected,uint32_t a=0,uint32_t b=0,
                  uint32_t c=0,uint32_t d=0,uint32_t e=0){
        submit(req,cmd,fd,a,b,c,d,e);
        assert(bus.tick()==S::Pump::Ack);clear(M::Y2);reply(req,cmd,expected);
    };
    auto open=[&](std::string_view name,int32_t expected){
        ram.string(path,name);call(S::Open,0,expected,path,0);
    };
    wr(B::IPC+H::PPC_MASK,H::IPC_PPC);wr(B::PI_MASK,H::PI_HOLLYWOOD);
    open("/dev/es",S::NotFound);
    assert(!bus.services().mount_title_metadata(0u));
    assert(bus.services().mount_title_metadata(title));
    assert(bus.services().mount_filesystem(std::make_shared<GuestFiles>()));
    open("/dev/stm/immediate",0);open("/dev/stm/eventhook",1);open("/dev/fs",2);open("/dev/es",3);
    assert(bus.services().is_open(3,S::Device::Es));
    assert(!bus.services().mount_title_metadata(title+1u));
    ram.write32(eventout,0x11112222);
    submit(event,S::Ioctl,1,S::EventHook,0,0,eventout,4);
    assert(bus.tick()==S::Pump::Deferred);clear(M::Y2);
    ram.write32(vec,out);ram.write32(vec+4,8);
    ram.write32(out+8,0xaabbccdd);
    call(S::Ioctlv,3,0,S::EsGetTitleId,0,1,vec);
    assert(ram.read32(out)==uint32_t(title>>32)&&ram.read32(out+4)==uint32_t(title));
    assert(ram.read32(out+8)==0xaabbccdd);
    ram.write32(input,ram.read32(out));ram.write32(input+4,ram.read32(out+4));
    ram.write32(vec,input);ram.write32(vec+4,8);
    ram.write32(vec+8,out);ram.write32(vec+12,32);
    for(unsigned i=0;i<32;++i)ram.write8(out+i,0xa5);
    call(S::Ioctlv,3,0,S::EsGetDataDir,1,1,vec);
    constexpr std::string_view expected="/title/00010000/41424344/data";
    for(unsigned i=0;i<expected.size();++i)assert(ram.read8(out+i)==uint8_t(expected[i]));
    assert(ram.read8(out+expected.size())==0u&&ram.read8(out+expected.size()+1)==0xa5u);
    const auto before=ram.data;
    ram.write32(input+4,1);call(S::Ioctlv,3,S::EsInvalid,S::EsGetDataDir,1,1,vec);
    for(unsigned i=0;i<32;++i)assert(ram.read8(out+i)==before[out+i]);
    ram.write32(input+4,uint32_t(title));
    for(uint32_t n:{0u,29u,0xffffffffu}){
        ram.write32(vec+12,n);call(S::Ioctlv,3,S::EsInvalid,S::EsGetDataDir,1,1,vec);
    }
    ram.write32(vec+12,32);
    for(uint32_t bad:{0u,req+4u,event+4u,eventout,vec,input,4090u,0xfffffffcu}){
        ram.write32(vec+8,bad);call(S::Ioctlv,3,S::EsInvalid,S::EsGetDataDir,1,1,vec);
    }
    ram.write32(vec+8,out);
    call(S::Ioctlv,3,S::EsInvalid,S::EsGetDataDir,2,1,vec);
    call(S::Ioctlv,3,S::EsInvalid,S::EsGetDataDir,1,0,vec);
    call(S::Ioctlv,3,S::EsInvalid,0x99,0,0,vec);
    call(S::Ioctl,3,S::EsInvalid,S::EsGetTitleId);
    assert(bus.services().event_pending()&&ram.read32(event)==S::Ioctl&&ram.read32(eventout)==0x11112222);
    call(S::Close,3,0);assert(!bus.services().is_open(3,S::Device::Es));
    assert(bus.services().is_open(2,S::Device::Fs)&&bus.services().mount_title_metadata({}));
    open("/dev/es",S::NotFound);
    // Original SCReloadConfFileAsync may issue a bounded but empty path
    // when optional configuration is absent. Verify failure propagation
    // through real IPC ACK/reply interrupts without inventing a file.
    ram.write32(req+32u,0xa1b2c3d4u);
    ram.string(path,"");
    call(S::Open,0,S::FsInvalid,path,1u);
    ram.string(path,"/shared2/sys/SYSCONF");
    call(S::Open,0,S::FsMissing,path,1u);
    assert(ram.read32(req+32u)==0xa1b2c3d4u);
    assert(bus.services().is_open(0,S::Device::Immediate)&&
           bus.services().is_open(1,S::Device::Event)&&
           bus.services().is_open(2,S::Device::Fs)&&
           !bus.services().is_open(3,S::Device::Es));
    assert(bus.services().event_pending()&&ram.read32(event)==S::Ioctl&&
           ram.read32(eventout)==0x11112222u&&
           bus.services().queued_replies()==0u&&!bus.external_irq_level());
    assert(bus.services().signal_event(0x20000u));reply(event,S::Ioctl,0);
    assert(ram.read32(eventout)==0x20000u&&bus.services().is_open(0,S::Device::Immediate));
    std::cout<<"PASS: explicit read-only native title metadata queries, validated IOS vector lengths and independent deferred STM event and negative SC async file paths\n";
}
