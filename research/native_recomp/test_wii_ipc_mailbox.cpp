#include "wii_ipc_mailbox.h"
#include <cassert>
#include <iostream>
using M=undercover::wii::IpcMailbox;
constexpr auto P=M::Side::Broadway,A=M::Side::Starlet;
int main(){
    M m;
    assert(m.read(P,M::PPCCTRL)==0&&m.read(A,M::ARMCTRL)==0);
    // Every pair of control values, including W1C and independent IRQ enables.
    for(uint32_t p=0;p<64;++p)for(uint32_t a=0;a<64;++a){
        m.reset();m.write(P,M::PPCCTRL,p);m.write(A,M::ARMCTRL,a);
        const bool x1=(p&1)&&!(a&4),x2=(p&8)&&!(a&2),y1=a&1,y2=a&8;
        const uint32_t pr=(x1?1u:0u)|(x2?8u:0u)|(y1?4u:0u)|(y2?2u:0u)|(p&48u);
        const uint32_t ar=(y1?1u:0u)|(y2?8u:0u)|(x1?4u:0u)|(x2?2u:0u)|(a&48u);
        assert(m.read(P,M::PPCCTRL)==pr&&m.read(A,M::ARMCTRL)==ar);
        assert(m.broadway_irq_level()==((y1&&(p&16))||(y2&&(p&32))));
        assert(m.starlet_irq_level()==((x1&&(a&16))||(x2&&(a&32))));
        assert(m.request_pending()==x1&&m.reply_pending()==y1);
    }
    for(uint32_t a=0;a<64;++a)for(uint32_t p=0;p<64;++p){
        m.reset();m.write(A,M::ARMCTRL,a);m.write(P,M::PPCCTRL,p);
        const bool x1=p&1,x2=p&8,y1=(a&1)&&!(p&4),y2=(a&8)&&!(p&2);
        assert(m.read(P,M::PPCCTRL)==((x1?1u:0u)|(x2?8u:0u)|(y1?4u:0u)|(y2?2u:0u)|(p&48u)));
        assert(m.read(A,M::ARMCTRL)==((y1?1u:0u)|(y2?8u:0u)|(x1?4u:0u)|(x2?2u:0u)|(a&48u)));
        assert(m.broadway_irq_level()==((y1&&(p&16))||(y2&&(p&32))));
        assert(m.starlet_irq_level()==((x1&&(a&16))||(x2&&(a&32))));
    }
    // Explicit request -> acknowledge -> reply, no automatic host result.
    m.reset();m.write(P,M::PPCCTRL,M::IY1|M::IY2);m.write(A,M::ARMCTRL,M::IX1);
    m.write(P,M::PPCMSG,0x01234560u);m.write(P,M::PPCCTRL,M::X1|M::IY1|M::IY2);
    assert(m.request_pending()&&m.starlet_irq_level()&&!m.broadway_irq_level());
    assert(m.read(A,M::PPCMSG)==0x01234560u&&!m.reply_pending());
    m.write(A,M::ARMCTRL,M::ARM_X1|M::ARM_Y2|M::IX1);
    assert(!m.request_pending()&&!m.starlet_irq_level()&&m.broadway_irq_level());
    m.write(P,M::PPCCTRL,M::Y2|M::IY1|M::IY2);assert(!m.broadway_irq_level());
    m.write(A,M::ARMMSG,0x01234560u);m.write(A,M::ARMCTRL,M::ARM_Y1|M::IX1);
    assert(m.reply_pending()&&m.broadway_irq_level()&&m.read(P,M::ARMMSG)==0x01234560u);
    m.write(P,M::PPCCTRL,M::Y1|M::IY1|M::IY2);assert(!m.reply_pending()&&!m.broadway_irq_level());
    const auto before=m.read(A,M::ARMCTRL);
    for(auto off:{1u,3u,12u,16u,0xffffffffu}){
        bool rd=false,wr=false;
        try{(void)m.read(P,off);}catch(const std::out_of_range&){rd=true;}
        try{m.write(P,off,0xffffffffu);}catch(const std::out_of_range&){wr=true;}
        assert(rd&&wr&&m.read(A,M::ARMCTRL)==before);
    }
    m.write(P,M::PPCCTRL,0xffffffc0u);assert(m.read(P,M::PPCCTRL)==0u);
    // An X1 assertion captures an IOS intake event independently from the
    // writable Broadway flag. A later X1=0 and PPCMSG overwrite must not
    // discard or redirect that single queued request.
    m.reset();
    m.write(P,M::PPCMSG,0x00000100u);
    m.write(P,M::PPCCTRL,M::X1|M::IY1|M::IY2);
    assert(m.request_pending()&&m.ios_request_queued()&&
           m.ios_request_address()==0x00000100u);
    m.write(P,M::PPCCTRL,M::IY1|M::IY2);
    assert(!m.request_pending()&&m.ios_request_queued()&&
           m.ios_request_address()==0x00000100u);
    m.write(P,M::PPCMSG,0x00000180u);
    m.write(P,M::PPCCTRL,M::X1|M::IY1|M::IY2);
    assert(m.request_pending()&&m.ios_request_queued()&&
           m.ios_request_address()==0x00000100u);
    m.write(A,M::ARMCTRL,M::ARM_X1|M::ARM_Y2);
    assert(!m.request_pending()&&!m.ios_request_queued());
    m.write(P,M::PPCCTRL,M::Y2|M::IY1|M::IY2);
    m.write(P,M::PPCCTRL,M::X1|M::IY1|M::IY2);
    assert(m.ios_request_queued()&&m.ios_request_address()==0x00000180u);
    m.reset();
    assert(!m.ios_request_queued()&&m.ios_request_address()==0u);
    m.reset();assert(m.read(P,M::PPCMSG)==0u&&m.read(P,M::ARMMSG)==0u&&!m.broadway_irq_level()&&!m.starlet_irq_level());
    std::cout<<"PASS: 8192 exhaustive asymmetric mailbox flag cases and request/ack/reply/invalid-access checks\n";
}
