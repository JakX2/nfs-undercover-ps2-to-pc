#include "wii_post_ack_submit_join_v1251.h"
#include <iostream>
#include <stdexcept>
using namespace undercover::wii;
using M=IpcMailbox;using H=HollywoodIrq;using J=PostAckSubmitJoin;
static void need(bool b){if(!b)throw std::runtime_error("V1254 submission control");}
int main(){
    unsigned accepted=0,refused=0;
    for(uint32_t before:{M::IY2,M::IY1|M::IY2,M::IY2|M::X2,M::IY1|M::IY2|M::X2})
    for(uint32_t v=0;v<128u;++v){
        constexpr auto en=M::IY1|M::IY2;
        const bool ok=v<64u&&(v&M::X1)&&(v&en)==(before&en);
        auto expected=J::submission_control(before,v);
        need(bool(expected)==ok);
        if(!ok){++refused;continue;}
        std::array<uint8_t,4096> m1{},m2{};
        std::atomic<uint32_t> cause{0},mask{H::PI_HOLLYWOOD};
        NativeIosTransport host(m1,m2,cause,mask);
        need(host.write32(IosBus::IPC+H::PPC_MASK,H::IPC_PPC));
        need(host.write32(IosBus::IPC+M::PPCCTRL,before));
        need(host.write32(IosBus::IPC+M::PPCMSG,0x100u));
        need(host.write32(IosBus::IPC+M::PPCCTRL,v));
        const auto s=host.cold_ipc_snapshot();
        need(s.control==*expected&&s.queued&&s.ppc==0x100u&&!s.steps&&!s.replies&&!cause.load());
        ++accepted;
    }
    need(accepted==32&&refused==480);
    for(uint32_t b:{0u,M::IY2|M::X1,M::IY2|M::Y1,M::IY2|M::Y2})
        need(!J::submission_control(b,M::IY2|M::X1));
    std::cout<<"V1254_SUBMIT_CONTROL accepted=32 refused=484 exact_native_mailbox=1 original_execution=0\n";
}
