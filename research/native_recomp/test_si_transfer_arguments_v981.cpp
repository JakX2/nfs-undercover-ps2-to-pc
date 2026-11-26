#include "wii_si_transfer_arguments_v981.h"
#include <iostream>
#include <map>
#include <stdexcept>
using namespace undercover::wii;
constexpr uint32_t Data=0x80004000u,Slots=0x80005000u,Cmd=0x80006000u,Resp=0x80007000u,Callback=0x80008000u;
struct Mmu{
    std::map<uint32_t,uint8_t> mem;
    uint8_t* get_ptr(uint32_t p){auto i=mem.find(p);return i==mem.end()?nullptr:&i->second;}
    uint8_t read8(uint32_t p){return mem.at(p);}
    uint32_t read32(uint32_t p){uint32_t w=0;for(unsigned i=0;i<4;++i)w=(w<<8)|read8(p+i);return w;}
    void write(uint32_t p,uint32_t w){for(unsigned i=0;i<4;++i)mem[p+i]=uint8_t(w>>(24-8*i));}
};
struct Cpu{Mmu mmu;std::array<uint32_t,32> gpr{};uint64_t inst_count=100;};
static void need(bool ok){if(!ok)throw std::runtime_error("V981 arguments");}
int main(){
    unsigned good=0,bad=0;
    for(unsigned f=0;f<16;++f){
        Cpu c;unsigned ch=f%4;
        for(unsigned i=0;i<5;++i)c.mmu.write(Data+4*i,0xffffffffu);
        for(unsigned i=0;i<32;++i)c.mmu.write(Slots+4*i,0);
        c.mmu.write(Cmd,0);c.mmu.write(Resp,0);c.mmu.write(Callback,0x60000000u);
        const std::array<uint32_t,8> request{ch,Cmd,1,Resp,3,Callback,0,3948};
        for(unsigned i=0;i<8;++i){c.gpr[3+i]=request[i];c.mmu.write(Slots+ch*32+4*i,request[i]);}
        if(f==4)c.gpr[3]=4;
        if(f==5)c.gpr[5]=2;
        if(f==6)c.gpr[7]=4;
        if(f==7)c.mmu.mem[Cmd]=1;
        if(f==8)c.mmu.mem.erase(Resp+2);
        if(f==9)c.mmu.write(Data,ch);
        if(f==10)c.gpr[8]=Callback+1;
        if(f==11)c.mmu.write(Slots+32*ch+28,3949);
        if(f==12)c.mmu.mem.erase(Slots+127);
        if(f==13)c.gpr[4]=0xffffffffu;
        if(f==14)c.mmu.mem.erase(Callback+3);
        if(f==15)c.gpr[10]=0;
        const auto before=c.mmu.mem;const auto gp=c.gpr;
        const auto a=inspect_si_transfer_arguments(c,Data,Slots,Callback);
        need(before==c.mmu.mem&&gp==c.gpr);
        if(f==11||f==15)need(a.mismatch_mask==128u&&a.slot_kind==1u&&!a.queue_match&&!a.queued_time_zero);
        if(f<4){need(a.admitted()&&a.channel==ch&&a.packet==request&&a.mismatch_mask==0u&&a.slot_kind==1u&&!a.argument_time_zero&&!a.queued_time_zero);++good;}
        else{need(!a.admitted());++bad;}
    }
    need(good==4&&bad==12);
    for(unsigned ch=0;ch<4;++ch){
        Cpu c;
        for(unsigned i=0;i<5;++i)c.mmu.write(Data+4*i,0xffffffffu);
        for(unsigned i=0;i<32;++i)c.mmu.write(Slots+4*i,0);
        c.mmu.write(Cmd,0);c.mmu.write(Resp,0);c.mmu.write(Callback,0x60000000u);
        const std::array<uint32_t,8> req{ch,Cmd,1,Resp,3,Callback,0,3948};
        for(unsigned i=0;i<8;++i){c.gpr[3+i]=req[i];c.mmu.write(Slots+ch*32+4*i,req[i]);}
        SiQueueHistory hist;need(hist.begin(c,Slots)&&!hist.begin(c,Slots));++c.inst_count;
        need(hist.sample(c)&&hist.sample(c));
        // Register-only mismatch; all eight original queued words remain.
        c.gpr[10]=0;
        auto a=inspect_si_transfer_arguments(c,Data,Slots,Callback);
        auto x=hist.finish(c,a);need(x.valid&&x.initial_mismatch==128u&&x.current_mismatch==128u&&!x.changed&&x.initial_slot_kind==1u&&x.samples==1u);
        // Observe actual sentinel consumption, then restoration. The
        // cumulative change mask is not erased by the restored value.
        c.mmu.write(Slots+32u*ch,0xffffffffu);++c.inst_count;need(hist.sample(c));
        a=inspect_si_transfer_arguments(c,Data,Slots,Callback);x=hist.finish(c,a);
        need(x.valid&&x.initial_mismatch==128u&&x.current_mismatch==129u&&x.changed==1u);
        c.mmu.write(Slots+32u*ch,ch);++c.inst_count;need(hist.sample(c));
        a=inspect_si_transfer_arguments(c,Data,Slots,Callback);x=hist.finish(c,a);
        need(x.valid&&x.current_mismatch==128u&&x.changed==1u&&x.samples==3u);
        Cpu other;need(!hist.sample(other));
        c.mmu.mem.erase(Slots+127);++c.inst_count;need(!hist.sample(c));
    }
    unsigned exact=0,tail=0,rejected=0;
    for(unsigned ch=0;ch<4;++ch)for(unsigned mask=0;mask<256;++mask){
        Cpu c;
        for(unsigned i=0;i<5;++i)c.mmu.write(Data+4*i,0xffffffffu);
        for(unsigned i=0;i<32;++i)c.mmu.write(Slots+4*i,0);
        c.mmu.write(Cmd,0);c.mmu.write(Resp,0);c.mmu.write(Callback,0x60000000u);
        const std::array<uint32_t,8> req{ch,Cmd,1,Resp,3,Callback,0,3948};
        for(unsigned i=0;i<8;++i){c.gpr[3+i]=req[i];c.mmu.write(Slots+32u*ch+4*i,req[i]);}
        SiQueueHistory hist;need(hist.begin(c,Slots));++c.inst_count;
        // Exercise every bitmask with a valid six-argument register set:
        // synthesize mismatching queue words before handler observation.
        if(mask&63u){
            SiTransferArguments a=inspect_si_transfer_arguments(c,Data,Slots,Callback);
            a.queue_match=false;a.mismatch_mask=mask;
            SiQueueHistoryResult proof{mask,mask,0u,1u,1u,true};
            need(!si_transfer_admission(a,&proof));++rejected;continue;
        }
        if(mask&64u)c.gpr[9]^=1u;
        if(mask&128u)c.gpr[10]^=1u;
        const auto a=inspect_si_transfer_arguments(c,Data,Slots,Callback);const auto proof=hist.finish(c,a);
        const auto admitted=si_transfer_admission(a,&proof);
        need(proof.valid&&admitted==(mask?2u:1u));
        if(!mask){++exact;continue;}
        ++tail;
        need(!si_transfer_admission(a));
        for(unsigned f=0;f<8;++f){
            auto q=proof;auto b=a;
            if(f==0)q.valid=false;
            if(f==1)q.changed=128u;
            if(f==2)q.initial_slot_kind=2;
            if(f==3)q.current_mismatch^=64u;
            if(f==4)q.samples=0;
            if(f==5)b.callback_known=false;
            if(f==6)b.idle=false;
            if(f==7)b.type=false;
            need(!si_transfer_admission(b,&q));
        }
    }
    need(exact==4u&&tail==12u&&rejected==1008u);
    std::cout<<"V1040_ARGUMENT_ABI exact=4 tail_only=12 core_refused=1008 invalid_proof_refused=96 original_execution=0\n";
    std::cout<<"V1037_QUEUE_HISTORY channels=4 register_only=4 consumed=4 restored=4 read_only=1 original_execution=0\n";
    std::cout<<"V981_TRANSFER_ARGUMENTS valid=4 refused=12 read_only=1 original_execution=0\n";
}
